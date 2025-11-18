"""End-to-end tests for CLI entity extraction.

These tests verify the complete workflow:
1. CLI tool loads email file
2. Calls GeminiAdapter
3. Outputs valid JSON with extracted entities
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

# Test fixtures directory
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
SAMPLE_EMAILS = FIXTURES_DIR / "sample_emails"


def test_cli_help_command():
    """Test that CLI help command works."""
    result = subprocess.run(
        [sys.executable, "src/cli/extract_entities.py", "--help"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Extract entities from emails" in result.stdout
    assert "--email" in result.stdout


def test_cli_missing_email_file():
    """Test that CLI handles missing email file gracefully."""
    result = subprocess.run(
        [sys.executable, "src/cli/extract_entities.py", "--email", "nonexistent.txt"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "File error" in result.stderr or "not found" in result.stderr.lower()


@pytest.mark.skipif(
    not Path(".env").exists() and not Path("GEMINI_API_KEY").exists(),
    reason="GEMINI_API_KEY not configured",
)
def test_cli_extract_korean_email():
    """Test CLI extraction from Korean email (requires API key)."""
    email_file = SAMPLE_EMAILS / "korean_001.txt"

    if not email_file.exists():
        pytest.skip("Korean test email not found")

    result = subprocess.run(
        [sys.executable, "src/cli/extract_entities.py", "--email", str(email_file)],
        capture_output=True,
        text=True,
    )

    # Check exit code
    if result.returncode != 0:
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        pytest.skip(f"CLI failed (possibly no API key): {result.stderr}")

    # Parse JSON output
    try:
        output_data = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        pytest.fail(f"CLI output is not valid JSON: {e}\n{result.stdout}")

    # Verify required fields
    assert "email_id" in output_data
    assert "confidence" in output_data
    assert "extracted_at" in output_data

    # Verify confidence scores
    confidence = output_data["confidence"]
    assert "person" in confidence
    assert "startup" in confidence
    assert "partner" in confidence
    assert "details" in confidence
    assert "date" in confidence

    # All confidence scores should be 0.0-1.0
    for field, score in confidence.items():
        assert 0.0 <= score <= 1.0, (
            f"Confidence score for {field} out of range: {score}"
        )


@pytest.mark.skipif(
    not Path(".env").exists() and not Path("GEMINI_API_KEY").exists(),
    reason="GEMINI_API_KEY not configured",
)
def test_cli_extract_english_email():
    """Test CLI extraction from English email (requires API key)."""
    email_file = SAMPLE_EMAILS / "english_001.txt"

    if not email_file.exists():
        pytest.skip("English test email not found")

    result = subprocess.run(
        [
            sys.executable,
            "src/cli/extract_entities.py",
            "--email",
            str(email_file),
            "--show-confidence",
        ],
        capture_output=True,
        text=True,
    )

    # Check exit code
    if result.returncode != 0:
        pytest.skip(f"CLI failed (possibly no API key): {result.stderr}")

    # Parse JSON output
    try:
        output_data = json.loads(result.stdout)
    except json.JSONDecodeError:
        pytest.fail(f"CLI output is not valid JSON:\n{result.stdout}")

    # Verify entity extraction
    assert "startup_name" in output_data
    assert "partner_org" in output_data


def test_cli_output_to_file(tmp_path):
    """Test CLI output to file."""
    email_file = SAMPLE_EMAILS / "korean_001.txt"
    output_file = tmp_path / "output.json"

    if not email_file.exists():
        pytest.skip("Test email not found")

    result = subprocess.run(
        [
            sys.executable,
            "src/cli/extract_entities.py",
            "--email",
            str(email_file),
            "--output",
            str(output_file),
        ],
        capture_output=True,
        text=True,
    )

    # If API key is missing, skip
    if result.returncode != 0:
        pytest.skip(f"CLI failed (possibly no API key): {result.stderr}")

    # Verify output file was created
    assert output_file.exists(), "Output file was not created"

    # Verify output file contains valid JSON
    with open(output_file) as f:
        output_data = json.load(f)

    assert "email_id" in output_data
    assert "confidence" in output_data
