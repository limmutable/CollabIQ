"""Pytest configuration for CollabIQ tests.

This module configures pytest for the CollabIQ test suite, including:
- Python path setup for importing src modules
- Shared fixtures
- Test markers
- E2E testing fixtures (Gmail, Notion)
"""

import sys
import os
from pathlib import Path
import pytest
from typing import Optional

# Add src directory to Python path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))


@pytest.fixture(autouse=True)
def reset_circuit_breakers():
    """Reset all circuit breakers before each test to ensure test isolation."""
    from error_handling.circuit_breaker import (
        gmail_circuit_breaker,
        gemini_circuit_breaker,
        notion_circuit_breaker,
        infisical_circuit_breaker,
        CircuitState,
    )

    # Reset all global circuit breaker instances to CLOSED state
    for cb in [
        gmail_circuit_breaker,
        gemini_circuit_breaker,
        notion_circuit_breaker,
        infisical_circuit_breaker,
    ]:
        cb.state_obj.state = CircuitState.CLOSED
        cb.state_obj.failure_count = 0
        cb.state_obj.success_count = 0
        cb.state_obj.last_failure_time = None
        cb.state_obj.open_timestamp = None

    yield

    # Clean up after test - reset to CLOSED
    for cb in [
        gmail_circuit_breaker,
        gemini_circuit_breaker,
        notion_circuit_breaker,
        infisical_circuit_breaker,
    ]:
        cb.state_obj.state = CircuitState.CLOSED
        cb.state_obj.failure_count = 0
        cb.state_obj.success_count = 0
        cb.state_obj.last_failure_time = None
        cb.state_obj.open_timestamp = None


# =============================================================================
# E2E Testing Fixtures (T014, T015)
# =============================================================================


@pytest.fixture(scope="session")
def gmail_test_account() -> Optional[dict]:
    """Provide Gmail account credentials for E2E testing.

    Uses production credentials from Settings (which loads from .env or Infisical).

    Required Configuration:
        - gmail_credentials_path: Gmail OAuth credentials JSON file
        - gmail_token_path: Gmail OAuth token JSON file
        - EMAIL_ADDRESS: Gmail account email address (env var)

    Returns:
        dict with keys: credentials_path, token_path, email_address
        None if credentials not configured
    """
    from config.settings import get_settings
    from dotenv import load_dotenv

    # Load .env to get EMAIL_ADDRESS (not in Settings)
    load_dotenv()

    settings = get_settings()

    # Get production credentials from Settings
    credentials_path = settings.get_gmail_credentials_path()
    token_path = settings.gmail_token_path
    # EMAIL_ADDRESS is in .env but not in Settings class
    email_address = os.getenv("EMAIL_ADDRESS")

    if not all([credentials_path, token_path, email_address]):
        pytest.skip(
            "Gmail credentials not configured. Required settings:\n"
            "  - GOOGLE_CREDENTIALS_PATH (or GMAIL_CREDENTIALS_PATH)\n"
            "  - GMAIL_TOKEN_PATH\n"
            "  - EMAIL_ADDRESS\n"
            "These can be set in .env file or retrieved from Infisical."
        )
        return None

    # Verify files exist
    if not Path(credentials_path).exists():
        pytest.skip(f"Gmail credentials file not found: {credentials_path}")
        return None

    if not Path(token_path).exists():
        pytest.skip(f"Gmail token file not found: {token_path}")
        return None

    return {
        "credentials_path": str(credentials_path),
        "token_path": str(token_path),
        "email_address": email_address,
    }


@pytest.fixture
def gmail_receiver(gmail_test_account):
    """Initialize GmailReceiver with test account credentials.

    Uses gmail_test_account fixture to get credentials.
    Will skip test if credentials not available.

    Yields:
        GmailReceiver: Configured and connected Gmail receiver instance
    """
    if gmail_test_account is None:
        pytest.skip("Gmail test account not configured")

    from email_receiver.gmail_receiver import GmailReceiver

    receiver = GmailReceiver(
        credentials_path=gmail_test_account["credentials_path"],
        token_path=gmail_test_account["token_path"],
    )

    # Connect to Gmail service before yielding
    receiver.connect()

    yield receiver

    # Teardown: No cleanup needed for Gmail (read-only operations)


@pytest.fixture(scope="session")
def notion_test_database() -> Optional[dict]:
    """Provide Notion database configuration for E2E testing.

    Uses production credentials from Settings (which loads from .env or Infisical).

    Required Configuration:
        - notion_api_key: Notion API token
        - notion_database_id_collabiq: CollabIQ database ID

    Returns:
        dict with keys: token, database_id
        None if not configured
    """
    from config.settings import get_settings

    settings = get_settings()

    # Get production credentials from Settings
    token = settings.get_notion_api_key()
    database_id = settings.get_notion_collabiq_db_id()

    if not all([token, database_id]):
        pytest.skip(
            "Notion database not configured. Required settings:\n"
            "  - NOTION_API_KEY\n"
            "  - NOTION_DATABASE_ID_COLLABIQ\n"
            "These can be set in .env file or retrieved from Infisical."
        )
        return None

    return {
        "token": token,
        "database_id": database_id,
    }


@pytest.fixture
def notion_writer(notion_test_database, notion_integrator):
    """Initialize NotionWriter with test database configuration.

    Uses notion_test_database fixture to get configuration.
    Will skip test if database not configured.

    Yields:
        NotionWriter: Configured Notion writer instance

    Note:
        Cleanup of test entries is handled by the cleanup mechanism (T018).
        Test entries should be marked with test_run_id for identification.
    """
    if notion_test_database is None:
        pytest.skip("Notion test database not configured")

    from notion_integrator.writer import NotionWriter

    # Override database ID for testing
    os.environ["NOTION_DATABASE_ID"] = notion_test_database["database_id"]
    os.environ["NOTION_TOKEN"] = notion_test_database["token"]

    writer = NotionWriter(
        notion_integrator=notion_integrator,
        collabiq_db_id=notion_test_database["database_id"],
    )

    yield writer

    # Teardown: Cleanup is handled by cleanup mechanism (T018)
    # Test entries are marked with test_run_id and cleaned up after test run


@pytest.fixture
def notion_integrator(notion_test_database):
    """Initialize NotionIntegrator with test database configuration.

    Uses notion_test_database fixture to get configuration.
    Will skip test if database not configured.

    Yields:
        NotionIntegrator: Configured Notion integrator instance
    """
    if notion_test_database is None:
        pytest.skip("Notion test database not configured")

    from notion_integrator.integrator import NotionIntegrator

    # Set environment variables for NotionIntegrator
    os.environ["NOTION_API_KEY"] = notion_test_database["token"]

    integrator = NotionIntegrator(api_key=notion_test_database["token"])

    yield integrator


@pytest.fixture
def gemini_adapter():
    """Initialize GeminiAdapter with API key from environment.

    Will skip test if GEMINI_API_KEY not set.

    Yields:
        GeminiAdapter: Configured Gemini adapter instance
    """
    from llm_adapters.gemini_adapter import GeminiAdapter

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        pytest.skip("GEMINI_API_KEY not set")

    yield GeminiAdapter(api_key=api_key)
