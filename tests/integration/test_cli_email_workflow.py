"""
Integration tests for CLI email command workflows.

Tests the interaction between email commands (fetch → clean → list → process).
"""

import json
import pytest
from pathlib import Path
from typer.testing import CliRunner
from collabiq import app

runner = CliRunner()


@pytest.fixture
def temp_data_dir(tmp_path):
    """Create temporary data directory for testing."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "raw").mkdir()
    (data_dir / "metadata").mkdir()
    (data_dir / "logs").mkdir()
    return data_dir


def test_fetch_clean_list_workflow(temp_data_dir, monkeypatch):
    """
    Integration test for fetch → clean → list workflow (T030).

    Verifies:
    - fetch command creates raw email files
    - clean command processes raw emails
    - list command displays processed emails
    - All commands produce valid JSON output with --json flag
    """
    # This test will verify the workflow once commands are implemented
    # For now, we just ensure commands exist and accept the right arguments

    # Test fetch command exists
    result = runner.invoke(app, ["email", "fetch", "--help"])
    assert result.exit_code == 0, "fetch command should exist"

    # Test clean command exists
    result = runner.invoke(app, ["email", "clean", "--help"])
    assert result.exit_code == 0, "clean command should exist"

    # Test list command exists
    result = runner.invoke(app, ["email", "list", "--help"])
    assert result.exit_code == 0, "list command should exist"


def test_full_email_process_pipeline(temp_data_dir, monkeypatch):
    """
    Integration test for full email process pipeline (T031).

    Verifies:
    - process command orchestrates fetch → clean → extract → write
    - Progress indicators are shown for each stage
    - Summary report is generated
    - Errors in one stage don't crash entire pipeline
    - JSON output includes results from all stages
    """
    # This test will verify the full pipeline once commands are implemented
    # For now, we just ensure process command exists

    result = runner.invoke(app, ["email", "process", "--help"])
    assert result.exit_code == 0, "process command should exist"
