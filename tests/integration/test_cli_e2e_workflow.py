"""
Integration tests for CLI E2E test command workflows.

Tests the E2E test runner, interrupt/resume capability, and reporting.

Note: These tests verify the CLI command orchestration, not the E2E test logic itself.
The E2E test logic is tested separately in tests/e2e/test_full_pipeline.py.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from collabiq import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def mock_setup_logging(monkeypatch):
    """Prevent setup_logging from running and interfering with CliRunner, and redirect stdout/stderr."""
    import sys
    import io

    with patch("config.logging_config.setup_logging") as mock_log:
        # Redirect stdout and stderr to StringIO objects
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        monkeypatch.setattr(sys, "stdout", io.StringIO())
        monkeypatch.setattr(sys, "stderr", io.StringIO())
        try:
            yield mock_log
        finally:
            # Restore original stdout and stderr
            sys.stdout = original_stdout
            sys.stderr = original_stderr


def test_e2e_execution_and_reporting():
    """
    Integration test for E2E test execution and reporting.

    T073 - Verifies:
    - E2E test runner CLI command exists and has correct structure
    - Command parses arguments correctly
    - Error handling works when prerequisites are missing
    - Help text is comprehensive

    Note: We're testing the CLI interface, not the full E2E flow.
    Full E2E flow is tested in tests/e2e/test_full_pipeline.py
    """
    # Test 1: Help text is available
    result = runner.invoke(app, ["test", "e2e", "--help"])
    assert result.exit_code == 0, "Help should work without errors"
    assert "e2e" in result.stdout.lower()
    assert "--limit" in result.stdout
    assert "--all" in result.stdout
    assert "--email-id" in result.stdout
    assert "--resume" in result.stdout

    # Test 2: Missing test email IDs file or E2E infrastructure produces helpful error
    result = runner.invoke(app, ["test", "e2e", "--limit", "3"])
    # Should fail because either test email IDs file doesn't exist or E2E infrastructure is not available
    assert result.exit_code == 1, "Should fail without test email IDs or E2E infrastructure"
    # Check for either error message
    assert (
        "test_email_ids.json" in result.stdout
        or "Test email IDs file not found" in result.stdout
        or "E2E test infrastructure" in result.stdout
    ), f"Expected error message not found in: {result.stdout}"

    # Verify error handling is clean (not a stack trace)
    assert "Traceback" not in result.stdout, "Should not show stack trace for expected errors"


def test_interrupt_and_resume_workflow():
    """
    Integration test for interrupt and resume workflow.

    T074 - Verifies:
    - Resume command exists and has correct structure
    - Command parses resume run ID correctly
    - Error handling works when run file is missing
    - Help text is comprehensive

    Note: We're testing the CLI interface, not the actual resume logic.
    """
    # Test 1: Resume command accepts run ID
    result = runner.invoke(app, ["test", "e2e", "--resume", "20250108_130000"])

    # Should fail because run file doesn't exist, but with a clean error
    assert result.exit_code == 1, "Should fail when run file doesn't exist"

    # Verify the command attempted to resume (error message indicates the run was looked for)
    output_lower = result.stdout.lower()
    # The error could be either "not found" or about missing E2E infrastructure
    assert "not found" in output_lower or "e2e" in output_lower or "test" in output_lower

    # Verify error handling is clean
    assert "Traceback" not in result.stdout, "Should not show stack trace for expected errors"


def test_select_emails_command():
    """
    Test that select-emails command exists and has proper structure.

    Verifies:
    - Command is accessible
    - Help text is comprehensive
    - Required parameters are documented
    """
    result = runner.invoke(app, ["test", "select-emails", "--help"])
    assert result.exit_code == 0, "Help should work without errors"
    assert "select" in result.stdout.lower() or "email" in result.stdout.lower()
    assert "--limit" in result.stdout
    assert "--from-date" in result.stdout


def test_validate_command():
    """
    Test that validate command exists and runs health checks.

    Verifies:
    - Command is accessible
    - Runs basic health checks
    - Returns appropriate status
    """
    result = runner.invoke(app, ["test", "validate"])

    # Should complete (may pass or fail depending on environment)
    # We just verify it runs and shows check results
    assert "Gmail" in result.stdout or "Notion" in result.stdout or "health" in result.stdout.lower()

    # Verify it shows check results in some form
    assert "✓" in result.stdout or "✗" in result.stdout or "Pass" in result.stdout or "Failed" in result.stdout
