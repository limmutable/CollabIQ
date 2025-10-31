"""
Integration tests for GmailReceiver.

These tests require real Gmail API credentials and should be run manually
or in a CI/CD environment with proper credentials configured.

To run these tests:
1. Set up Gmail API credentials (credentials.json)
2. Run OAuth flow to get token.json
3. Set GMAIL_INTEGRATION_TEST=1 environment variable
4. Execute: pytest tests/integration/test_email_receiver_gmail.py
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from email_receiver.gmail_receiver import GmailReceiver
from models.raw_email import RawEmail

# Skip integration tests unless explicitly enabled
pytestmark = pytest.mark.skipif(
    os.getenv("GMAIL_INTEGRATION_TEST") != "1",
    reason="Integration tests require GMAIL_INTEGRATION_TEST=1 and real credentials"
)


@pytest.fixture
def gmail_credentials():
    """Load real Gmail API credentials from environment or config."""
    creds_path = Path(os.getenv("GMAIL_CREDENTIALS_PATH", "credentials.json"))
    token_path = Path(os.getenv("GMAIL_TOKEN_PATH", "token.json"))

    if not creds_path.exists():
        pytest.skip(f"Gmail credentials not found at {creds_path}")

    return creds_path, token_path


@pytest.fixture
def gmail_receiver(gmail_credentials, tmp_path):
    """Create GmailReceiver with real credentials and temporary storage."""
    creds_path, token_path = gmail_credentials

    receiver = GmailReceiver(
        credentials_path=creds_path,
        token_path=token_path,
        raw_email_dir=tmp_path / "data" / "raw",
        metadata_dir=tmp_path / "data" / "metadata"
    )

    return receiver


# T039: Integration test - end to end flow
def test_gmail_receiver_end_to_end(gmail_receiver, tmp_path):
    """
    Test complete email fetch and save flow with real Gmail API.

    This test:
    1. Connects to Gmail API with OAuth2
    2. Fetches recent emails (last 7 days)
    3. Saves emails to file storage
    4. Verifies file structure and content

    Requirements:
    - Valid Gmail credentials
    - Access to portfolioupdates@signite.co inbox
    - At least 1 email in the last 7 days
    """
    # Connect to Gmail API
    gmail_receiver.connect()
    assert gmail_receiver.service is not None, "Gmail service should be initialized"

    # Fetch emails from last 7 days
    since = datetime.now() - timedelta(days=7)
    emails = gmail_receiver.fetch_emails(since=since, max_emails=5)

    # Verify we got some emails
    assert isinstance(emails, list), "Should return a list of emails"
    print(f"\n✓ Fetched {len(emails)} emails from last 7 days")

    if len(emails) == 0:
        pytest.skip("No emails found in last 7 days - cannot test save functionality")

    # Verify email structure
    for email in emails:
        assert isinstance(email, RawEmail), "Each email should be a RawEmail object"
        assert email.metadata.message_id, "Email should have message_id"
        assert email.metadata.sender, "Email should have sender"
        assert email.body, "Email should have body content"
        print(f"  - {email.metadata.subject} from {email.metadata.sender}")

    # Save first email to storage
    first_email = emails[0]
    saved_path = gmail_receiver.save_raw_email(first_email)

    # Verify file was created
    assert saved_path.exists(), f"Email file should exist at {saved_path}"
    assert saved_path.suffix == ".json", "Email file should be JSON"

    # Verify file structure (data/raw/YYYY/MM/filename.json)
    assert saved_path.parent.name.isdigit(), "Month directory should be numeric"
    assert saved_path.parent.parent.name.isdigit(), "Year directory should be numeric"

    # Verify file content
    saved_content = json.loads(saved_path.read_text())
    assert saved_content["metadata"]["message_id"] == first_email.metadata.message_id
    assert saved_content["body"] == first_email.body

    print(f"✓ Saved email to {saved_path}")
    print(f"✓ End-to-end test passed: fetched and saved {len(emails)} emails")


# T040: Integration test - duplicate detection
def test_duplicate_detection(gmail_receiver):
    """
    Test duplicate email detection using message IDs.

    This test:
    1. Fetches emails from inbox
    2. Checks duplicate detection before processing
    3. Marks emails as processed
    4. Verifies duplicate detection after processing

    Note: This test uses placeholder is_duplicate() and mark_processed()
    methods which will be fully implemented in Phase 4 with DuplicateTracker.
    """
    # Connect and fetch emails
    gmail_receiver.connect()
    since = datetime.now() - timedelta(days=7)
    emails = gmail_receiver.fetch_emails(since=since, max_emails=3)

    if len(emails) == 0:
        pytest.skip("No emails found - cannot test duplicate detection")

    first_email = emails[0]
    message_id = first_email.metadata.message_id

    # TODO: Currently placeholder methods return False/None
    # In Phase 4, implement full DuplicateTracker integration

    # Check if email is duplicate (should be False initially)
    is_dup = gmail_receiver.is_duplicate(message_id)
    assert is_dup is False, "New email should not be marked as duplicate"
    print(f"✓ Email {message_id} is not a duplicate")

    # Mark as processed
    gmail_receiver.mark_processed(message_id)
    print(f"✓ Marked email {message_id} as processed")

    # TODO: In Phase 4, verify is_duplicate returns True after mark_processed
    # For now, we just verify the methods don't raise exceptions

    print("✓ Duplicate detection test passed (placeholder implementation)")
    print("  Note: Full DuplicateTracker integration coming in Phase 4")


# T041: Integration test - empty inbox handling
def test_empty_inbox(gmail_receiver):
    """
    Test graceful handling of empty inbox or no new emails.

    This test:
    1. Connects to Gmail API
    2. Fetches emails from a very old date (likely no results)
    3. Verifies empty list is returned (not None or exception)
    4. Verifies no errors are raised

    Requirements:
    - Valid Gmail credentials
    - No emails from year 2000 in inbox
    """
    # Connect to Gmail API
    gmail_receiver.connect()

    # Fetch emails from year 2000 (should be empty)
    since = datetime(2000, 1, 1)
    emails = gmail_receiver.fetch_emails(since=since, max_emails=10)

    # Verify empty list is returned
    assert isinstance(emails, list), "Should return a list even when empty"
    assert len(emails) == 0, "Should return empty list for old date range"

    print("✓ Empty inbox handled gracefully")
    print("✓ Returned empty list instead of raising exception")

    # Also test with very recent date (might also be empty)
    since_recent = datetime.now() - timedelta(minutes=5)
    recent_emails = gmail_receiver.fetch_emails(since=since_recent, max_emails=10)

    assert isinstance(recent_emails, list), "Should return list for recent date"
    print(f"✓ Fetched {len(recent_emails)} emails from last 5 minutes")
    print("✓ Empty inbox test passed")


# Additional helper test
def test_gmail_connection_only(gmail_receiver):
    """
    Quick test to verify Gmail API connection works.

    Useful for debugging OAuth2 flow and credentials.
    """
    gmail_receiver.connect()
    assert gmail_receiver.service is not None
    assert gmail_receiver.creds is not None
    assert gmail_receiver.creds.valid

    print("✓ Gmail API connection successful")
    print(f"  Credentials path: {gmail_receiver.credentials_path}")
    print(f"  Token path: {gmail_receiver.token_path}")
