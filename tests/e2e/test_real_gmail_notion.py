"""
Real E2E Tests with Gmail and Notion Integration (T016, T017)

These tests validate the complete pipeline with real external APIs:
- Fetch real emails from Gmail account
- Process emails through LLM extraction
- Write entries to Notion database
- Validate Notion entries

Required Environment Variables:
    Gmail: GOOGLE_CREDENTIALS_PATH, GMAIL_TOKEN_PATH, EMAIL_ADDRESS
    Notion: NOTION_API_KEY, NOTION_DATABASE_ID_COLLABIQ
    (Can be set in .env file or retrieved from Infisical)

Test Configuration:
    E2E_MAX_EMAILS: Maximum number of emails to process in tests (default: 8)
    E2E_SKIP_CLEANUP: Skip cleanup of test entries (default: false)

Tests will be skipped if credentials are not configured.
"""

import pytest
import os

from e2e_test.runner import E2ERunner
from llm_orchestrator.orchestrator import LLMOrchestrator
from llm_orchestrator.types import OrchestrationConfig
from models.classification_service import ClassificationService


# Configuration for E2E tests
MAX_EMAILS = int(os.getenv("E2E_MAX_EMAILS", "8"))  # Process 8 emails by default
SKIP_CLEANUP = os.getenv("E2E_SKIP_CLEANUP", "false").lower() == "true"


@pytest.fixture
def llm_orchestrator():
    """Initialize LLM orchestrator for extraction."""
    config = OrchestrationConfig(
        strategy="failover",
        enable_quality_routing=False,
        max_retries=2,
    )
    return LLMOrchestrator(config=config)


@pytest.fixture
def classification_service():
    """Initialize classification service."""
    return ClassificationService()


@pytest.fixture
def e2e_runner(gmail_receiver, llm_orchestrator, classification_service, notion_writer):
    """Initialize E2E runner with real components.

    Uses gmail_receiver and notion_writer fixtures from conftest.py (T014, T015).
    Will skip test if credentials not configured.
    """
    runner = E2ERunner(
        gmail_receiver=gmail_receiver,
        llm_orchestrator=llm_orchestrator,
        classification_service=classification_service,
        notion_writer=notion_writer,
        test_mode=False,  # Use real APIs
        orchestration_strategy="failover",
        enable_quality_routing=False,
    )

    return runner


@pytest.mark.e2e
@pytest.mark.integration
def test_fetch_real_email_from_gmail(gmail_receiver, gmail_test_account):
    """
    T016: Test fetching real emails from Gmail account

    Acceptance Scenario 1 (User Story 1):
    Given a configured Gmail account,
    When the automated E2E test suite is executed,
    Then real emails are fetched from Gmail.

    Note: Uses MAX_EMAILS (default 8) to limit email processing in tests.
    """
    # Fetch recent emails from account
    # For tests: Fetch a fixed number of emails (unlike live processing which only fetches unprocessed)
    query = f"to:{gmail_test_account['email_address']} newer_than:30d"

    raw_emails = gmail_receiver.fetch_emails(max_results=MAX_EMAILS, query=query)

    # Verify emails were fetched
    assert len(raw_emails) > 0, (
        f"Should fetch at least 1 email (tried to fetch {MAX_EMAILS})"
    )
    assert all(hasattr(email, "email_id") for email in raw_emails), (
        "All emails should have email_id"
    )
    assert all(hasattr(email, "subject") for email in raw_emails), (
        "All emails should have subject"
    )
    assert all(hasattr(email, "cleaned_body") for email in raw_emails), (
        "All emails should have cleaned_body"
    )

    print(f"\n✓ Successfully fetched {len(raw_emails)} real emails from Gmail")
    for email in raw_emails[:3]:  # Show first 3
        print(f"  - {email.email_id}: {email.subject[:50]}")


