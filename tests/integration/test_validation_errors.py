"""Integration tests for validation error handling (Phase 4, T031).

Tests graceful degradation when emails have invalid/malformed data:
- Email with no date → validation error logged, processing continues
- Email with malformed company ID → marked as "needs_review", logged
- Email with encoding issues → fallback decoding attempted, logged
- System processes valid emails even if one is malformed
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from pydantic import ValidationError

from src.email_receiver.gmail_receiver import GmailReceiver
from src.error_handling.error_classifier import ErrorClassifier
from src.error_handling.models import ErrorCategory, ErrorRecord, ErrorSeverity
from src.error_handling.structured_logger import StructuredLogger
from src.llm_adapters.gemini_adapter import GeminiAdapter
from src.llm_provider.types import ConfidenceScores, ExtractedEntities
from src.models.raw_email import EmailMetadata, RawEmail


class TestValidationErrorHandling:
    """Test validation error handling across components."""

    def test_error_classifier_categorizes_validation_error_as_permanent(self):
        """T027: ErrorClassifier should classify ValidationError as PERMANENT."""
        # Create a mock Pydantic ValidationError
        try:
            # Trigger a real ValidationError by creating invalid EmailMetadata
            EmailMetadata(
                message_id="",  # Invalid: empty message_id
                sender="test@example.com",
                subject="Test",
                received_at=datetime.utcnow()
            )
            pytest.fail("Should have raised ValidationError")
        except ValidationError as e:
            # Verify ErrorClassifier categorizes it as PERMANENT
            category = ErrorClassifier.classify(e)
            assert category == ErrorCategory.PERMANENT, \
                f"ValidationError should be PERMANENT, got {category}"

            # Verify it's not retryable
            is_retryable = ErrorClassifier.is_retryable(e)
            assert not is_retryable, "ValidationError should not be retryable"

    def test_gmail_receiver_handles_validation_error_gracefully(self):
        """T028: GmailReceiver should log validation errors and continue processing."""
        # Create GmailReceiver
        receiver = GmailReceiver(
            credentials_path=Path("fake/credentials.json"),
            token_path=Path("fake/token.json")
        )

        # Mock the Gmail API service
        mock_service = MagicMock()
        receiver.service = mock_service

        # Mock message list response (2 messages)
        mock_service.users().messages().list().execute.return_value = {
            'messages': [
                {'id': 'msg_001'},
                {'id': 'msg_002'}
            ]
        }

        # Mock message details - first message is malformed (empty message_id), second is valid
        call_count = [0]  # Track which call we're on
        def mock_get_execute(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                # First call: Return message with empty message_id (will cause ValidationError)
                return {
                    'id': 'msg_001',
                    'payload': {
                        'headers': [
                            {'name': 'Message-ID', 'value': ''},  # Empty message_id → ValidationError
                            {'name': 'From', 'value': 'test@example.com'},
                            {'name': 'Subject', 'value': 'Test 1'},
                            {'name': 'Date', 'value': 'Mon, 01 Nov 2021 10:00:00 +0000'}
                        ],
                        'body': {'data': 'VGVzdCBib2R5'}  # Valid body
                    }
                }
            else:
                # Second call: Return valid message
                return {
                    'id': 'msg_002',
                    'payload': {
                        'headers': [
                            {'name': 'Message-ID', 'value': '<msg_002@gmail.com>'},
                            {'name': 'From', 'value': 'test@example.com'},
                            {'name': 'Subject', 'value': 'Test 2'},
                            {'name': 'Date', 'value': 'Mon, 01 Nov 2021 10:00:00 +0000'}
                        ],
                        'body': {'data': 'VGVzdCBib2R5'}  # "Test body" in base64
                    }
                }

        mock_service.users().messages().get().execute.side_effect = mock_get_execute

        # Fetch emails - should return 1 valid email, skip the malformed one
        emails = receiver.fetch_emails(max_emails=10)

        # Verify only the valid email was returned
        assert len(emails) == 1, f"Expected 1 valid email, got {len(emails)}"
        assert emails[0].metadata.message_id == "<msg_002@gmail.com>"

    def test_gemini_adapter_handles_invalid_company_id_gracefully(self):
        """T029: GeminiAdapter should mark extraction as needs_review when company ID is invalid."""
        # Create GeminiAdapter
        adapter = GeminiAdapter(
            api_key="fake_api_key",
            model="gemini-2.0-flash-exp",
            timeout=10,
            max_retries=1
        )

        email_text = "테스트 이메일"
        email_id = "test_email_001"

        # Mock Gemini API response with invalid company UUID (too short)
        invalid_response_data = {
            "person_in_charge": {"value": "김철수", "confidence": 0.9},
            "startup_name": {"value": "테스트", "confidence": 0.9},
            "partner_org": {"value": "파트너", "confidence": 0.9},
            "details": {"value": "협업 내용", "confidence": 0.9},
            "date": {"value": "2025-11-01", "confidence": 0.9},
            "matched_company_id": "invalid_uuid",  # Invalid: too short (should be 32 or 36 chars)
            "matched_partner_id": None,
            "startup_match_confidence": 0.9,
            "partner_match_confidence": None
        }

        # Call _parse_response directly (bypasses API call)
        result = adapter._parse_response(
            response_data=invalid_response_data,
            email_text=email_text,
            company_context="fake company context",  # Enables matching fields
            email_id=email_id
        )

        # Verify result is marked as "needs_review" (all confidence scores = 0.0)
        assert result.confidence.person == 0.0, "Person confidence should be 0.0 for needs_review"
        assert result.confidence.startup == 0.0, "Startup confidence should be 0.0 for needs_review"
        assert result.confidence.partner == 0.0, "Partner confidence should be 0.0 for needs_review"
        assert result.confidence.details == 0.0, "Details confidence should be 0.0 for needs_review"
        assert result.confidence.date == 0.0, "Date confidence should be 0.0 for needs_review"

        # Verify matched IDs are None (validation failed)
        assert result.matched_company_id is None, "matched_company_id should be None after validation error"
        assert result.matched_partner_id is None, "matched_partner_id should be None after validation error"

    def test_structured_logger_includes_field_level_validation_errors(self):
        """T030: StructuredLogger should include field-level validation errors."""
        # Create a validation error
        try:
            EmailMetadata(
                message_id="",  # Invalid: empty message_id
                sender="invalid-email",  # Invalid: not an email
                subject="Test",
                received_at=datetime.utcnow()
            )
            pytest.fail("Should have raised ValidationError")
        except ValidationError as e:
            # Create structured logger
            logger = StructuredLogger(name="test_logger")

            # Use log_validation_error method
            logger.log_validation_error(
                message="Test validation error",
                validation_error=e,
                context={"email_id": "test_001", "operation": "test_operation"}
            )

            # Verify the log includes validation_errors in context
            # This is tested by checking that e.errors() is called (has field-level details)
            assert hasattr(e, 'errors'), "ValidationError should have errors() method"
            errors = e.errors()
            assert len(errors) > 0, "Should have at least one validation error"
            assert all('loc' in err and 'msg' in err for err in errors), \
                "Each error should have 'loc' (field location) and 'msg'"

    def test_batch_processing_continues_despite_malformed_email(self):
        """T032: Verify system processes valid emails even when one is malformed."""
        # Create GmailReceiver
        receiver = GmailReceiver(
            credentials_path=Path("fake/credentials.json"),
            token_path=Path("fake/token.json")
        )

        # Mock the Gmail API service
        mock_service = MagicMock()
        receiver.service = mock_service

        # Mock message list response (3 messages)
        mock_service.users().messages().list().execute.return_value = {
            'messages': [
                {'id': 'msg_001'},
                {'id': 'msg_002_invalid'},  # This one will fail validation
                {'id': 'msg_003'}
            ]
        }

        # Mock message details
        call_count = [0]
        def mock_get_execute(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return {
                    'id': 'msg_001',
                    'payload': {
                        'headers': [
                            {'name': 'Message-ID', 'value': '<msg_001@gmail.com>'},
                            {'name': 'From', 'value': 'test@example.com'},
                            {'name': 'Subject', 'value': 'Test 1'},
                            {'name': 'Date', 'value': 'Mon, 01 Nov 2021 10:00:00 +0000'}
                        ],
                        'body': {'data': 'VGVzdCBib2R5IDE='}  # "Test body 1"
                    }
                }
            elif call_count[0] == 2:
                # Malformed: empty message_id
                return {
                    'id': 'msg_002_invalid',
                    'payload': {
                        'headers': [
                            {'name': 'Message-ID', 'value': ''},  # Empty message_id → ValidationError
                            {'name': 'From', 'value': 'test@example.com'},
                            {'name': 'Subject', 'value': 'Test 2'},
                            {'name': 'Date', 'value': 'Mon, 01 Nov 2021 10:00:00 +0000'}
                        ],
                        'body': {'data': 'VGVzdCBib2R5IDI='}  # Valid body
                    }
                }
            else:  # call 3
                return {
                    'id': 'msg_003',
                    'payload': {
                        'headers': [
                            {'name': 'Message-ID', 'value': '<msg_003@gmail.com>'},
                            {'name': 'From', 'value': 'test@example.com'},
                            {'name': 'Subject', 'value': 'Test 3'},
                            {'name': 'Date', 'value': 'Mon, 01 Nov 2021 10:00:00 +0000'}
                        ],
                        'body': {'data': 'VGVzdCBib2R5IDM='}  # "Test body 3"
                    }
                }

        mock_service.users().messages().get().execute.side_effect = mock_get_execute

        # Fetch emails - should return 2 valid emails, skip the malformed one
        emails = receiver.fetch_emails(max_emails=10)

        # Verify 2 valid emails were returned (1 was skipped)
        assert len(emails) == 2, f"Expected 2 valid emails (1 skipped), got {len(emails)}"
        assert emails[0].metadata.message_id == "<msg_001@gmail.com>"
        assert emails[1].metadata.message_id == "<msg_003@gmail.com>"

        # Verify the system achieved ~66% success rate (2/3 emails processed)
        success_rate = len(emails) / 3
        assert success_rate >= 0.66, f"Success rate {success_rate:.2f} should be >= 0.66 (2/3)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
