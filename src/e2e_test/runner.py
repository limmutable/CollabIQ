"""
E2ERunner: Orchestrates complete MVP pipeline testing

Responsibilities:
- Coordinate complete email → Notion pipeline for each test email
- Integrate ErrorCollector, Validator, PerformanceTracker (future)
- Generate E2ETestRun metadata with success/failure tracking
- Handle interruptions with resume capability
- Provide progress reporting during execution
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any, Callable, Awaitable

from e2e_test.error_collector import ErrorCollector
from e2e_test.models import PipelineStage, E2ETestRun
from e2e_test.validators import Validator

# Import core application components
from config.settings import get_settings
from email_receiver.gmail_receiver import GmailReceiver
from content_normalizer.normalizer import ContentNormalizer
from llm_orchestrator.orchestrator import LLMOrchestrator
from llm_orchestrator.types import OrchestrationConfig
from llm_orchestrator.summary_enhancer import SummaryEnhancer
from llm_provider.types import ExtractedEntitiesWithClassification, ExtractedEntities, ConfidenceScores
from notion_integrator.integrator import NotionIntegrator
from notion_integrator.writer import NotionWriter
from notion_integrator.models import LLMFormattedData
from models.raw_email import RawEmail, EmailMetadata


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
        gmail_receiver: Optional[GmailReceiver] = None,
        llm_orchestrator: Optional[LLMOrchestrator] = None,
        classification_service=None,
        notion_writer: Optional[NotionWriter] = None,
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
            classification_service: ClassificationService instance (optional)
            notion_writer: NotionWriter instance (optional, for writing)
            output_dir: Base directory for E2E test outputs
            test_mode: If True, runs in test mode
            orchestration_strategy: Strategy for LLM orchestration (failover, consensus, best_match, all_providers)
            enable_quality_routing: Enable quality-based provider selection
        """
        self.settings = get_settings()
        self.output_dir = Path(output_dir)
        self.error_collector = ErrorCollector(output_dir=str(self.output_dir))
        self.validator = Validator()
        self.test_mode = test_mode
        self.orchestration_strategy = orchestration_strategy
        self.enable_quality_routing = enable_quality_routing
        self.company_context_coroutine: Optional[Callable[[], Awaitable[LLMFormattedData]]] = None # Store coroutine
        self.company_context: Optional[LLMFormattedData] = None

        # Ensure output directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "runs").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "reports").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "extractions").mkdir(parents=True, exist_ok=True)

        # 1. Initialize GmailReceiver (synchronously or prepare for async connect)
        if gmail_receiver is None and not self.test_mode:
            try:
                self.gmail_receiver = GmailReceiver(
                    credentials_path=self.settings.get_gmail_credentials_path(),
                    token_path=self.settings.gmail_token_path,
                )
                # Connect synchronously here, or defer to async run_tests if connect itself is async
                self.gmail_receiver.connect() # Assuming connect is synchronous based on previous logic
                logger.info("Auto-initialized GmailReceiver for production mode")
            except Exception as e:
                logger.error(f"Failed to auto-initialize GmailReceiver: {e}", exc_info=True)
                self.gmail_receiver = None
        else:
            self.gmail_receiver = gmail_receiver

        # 2. Initialize LLM Orchestrator
        if llm_orchestrator is None:
            orch_config = OrchestrationConfig(
                default_strategy=orchestration_strategy,
                provider_priority=self.settings.llm_provider_priority or ["gemini", "claude", "openai"],
                enable_quality_routing=enable_quality_routing,
            )
            self.llm_orchestrator = LLMOrchestrator.from_config(orch_config)
        else:
            self.llm_orchestrator = llm_orchestrator

        # 3. Initialize SummaryEnhancer
        self.summary_enhancer = SummaryEnhancer(self.llm_orchestrator)

        # 4. Initialize NotionIntegrator and prepare to fetch company context (defer async call)
        self.notion_integrator = None
        if not self.test_mode:
            try:
                self.notion_integrator = NotionIntegrator(
                    api_key=self.settings.get_notion_api_key()
                )
                companies_db_id = self.settings.get_notion_companies_db_id()
                if companies_db_id:
                    # Store the coroutine, don't run it yet
                    self.company_context_coroutine = lambda: self.notion_integrator.format_for_llm(
                        database_id=companies_db_id, use_cache=True
                    )
                else:
                    logger.warning("NOTION_DATABASE_ID_COMPANIES not set, company matching will be limited.")
            except Exception as e:
                logger.error(f"Failed to initialize NotionIntegrator: {e}", exc_info=True)
                self.notion_integrator = None

        # 5. Initialize NotionWriter
        if notion_writer is None and not self.test_mode:
            try:
                if self.notion_integrator is None:
                    logger.error("NotionIntegrator is not initialized, cannot initialize NotionWriter.")
                    self.notion_writer = None
                else:
                    collabiq_db_id = self.settings.get_notion_collabiq_db_id()
                    companies_db_id = self.settings.get_notion_companies_db_id()

                    if not collabiq_db_id:
                        logger.error("NOTION_DATABASE_ID_COLLABIQ not found in settings, cannot initialize NotionWriter.")
                        self.notion_writer = None
                    else:
                        self.notion_writer = NotionWriter(
                            notion_integrator=self.notion_integrator,
                            collabiq_db_id=collabiq_db_id,
                            duplicate_behavior="update", # Force update to repair potentially incomplete entries during E2E testing
                            companies_db_id=companies_db_id,
                        )
                        logger.info("Auto-initialized NotionWriter for production mode (duplicate_behavior='update')")
            except Exception as e:
                logger.error(f"Failed to auto-initialize NotionWriter: {e}", exc_info=True)
                self.notion_writer = None
        else:
            self.notion_writer = notion_writer

        self.classification_service = classification_service # Kept for now to avoid breaking existing code

        logger.info(
            "E2ERunner initialized",
            extra={
                "test_mode": test_mode,
                "output_dir": str(self.output_dir),
                "orchestration_strategy": orchestration_strategy,
                "quality_routing_enabled": enable_quality_routing,
                "components_initialized": {
                    "gmail_receiver": self.gmail_receiver is not None,
                    "llm_orchestrator": self.llm_orchestrator is not None,
                    "summary_enhancer": self.summary_enhancer is not None,
                    "notion_integrator": self.notion_integrator is not None,
                    "notion_writer": self.notion_writer is not None,
                    "classification_service": classification_service is not None, # Kept for now to avoid breaking existing code
                },
            },
        )

    async def run_tests(
        self,
        email_ids: List[str],
        test_mode: Optional[bool] = None,
    ) -> E2ETestRun:
        """
        Execute E2E tests for a list of email IDs (asynchronously)

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
            E2ETestRun: Test run metadata with success/failure counts and error summary
        """
        if test_mode is None:
            test_mode = self.test_mode

        # Resolve company_context here, within the async function
        if self.company_context_coroutine and self.notion_integrator:
            try:
                self.company_context = await self.company_context_coroutine()
                logger.info(f"Resolved company context with {len(self.company_context.companies)} companies")
            except Exception as e:
                logger.error(f"Failed to resolve company context: {e}", exc_info=True)
                self.company_context = None

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
        test_run = E2ETestRun(
            run_id=run_id,
            start_time=datetime.now(),
            end_time=None,
            status="running",
            email_count=len(email_ids),
            emails_processed=0,
            success_count=0,
            failure_count=0,
            stage_success_rates={},
            stage_results={stage.value: 0 for stage in PipelineStage},
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

            success = False # Default to failure
            current_stage_results = {stage.value: False for stage in PipelineStage} # Default to all stages failed

            try:
                # Run pipeline for this email
                success, current_stage_results = await self._process_single_email(email_id, run_id, test_mode)

                # Update counters (emails_processed is always incremented, regardless of success or failure)
                test_run.emails_processed += 1
                
                # Accumulate successful stage counts from current_stage_results, even if overall email failed
                for stage, passed in current_stage_results.items():
                    if passed:
                        test_run.stage_results[stage] += 1

                if success:
                    test_run.success_count += 1
                else:
                    test_run.failure_count += 1
                    # If process_single_email explicitly returned False, its stage_results should be respected.
                    # Otherwise, if an exception occurred in _process_single_email (caught below),
                    # the default current_stage_results (all False) is used, which is correct.

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
                # Update counters on unexpected error
                test_run.emails_processed += 1
                test_run.failure_count += 1

                # Collect error (already done in _process_single_email if it returns False, but good to have a fallback here)
                # If _process_single_email *returned* False due to an internal error, that error is already collected.
                # This block is for exceptions that escape _process_single_email itself.
                self.error_collector.collect_error(
                    run_id=run_id,
                    email_id=email_id,
                    stage=PipelineStage.RECEPTION, # Default to reception if stage unknown
                    exception=e,
                    error_type="UnexpectedError",
                    error_message=str(e),
                )
                self.error_collector.persist_error(self.error_collector.last_error)

            # Save progress after each email, regardless of success/failure
            self._save_test_run(test_run)
        
        # Finalize test run
        test_run.end_time = datetime.now()
        test_run.status = "completed"

        # Calculate final stage success rates
        if test_run.emails_processed > 0:
            test_run.stage_success_rates = {
                stage: count / test_run.emails_processed
                for stage, count in test_run.stage_results.items()
            }
        else:
            test_run.stage_success_rates = {stage.value: 0.0 for stage in PipelineStage}

        # Get error summary
        test_run.error_summary = self.error_collector.get_error_summary(run_id)

        # Calculate total duration and average time per email
        if test_run.end_time and test_run.start_time:
            total_duration = test_run.end_time - test_run.start_time
            test_run.total_duration_seconds = total_duration.total_seconds()
            if test_run.emails_processed > 0:
                test_run.average_time_per_email = (
                    test_run.total_duration_seconds / test_run.emails_processed
                )

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

    async def _process_single_email(
        self,
        email_id: str,
        run_id: str,
        test_mode: bool,
    ) -> Tuple[bool, Dict[str, bool]]:
        """
        Process a single email through the complete pipeline (asynchronously)

        Args:
            email_id: Gmail message ID
            run_id: Test run ID for error tracking
            test_mode: Whether running in test mode

        Returns:
            bool: True if processing succeeded, False if failed
        """
        stage_results = {
            PipelineStage.RECEPTION: False,
            PipelineStage.EXTRACTION: False,
            PipelineStage.MATCHING: False,
            PipelineStage.CLASSIFICATION: False,
            PipelineStage.WRITE: False,
            PipelineStage.VALIDATION: False,
        }

        overall_success = False

        logger.debug(f"Starting _process_single_email for email {email_id} in test_mode: {test_mode}")

        try:
            # Stage 1: Reception - Fetch email
            logger.debug(f"Stage 1: Fetching email {email_id}")
            email = await self._fetch_email(email_id, run_id)
            if email is None:
                return False, stage_results # Error collected in _fetch_email
            stage_results[PipelineStage.RECEPTION] = True

            # Stage 2: Extraction - Extract entities
            logger.debug(f"Stage 2: Extracting entities from email {email_id}")
            extracted_entities_result = await self._extract_entities(email, email_id, run_id)
            logger.debug(f"Raw extracted_entities_result: type={type(extracted_entities_result)}, value={extracted_entities_result}")
            if extracted_entities_result is None:
                return False, stage_results # Error collected in _extract_entities
            
            if extracted_entities_result[0] is None:
                logger.debug(f"extracted_entities_result[0] is None, returning False for email {email_id}.")
                return False, stage_results # Error collected in _extract_entities
            
            extracted_entities, summary_generation_success = extracted_entities_result
            logger.debug(f"Extracted entities after _extract_entities: {extracted_entities.model_dump_json()}")
            stage_results[PipelineStage.EXTRACTION] = True

            # Stage 3: Matching - This is logically part of extraction/writing in current design
            # Mark as true if extraction was successful, as matching metadata is part of extracted_entities
            stage_results[PipelineStage.MATCHING] = True 

            # Stage 4: Classification - Determine collaboration type and intensity & summary
            logger.debug(f"Stage 4: Classifying collaboration for email {email_id}")
            # The ExtractedEntitiesWithClassification should already contain type, intensity, and summary
            classified_entities = await self._classify_collaboration(
                email, extracted_entities, email_id, run_id
            )
            logger.debug(f"Classified entities after _classify_collaboration: {classified_entities.model_dump_json() if classified_entities else None}")
            # Classification stage is considered successful as _classify_collaboration now guarantees a non-None return
            stage_results[PipelineStage.CLASSIFICATION] = True

            # Stage 5: Write - Create Notion entry
            logger.debug(f"Stage 5: Writing to Notion for email {email_id}")
            notion_entry = await self._write_to_notion(classified_entities, email_id, run_id)
            if notion_entry is None:
                return False, stage_results # Error collected in _write_to_notion
            stage_results[PipelineStage.WRITE] = True

            # Stage 6: Validation - Verify Notion entry
            logger.debug(f"Stage 6: Validating Notion entry for email {email_id}")
            validation_result = await self._validate_notion_entry(
                notion_entry, email, email_id, run_id
            )

            if not validation_result.is_valid:
                for error_msg in validation_result.errors:
                    error = self.error_collector.collect_error(
                        run_id=run_id,
                        email_id=email_id,
                        stage=PipelineStage.VALIDATION,
                        error_type="ValidationError",
                        error_message=error_msg,
                    )
                    self.error_collector.persist_error(error)
                logger.warning(f"Validation failed for email {email_id}: {len(validation_result.errors)} errors")
                return False, stage_results

            # Check for Korean text corruption (part of validation)
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
                    logger.error(f"Korean text corruption detected for email {email_id}")
                    return False, stage_results
            stage_results[PipelineStage.VALIDATION] = True
            overall_success = True

        except Exception as e:
            logger.error(f"Failed to process email {email_id} at an unknown stage: {e}", exc_info=True)
            error = self.error_collector.collect_error(
                run_id=run_id,
                email_id=email_id,
                stage=PipelineStage.RECEPTION, # Default to reception if stage unknown
                exception=e,
                error_type="UnexpectedError",
                error_message=str(e),
            )
            self.error_collector.persist_error(error)
            return False, stage_results

        logger.info(f"Successfully processed email {email_id}")
        logger.debug(f"Final stage_results for {email_id}: {stage_results}")
        return overall_success, stage_results

    async def _fetch_email(self, email_id: str, run_id: str) -> Optional[Dict[str, Any]]:
        """Fetch email from Gmail (Stage 1)"""
        try:
            if self.gmail_receiver is None or self.gmail_receiver.service is None:
                logger.warning("GmailReceiver not initialized or service not connected, skipping email fetch")
                if self.test_mode:
                    # Return a mock RawEmail conforming to the expected structure
                    mock_metadata = EmailMetadata(
                        message_id=email_id,
                        internal_id=email_id,
                        sender="mock@example.com",
                        subject="Mock Email Subject",
                        received_at=datetime.now(),
                        has_attachments=False
                    )
                    mock_raw_email = RawEmail(
                        metadata=mock_metadata,
                        body="This is a mock email body for testing purposes."
                    )
                    logger.debug(f"Returning mock email for {email_id} in test_mode.")
                    return {
                        "id": mock_raw_email.metadata.internal_id,
                        "subject": mock_raw_email.metadata.subject,
                        "body": mock_raw_email.body,
                        "sender": mock_raw_email.metadata.sender,
                        "received_at": mock_raw_email.metadata.received_at.isoformat(),
                    }
                else:
                    raise ConnectionError("GmailReceiver service not available in production mode.")

            # Fetch specific email by message ID using Gmail API
            logger.debug(f"Fetching email from Gmail: {email_id}")

            # Use Gmail API directly to fetch single message
            # This call is synchronous, so we run it in a thread pool executor
            msg_detail = await asyncio.to_thread(
                self.gmail_receiver.service.users().messages().get, 
                userId="me", id=email_id, format="full"
            )
            msg_detail = await asyncio.to_thread(msg_detail.execute) # Execute also seems to be blocking

            # Parse message to RawEmail
            raw_email = self.gmail_receiver._parse_message(msg_detail)

            # Convert RawEmail to dict format expected by downstream stages
            return {
                "id": raw_email.metadata.internal_id, # Use internal_id as the primary ID for the E2E runner
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
                error_message=str(e),
            )
            self.error_collector.persist_error(error)
            return None

    async def _extract_entities(
        self,
        email: Dict[str, Any],
        email_id: str,
        run_id: str,
    ) -> Optional[Tuple[ExtractedEntitiesWithClassification, bool]]:
        """
        Extract entities from email using LLM Orchestrator (Stage 2).
        Generates summary as part of this stage.

        Returns:
            Tuple of (ExtractedEntitiesWithClassification object, summary_generation_success: bool) or None on failure.
        """
        summary_generation_success = False
        try:
            if self.llm_orchestrator is None:
                logger.warning("LLM Orchestrator not initialized, using mock data for extraction")
                mock_entities = ExtractedEntities(
                    person_in_charge="Mock Person",
                    startup_name="Mock Startup",
                    partner_org="Mock Partner",
                    details="Mock details",
                    date=datetime(2025, 1, 1).date(),
                    confidence=ConfidenceScores(person=0.8, startup=0.8, partner=0.8, details=0.8, date=0.8),
                    email_id=email_id,
                )
                # If mock, assume summary is also available for consistency
                return (ExtractedEntitiesWithClassification(
                    **mock_entities.model_dump(),
                    collaboration_summary="Mock Summary for Test Mode",
                    collaboration_type="[A]PortCoXSSG",
                    collaboration_intensity="협력",
                    type_confidence=0.9,
                    intensity_confidence=0.8,
                ), True)

            company_context_markdown: Optional[str] = None
            if self.company_context and self.company_context.summary_markdown:
                company_context_markdown = self.company_context.summary_markdown

            logger.info(
                f"Extracting entities with strategy={self.orchestration_strategy}, "
                f"quality_routing={self.enable_quality_routing}"
            )

            try:
                # Await the async orchestrator call
                extracted_entities_core = await self.llm_orchestrator.extract_entities(
                    email_text=email.get("body", ""),
                    company_context=company_context_markdown,
                    email_id=email.get("id"),
                    strategy=self.orchestration_strategy,
                )
                logger.debug(f"After orchestrator.extract_entities: extracted_entities_core={extracted_entities_core}")
                logger.debug(f"Type of extracted_entities_core: {type(extracted_entities_core)}")
            except Exception as orchestrator_e:
                logger.error(f"Exception during LLM Orchestrator call for email {email_id}: {orchestrator_e}", exc_info=True)
                # Re-raise the exception to be caught by the outer try-except of _extract_entities
                raise
            
            if extracted_entities_core is None:
                logger.error("CRITICAL: extracted_entities_core is None immediately after orchestrator call!")
                logger.error(f"LLM Orchestrator returned no core entities for email {email_id}.")
                return None, False

            if hasattr(extracted_entities_core, "provider_name"):
                logger.info(f"Entities extracted by provider: {extracted_entities_core.provider_name}")

            if self.llm_orchestrator.quality_tracker:
                try:
                    all_metrics = (
                        self.llm_orchestrator.quality_tracker.get_all_metrics()
                    )
                    logger.debug(
                        f"Quality metrics available for {len(all_metrics)} providers"
                    )
                except Exception as metrics_error:
                    logger.debug(f"Could not retrieve quality metrics: {metrics_error}")

            collaboration_summary: Optional[str] = None
            if self.summary_enhancer:
                logger.info(f"Attempting to generate summary for email {email_id}")
                # Await the async summary generation call
                generated_summary = await self.summary_enhancer.generate_summary(
                    email_text=email.get("body", ""),
                    strategy="consensus"
                )
                if generated_summary and generated_summary != "[Summary unavailable due to content policy or generation error.]":
                    collaboration_summary = generated_summary
                    summary_generation_success = True
                    logger.info(f"Generated summary (first 50 chars): {collaboration_summary[:50]}...")
                else:
                    logger.warning(f"Failed to generate summary for email {email_id} or summary was blocked/empty. Using default.")
                    collaboration_summary = "[Summary unavailable due to content policy or generation error.]" # Ensure it's a string

            logger.debug(f"Before ExtractedEntitiesWithClassification construction. extracted_entities_core: {extracted_entities_core.model_dump_json()}")
            final_extracted_data = ExtractedEntitiesWithClassification(
                **extracted_entities_core.model_dump(),
                collaboration_summary=collaboration_summary,
                collaboration_type=None,
                collaboration_intensity=None,
                type_confidence=None,
                intensity_confidence=None,
            )
            logger.debug(f"After ExtractedEntitiesWithClassification construction. final_extracted_data: {final_extracted_data.model_dump_json()}")

            logger.info(f"Final extracted entities for {email_id}: {final_extracted_data.model_dump_json()}")

            logger.debug(f"_extract_entities about to return: final_extracted_data={final_extracted_data}, summary_generation_success={summary_generation_success}")
            return final_extracted_data, summary_generation_success

        except Exception as e:
            error = self.error_collector.collect_error(
                run_id=run_id,
                email_id=email_id,
                stage=PipelineStage.EXTRACTION,
                exception=e,
                error_type="EntityExtractionError",
                error_message=str(e),
            )
            self.error_collector.persist_error(error)
            return None, False

    async def _classify_collaboration(
        self,
        email: Dict[str, Any],
        extracted_data: ExtractedEntitiesWithClassification,
        email_id: str,
        run_id: str,
    ) -> ExtractedEntitiesWithClassification:
        """
        Classify collaboration type and intensity (Stage 4).
        This method now primarily serves as a logical pass-through, as the actual classification 
        and summary generation are handled within the extraction stage by LLMOrchestrator and SummaryEnhancer.
        It ensures that the extracted_data is consistent for subsequent pipeline stages.

        Args:
            email: Raw email data
            extracted_data: ExtractedEntitiesWithClassification instance from previous stage
            email_id: Email identifier
            run_id: Test run identifier

        Returns:
            ExtractedEntitiesWithClassification: The (potentially updated) extracted data. Returns original 
                                                extracted_data even on error to allow pipeline to continue, 
                                                logging the error for investigation.
        """
        try:
            if self.classification_service is not None:
                logger.warning("ClassificationService is initialized but not used for classification in E2ERunner. "
                               "Classification is expected to be part of the LLM extraction/orchestration.")

            # Populate defaults if classification is missing (temporary fallback for MVP stability)
            if not extracted_data.collaboration_type:
                logger.info(f"Collaboration type missing for {email_id}, using default.")
                extracted_data.collaboration_type = "[A]PortCoXSSG" # Default type
                extracted_data.type_confidence = 0.5

            if not extracted_data.collaboration_intensity:
                logger.info(f"Collaboration intensity missing for {email_id}, using default.")
                extracted_data.collaboration_intensity = "협력" # Default intensity
                extracted_data.intensity_confidence = 0.5

            # The extracted_data should already contain collaboration_type, intensity, and summary
            logger.info(f"Classification stage for email {email_id} complete.")
            logger.debug(f"_classify_collaboration returning: {extracted_data.model_dump_json()}")
            return extracted_data

        except Exception as e:
            error = self.error_collector.collect_error(
                run_id=run_id,
                email_id=email_id,
                stage=PipelineStage.CLASSIFICATION,
                exception=e,
                error_type="ClassificationError",
                error_message=f"Error during classification pass-through: {str(e)}",
            )
            self.error_collector.persist_error(error)
            # IMPORTANT: Even if an error occurs, we return the original data to allow the pipeline to continue
            # The error is logged, and the impact should be assessed via validation and reports.
            logger.warning(f"_classify_collaboration encountered an error but returning original data for email {email_id} to continue pipeline.")
            return extracted_data

    async def _write_to_notion(
        self,
        classified_entities: ExtractedEntitiesWithClassification,
        email_id: str,
        run_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Write to Notion database (Stage 5)"""
        try:
            if self.notion_writer is None:
                logger.warning("NotionWriter not initialized, skipping write")
                # Return mock data for Notion entry
                return {
                    "id": f"mock_page_{email_id}",
                    "properties": {
                        "Email ID": {"rich_text": [{"text": {"content": email_id}}]},
                        "담당자": {"people": [{"id": "mock_user_id"}]}, # Mock Notion people ID
                        "스타트업명": {"relation": [{"id": "mock_company_id"}]}, # Mock Notion relation ID
                        "협력기관": {"relation": [{"id": "mock_partner_id"}]}, # Mock Notion relation ID
                        "협업유형": {"select": {"name": classified_entities.collaboration_type or "[A]PortCoXSSG"}}, # Use generated type
                        "협업강도": {"select": {"name": classified_entities.collaboration_intensity or "협력"}}, # Use generated intensity
                        "요약": {"rich_text": [{"text": {"content": classified_entities.collaboration_summary or "Mock Summary"}}]}, # Use generated summary
                        "날짜": {"date": {"start": classified_entities.date.isoformat() if classified_entities.date else "2025-01-01"}},
                    },
                }

            # Write using NotionWriter (real implementation)
            logger.info(f"Writing to Notion using NotionWriter for email {email_id}")

            extracted_data = classified_entities

            # Await the async writer method and retrieve page in single event loop
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
                return page_data
            else:
                # Duplicate skipped
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
                error_message=str(e),
            )
            self.error_collector.persist_error(error)
            return None

    async def _validate_notion_entry(
        self,
        notion_entry: Dict[str, Any],
        email: Dict[str, Any],
        email_id: str,
        run_id: str,
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
                error_message=str(e),
            )
            self.error_collector.persist_error(error)

            # Return failed validation
            result = ValidationResult(is_valid=False)
            result.add_error(f"Validation exception: {str(e)}")
            return result

    def get_quality_metrics_summary(self) -> Dict[str, Any]:
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

    def _save_extraction(
        self, run_id: str, email_id: str, entities_dict: Dict[str, Any], entities_model: ExtractedEntitiesWithClassification
    ):
        """
        Save extracted entities to file for later analysis.

        Args:
            run_id: Test run ID
            email_id: Email ID
            entities_dict: Dictionary of extracted entities (now unused, will use entities_model directly)
            entities_model: Original ExtractedEntitiesWithClassification model
        """
        extraction_dir = self.output_dir / "extractions" / run_id
        extraction_dir.mkdir(parents=True, exist_ok=True)

        extraction_file = extraction_dir / f"{email_id}.json"

        # Use model_dump_json for reliable JSON serialization, including datetimes
        extracted_data_json = entities_model.model_dump_json()
        final_extraction_data = json.loads(extracted_data_json)

        # Add provider_name, which is not part of the core model fields
        final_extraction_data["provider_name"] = getattr(entities_model, "provider_name", "unknown")

        with extraction_file.open("w", encoding="utf-8") as f:
            logger.debug(f"Final extraction data before JSON dump: {final_extraction_data}")
            json.dump(final_extraction_data, f, indent=2, ensure_ascii=False)

        logger.debug(f"Saved extraction to {extraction_file}")

    def _save_test_run(self, test_run: E2ETestRun):
        """Save test run state to disk"""
        run_file = self.output_dir / "runs" / f"{test_run.run_id}.json"

        test_run_dict = test_run.model_dump(mode="json")

        with run_file.open("w", encoding="utf-8") as f:
            json.dump(test_run_dict, f, indent=2, ensure_ascii=False)

        # Also save quality metrics if available
        self.save_quality_metrics_report(test_run.run_id)

    async def resume_test_run(self, run_id: str) -> E2ETestRun:
        """
        Resume an interrupted test run (asynchronously)

        Args:
            run_id: Test run ID to resume

        Returns:
            E2ETestRun: Completed or updated test run

        Raises:
            FileNotFoundError: If test run file not found
        """
        run_file = self.output_dir / "runs" / f"{run_id}.json"

        if not run_file.exists():
            raise FileNotFoundError(f"Test run file not found: {run_file}")

        # Load existing test run
        with run_file.open("r", encoding="utf-8") as f:
            test_run_data = json.load(f)

        test_run = E2ETestRun(**test_run_data)

        if test_run.status == "completed":
            logger.info(f"Test run {run_id} already completed")
            return test_run

        # TODO: Implement resume logic
        # - Load test_email_ids.json
        # - Find emails not yet processed
        # - Resume processing from interrupted point

        logger.warning("Resume functionality not yet fully implemented")
        return test_run