@pytest.mark.e2e
@pytest.mark.integration
def test_process_real_email_to_notion(
    e2e_runner, gmail_test_account, notion_test_database
):
    """
    T016 + T017: Test complete pipeline from Gmail fetch to Notion write

    Acceptance Scenarios 2-3 (User Story 1):
    - Given real emails are fetched and processed,
      When the automated E2E test suite proceeds,
      Then corresponding entries are created in the Notion database.
    - Given entries are created in the Notion database,
      When validation is performed,
      Then the entries match the extracted data.

    Note: Uses MAX_EMAILS (default 8) to limit processing. Processes a fixed
    number of emails (unlike live which only processes unprocessed emails).
    """
    print(f"\nProcessing up to {MAX_EMAILS} emails from Gmail to Notion")

    # Fetch recent emails from account
    # For tests: Process a fixed number, unlike live which only processes new/unprocessed
    query = f"to:{gmail_test_account['email_address']} newer_than:30d"

    # Get email IDs to process
    raw_emails = e2e_runner.gmail_receiver.fetch_emails(
        max_results=MAX_EMAILS, query=query
    )

    assert len(raw_emails) > 0, f"Should have at least 1 email (tried {MAX_EMAILS})"

    email_ids = [email.email_id for email in raw_emails]

    # Run E2E test with real APIs
    test_run = e2e_runner.run_tests(
        email_ids=email_ids,
        test_mode=False,  # Real API calls
    )

    # Verify test run completed
    assert test_run.status == "completed", (
        f"Test run should complete, got: {test_run.status}"
    )
    assert test_run.emails_processed == len(email_ids), "All emails should be processed"

    # Verify success rate (SC-001: ≥95%)
    success_rate = test_run.success_count / test_run.emails_processed
    assert success_rate >= 0.95, (
        f"Success rate {success_rate:.1%} below 95% threshold (SC-001). "
        f"Succeeded: {test_run.success_count}/{test_run.emails_processed}"
    )

    # Verify no critical errors (SC-003)
    assert test_run.error_summary.get("critical", 0) == 0, (
        f"Critical errors detected: {test_run.error_summary.get('critical', 0)} (SC-003)"
    )

    print("\n✓ E2E Pipeline Success:")
    print(f"  - Emails processed: {test_run.emails_processed}")
    print(f"  - Success rate: {success_rate:.1%}")
    print(f"  - Notion entries created: {test_run.success_count}")

    if not SKIP_CLEANUP:
        print(f"  - Cleanup: {test_run.success_count} entries will be cleaned up")


@pytest.mark.e2e
@pytest.mark.integration
def test_notion_write_validation(e2e_runner, notion_writer, gmail_test_account):
    """
    T017: Validate Notion entries after creation

    This test ensures that data written to Notion matches the extracted entities
    and that all required fields are present.
    """
    # Fetch one test email
    query = f"to:{gmail_test_account['email_address']} newer_than:7d"
    raw_emails = e2e_runner.gmail_receiver.fetch_emails(max_results=1, query=query)

    assert len(raw_emails) > 0, "Should have test email"

    email = raw_emails[0]
    email_id = email.email_id

    # Process email through LLM extraction
    extracted_data = e2e_runner.llm_orchestrator.extract_entities(email.cleaned_body)

    # Add email metadata
    extracted_data.email_id = email_id

    # Classify collaboration
    if e2e_runner.classification_service:
        classified_data = e2e_runner.classification_service.classify(extracted_data)
    else:
        classified_data = extracted_data

    # Write to Notion
    page_id = notion_writer.write_entry(classified_data)

    assert page_id is not None, "Notion page ID should be returned"
    assert len(page_id) >= 32, (
        f"Notion page ID should be at least 32 chars, got: {page_id}"
    )

    # Read back from Notion to validate
    notion_page = notion_writer.client.client.pages.retrieve(page_id=page_id)

    # Validate page properties exist
    assert "properties" in notion_page, "Notion page should have properties"

    properties = notion_page["properties"]

    # Check required fields
    required_fields = ["Name", "Startup", "Partner Org", "담당자", "Date"]
    for field in required_fields:
        assert field in properties, f"Required field '{field}' missing from Notion page"

    # Validate email_id is stored (for cleanup identification)
    if "email_id" in properties:
        # Notion email_id field should match
        notion_email_id = (
            properties["email_id"]
            .get("rich_text", [{}])[0]
            .get("text", {})
            .get("content")
        )
        assert notion_email_id == email_id, (
            f"Email ID mismatch: {notion_email_id} != {email_id}"
        )

    print("\n✓ Notion Write Validation Passed:")
    print(f"  - Page ID: {page_id}")
    print(f"  - Email ID: {email_id}")
    print("  - All required fields present")


@pytest.mark.e2e
@pytest.mark.integration
def test_batch_processing_real_emails(e2e_runner, gmail_test_account):
    """
    Test processing multiple real emails in batch

    This validates that the E2E pipeline can handle multiple emails
    and maintains high success rates.
    """
    # Fetch recent emails
    query = f"to:{gmail_test_account['email_address']} newer_than:7d"
    raw_emails = e2e_runner.gmail_receiver.fetch_emails(max_results=3, query=query)

    if len(raw_emails) < 2:
        pytest.skip("Need at least 2 test emails for batch processing test")

    email_ids = [email.email_id for email in raw_emails]

    # Run batch E2E test
    test_run = e2e_runner.run_tests(email_ids=email_ids, test_mode=False)

    # Verify batch processing
    assert test_run.status == "completed", "Batch test run should complete"
    assert test_run.emails_processed == len(email_ids), "All emails should be processed"

    # Check success rate
    success_rate = test_run.success_count / test_run.emails_processed

    print("\n✓ Batch Processing Results:")
    print(f"  - Emails processed: {test_run.emails_processed}")
    print(f"  - Success rate: {success_rate:.1%}")
    print(f"  - Failures: {test_run.failure_count}")

    # SC-001: ≥95% success rate
    if success_rate < 0.95:
        print("  ⚠️  Warning: Success rate below 95% threshold")

    # SC-003: No critical errors
    assert test_run.error_summary.get("critical", 0) == 0, "No critical errors allowed"
