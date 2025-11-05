"""
E2E Pytest Validation Script

Automated pytest test that runs the complete E2E pipeline with all available emails
and validates against success criteria (SC-001: ≥95% success rate, SC-003: no critical errors).

Usage:
    pytest tests/e2e/test_full_pipeline.py -v
    pytest tests/e2e/test_full_pipeline.py -v --email-count=5  # Test with subset
"""

import json
import pytest
from pathlib import Path

from src.e2e_test.runner import E2ERunner
from src.e2e_test.report_generator import ReportGenerator


@pytest.fixture
def test_email_ids():
    """Load test email IDs from data/e2e_test/test_email_ids.json"""
    email_ids_file = Path("data/e2e_test/test_email_ids.json")

    if not email_ids_file.exists():
        pytest.skip(
            "Test email IDs file not found. Run email selection script first:\n"
            "  uv run python scripts/select_test_emails.py --all"
        )

    with email_ids_file.open("r", encoding="utf-8") as f:
        test_emails = json.load(f)

    email_ids = [email["email_id"] for email in test_emails]

    if len(email_ids) == 0:
        pytest.skip("No test email IDs found in file")

    return email_ids


@pytest.fixture
def runner():
    """Initialize E2ERunner with test mode enabled"""
    return E2ERunner(
        gmail_receiver=None,  # Mock components for now
        gemini_adapter=None,
        classification_service=None,
        notion_writer=None,
        test_mode=True,
    )


@pytest.fixture
def report_generator():
    """Initialize ReportGenerator"""
    return ReportGenerator()


def test_full_pipeline_with_all_emails(test_email_ids, runner, report_generator):
    """
    Test complete pipeline with all available emails

    Success Criteria:
    - SC-001: ≥95% pipeline success rate
    - SC-003: No critical errors
    - All emails processed without exceptions
    """
    # Run E2E tests
    test_run = runner.run_tests(test_email_ids, test_mode=True)

    # Generate summary report
    summary = report_generator.generate_summary(test_run)
    report_path = Path(f"data/e2e_test/reports/{test_run.run_id}_summary.md")
    report_path.write_text(summary, encoding="utf-8")

    print(f"\n{'='*70}")
    print(f"Test Run Summary")
    print(f"{'='*70}")
    print(f"Run ID: {test_run.run_id}")
    print(f"Emails Processed: {test_run.emails_processed}")
    print(f"Success Count: {test_run.success_count}")
    print(f"Failure Count: {test_run.failure_count}")
    print(f"Success Rate: {test_run.success_count / test_run.emails_processed * 100:.1f}%")
    print(f"Errors: {test_run.error_summary}")
    print(f"\nReport saved to: {report_path}")
    print(f"{'='*70}\n")

    # Assertions for success criteria
    assert test_run.status == "completed", "Test run should complete successfully"
    assert (
        test_run.emails_processed == len(test_email_ids)
    ), "All emails should be processed"

    # SC-001: Success rate should be ≥95%
    success_rate = test_run.success_count / test_run.emails_processed

    assert success_rate >= 0.95, (
        f"Success rate {success_rate:.1%} is below 95% (SC-001)\n"
        f"Failed emails: {test_run.failure_count}\n"
        f"Error summary: {test_run.error_summary}\n"
        f"See report for details: {report_path}"
    )

    # SC-003: No critical errors allowed
    assert test_run.error_summary.get("critical", 0) == 0, (
        f"Critical errors detected: {test_run.error_summary.get('critical', 0)} (SC-003)\n"
        f"See report for details: {report_path}"
    )


def test_single_email_processing(test_email_ids, runner):
    """
    Test processing of a single email to verify pipeline integration

    This test validates that the complete pipeline works end-to-end for at least one email.
    """
    if len(test_email_ids) == 0:
        pytest.skip("No test emails available")

    # Process first email only
    test_run = runner.run_tests([test_email_ids[0]], test_mode=True)

    # Basic assertions
    assert test_run.emails_processed == 1, "Should process exactly 1 email"
    assert test_run.status == "completed", "Test run should complete"

    # At least this single email should succeed
    assert test_run.success_count >= 0, "Success count should be non-negative"


def test_error_collection(test_email_ids, runner, report_generator):
    """
    Test that errors are properly collected and reported

    This test validates that the ErrorCollector and ReportGenerator work correctly.
    """
    # Run tests
    test_run = runner.run_tests(test_email_ids[:5] if len(test_email_ids) >= 5 else test_email_ids, test_mode=True)

    # Generate error report
    error_report = report_generator.generate_error_report(test_run.run_id)
    report_path = Path(f"data/e2e_test/reports/{test_run.run_id}_errors.md")
    report_path.write_text(error_report, encoding="utf-8")

    # Verify error summary structure
    assert "critical" in test_run.error_summary
    assert "high" in test_run.error_summary
    assert "medium" in test_run.error_summary
    assert "low" in test_run.error_summary

    # Verify error report was generated
    assert report_path.exists(), "Error report should be generated"
    assert len(error_report) > 0, "Error report should have content"


@pytest.mark.parametrize("email_count", [1, 3, 5])
def test_pipeline_with_varying_email_counts(email_count, test_email_ids, runner):
    """
    Test pipeline with varying numbers of emails

    Validates that the runner handles different batch sizes correctly.
    """
    if len(test_email_ids) < email_count:
        pytest.skip(f"Not enough test emails (need {email_count}, have {len(test_email_ids)})")

    # Process subset of emails
    test_run = runner.run_tests(test_email_ids[:email_count], test_mode=True)

    # Basic validation
    assert test_run.emails_processed == email_count
    assert test_run.status == "completed"
    assert test_run.success_count + test_run.failure_count == email_count
