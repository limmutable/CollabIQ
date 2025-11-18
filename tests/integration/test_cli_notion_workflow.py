"""
Integration tests for CLI Notion command workflows.

Tests the interaction between Notion commands (verify → test-write → cleanup).
"""

import pytest
from typer.testing import CliRunner
from collabiq import app
from unittest.mock import patch

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
            sys.stderr = original_stderr
            sys.stdout = original_stdout


@pytest.mark.integration
@pytest.mark.notion
def test_notion_verify_test_write_cleanup_workflow():
    """
    Integration: Complete workflow from verify to test-write to cleanup.

    This test verifies the full Notion integration workflow:
    1. Verify Notion connection and schema
    2. Create a test entry and auto-cleanup
    3. Manually cleanup any remaining test entries

    Note: This test requires valid Notion credentials and database access.
    """
    # Step 1: Verify Notion connection and schema
    result = runner.invoke(app, ["notion", "verify"])

    # Verify should succeed or provide clear error message
    # Exit code 0 = success, 1 = failure with error message
    assert result.exit_code in [0, 1], f"Unexpected exit code: {result.exit_code}"

    # If verify failed, the rest of the workflow cannot continue
    if result.exit_code == 1:
        pytest.skip(
            "Notion verification failed - cannot test workflow without valid connection"
        )

    # Step 2: Test write (creates and auto-cleans up a test entry)
    result = runner.invoke(app, ["notion", "test-write"])

    # Test write should succeed
    assert result.exit_code == 0, f"test-write failed with exit code {result.exit_code}"
    assert "success" in result.stdout.lower() or "created" in result.stdout.lower()

    # Step 3: Cleanup any remaining test entries (using --yes to skip confirmation)
    result = runner.invoke(app, ["notion", "cleanup-tests", "--yes"])

    # Cleanup should succeed (even if no entries to clean)
    assert result.exit_code == 0, (
        f"cleanup-tests failed with exit code {result.exit_code}"
    )


@pytest.mark.integration
@pytest.mark.notion
def test_notion_verify_json_output():
    """
    Integration: Verify JSON output mode for notion verify.

    Ensures --json flag produces valid JSON output.
    """
    result = runner.invoke(app, ["notion", "verify", "--json"])

    # Should succeed or fail with valid JSON
    assert result.exit_code in [0, 1], f"Unexpected exit code: {result.exit_code}"

    # Output should be valid JSON
    import json

    try:
        data = json.loads(result.stdout)
        assert "status" in data, "JSON output missing 'status' field"
        assert "data" in data, "JSON output missing 'data' field"
    except json.JSONDecodeError as e:
        pytest.fail(f"Invalid JSON output: {e}\nOutput: {result.stdout}")


@pytest.mark.integration
@pytest.mark.notion
def test_notion_schema_display():
    """
    Integration: Verify schema display shows database structure.

    Tests that schema command displays database properties and types.
    """
    result = runner.invoke(app, ["notion", "schema"])

    # Should succeed or provide clear error
    assert result.exit_code in [0, 1], f"Unexpected exit code: {result.exit_code}"

    # If successful, should show schema information
    if result.exit_code == 0:
        # Should show property information
        assert (
            "property" in result.stdout.lower()
            or "field" in result.stdout.lower()
            or "type" in result.stdout.lower()
        )
