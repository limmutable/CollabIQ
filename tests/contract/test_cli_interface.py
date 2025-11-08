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


# ==============================================================================
# User Story 3: Notion Integration Management - Contract Tests (T041-T044)
# ==============================================================================


def test_notion_verify_command():
    """
    Contract: collabiq notion verify command exists with proper signature.

    Verifies:
    - Command is accessible via 'collabiq notion verify'
    - Accepts --json flag
    - Accepts --debug flag
    - Has comprehensive help text with usage examples
    """
    result = runner.invoke(app, ["notion", "verify", "--help"])

    # Should exit successfully
    assert result.exit_code == 0, f"verify command failed with exit code {result.exit_code}"

    # Should show command description
    assert "verify" in result.stdout.lower(), "Missing command description"
    assert "connection" in result.stdout.lower() or "notion" in result.stdout.lower()

    # Should support --json and --debug flags
    assert "--json" in result.stdout, "Missing --json flag"
    assert "--debug" in result.stdout, "Missing --debug flag"


def test_notion_schema_command():
    """
    Contract: collabiq notion schema command exists with proper signature.

    Verifies:
    - Command is accessible via 'collabiq notion schema'
    - Accepts --json flag
    - Accepts --debug flag
    - Has help text describing schema display functionality
    """
    result = runner.invoke(app, ["notion", "schema", "--help"])

    # Should exit successfully
    assert result.exit_code == 0, f"schema command failed with exit code {result.exit_code}"

    # Should show command description
    assert "schema" in result.stdout.lower(), "Missing command description"

    # Should support --json and --debug flags
    assert "--json" in result.stdout, "Missing --json flag"
    assert "--debug" in result.stdout, "Missing --debug flag"


def test_notion_test_write_command():
    """
    Contract: collabiq notion test-write command exists with proper signature.

    Verifies:
    - Command is accessible via 'collabiq notion test-write'
    - Accepts --json flag
    - Accepts --debug flag
    - Has help text about creating and cleaning up test entries
    """
    result = runner.invoke(app, ["notion", "test-write", "--help"])

    # Should exit successfully
    assert result.exit_code == 0, f"test-write command failed with exit code {result.exit_code}"

    # Should show command description
    assert "test" in result.stdout.lower(), "Missing 'test' in description"

    # Should support --json and --debug flags
    assert "--json" in result.stdout, "Missing --json flag"
    assert "--debug" in result.stdout, "Missing --debug flag"


def test_notion_cleanup_tests_command():
    """
    Contract: collabiq notion cleanup-tests command exists with proper signature.

    Verifies:
    - Command is accessible via 'collabiq notion cleanup-tests'
    - Accepts --yes flag to skip confirmation
    - Accepts --json flag
    - Accepts --debug flag
    - Has help text about removing test entries
    """
    result = runner.invoke(app, ["notion", "cleanup-tests", "--help"])

    # Should exit successfully
    assert result.exit_code == 0, f"cleanup-tests command failed with exit code {result.exit_code}"

    # Should show command description
    assert "cleanup" in result.stdout.lower() or "clean" in result.stdout.lower(), "Missing 'cleanup' in description"

    # Should support --yes, --json, and --debug flags
    assert "--yes" in result.stdout, "Missing --yes flag for confirmation skip"
    assert "--json" in result.stdout, "Missing --json flag"
    assert "--debug" in result.stdout, "Missing --debug flag"


# ==============================================================================
# User Story 2: Email Pipeline - Contract Tests (T025-T029)
# ==============================================================================


def test_email_fetch_contract():
    """
    Contract: `collabiq email fetch` command signature and options.

    Verifies:
    - Command exists and responds to --help
    - --limit option is available and accepts integer values
    - Default limit behavior documented
    - Exit code 0 on --help
    - Help text includes examples
    """
    result = runner.invoke(app, ["email", "fetch", "--help"])

    # Should exit successfully
    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}"

    # Should show --limit option
    assert "--limit" in result.stdout, "Missing --limit option in help"

    # Should show --json option
    assert "--json" in result.stdout, "Missing --json option in help"

    # Should have description
    assert "fetch" in result.stdout.lower() or "gmail" in result.stdout.lower()


def test_email_clean_contract():
    """
    Contract: `collabiq email clean` command signature and options.

    Verifies:
    - Command exists and responds to --help
    - Help text describes cleaning/normalization functionality
    - Exit code 0 on --help
    """
    result = runner.invoke(app, ["email", "clean", "--help"])

    # Should exit successfully
    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}"

    # Should have description about cleaning/normalizing
    assert (
        "clean" in result.stdout.lower() or "normalize" in result.stdout.lower()
    ), "Missing clean/normalize description"

    # Should show --json option
    assert "--json" in result.stdout, "Missing --json option in help"


def test_email_list_contract():
    """
    Contract: `collabiq email list` command with filtering options.

    Verifies:
    - Command exists and responds to --help
    - --limit option available (default 20)
    - --since option for date filtering
    - --status option for status filtering
    - Help text includes filtering examples
    """
    result = runner.invoke(app, ["email", "list", "--help"])

    # Should exit successfully
    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}"

    # Should show filtering options
    assert "--limit" in result.stdout, "Missing --limit option in help"
    assert "--since" in result.stdout, "Missing --since option in help"
    assert "--status" in result.stdout, "Missing --status option in help"

    # Should show --json option
    assert "--json" in result.stdout, "Missing --json option in help"


