"""Contract tests for DLQManager class.

Tests verify the API contract for Dead Letter Queue operations:
- save_failed_write() - persist failed write attempts
- load_dlq_entry() - deserialize DLQ entries
- list_dlq_entries() - enumerate all DLQ files
- retry_failed_write() - attempt to reprocess failed writes

TDD: These tests are written FIRST and should FAIL before implementation.
"""

import pytest
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from typing import Optional

from notion_integrator import DLQManager
from llm_provider.types import DLQEntry, WriteResult
from tests.fixtures import create_valid_extracted_data


class TestDLQManagerContract:
    """Contract tests for DLQManager operations."""

    @pytest.fixture
    def temp_dlq_dir(self, tmp_path):
        """Create a temporary DLQ directory for testing."""
        dlq_dir = tmp_path / "data" / "dlq"
        dlq_dir.mkdir(parents=True, exist_ok=True)
        return dlq_dir

    @pytest.fixture
    def dlq_manager(self, temp_dlq_dir):
        """Create DLQManager instance with temporary directory."""
        return DLQManager(dlq_dir=str(temp_dlq_dir))

    @pytest.fixture
    def sample_extracted_data(self):
        """Sample extracted data for testing."""
        return create_valid_extracted_data(email_id="test-dlq-001")

    @pytest.fixture
    def sample_error_details(self):
        """Sample error details for DLQ entry."""
        return {
            "error_type": "APIResponseError",
            "error_message": "Invalid property value",
            "status_code": 400,
        }

    def test_save_failed_write_method_signature(self, dlq_manager):
        """T055: Verify save_failed_write() method exists with correct signature.

        Contract:
        - Method name: save_failed_write
        - Parameters: extracted_data, error_details
        - Returns: str (file path to created DLQ entry)
        - Not async (synchronous method)
        """
        # Verify method exists
        assert hasattr(dlq_manager, "save_failed_write"), \
            "DLQManager must have save_failed_write method"

        # Verify method is callable
        method = getattr(dlq_manager, "save_failed_write")
        assert callable(method), "save_failed_write must be callable"

        # Verify method is NOT async
        import inspect
        assert not inspect.iscoroutinefunction(method), \
            "save_failed_write must be synchronous (not async)"

    def test_save_failed_write_file_creation(
        self, dlq_manager, sample_extracted_data, sample_error_details, temp_dlq_dir
    ):
        """T056: Verify save_failed_write() creates file with correct naming.

        Contract:
        - File naming format: {email_id}_{timestamp}.json
        - File created in dlq_dir
        - Returns file path
        - File contains valid JSON
        """
        # Execute save operation
        file_path = dlq_manager.save_failed_write(
            extracted_data=sample_extracted_data,
            error_details=sample_error_details
        )

        # Verify file path returned
        assert isinstance(file_path, str), \
            "save_failed_write must return file path as string"

        # Verify file exists
        assert Path(file_path).exists(), \
            f"DLQ file must be created at {file_path}"

        # Verify file is in correct directory
        assert str(temp_dlq_dir) in file_path, \
            "DLQ file must be created in dlq_dir"

        # Verify file naming pattern (email_id_timestamp.json)
        filename = Path(file_path).name
        assert filename.startswith("test-dlq-001_"), \
            "Filename must start with email_id"
        assert filename.endswith(".json"), \
            "Filename must have .json extension"

        # Verify file contains valid JSON
        with open(file_path, "r") as f:
            data = json.load(f)
            assert isinstance(data, dict), "DLQ file must contain JSON object"

    def test_save_failed_write_serialization(
        self, dlq_manager, sample_extracted_data, sample_error_details
    ):
        """T057: Verify save_failed_write() serializes data correctly.

        Contract:
        - DLQ entry includes email_id
        - DLQ entry includes failed_at timestamp
        - DLQ entry includes error details
        - DLQ entry includes full extracted_data
        - ExtractedEntitiesWithClassification is serialized to JSON
        """
        # Execute save operation
        file_path = dlq_manager.save_failed_write(
            extracted_data=sample_extracted_data,
            error_details=sample_error_details
        )

        # Load and verify serialized data
        with open(file_path, "r") as f:
            data = json.load(f)

        # Verify required fields
        assert "email_id" in data, "DLQ entry must include email_id"
        assert data["email_id"] == "test-dlq-001", \
            "email_id must match input"

        assert "failed_at" in data, "DLQ entry must include failed_at timestamp"
        assert isinstance(data["failed_at"], str), \
            "failed_at must be serialized as ISO string"

        assert "error" in data, "DLQ entry must include error details"
        assert data["error"]["error_type"] == "APIResponseError", \
            "error_type must be preserved"
        assert data["error"]["status_code"] == 400, \
            "status_code must be preserved"

        assert "extracted_data" in data, "DLQ entry must include full extracted_data"
        assert data["extracted_data"]["email_id"] == "test-dlq-001", \
            "extracted_data must be fully serialized"

        assert "retry_count" in data, "DLQ entry must include retry_count"
        assert data["retry_count"] == 0, \
            "Initial retry_count must be 0"

    def test_load_dlq_entry_method_signature(self, dlq_manager):
        """T058: Verify load_dlq_entry() method exists with correct signature.

        Contract:
        - Method name: load_dlq_entry
        - Parameter: file_path (str)
        - Returns: DLQEntry (Pydantic model)
        - Not async (synchronous method)
        """
        # Verify method exists
        assert hasattr(dlq_manager, "load_dlq_entry"), \
            "DLQManager must have load_dlq_entry method"

        # Verify method is callable
        method = getattr(dlq_manager, "load_dlq_entry")
        assert callable(method), "load_dlq_entry must be callable"

        # Verify method is NOT async
        import inspect
        assert not inspect.iscoroutinefunction(method), \
            "load_dlq_entry must be synchronous (not async)"

    def test_load_dlq_entry_deserialization(
        self, dlq_manager, sample_extracted_data, sample_error_details
    ):
        """T058: Verify load_dlq_entry() deserializes DLQ entry correctly.

        Contract:
        - Returns DLQEntry instance
        - email_id is preserved
        - failed_at is deserialized to datetime
        - error details are preserved
        - extracted_data is deserialized to ExtractedEntitiesWithClassification
        """
        # First, create a DLQ entry
        file_path = dlq_manager.save_failed_write(
            extracted_data=sample_extracted_data,
            error_details=sample_error_details
        )

        # Load the entry back
        dlq_entry = dlq_manager.load_dlq_entry(file_path)

        # Verify return type
        assert isinstance(dlq_entry, DLQEntry), \
            "load_dlq_entry must return DLQEntry instance"

        # Verify fields
        assert dlq_entry.email_id == "test-dlq-001", \
            "email_id must be preserved"

        assert isinstance(dlq_entry.failed_at, datetime), \
            "failed_at must be deserialized to datetime"

        assert dlq_entry.error["error_type"] == "APIResponseError", \
            "error_type must be preserved"
        assert dlq_entry.error["status_code"] == 400, \
            "status_code must be preserved"

        assert dlq_entry.extracted_data.email_id == "test-dlq-001", \
            "extracted_data must be deserialized correctly"

        assert dlq_entry.retry_count == 0, \
            "retry_count must be preserved"

    def test_list_dlq_entries_method_signature(self, dlq_manager):
        """T059: Verify list_dlq_entries() method exists with correct signature.

        Contract:
        - Method name: list_dlq_entries
        - No parameters
        - Returns: List[str] (list of file paths)
        - Not async (synchronous method)
        """
        # Verify method exists
        assert hasattr(dlq_manager, "list_dlq_entries"), \
            "DLQManager must have list_dlq_entries method"

        # Verify method is callable
        method = getattr(dlq_manager, "list_dlq_entries")
        assert callable(method), "list_dlq_entries must be callable"

        # Verify method is NOT async
        import inspect
        assert not inspect.iscoroutinefunction(method), \
            "list_dlq_entries must be synchronous (not async)"

    def test_list_dlq_entries_listing(
        self, dlq_manager, sample_extracted_data, sample_error_details
    ):
        """T059: Verify list_dlq_entries() lists all DLQ files.

        Contract:
        - Returns list of file paths
        - Includes all .json files in dlq_dir
        - Files are sorted (oldest first)
        - Empty list if no DLQ entries
        """
        # Initially, no DLQ entries
        entries = dlq_manager.list_dlq_entries()
        initial_count = len(entries)

        # Create 3 DLQ entries
        file1 = dlq_manager.save_failed_write(
            extracted_data=create_valid_extracted_data(email_id="dlq-test-001"),
            error_details=sample_error_details
        )

        file2 = dlq_manager.save_failed_write(
            extracted_data=create_valid_extracted_data(email_id="dlq-test-002"),
            error_details=sample_error_details
        )

        file3 = dlq_manager.save_failed_write(
            extracted_data=create_valid_extracted_data(email_id="dlq-test-003"),
            error_details=sample_error_details
        )

        # List entries
        entries = dlq_manager.list_dlq_entries()

        # Verify count
        assert len(entries) == initial_count + 3, \
            "list_dlq_entries must return all DLQ files"

        # Verify all files are in the list
        entry_paths = [str(Path(e).resolve()) for e in entries]
        assert str(Path(file1).resolve()) in entry_paths, "file1 must be in list"
        assert str(Path(file2).resolve()) in entry_paths, "file2 must be in list"
        assert str(Path(file3).resolve()) in entry_paths, "file3 must be in list"

        # Verify return type
        assert isinstance(entries, list), \
            "list_dlq_entries must return a list"
        assert all(isinstance(e, str) for e in entries), \
            "All entries must be file path strings"
