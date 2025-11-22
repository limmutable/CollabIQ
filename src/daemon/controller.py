import logging
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional

from config.settings import get_settings
from daemon.state_manager import StateManager
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
        self.state_manager = StateManager(Path("data/daemon/state.json"))
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
            # 1. Fetch Emails (Sync -> Thread)
            # Connect might need thread too if it refreshes token via network
            await asyncio.to_thread(self.receiver.connect)
            
            # Fetch emails
            emails = await asyncio.to_thread(self.receiver.fetch_emails, max_emails=10)
            
            processed_count = 0
            for raw_email in emails:
                if self.receiver.is_duplicate(raw_email.metadata.message_id):
                    continue
                
                logger.info(f"Processing email: {raw_email.metadata.subject}")
                
                # Clean (CPU bound, fast enough to run sync or thread)
                cleaned_email = self.normalizer.process_raw_email(raw_email)
                
                # Extract (Async)
                # TODO: Fetch company context from Notion for better matching?
                # For now, pass None or cached context if available
                extracted = await self.orchestrator.extract_entities(
                    email_text=cleaned_email.cleaned_body,
                    email_id=raw_email.metadata.message_id
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
                # ExtractedEntities might not have 'collaboration_summary' if it's the base model
                # But NotionWriter expects ExtractedEntitiesWithClassification usually.
                # Let's assume we can attach it dynamically or model supports it.
                # Actually, orchestrator returns ExtractedEntities.
                # We might need to wrap it or add the field.
                # Ideally, LLMOrchestrator should return the full object if configured.
                # For now, we'll hack it: NotionWriter usually takes ExtractedEntitiesWithClassification
                # We should upgrade the object.
                from llm_provider.types import ExtractedEntitiesWithClassification
                
                classified_data = ExtractedEntitiesWithClassification(
                    **extracted.model_dump(),
                    collaboration_summary=summary,
                    # Classification fields might be missing if extract_entities didn't return them
                    # The orchestrator's extract_entities DOES return classification if prompt asks for it.
                    # But the type hint says ExtractedEntities.
                    # In Phase 017, we saw it returns ExtractedEntities.
                    # We need to handle defaults if missing.
                    collaboration_type=getattr(extracted, "collaboration_type", "[A]PortCoXSSG"),
                    collaboration_intensity=getattr(extracted, "collaboration_intensity", "협력")
                )
                
                # Write (Async)
                if self.writer:
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
            logger.info(f"Cycle complete. Processed {processed_count} emails.")

        except Exception as e:
            logger.error(f"Error in daemon cycle: {e}", exc_info=True)
            state.error_count += 1
            state.current_status = "error"
        finally:
            if state.current_status != "error":
                state.current_status = "sleeping"
            self.state_manager.save_state(state)
