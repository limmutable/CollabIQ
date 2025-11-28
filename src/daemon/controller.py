import logging
import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from config.settings import get_settings
from daemon.state_manager import StateManager
from daemon.gcs_state_manager import GCSStateManager
from daemon.scheduler import Scheduler
from email_receiver.gmail_receiver import GmailReceiver
from content_normalizer.normalizer import ContentNormalizer
from llm_orchestrator.orchestrator import LLMOrchestrator
from llm_orchestrator.summary_enhancer import SummaryEnhancer
from notion_integrator.writer import NotionWriter
from notion_integrator.integrator import NotionIntegrator
from llm_orchestrator.types import OrchestrationConfig

logger = logging.getLogger(__name__)

class DaemonController:
    def __init__(self, interval_minutes: int = 15):
        self.settings = get_settings()

        # Use GCS state manager if bucket is configured (for Cloud Run persistence)
        gcs_bucket = os.getenv("GCS_STATE_BUCKET")
        if gcs_bucket:
            self.state_manager = GCSStateManager(
                bucket_name=gcs_bucket,
                blob_name="daemon/state.json",
                local_fallback_path=Path("data/daemon/state.json")
            )
            logger.info(f"Using GCS state manager with bucket: {gcs_bucket}")
        else:
            self.state_manager = StateManager(Path("data/daemon/state.json"))
            logger.info("Using local state manager")

        self.scheduler = Scheduler(interval_minutes * 60)
        
        # Initialize components
        # GmailReceiver is synchronous
        self.receiver = GmailReceiver(
            credentials_path=self.settings.get_gmail_credentials_path(),
            token_path=self.settings.gmail_token_path,
            raw_email_dir=self.settings.raw_email_dir,
        )
        self.normalizer = ContentNormalizer()
        
        # Initialize Orchestrator
        orch_config = OrchestrationConfig(
            default_strategy="failover",
            provider_priority=self.settings.llm_provider_priority or ["gemini", "claude", "openai"]
        )
        self.orchestrator = LLMOrchestrator.from_config(orch_config)
        self.summary_enhancer = SummaryEnhancer(self.orchestrator)
        
        # Notion components (clients handle async internally, but init is sync)
        self.notion_integrator = NotionIntegrator(
            api_key=self.settings.get_notion_api_key()
        )
        
        collabiq_db = self.settings.get_notion_collabiq_db_id()
        if not collabiq_db:
            logger.warning("Notion CollabIQ DB ID not set, writer disabled")
            self.writer = None
        else:
            self.writer = NotionWriter(
                notion_integrator=self.notion_integrator,
                collabiq_db_id=collabiq_db,
                companies_db_id=self.settings.get_notion_companies_db_id(),
                duplicate_behavior=self.settings.duplicate_behavior
            )

    def run(self):
        """Entry point for the daemon"""
        try:
            asyncio.run(self.scheduler.run_loop_async(self.process_cycle))
        except KeyboardInterrupt:
            logger.info("Daemon interrupted")

    async def process_cycle(self):
        """Async processing cycle"""
        state = self.state_manager.load_state()
        state.current_status = "running"
        state.last_check_timestamp = datetime.now()
        self.state_manager.save_state(state)

        try:
            # 0. Fetch Company Context (Cached)
            company_context = None
            companies_db = self.settings.get_notion_companies_db_id()
            if companies_db:
                try:
                    # Use format_for_llm to get markdown list of existing companies
                    formatted = await self.notion_integrator.format_for_llm(
                        database_id=companies_db, 
                        use_cache=True
                    )
                    company_context = formatted.summary_markdown
                    logger.info(f"Loaded company context ({formatted.metadata.total_companies} companies)")
                except Exception as e:
                    logger.warning(f"Failed to fetch company context: {e}")

            # 1. Fetch Emails (Sync -> Thread)
            await asyncio.to_thread(self.receiver.connect)

            # Fetch only NEW emails since last successful run
            # This prevents re-processing emails on subsequent runs
            since_timestamp = state.last_successful_fetch_timestamp
            fetch_start_time = datetime.now()

            if since_timestamp:
                logger.info(f"Fetching emails since {since_timestamp.isoformat()}")
            else:
                logger.info("No previous run timestamp found, fetching recent emails")

            emails = await asyncio.to_thread(
                self.receiver.fetch_emails,
                since=since_timestamp,
                max_emails=10
            )
            
            processed_count = 0
            for raw_email in emails:
                if self.receiver.is_duplicate(raw_email.metadata.message_id):
                    continue
                
                logger.info(f"Processing email: {raw_email.metadata.subject}")

                # 1.5 Early Duplicate Check in Notion
                # Avoid expensive LLM calls if entry already exists
                if self.writer:
                    try:
                        existing_id = await self.writer.check_duplicate(raw_email.metadata.message_id)
                        if existing_id:
                            logger.info(f"Duplicate found in Notion (page_id={existing_id}). Skipping processing.")
                            self.receiver.mark_processed(raw_email.metadata.message_id)
                            processed_count += 1
                            continue
                    except Exception as e:
                        logger.warning(f"Failed to check Notion duplicate: {e}")
                
                # Clean (CPU bound, fast enough to run sync or thread)
                cleaned_email = self.normalizer.process_raw_email(raw_email)
                
                # Extract (Async)
                extracted = await self.orchestrator.extract_entities(
                    email_text=cleaned_email.cleaned_body,
                    email_id=raw_email.metadata.message_id,
                    company_context=company_context  # Pass context for better matching
                )
                
                if not extracted:
                    logger.error(f"Failed to extract entities for {raw_email.metadata.message_id}")
                    state.error_count += 1
                    continue

                # Summarize (Async)
                try:
                    summary = await self.summary_enhancer.generate_summary(cleaned_email.cleaned_body)
                except Exception as e:
                    logger.warning(f"Summary generation failed: {e}")
                    summary = "[Summary unavailable due to error.]"

                # Ensure summary meets minimum length requirements (50 chars)
                if not summary or len(summary) < 50:
                    summary = "[Summary unavailable due to content policy, generation error, or insufficient length for validation requirements.]"

                # Inject summary into extracted entities (requires field existence)
                from llm_provider.types import ExtractedEntitiesWithClassification
                
                classified_data = ExtractedEntitiesWithClassification(
                    **extracted.model_dump(),
                    collaboration_summary=summary,
                    # Classification fields might be missing if extract_entities didn't return them
                    collaboration_type=getattr(extracted, "collaboration_type", "[A]PortCoXSSG"),
                    collaboration_intensity=getattr(extracted, "collaboration_intensity", "협력")
                )
                
                # Write (Async)
                if self.writer:
                    # Note: writer.create_collabiq_entry also checks duplicates, 
                    # but we did it early to save LLM costs.
                    result = await self.writer.create_collabiq_entry(classified_data)
                    
                    if result.success:
                        self.receiver.mark_processed(raw_email.metadata.message_id)
                        processed_count += 1
                        state.last_processed_email_id = raw_email.metadata.message_id
                    else:
                        logger.error(f"Failed to write email {raw_email.metadata.message_id}: {result.error_message}")
                        state.error_count += 1
                else:
                    logger.warning("Writer disabled, skipping Notion write")

            state.emails_processed_count += processed_count
            state.total_processing_cycles += 1

            # Update the fetch timestamp ONLY on successful completion
            # This ensures we don't skip emails if there was an error mid-cycle
            state.last_successful_fetch_timestamp = fetch_start_time

            logger.info(f"Cycle complete. Processed {processed_count} emails. Next fetch will start from {fetch_start_time.isoformat()}")

        except Exception as e:
            logger.error(f"Error in daemon cycle: {e}", exc_info=True)
            state.error_count += 1
            state.current_status = "error"
        finally:
            if state.current_status != "error":
                state.current_status = "sleeping"
            self.state_manager.save_state(state)
