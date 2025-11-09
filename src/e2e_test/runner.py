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

from e2e_test.error_collector import ErrorCollector
from e2e_test.models import PipelineStage, TestRun
from e2e_test.validators import Validator
from llm_orchestrator.orchestrator import LLMOrchestrator
from llm_orchestrator.types import OrchestrationConfig
from llm_provider.types import ExtractedEntitiesWithClassification

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
        llm_orchestrator: Optional[LLMOrchestrator] = None,
        gemini_adapter=None,  # Deprecated: kept for backward compatibility
        classification_service=None,
        notion_writer=None,
        output_dir: str = "data/e2e_test",
        test_mode: bool = True,
        orchestration_strategy: str = "failover",
        enable_quality_routing: bool = False,
    ):
        """
        Initialize E2ERunner

        Args:
            gmail_receiver: GmailReceiver instance (optional, for email fetching)
            llm_orchestrator: LLMOrchestrator instance (recommended, for multi-LLM support)
            gemini_adapter: DEPRECATED - GeminiAdapter instance (for backward compatibility)
            classification_service: ClassificationService instance (optional)
            notion_writer: NotionWriter instance (optional, for writing)
            output_dir: Base directory for E2E test outputs
            test_mode: If True, runs in test mode
            orchestration_strategy: Strategy for LLM orchestration (failover, consensus, best_match, all_providers)
            enable_quality_routing: Enable quality-based provider selection
        """
        self.gmail_receiver = gmail_receiver

        # Initialize LLM Orchestrator (preferred) or fall back to legacy gemini_adapter
        if llm_orchestrator is not None:
            self.llm_orchestrator = llm_orchestrator
            self.gemini_adapter = None  # Don't use legacy adapter
        elif gemini_adapter is not None:
            # Legacy mode: wrap single adapter in orchestrator for consistency
            logger.warning(
                "Using legacy gemini_adapter parameter. "
                "Consider using llm_orchestrator for multi-LLM support and quality tracking."
            )
            self.gemini_adapter = gemini_adapter
            # Create orchestrator with single provider for consistency
            config = OrchestrationConfig(
                default_strategy=orchestration_strategy,
                provider_priority=["gemini"],
                enable_quality_routing=False,  # Disable for legacy mode
            )
            self.llm_orchestrator = LLMOrchestrator.from_config(config)
        else:
            # No LLM adapter provided - initialize orchestrator with default config
            config = OrchestrationConfig(
                default_strategy=orchestration_strategy,
                provider_priority=["gemini", "claude", "openai"],
                enable_quality_routing=enable_quality_routing,
            )
            self.llm_orchestrator = LLMOrchestrator.from_config(config)
            self.gemini_adapter = None

        self.classification_service = classification_service
        self.notion_writer = notion_writer

        self.output_dir = Path(output_dir)
        self.error_collector = ErrorCollector(output_dir=str(self.output_dir))
        self.validator = Validator()
        self.test_mode = test_mode
        self.orchestration_strategy = orchestration_strategy
        self.enable_quality_routing = enable_quality_routing

        # Ensure output directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "runs").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "reports").mkdir(parents=True, exist_ok=True)

        logger.info(
            "E2ERunner initialized",
            extra={
                "test_mode": test_mode,
                "output_dir": str(self.output_dir),
                "orchestration_strategy": orchestration_strategy,
                "quality_routing_enabled": enable_quality_routing,
                "components_initialized": {
                    "gmail_receiver": gmail_receiver is not None,
                    "llm_orchestrator": self.llm_orchestrator is not None,
                    "gemini_adapter_legacy": gemini_adapter is not None,
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
            "Starting E2E test run",
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
                logger.warning(
                    f"Test run interrupted by user at email {i}/{len(email_ids)}"
                )
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
            "E2E test run completed",
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
            logger.error(f"Failed to process email {email_id}: {e}", exc_info=True)
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

            # Fetch specific email by message ID using Gmail API
            logger.debug(f"Fetching email from Gmail: {email_id}")

            # Use Gmail API directly to fetch single message
            msg_detail = (
                self.gmail_receiver.service.users()
                .messages()
                .get(userId="me", id=email_id, format="full")
                .execute()
            )

            # Parse message to RawEmail
            raw_email = self.gmail_receiver._parse_message(msg_detail)

            # Convert RawEmail to dict format expected by downstream stages
            return {
                "id": raw_email.metadata.message_id,
                "subject": raw_email.metadata.subject,
                "body": raw_email.body,
                "sender": raw_email.metadata.sender,
                "received_at": raw_email.metadata.received_at.isoformat(),
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
        """Extract entities from email using LLM Orchestrator (Stage 2)

        Uses multi-LLM orchestration with the configured strategy (failover,
        consensus, best_match, or all_providers). Automatically tracks quality
        metrics and supports quality-based routing.

        Returns:
            Dictionary with extracted entities, or None on failure
        """
        try:
            if self.llm_orchestrator is None:
                logger.warning("LLM Orchestrator not initialized, using mock data")
                return {
                    "person_in_charge": "Mock Person",
                    "startup_name": "Mock Startup",
                    "partner_org": "Mock Partner",
                    "details": "Mock details",
                    "date": "2025-01-01",
                }

            # Extract entities using LLM Orchestrator with multi-LLM support
            logger.info(
                f"Extracting entities with strategy={self.orchestration_strategy}, "
                f"quality_routing={self.enable_quality_routing}"
            )

            entities = self.llm_orchestrator.extract_entities(
                email_text=email.get("body", ""),
                company_context=None,  # Company context would be provided here
                email_id=email.get("id"),  # Pass actual Gmail message ID
                strategy=self.orchestration_strategy,  # Use configured strategy
            )

            # Log provider selection if available
            if hasattr(entities, 'provider_name'):
                logger.info(f"Entities extracted by provider: {entities.provider_name}")

            # Log quality metrics if quality tracker is available
            if self.llm_orchestrator.quality_tracker:
                try:
                    all_metrics = self.llm_orchestrator.quality_tracker.get_all_metrics()
                    logger.debug(f"Quality metrics available for {len(all_metrics)} providers")
                except Exception as metrics_error:
                    logger.debug(f"Could not retrieve quality metrics: {metrics_error}")

            # Convert ExtractedEntities to dictionary for downstream processing
            entities_dict = {
                "person_in_charge": entities.person_in_charge or "N/A",
                "startup_name": entities.startup_name or "N/A",
                "partner_org": entities.partner_org or "N/A",
                "details": entities.details or "N/A",
                "date": str(entities.date) if entities.date else "2025-01-01",
            }

            logger.info(f"Extracted entities: {entities_dict}")

            # Save extraction to file for later analysis
            self._save_extraction(run_id, email_id, entities_dict, entities)

            return entities_dict

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
                extracted_data = ExtractedEntitiesWithClassification(
                    **classified_entities
                )
            else:
                # Handle ExtractedEntities or other types - convert via model_dump
                data_dict = (
                    classified_entities.model_dump()
                    if hasattr(classified_entities, "model_dump")
                    else classified_entities
                )
                extracted_data = ExtractedEntitiesWithClassification(**data_dict)

            # Call async writer method and retrieve page in single event loop
            async def write_and_retrieve():
                # Write to Notion
                write_result = await self.notion_writer.create_collabiq_entry(
                    extracted_data
                )

                if not write_result.success:
                    return None, write_result.error_message

                # Fetch the created page to get full properties for validation
                page_id = write_result.page_id or write_result.existing_page_id
                if page_id:
                    page_data = await self.notion_writer.notion_integrator.client.client.pages.retrieve(
                        page_id=page_id
                    )
                    return page_data, None
                else:
                    # Duplicate skipped
                    return {
                        "id": "duplicate_skipped",
                        "properties": {},
                        "duplicate": True,
                    }, None

            # Execute both operations in single event loop
            page_data, error_message = asyncio.run(write_and_retrieve())

            if page_data is None:
                logger.error(
                    f"Notion write failed for email {email_id}: {error_message}"
                )
                error = self.error_collector.collect_error(
                    run_id=run_id,
                    email_id=email_id,
                    stage=PipelineStage.WRITE,
                    error_type="NotionWriteError",
                    error_message=error_message or "Unknown error",
                )
                self.error_collector.persist_error(error)
                return None

            logger.info(f"Successfully wrote to Notion, page_id={page_data.get('id')}")
            return page_data

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
        from e2e_test.validators import ValidationResult

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

    def get_quality_metrics_summary(self) -> dict:
        """Get quality metrics summary from LLM Orchestrator.

        Returns:
            Dictionary containing quality metrics for all providers, or empty dict if not available.
        """
        if not self.llm_orchestrator or not self.llm_orchestrator.quality_tracker:
            return {}

        try:
            all_metrics = self.llm_orchestrator.quality_tracker.get_all_metrics()

            summary = {}
            for provider_name, metrics in all_metrics.items():
                if metrics.total_extractions > 0:
                    summary[provider_name] = {
                        "total_extractions": metrics.total_extractions,
                        "avg_confidence": metrics.average_overall_confidence,
                        "field_completeness": metrics.average_field_completeness,
                        "validation_success_rate": metrics.validation_success_rate,
                        "per_field_confidence": metrics.per_field_confidence_averages,
                    }

            return summary
        except Exception as e:
            logger.error(f"Failed to get quality metrics summary: {e}")
            return {}

    def save_quality_metrics_report(self, run_id: str) -> None:
        """Save quality metrics report to a JSON file.

        Args:
            run_id: Test run ID for the report filename
        """
        try:
            metrics_summary = self.get_quality_metrics_summary()

            if not metrics_summary:
                logger.info("No quality metrics available to save")
                return

            report_path = self.output_dir / "reports" / f"{run_id}_quality_metrics.json"
            report_path.parent.mkdir(parents=True, exist_ok=True)

            with report_path.open("w", encoding="utf-8") as f:
                json.dump(metrics_summary, f, indent=2, ensure_ascii=False)

            logger.info(f"Quality metrics report saved to {report_path}")

        except Exception as e:
            logger.error(f"Failed to save quality metrics report: {e}")

    def _save_extraction(self, run_id: str, email_id: str, entities_dict: dict, entities_model):
        """Save extracted entities to file for later analysis.

        Args:
            run_id: Test run ID
            email_id: Email ID
            entities_dict: Dictionary of extracted entities
            entities_model: Original ExtractedEntities model with confidence scores
        """
        extraction_dir = self.output_dir / "extractions" / run_id
        extraction_dir.mkdir(parents=True, exist_ok=True)

        extraction_file = extraction_dir / f"{email_id}.json"

        # Include confidence scores and provider info from model
        extraction_data = {
            **entities_dict,
            "confidence": {
                "person": entities_model.confidence.person,
                "startup": entities_model.confidence.startup,
                "partner": entities_model.confidence.partner,
                "details": entities_model.confidence.details,
                "date": entities_model.confidence.date,
            },
            "provider_name": getattr(entities_model, 'provider_name', 'unknown'),
            "email_id": email_id,
            "extracted_at": str(entities_model.extracted_at) if hasattr(entities_model, 'extracted_at') else None,
        }

        with extraction_file.open("w", encoding="utf-8") as f:
            json.dump(extraction_data, f, indent=2, ensure_ascii=False)

        logger.debug(f"Saved extraction to {extraction_file}")

    def _save_test_run(self, test_run: TestRun):
        """Save test run state to disk"""
        run_file = self.output_dir / "runs" / f"{test_run.run_id}.json"

        test_run_dict = test_run.model_dump(mode="json")

        with run_file.open("w", encoding="utf-8") as f:
            json.dump(test_run_dict, f, indent=2, ensure_ascii=False)

        # Also save quality metrics if available
        self.save_quality_metrics_report(test_run.run_id)

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
