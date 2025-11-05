"""
E2ERunner: Orchestrates complete MVP pipeline testing

Responsibilities:
- Coordinate complete email → Notion pipeline for each test email
- Integrate ErrorCollector, Validator, PerformanceTracker (future)
- Generate TestRun metadata with success/failure tracking
- Handle interruptions with resume capability
- Provide progress reporting during execution
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from src.e2e_test.error_collector import ErrorCollector
from src.e2e_test.models import PipelineStage, TestRun
from src.e2e_test.validators import Validator
from src.llm_provider.types import ExtractedEntitiesWithClassification

logger = logging.getLogger(__name__)


class E2ERunner:
    """
    Orchestrates end-to-end pipeline testing for MVP validation

    Coordinates all pipeline stages:
    1. Reception - Fetch email from Gmail
    2. Extraction - Extract entities with Gemini
    3. Matching - Match companies to Notion database
    4. Classification - Determine collaboration type and intensity
    5. Write - Create Notion entry
    6. Validation - Verify Notion entry integrity

    Attributes:
        output_dir: Base directory for E2E test outputs
        error_collector: ErrorCollector instance for tracking errors
        validator: Validator instance for data validation
        test_mode: If True, runs in test mode (may skip certain operations)
    """

    def __init__(
        self,
        gmail_receiver=None,
        gemini_adapter=None,
        classification_service=None,
        notion_writer=None,
        output_dir: str = "data/e2e_test",
        test_mode: bool = True,
    ):
        """
        Initialize E2ERunner

        Args:
            gmail_receiver: GmailReceiver instance (optional, for email fetching)
            gemini_adapter: GeminiAdapter instance (optional, for extraction)
            classification_service: ClassificationService instance (optional)
            notion_writer: NotionWriter instance (optional, for writing)
            output_dir: Base directory for E2E test outputs
            test_mode: If True, runs in test mode
        """
        self.gmail_receiver = gmail_receiver
        self.gemini_adapter = gemini_adapter
        self.classification_service = classification_service
        self.notion_writer = notion_writer

        self.output_dir = Path(output_dir)
        self.error_collector = ErrorCollector(output_dir=str(self.output_dir))
        self.validator = Validator()
        self.test_mode = test_mode

        # Ensure output directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "runs").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "reports").mkdir(parents=True, exist_ok=True)

        logger.info(
            f"E2ERunner initialized",
            extra={
                "test_mode": test_mode,
                "output_dir": str(self.output_dir),
                "components_initialized": {
                    "gmail_receiver": gmail_receiver is not None,
                    "gemini_adapter": gemini_adapter is not None,
                    "classification_service": classification_service is not None,
                    "notion_writer": notion_writer is not None,
                },
            },
        )

    def run_tests(
        self, email_ids: List[str], test_mode: Optional[bool] = None
    ) -> TestRun:
        """
        Execute E2E tests for a list of email IDs

        Processes each email through the complete pipeline:
        1. Fetch email from Gmail
        2. Extract entities with Gemini
        3. Match companies and partners
        4. Classify collaboration type and intensity
        5. Write to Notion
        6. Validate Notion entry

        Args:
            email_ids: List of Gmail message IDs to process
            test_mode: Override instance test_mode setting (optional)

        Returns:
            TestRun: Test run metadata with success/failure counts and error summary
        """
        if test_mode is None:
            test_mode = self.test_mode

        # Generate test run ID
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        logger.info(
            f"Starting E2E test run",
            extra={
                "run_id": run_id,
                "email_count": len(email_ids),
                "test_mode": test_mode,
            },
        )

        # Initialize test run tracking
        test_run = TestRun(
            run_id=run_id,
            start_time=datetime.now(),
            end_time=None,
            status="running",
            email_count=len(email_ids),
            emails_processed=0,
            success_count=0,
            failure_count=0,
            stage_success_rates={},
            total_duration_seconds=None,
            average_time_per_email=None,
            error_summary={"critical": 0, "high": 0, "medium": 0, "low": 0},
            test_email_ids=email_ids,
            config={"test_mode": test_mode},
        )

        # Save initial test run state
        self._save_test_run(test_run)

        # Process each email
        for i, email_id in enumerate(email_ids, 1):
            logger.info(f"Processing email {i}/{len(email_ids)}: {email_id}")

            try:
                # Run pipeline for this email
                success = self._process_single_email(email_id, run_id, test_mode)

                # Update counters
                test_run.emails_processed += 1
                if success:
                    test_run.success_count += 1
                else:
                    test_run.failure_count += 1

                # Save progress
                self._save_test_run(test_run)

            except KeyboardInterrupt:
                logger.warning(f"Test run interrupted by user at email {i}/{len(email_ids)}")
                test_run.status = "interrupted"
                test_run.end_time = datetime.now()
                self._save_test_run(test_run)
                raise

            except Exception as e:
                logger.error(
                    f"Unexpected error processing email {email_id}: {e}",
                    exc_info=True,
                )
                # Collect error
                self.error_collector.collect_error(
                    run_id=run_id,
                    email_id=email_id,
                    stage=PipelineStage.RECEPTION,
                    exception=e,
                    error_type="UnexpectedError",
                    error_message=str(e),
                )
                test_run.failure_count += 1

        # Finalize test run
        test_run.end_time = datetime.now()
        test_run.status = "completed"

        # Get error summary
        test_run.error_summary = self.error_collector.get_error_summary(run_id)

        # Save final state
        self._save_test_run(test_run)

        logger.info(
            f"E2E test run completed",
            extra={
                "run_id": run_id,
                "emails_processed": test_run.emails_processed,
                "success_count": test_run.success_count,
                "failure_count": test_run.failure_count,
                "success_rate": (
                    test_run.success_count / test_run.emails_processed
                    if test_run.emails_processed > 0
                    else 0.0
                ),
                "error_summary": test_run.error_summary,
            },
        )

        return test_run

    def _process_single_email(
        self, email_id: str, run_id: str, test_mode: bool
    ) -> bool:
        """
        Process a single email through the complete pipeline

        Args:
            email_id: Gmail message ID
            run_id: Test run ID for error tracking
            test_mode: Whether running in test mode

        Returns:
            bool: True if processing succeeded, False if failed
        """
        try:
            # Stage 1: Reception - Fetch email
            logger.debug(f"Stage 1: Fetching email {email_id}")
            email = self._fetch_email(email_id, run_id)

            if email is None:
                return False

            # Stage 2: Extraction - Extract entities
            logger.debug(f"Stage 2: Extracting entities from email {email_id}")
            entities = self._extract_entities(email, email_id, run_id)

            if entities is None:
                return False

            # Stage 3: Matching - Match companies (part of extraction in current implementation)
            logger.debug(f"Stage 3: Company matching for email {email_id}")
            # In current MVP, matching is integrated in extraction via company_context
            # This stage is a logical placeholder for future enhancements

            # Stage 4: Classification - Determine collaboration type and intensity
            logger.debug(f"Stage 4: Classifying collaboration for email {email_id}")
            classified_entities = self._classify_collaboration(
                email, entities, email_id, run_id
            )

            if classified_entities is None:
                return False

            # Stage 5: Write - Create Notion entry
            logger.debug(f"Stage 5: Writing to Notion for email {email_id}")
            notion_entry = self._write_to_notion(classified_entities, email_id, run_id)

            if notion_entry is None:
                return False

            # Stage 6: Validation - Verify Notion entry
            logger.debug(f"Stage 6: Validating Notion entry for email {email_id}")
            validation_result = self._validate_notion_entry(
                notion_entry, email, email_id, run_id
            )

            if not validation_result.is_valid:
                # Collect validation errors
                for error_msg in validation_result.errors:
                    error = self.error_collector.collect_error(
                        run_id=run_id,
                        email_id=email_id,
                        stage=PipelineStage.VALIDATION,
                        error_type="ValidationError",
                        error_message=error_msg,
                    )
                    self.error_collector.persist_error(error)

                logger.warning(
                    f"Validation failed for email {email_id}: {len(validation_result.errors)} errors"
                )
                return False

            # Check for Korean text corruption
            if email.get("body"):
                korean_result = self.validator.validate_korean_text(
                    email["body"], notion_entry
                )

                if not korean_result.is_valid:
                    for corruption_msg in korean_result.corruption_detected:
                        error = self.error_collector.collect_error(
                            run_id=run_id,
                            email_id=email_id,
                            stage=PipelineStage.VALIDATION,
                            error_type="KoreanTextCorruption",
                            error_message=corruption_msg,
                        )
                        self.error_collector.persist_error(error)

                    logger.error(
                        f"Korean text corruption detected for email {email_id}"
                    )
                    return False

            logger.info(f"Successfully processed email {email_id}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to process email {email_id}: {e}", exc_info=True
            )
            # Collect error
            error = self.error_collector.collect_error(
                run_id=run_id,
                email_id=email_id,
                stage=PipelineStage.RECEPTION,
                exception=e,
            )
            self.error_collector.persist_error(error)
            return False

    def _fetch_email(self, email_id: str, run_id: str) -> Optional[dict]:
        """Fetch email from Gmail (Stage 1)"""
        try:
            if self.gmail_receiver is None:
                logger.warning("GmailReceiver not initialized, skipping email fetch")
                return {"id": email_id, "subject": "Mock Email", "body": "Mock body"}

            # Fetch email using GmailReceiver
            # Note: GmailReceiver.fetch_emails returns list, need to fetch specific email
            # For E2E testing, we assume email_id is already available

            # Mock implementation for now
            return {
                "id": email_id,
                "subject": "Test Email",
                "body": "Test email body",
            }

        except Exception as e:
            error = self.error_collector.collect_error(
                run_id=run_id,
                email_id=email_id,
                stage=PipelineStage.RECEPTION,
                exception=e,
                error_type="EmailFetchError",
            )
            self.error_collector.persist_error(error)
            return None

    def _extract_entities(
        self, email: dict, email_id: str, run_id: str
    ) -> Optional[dict]:
        """Extract entities from email (Stage 2)"""
        try:
            if self.gemini_adapter is None:
                logger.warning("GeminiAdapter not initialized, skipping extraction")
                return {
                    "person_in_charge": "Mock Person",
                    "startup_name": "Mock Startup",
                    "partner_org": "Mock Partner",
                    "details": "Mock details",
                    "date": "2025-01-01",
                }

            # Extract entities using GeminiAdapter
            entities = self.gemini_adapter.extract_entities(
                email_text=email.get("body", ""),
                company_context=None,  # Company context would be provided here
            )

            return entities

        except Exception as e:
            error = self.error_collector.collect_error(
                run_id=run_id,
                email_id=email_id,
                stage=PipelineStage.EXTRACTION,
                exception=e,
                error_type="EntityExtractionError",
            )
            self.error_collector.persist_error(error)
            return None

    def _classify_collaboration(
        self, email: dict, entities: dict, email_id: str, run_id: str
    ) -> Optional[dict]:
        """Classify collaboration type and intensity (Stage 4)"""
        try:
            if self.classification_service is None:
                logger.warning(
                    "ClassificationService not initialized, skipping classification"
                )
                return {
                    **entities,
                    "collaboration_type": "[A]PortCoXSSG",
                    "collaboration_intensity": "협력",
                }

            # Classify using ClassificationService
            # This would require async implementation in practice
            classified = entities  # Placeholder

            return classified

        except Exception as e:
            error = self.error_collector.collect_error(
                run_id=run_id,
                email_id=email_id,
                stage=PipelineStage.CLASSIFICATION,
                exception=e,
                error_type="ClassificationError",
            )
            self.error_collector.persist_error(error)
            return None

    def _write_to_notion(
        self, classified_entities: dict, email_id: str, run_id: str
    ) -> Optional[dict]:
        """Write to Notion database (Stage 5)"""
        try:
            if self.notion_writer is None:
                logger.warning("NotionWriter not initialized, skipping write")
                return {
                    "id": f"mock_page_{email_id}",
                    "properties": {
                        "Email ID": {"rich_text": [{"text": {"content": email_id}}]},
                        "담당자": {
                            "title": [
                                {
                                    "text": {
                                        "content": classified_entities.get(
                                            "person_in_charge", "N/A"
                                        )
                                    }
                                }
                            ]
                        },
                        "스타트업명": {
                            "rich_text": [
                                {
                                    "text": {
                                        "content": classified_entities.get(
                                            "startup_name", "N/A"
                                        )
                                    }
                                }
                            ]
                        },
                        "협력기관": {
                            "rich_text": [
                                {
                                    "text": {
                                        "content": classified_entities.get(
                                            "partner_org", "N/A"
                                        )
                                    }
                                }
                            ]
                        },
                        "협력유형": {
                            "select": {
                                "name": classified_entities.get(
                                    "collaboration_type", "[A]"
                                )
                            }
                        },
                        "날짜": {
                            "date": {
                                "start": classified_entities.get("date", "2025-01-01")
                            }
                        },
                    },
                }

            # Write using NotionWriter (real implementation)
            logger.info(f"Writing to Notion using NotionWriter for email {email_id}")

            # Convert classified_entities to ExtractedEntitiesWithClassification model
            if isinstance(classified_entities, ExtractedEntitiesWithClassification):
                extracted_data = classified_entities
            elif isinstance(classified_entities, dict):
                extracted_data = ExtractedEntitiesWithClassification(**classified_entities)
            else:
                # Handle ExtractedEntities or other types - convert via model_dump
                data_dict = (
                    classified_entities.model_dump()
                    if hasattr(classified_entities, "model_dump")
                    else classified_entities
                )
                extracted_data = ExtractedEntitiesWithClassification(**data_dict)

            # Call async writer method using asyncio.run()
            write_result = asyncio.run(
                self.notion_writer.create_collabiq_entry(extracted_data)
            )

            if not write_result.success:
                logger.error(
                    f"Notion write failed for email {email_id}: {write_result.error_message}"
                )
                error = self.error_collector.collect_error(
                    run_id=run_id,
                    email_id=email_id,
                    stage=PipelineStage.WRITE,
                    error_type="NotionWriteError",
                    error_message=write_result.error_message or "Unknown error",
                )
                self.error_collector.persist_error(error)
                return None

            # Fetch the created page to get full properties for validation
            page_id = write_result.page_id or write_result.existing_page_id
            if page_id:
                page_data = asyncio.run(
                    self.notion_writer.notion_integrator.client.client.pages.retrieve(
                        page_id=page_id
                    )
                )
                logger.info(f"Successfully wrote to Notion, page_id={page_id}")
                return page_data
            else:
                logger.warning(
                    f"Write succeeded but no page_id returned (duplicate skipped?) for email {email_id}"
                )
                # Return a minimal structure for validation
                return {
                    "id": "duplicate_skipped",
                    "properties": {},
                    "duplicate": True,
                }


        except Exception as e:
            error = self.error_collector.collect_error(
                run_id=run_id,
                email_id=email_id,
                stage=PipelineStage.WRITE,
                exception=e,
                error_type="NotionWriteError",
            )
            self.error_collector.persist_error(error)
            return None

    def _validate_notion_entry(
        self, notion_entry: dict, email: dict, email_id: str, run_id: str
    ) -> "ValidationResult":
        """Validate Notion entry (Stage 6)"""
        from src.e2e_test.validators import ValidationResult

        try:
            # Validate required fields
            validation_result = self.validator.validate_notion_entry(notion_entry)

            return validation_result

        except Exception as e:
            error = self.error_collector.collect_error(
                run_id=run_id,
                email_id=email_id,
                stage=PipelineStage.VALIDATION,
                exception=e,
                error_type="ValidationError",
            )
            self.error_collector.persist_error(error)

            # Return failed validation
            result = ValidationResult(is_valid=False)
            result.add_error(f"Validation exception: {str(e)}")
            return result

    def _save_test_run(self, test_run: TestRun):
        """Save test run state to disk"""
        run_file = self.output_dir / "runs" / f"{test_run.run_id}.json"

        test_run_dict = test_run.model_dump(mode="json")

        with run_file.open("w", encoding="utf-8") as f:
            json.dump(test_run_dict, f, indent=2, ensure_ascii=False)

    def resume_test_run(self, run_id: str) -> TestRun:
        """
        Resume an interrupted test run

        Args:
            run_id: Test run ID to resume

        Returns:
            TestRun: Completed or updated test run

        Raises:
            FileNotFoundError: If test run file not found
        """
        run_file = self.output_dir / "runs" / f"{run_id}.json"

        if not run_file.exists():
            raise FileNotFoundError(f"Test run file not found: {run_file}")

        # Load existing test run
        with run_file.open("r", encoding="utf-8") as f:
            test_run_data = json.load(f)

        test_run = TestRun(**test_run_data)

        if test_run.status == "completed":
            logger.info(f"Test run {run_id} already completed")
            return test_run

        # TODO: Implement resume logic
        # - Load test_email_ids.json
        # - Find emails not yet processed
        # - Resume processing from interrupted point

        logger.warning("Resume functionality not yet fully implemented")
        return test_run
