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
    """Provide test Gmail account credentials for E2E testing.

    Checks environment variables for test Gmail configuration.
    Falls back to production credentials if test credentials not configured.

    Priority order:
    1. TEST_GMAIL_* (dedicated test account)
    2. GOOGLE_CREDENTIALS_PATH / GMAIL_TOKEN_PATH (production account)

    Required Environment Variables:
        TEST_GMAIL_CREDENTIALS_PATH: Path to Gmail OAuth credentials JSON (optional)
        TEST_GMAIL_TOKEN_PATH: Path to Gmail OAuth token JSON (optional)
        TEST_GMAIL_ADDRESS: Email address of test account (optional)

        OR (fallback to production):
        GOOGLE_CREDENTIALS_PATH or GMAIL_CREDENTIALS_PATH: Production credentials
        GMAIL_TOKEN_PATH: Production token
        EMAIL_ADDRESS: Production email address

    Returns:
        dict with keys: credentials_path, token_path, email_address, is_production
        None if credentials not configured
    """
    # Try dedicated test credentials first
    credentials_path = os.getenv("TEST_GMAIL_CREDENTIALS_PATH")
    token_path = os.getenv("TEST_GMAIL_TOKEN_PATH")
    email_address = os.getenv("TEST_GMAIL_ADDRESS")
    is_production = False

    # Fallback to production credentials if test credentials not available
    if not all([credentials_path, token_path, email_address]):
        credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH") or os.getenv("GMAIL_CREDENTIALS_PATH")
        token_path = os.getenv("GMAIL_TOKEN_PATH")
        email_address = os.getenv("EMAIL_ADDRESS")
        is_production = True

    if not all([credentials_path, token_path, email_address]):
        pytest.skip(
            "Gmail credentials not configured. Set either:\n"
            "  Test account: TEST_GMAIL_CREDENTIALS_PATH, TEST_GMAIL_TOKEN_PATH, TEST_GMAIL_ADDRESS\n"
            "  OR Production: GOOGLE_CREDENTIALS_PATH, GMAIL_TOKEN_PATH, EMAIL_ADDRESS"
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
        "is_production": is_production,
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
    """Provide test Notion database configuration for E2E testing.

    Checks environment variables for test Notion database.
    Falls back to production database if test database not configured.

    Priority order:
    1. TEST_NOTION_* (dedicated test database)
    2. NOTION_API_KEY / NOTION_DATABASE_ID_COLLABIQ (production database)

    Required Environment Variables:
        TEST_NOTION_TOKEN: Notion API token for testing (optional)
        TEST_NOTION_DATABASE_ID: ID of test database for E2E tests (optional)

        OR (fallback to production):
        NOTION_API_KEY: Production Notion token
        NOTION_DATABASE_ID_COLLABIQ: Production CollabIQ database ID

    Returns:
        dict with keys: token, database_id, is_production
        None if not configured
    """
    # Try dedicated test database first
    token = os.getenv("TEST_NOTION_TOKEN")
    database_id = os.getenv("TEST_NOTION_DATABASE_ID")
    is_production = False

    # Fallback to production database if test database not available
    if not all([token, database_id]):
        token = os.getenv("NOTION_API_KEY")
        database_id = os.getenv("NOTION_DATABASE_ID_COLLABIQ")
        is_production = True

    if not all([token, database_id]):
        pytest.skip(
            "Notion database not configured. Set either:\n"
            "  Test database: TEST_NOTION_TOKEN, TEST_NOTION_DATABASE_ID\n"
            "  OR Production: NOTION_API_KEY, NOTION_DATABASE_ID_COLLABIQ"
        )
        return None

    return {
        "token": token,
        "database_id": database_id,
        "is_production": is_production,
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
