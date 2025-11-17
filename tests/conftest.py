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
    for cb in [gmail_circuit_breaker, gemini_circuit_breaker, notion_circuit_breaker, infisical_circuit_breaker]:
        cb.state_obj.state = CircuitState.CLOSED
        cb.state_obj.failure_count = 0
        cb.state_obj.success_count = 0
        cb.state_obj.last_failure_time = None
        cb.state_obj.open_timestamp = None

    yield

    # Clean up after test - reset to CLOSED
    for cb in [gmail_circuit_breaker, gemini_circuit_breaker, notion_circuit_breaker, infisical_circuit_breaker]:
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

    Uses production credentials from environment variables or Infisical.

    Required Environment Variables:
        GOOGLE_CREDENTIALS_PATH or GMAIL_CREDENTIALS_PATH: Gmail OAuth credentials JSON
        GMAIL_TOKEN_PATH: Gmail OAuth token JSON
        EMAIL_ADDRESS: Gmail account email address

    Returns:
        dict with keys: credentials_path, token_path, email_address
        None if credentials not configured
    """
    # Get production credentials
    credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH") or os.getenv("GMAIL_CREDENTIALS_PATH")
    token_path = os.getenv("GMAIL_TOKEN_PATH")
    email_address = os.getenv("EMAIL_ADDRESS")

    if not all([credentials_path, token_path, email_address]):
        pytest.skip(
            "Gmail credentials not configured. Required environment variables:\n"
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
        "credentials_path": credentials_path,
        "token_path": token_path,
        "email_address": email_address,
    }


@pytest.fixture
def gmail_receiver(gmail_test_account):
    """Initialize GmailReceiver with test account credentials.

    Uses gmail_test_account fixture to get credentials.
    Will skip test if credentials not available.

    Yields:
        GmailReceiver: Configured Gmail receiver instance
    """
    if gmail_test_account is None:
        pytest.skip("Gmail test account not configured")

    from email_receiver.gmail_receiver import GmailReceiver

    receiver = GmailReceiver(
        credentials_path=gmail_test_account["credentials_path"],
        token_path=gmail_test_account["token_path"],
    )

    yield receiver

    # Teardown: No cleanup needed for Gmail (read-only operations)


@pytest.fixture(scope="session")
def notion_test_database() -> Optional[dict]:
    """Provide Notion database configuration for E2E testing.

    Uses production credentials from environment variables or Infisical.

    Required Environment Variables:
        NOTION_API_KEY: Notion API token
        NOTION_DATABASE_ID_COLLABIQ: CollabIQ database ID

    Returns:
        dict with keys: token, database_id
        None if not configured
    """
    # Get production credentials
    token = os.getenv("NOTION_API_KEY")
    database_id = os.getenv("NOTION_DATABASE_ID_COLLABIQ")

    if not all([token, database_id]):
        pytest.skip(
            "Notion database not configured. Required environment variables:\n"
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
def notion_writer(notion_test_database):
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

    writer = NotionWriter()

    yield writer

    # Teardown: Cleanup is handled by cleanup mechanism (T018)
    # Test entries are marked with test_run_id and cleaned up after test run
