import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from daemon.controller import DaemonController
from llm_provider.types import ExtractedEntities
from models.daemon_state import DaemonProcessState

@pytest.fixture
def mock_settings():
    with patch("daemon.controller.get_settings") as mock:
        mock.return_value.get_gmail_credentials_path.return_value = "mock_creds.json"
        mock.return_value.gmail_token_path = "mock_token.json"
        mock.return_value.raw_email_dir = "data/raw"
        mock.return_value.llm_provider_priority = ["gemini"]
        mock.return_value.get_notion_api_key.return_value = "mock_key"
        mock.return_value.get_notion_collabiq_db_id.return_value = "mock_db"
        mock.return_value.get_notion_companies_db_id.return_value = "mock_companies_db"
        mock.return_value.duplicate_behavior = "skip"
        yield mock

@pytest.fixture
def mock_components():
    with patch("daemon.controller.GmailReceiver") as mock_gmail, \
         patch("daemon.controller.ContentNormalizer") as mock_normalizer, \
         patch("daemon.controller.LLMOrchestrator") as mock_orch, \
         patch("daemon.controller.SummaryEnhancer") as mock_summary, \
         patch("daemon.controller.NotionIntegrator") as mock_notion, \
         patch("daemon.controller.NotionWriter") as mock_writer, \
         patch("daemon.controller.StateManager") as mock_state_manager, \
         patch("daemon.controller.Scheduler") as mock_scheduler:
        
        # Setup async mocks
        mock_orch.from_config.return_value.extract_entities = AsyncMock()
        mock_summary.return_value.generate_summary = AsyncMock()
        mock_writer.return_value.create_collabiq_entry = AsyncMock()
        
        # Setup state manager mock to return a REAL state object
        # This ensures += operations work correctly
        real_state = DaemonProcessState()
        mock_state_manager.return_value.load_state.return_value = real_state
        
        yield {
            "gmail": mock_gmail,
            "normalizer": mock_normalizer,
            "orch": mock_orch,
            "summary": mock_summary,
            "notion": mock_notion,
            "writer": mock_writer,
            "state": mock_state_manager,
            "scheduler": mock_scheduler,
            "real_state": real_state
        }

def test_daemon_init(mock_settings, mock_components):
    """Test DaemonController initialization"""
    controller = DaemonController(interval_minutes=30)
    
    assert controller.scheduler is not None
    assert controller.receiver is not None
    assert controller.orchestrator is not None
    assert controller.writer is not None
    
    mock_components["state"].assert_called_once()
    # Check scheduler interval (30 * 60 = 1800)
    mock_components["scheduler"].assert_called_with(1800)

@pytest.mark.asyncio
async def test_process_cycle_success(mock_settings, mock_components):
    """Test a successful processing cycle"""
    controller = DaemonController()
    
    # Setup mock data
    mock_raw_email = MagicMock()
    mock_raw_email.metadata.message_id = "msg_123"
    mock_raw_email.metadata.subject = "Test Email"
    
    mock_components["gmail"].return_value.fetch_emails.return_value = [mock_raw_email]
    mock_components["gmail"].return_value.is_duplicate.return_value = False
    
    mock_cleaned = MagicMock()
    mock_cleaned.cleaned_body = "Cleaned body"
    mock_components["normalizer"].return_value.process_raw_email.return_value = mock_cleaned
    
    # Setup extraction result with VALID data for Pydantic
    mock_extracted = MagicMock(spec=ExtractedEntities)
    mock_extracted.model_dump.return_value = {
        "person_in_charge": "Test Person",
        "startup_name": "Test Startup",
        "partner_org": "Test Org",
        "details": "Details",
        "date": "2025-01-01",
        "email_id": "msg_123",
        "confidence": {
            "person": 0.9, "startup": 0.9, "partner": 0.9, 
            "details": 0.9, "date": 0.9
        }
    }
    # Mock attributes for getattr check
    mock_extracted.collaboration_type = "[A]PortCoXSSG"
    mock_extracted.collaboration_intensity = "협력"
    
    mock_components["orch"].from_config.return_value.extract_entities.return_value = mock_extracted
    # Summary must be > 50 chars
    mock_components["summary"].return_value.generate_summary.return_value = "Summary that is definitely long enough to pass the fifty character validation requirement."
    
    mock_components["writer"].return_value.create_collabiq_entry.return_value.success = True
    
    # Run cycle
    await controller.process_cycle()
    
    # Verification
    # connect is called in to_thread, tricky to assert strictly with mock_components if it's just a method
    # But fetch_emails is definitely called
    mock_components["gmail"].return_value.fetch_emails.assert_called()
    
    mock_components["orch"].from_config.return_value.extract_entities.assert_awaited()
    mock_components["writer"].return_value.create_collabiq_entry.assert_awaited()
    mock_components["gmail"].return_value.mark_processed.assert_called_with("msg_123")
    
    # State updates (check the real object)
    state = mock_components["real_state"]
    assert state.emails_processed_count == 1
    assert state.total_processing_cycles == 1

@pytest.mark.asyncio
async def test_process_cycle_error_handling(mock_settings, mock_components):
    """Test error handling in processing cycle"""
    controller = DaemonController()
    
    # Gmail raises exception
    mock_components["gmail"].return_value.fetch_emails.side_effect = Exception("Gmail error")
    
    await controller.process_cycle()
    
    # State updates
    state = mock_components["real_state"]
    assert state.current_status == "error"
    assert state.error_count == 1