"""
Unit tests for DuplicateTracker model.

Tests cover tracking, persistence, and duplicate detection per FR-011.
"""

import json
from datetime import datetime
from pathlib import Path
import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from models.duplicate_tracker import DuplicateTracker


def test_duplicate_tracker_init():
    """Test DuplicateTracker initialization with empty set."""
    tracker = DuplicateTracker()

    assert isinstance(tracker.processed_message_ids, set)
    assert len(tracker.processed_message_ids) == 0
    assert isinstance(tracker.last_updated, datetime)
    assert tracker.count() == 0


def test_duplicate_tracker_mark_processed():
    """Test marking message IDs as processed."""
    tracker = DuplicateTracker()

    # Mark first message
    tracker.mark_processed("<MSG1@example.com>")
    assert "<MSG1@example.com>" in tracker.processed_message_ids
    assert tracker.count() == 1

    # Mark second message
    tracker.mark_processed("<MSG2@example.com>")
    assert tracker.count() == 2

    # Mark duplicate (should not increase count)
    tracker.mark_processed("<MSG1@example.com>")
    assert tracker.count() == 2


def test_duplicate_tracker_is_duplicate():
    """Test duplicate detection."""
    tracker = DuplicateTracker()

    message_id = "<TEST@example.com>"

    # Initially not a duplicate
    assert tracker.is_duplicate(message_id) is False

    # Mark as processed
    tracker.mark_processed(message_id)

    # Now it's a duplicate
    assert tracker.is_duplicate(message_id) is True


def test_duplicate_tracker_save_and_load(tmp_path):
    """Test saving and loading tracker from JSON file."""
    tracker_path = tmp_path / "processed_ids.json"

    # Create tracker with some data
    tracker1 = DuplicateTracker()
    tracker1.mark_processed("<MSG1@example.com>")
    tracker1.mark_processed("<MSG2@example.com>")
    tracker1.mark_processed("<MSG3@example.com>")

    # Save to file
    tracker1.save(tracker_path)

    # Verify file exists and contains JSON
    assert tracker_path.exists()
    data = json.loads(tracker_path.read_text())
    assert "processed_message_ids" in data
    assert "last_updated" in data
    assert len(data["processed_message_ids"]) == 3

    # Load from file
    tracker2 = DuplicateTracker.load(tracker_path)

    # Verify loaded tracker has same data
    assert tracker2.count() == 3
    assert tracker2.is_duplicate("<MSG1@example.com>")
    assert tracker2.is_duplicate("<MSG2@example.com>")
    assert tracker2.is_duplicate("<MSG3@example.com>")
    assert tracker2.is_duplicate("<MSG4@example.com>") is False


def test_duplicate_tracker_load_nonexistent_file(tmp_path):
    """Test loading from nonexistent file returns empty tracker."""
    tracker_path = tmp_path / "does_not_exist.json"

    # Load from nonexistent file
    tracker = DuplicateTracker.load(tracker_path)

    # Should return empty tracker
    assert tracker.count() == 0
    assert isinstance(tracker.processed_message_ids, set)


def test_duplicate_tracker_load_invalid_json(tmp_path):
    """Test loading from invalid JSON file raises ValueError."""
    tracker_path = tmp_path / "invalid.json"
    tracker_path.write_text("{ invalid json }")

    # Should raise ValueError
    with pytest.raises(ValueError, match="Invalid JSON"):
        DuplicateTracker.load(tracker_path)


def test_duplicate_tracker_save_creates_directories(tmp_path):
    """Test save creates parent directories if they don't exist."""
    tracker_path = tmp_path / "nested" / "path" / "processed_ids.json"

    tracker = DuplicateTracker()
    tracker.mark_processed("<MSG1@example.com>")

    # Save should create nested directories
    tracker.save(tracker_path)

    assert tracker_path.exists()
    assert tracker_path.parent.exists()


def test_duplicate_tracker_last_updated():
    """Test last_updated timestamp is updated when marking processed."""
    tracker = DuplicateTracker()
    initial_time = tracker.last_updated

    # Mark as processed
    tracker.mark_processed("<MSG1@example.com>")

    # last_updated should be newer
    assert tracker.last_updated >= initial_time


def test_duplicate_tracker_set_serialization(tmp_path):
    """Test that set is properly serialized to list in JSON."""
    tracker_path = tmp_path / "processed_ids.json"

    tracker = DuplicateTracker()
    tracker.mark_processed("<MSG1@example.com>")
    tracker.mark_processed("<MSG2@example.com>")

    # Save to file
    tracker.save(tracker_path)

    # Load raw JSON
    data = json.loads(tracker_path.read_text())

    # processed_message_ids should be a list in JSON
    assert isinstance(data["processed_message_ids"], list)
    assert len(data["processed_message_ids"]) == 2
    assert "<MSG1@example.com>" in data["processed_message_ids"]
    assert "<MSG2@example.com>" in data["processed_message_ids"]


def test_duplicate_tracker_with_gmail_receiver(tmp_path):
    """Test DuplicateTracker integration with GmailReceiver workflow."""
    from email_receiver.gmail_receiver import GmailReceiver

    tracker_path = tmp_path / "metadata" / "processed_ids.json"
    credentials_path = tmp_path / "credentials.json"
    token_path = tmp_path / "token.json"

    # Create dummy credential files
    credentials_path.write_text("{}")
    token_path.write_text("{}")

    # Create receiver
    receiver = GmailReceiver(
        credentials_path=credentials_path,
        token_path=token_path,
        metadata_dir=tmp_path / "metadata"
    )

    message_id = "<TEST@gmail.com>"

    # Initially not a duplicate
    assert receiver.is_duplicate(message_id) is False

    # Mark as processed
    receiver.mark_processed(message_id)

    # Verify file was created
    assert tracker_path.exists()

    # Now it's a duplicate
    assert receiver.is_duplicate(message_id) is True

    # Create new receiver instance (simulating restart)
    receiver2 = GmailReceiver(
        credentials_path=credentials_path,
        token_path=token_path,
        metadata_dir=tmp_path / "metadata"
    )

    # Should still be marked as duplicate
    assert receiver2.is_duplicate(message_id) is True


def test_duplicate_tracker_count():
    """Test count method returns correct number of processed IDs."""
    tracker = DuplicateTracker()

    assert tracker.count() == 0

    tracker.mark_processed("<MSG1@example.com>")
    assert tracker.count() == 1

    tracker.mark_processed("<MSG2@example.com>")
    assert tracker.count() == 2

    tracker.mark_processed("<MSG3@example.com>")
    assert tracker.count() == 3

    # Marking duplicate should not increase count
    tracker.mark_processed("<MSG1@example.com>")
    assert tracker.count() == 3
