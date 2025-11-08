"""
Contract tests for CollabIQ CLI interface.

These tests verify the CLI command signatures, argument parsing,
help text, and exit codes remain stable across changes.
"""

import pytest
from typer.testing import CliRunner
from collabiq import app

runner = CliRunner()


# ==============================================================================
# User Story 1: Single Entry Point - Contract Tests (T018-T020)
# ==============================================================================


def test_main_app_help_text():
    """
    Contract: Main app displays help with all command groups listed.

    Verifies:
    - Exit code 0 when --help is used
    - All 7 command groups are listed (email, notion, test, errors, status, llm, config)
    - Help text includes descriptions for each group
    """
    result = runner.invoke(app, ["--help"])

    # Should exit successfully
    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}"

    # Should show all command groups
    assert "email" in result.stdout, "Missing 'email' command group in help"
    assert "notion" in result.stdout, "Missing 'notion' command group in help"
    assert "test" in result.stdout, "Missing 'test' command group in help"
    assert "errors" in result.stdout, "Missing 'errors' command group in help"
    assert "status" in result.stdout, "Missing 'status' command group in help"
    assert "llm" in result.stdout, "Missing 'llm' command group in help"
    assert "config" in result.stdout, "Missing 'config' command group in help"

    # Should show help descriptions
    assert "Email pipeline" in result.stdout or "email" in result.stdout.lower()
    assert "Notion" in result.stdout or "notion" in result.stdout.lower()


def test_command_group_registration():
    """
    Contract: All command groups are properly registered and accessible.

    Verifies each command group shows its own help when invoked with --help.
    """
    command_groups = ["email", "notion", "test", "errors", "status", "llm", "config"]

    for group in command_groups:
        result = runner.invoke(app, [group, "--help"])

        # Each group should show help successfully
        assert (
            result.exit_code == 0
        ), f"Command group '{group}' failed with exit code {result.exit_code}"

        # Help should contain the group name
        assert group in result.stdout.lower(), f"Help text for '{group}' missing group name"


def test_global_options():
    """
    Contract: Global options (--help, --debug, --quiet, --no-color) are available.

    Verifies:
    - --help shows global options
    - --debug flag is accepted
    - --quiet flag is accepted
    - --no-color flag is accepted
    """
    result = runner.invoke(app, ["--help"])

    # Should show global options in help
    assert "--debug" in result.stdout, "Missing --debug option in help"
    assert "--quiet" in result.stdout, "Missing --quiet option in help"
    assert "--no-color" in result.stdout, "Missing --no-color option in help"

    # Test that flags are accepted (should not error)
    # Note: Testing with a command group to verify flags work
    result = runner.invoke(app, ["--debug", "email", "--help"])
    assert result.exit_code == 0, "--debug flag not accepted"

    result = runner.invoke(app, ["--quiet", "email", "--help"])
    assert result.exit_code == 0, "--quiet flag not accepted"

    result = runner.invoke(app, ["--no-color", "email", "--help"])
    assert result.exit_code == 0, "--no-color flag not accepted"