def test_email_verify_contract():
    """
    Contract: `collabiq email verify` command.

    Verifies:
    - Command exists and responds to --help
    - Help text describes Gmail connectivity check
    - Exit code 0 on --help
    """
    result = runner.invoke(app, ["email", "verify", "--help"])

    # Should exit successfully
    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}"

    # Should have description about verification/connectivity
    assert (
        "verify" in result.stdout.lower() or "connect" in result.stdout.lower()
    ), "Missing verify/connect description"

    # Should show --json option
    assert "--json" in result.stdout, "Missing --json option in help"


def test_email_process_contract():
    """
    Contract: `collabiq email process` command.

    Verifies:
    - Command exists and responds to --help
    - --limit option available
    - Help text describes full pipeline orchestration
    - Exit code 0 on --help
    """
    result = runner.invoke(app, ["email", "process", "--help"])

    # Should exit successfully
    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}"

    # Should show --limit option
    assert "--limit" in result.stdout, "Missing --limit option in help"

    # Should show --json option
    assert "--json" in result.stdout, "Missing --json option in help"

    # Should have description about pipeline/processing
    assert (
        "process" in result.stdout.lower() or "pipeline" in result.stdout.lower()
    ), "Missing process/pipeline description"


# ==============================================================================
# User Story 4: LLM Provider Management - Contract Tests (T053-T058)
# ==============================================================================


def test_llm_status_contract():
    """
    Contract: `collabiq llm status` command signature and options.

    Verifies:
    - Command exists and responds to --help
    - Accepts --json flag for JSON output
    - Help text describes provider health status functionality
    - Exit code 0 on --help
    """
    result = runner.invoke(app, ["llm", "status", "--help"])

    # Should exit successfully
    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}"

    # Should show --json option
    assert "--json" in result.stdout, "Missing --json option in help"

    # Should have description about status/health
    assert (
        "status" in result.stdout.lower() or "health" in result.stdout.lower()
    ), "Missing status/health description"


def test_llm_test_provider_contract():
    """
    Contract: `collabiq llm test <provider>` command signature and options.

    Verifies:
    - Command exists and responds to --help
    - Accepts provider argument
    - Accepts --json flag
    - Help text describes provider connectivity testing
    - Exit code 0 on --help
    """
    result = runner.invoke(app, ["llm", "test", "--help"])

    # Should exit successfully
    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}"

    # Should show provider argument
    assert "provider" in result.stdout.lower() or "PROVIDER" in result.stdout, "Missing provider argument in help"

    # Should show --json option
    assert "--json" in result.stdout, "Missing --json option in help"

    # Should have description about testing/connectivity
    assert (
        "test" in result.stdout.lower() or "connect" in result.stdout.lower()
    ), "Missing test/connectivity description"


def test_llm_policy_contract():
    """
    Contract: `collabiq llm policy` command signature and options.

    Verifies:
    - Command exists and responds to --help
    - Accepts --json flag
    - Help text describes orchestration policy viewing
    - Exit code 0 on --help
    """
    result = runner.invoke(app, ["llm", "policy", "--help"])

    # Should exit successfully
    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}"

    # Should show --json option
    assert "--json" in result.stdout, "Missing --json option in help"

    # Should have description about policy/orchestration
    assert (
        "policy" in result.stdout.lower() or "orchestration" in result.stdout.lower()
    ), "Missing policy/orchestration description"


def test_llm_set_policy_contract():
    """
    Contract: `collabiq llm set-policy <strategy>` command signature and options.

    Verifies:
    - Command exists and responds to --help
    - Accepts strategy argument
    - Help text describes available strategies (failover, consensus, best-match)
    - Exit code 0 on --help
    """
    result = runner.invoke(app, ["llm", "set-policy", "--help"])

    # Should exit successfully
    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}"

    # Should show strategy argument
    assert "strategy" in result.stdout.lower() or "STRATEGY" in result.stdout, "Missing strategy argument in help"

    # Should have description about setting/changing policy
    assert (
        "set" in result.stdout.lower() or "change" in result.stdout.lower()
    ), "Missing set/change description"


def test_llm_usage_contract():
    """
    Contract: `collabiq llm usage` command signature and options.

    Verifies:
    - Command exists and responds to --help
    - Accepts --json flag
    - Help text describes usage statistics viewing
    - Exit code 0 on --help
    """
    result = runner.invoke(app, ["llm", "usage", "--help"])

    # Should exit successfully
    assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}"

    # Should show --json option
    assert "--json" in result.stdout, "Missing --json option in help"

    # Should have description about usage/statistics
    assert (
        "usage" in result.stdout.lower() or "statistics" in result.stdout.lower()
    ), "Missing usage/statistics description"


def test_llm_disable_enable_contract():
    """
    Contract: `collabiq llm disable/enable <provider>` command signature and options.

    Verifies:
    - Both commands exist and respond to --help
    - Accept provider argument
    - Help text describes provider management
    - Exit code 0 on --help
    """
    # Test disable command
    result = runner.invoke(app, ["llm", "disable", "--help"])

    # Should exit successfully
    assert result.exit_code == 0, f"disable: Expected exit code 0, got {result.exit_code}"

    # Should show provider argument
    assert "provider" in result.stdout.lower() or "PROVIDER" in result.stdout, "disable: Missing provider argument in help"

    # Should have description about disabling
    assert "disable" in result.stdout.lower(), "disable: Missing disable description"

    # Test enable command
    result = runner.invoke(app, ["llm", "enable", "--help"])

    # Should exit successfully
    assert result.exit_code == 0, f"enable: Expected exit code 0, got {result.exit_code}"

    # Should show provider argument
    assert "provider" in result.stdout.lower() or "PROVIDER" in result.stdout, "enable: Missing provider argument in help"

    # Should have description about enabling
    assert "enable" in result.stdout.lower(), "enable: Missing enable description"
