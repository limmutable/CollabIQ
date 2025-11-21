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

logger = logging.getLogger(__name__)

class DaemonController:
    def __init__(self, interval_minutes: int = 15):
        self.settings = get_settings()
        self.state_manager = StateManager(Path("data/daemon/state.json"))
        self.scheduler = Scheduler(interval_minutes * 60)
        
        # Initialize components
        self.receiver = GmailReceiver(
            credentials_path=self.settings.get_gmail_credentials_path(),
            token_path=self.settings.gmail_token_path,
            raw_email_dir=self.settings.raw_email_dir,
        )
        self.normalizer = ContentNormalizer()
        
        # Initialize Orchestrator
        # Assuming config exists or we create one
        from src.llm_orchestrator.types import OrchestrationConfig
        orch_config = OrchestrationConfig(
            default_strategy="failover", # Or use setting
            provider_priority=["gemini", "claude", "openai"]
        )
        self.orchestrator = LLMOrchestrator.from_config(orch_config)
        self.summary_enhancer = SummaryEnhancer(self.orchestrator)
        
        self.notion_integrator = NotionIntegrator(
            api_key=self.settings.get_notion_api_key()
        )
        self.writer = NotionWriter(
            notion_integrator=self.notion_integrator,
            collabiq_db_id=self.settings.get_notion_collabiq_db_id(),
            companies_db_id=self.settings.get_notion_companies_db_id(),
            duplicate_behavior=self.settings.duplicate_behavior
        )

    def run(self):
        self.scheduler.run_loop(self.process_cycle)

    def process_cycle(self):
        state = self.state_manager.load_state()
        state.current_status = "running"
        state.last_check_timestamp = datetime.now()
        self.state_manager.save_state(state)

        try:
            self.receiver.connect()
            # Fetch emails since last check or default
            # For simplicity, just fetch recent unread or use internal tracker of receiver
            emails = self.receiver.fetch_emails(max_emails=10) # Adjustable limit
            
            processed_count = 0
            for raw_email in emails:
                if self.receiver.is_duplicate(raw_email.metadata.message_id):
                    continue
                
                # Clean
                cleaned_email = self.normalizer.process_raw_email(raw_email)
                
                # Extract & Summarize
                # 1. Basic extraction
                extracted = self.orchestrator.extract_entities(cleaned_email.cleaned_body)
                
                # 2. Summary enhancement (US2)
                summary = self.summary_enhancer.generate_summary(cleaned_email.cleaned_body)
                extracted.collaboration_summary = summary # Assuming field exists now
                
                # Write
                result = asyncio.run(self.writer.create_collabiq_entry(extracted))
                
                if result.success:
                    self.receiver.mark_processed(raw_email.metadata.message_id)
                    processed_count += 1
                    state.last_processed_email_id = raw_email.metadata.message_id
                else:
                    logger.error(f"Failed to write email {raw_email.metadata.message_id}: {result.error_message}")
                    state.error_count += 1

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
