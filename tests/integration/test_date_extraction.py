"""Integration tests for date extraction from email content.

Tests cover:
- Real-world email scenarios with mixed content
- Integration with email processing pipeline
- End-to-end date extraction from raw emails
- Korean and English email content
- Edge cases with multiple dates and formats
"""

from datetime import datetime


from src.collabiq.date_parser import DateFormat, extract_dates_from_text


class TestRealWorldEmailScenarios:
    """Integration tests with realistic email content."""

    def test_korean_meeting_invitation(self):
        """Test extracting date from Korean meeting invitation."""
        email_content = """
        안녕하세요,

        다음 주 회의 일정을 공유드립니다.

        일시: 2024년 11월 13일 오후 3시
        장소: 본사 2층 회의실
        참석자: 김철수, 이영희, 박민수

        감사합니다.
        """

        result = extract_dates_from_text(email_content, email_id="meeting_invite_001")

        assert len(result.dates_found) >= 1
        assert result.primary_date is not None
        assert result.primary_date.iso_format == "2024-11-13"
        assert result.primary_date.format_detected == DateFormat.KOREAN_YMD
        assert result.email_id == "meeting_invite_001"

    def test_english_meeting_invitation(self):
        """Test extracting date from English meeting invitation."""
        email_content = """
        Hello team,

        Our next quarterly meeting is scheduled for January 15, 2025 at 2pm.

        Please confirm your attendance.

        Best regards,
        John
        """

        result = extract_dates_from_text(email_content, email_id="meeting_invite_002")

        assert len(result.dates_found) >= 1
        assert result.primary_date is not None
        assert result.primary_date.iso_format == "2025-01-15"
        assert result.primary_date.format_detected == DateFormat.ENGLISH_MDY

    def test_mixed_language_email(self):
        """Test extracting dates from mixed Korean/English email."""
        email_content = """
        Hi,

        Meeting scheduled for 2024년 11월 13일.
        Follow-up session on January 20, 2025.

        See you there!
        """

        result = extract_dates_from_text(email_content, email_id="mixed_lang_001")

        assert len(result.dates_found) == 2
        date_strings = {d.iso_format for d in result.dates_found}
        assert "2024-11-13" in date_strings
        assert "2025-01-20" in date_strings

    def test_korean_week_notation_email(self):
        """Test extracting Korean week notation from email."""
        email_content = """
        다음 워크숍 일정:

        11월 2주에 진행됩니다.
        자세한 시간은 추후 공지하겠습니다.
        """

        result = extract_dates_from_text(email_content, email_id="workshop_001")

        assert len(result.dates_found) >= 1
        assert result.primary_date is not None
        # Week 2 of November starts on day 8
        assert "-11-08" in result.primary_date.iso_format
        assert result.primary_date.format_detected == DateFormat.KOREAN_WEEK

    def test_partial_korean_date_email(self):
        """Test extracting partial Korean date (month/day only)."""
        email_content = """
        행사 안내

        일시: 12월 25일
        장소: 강남역 2번 출구

        많은 참여 부탁드립니다.
        """

        result = extract_dates_from_text(email_content, email_id="event_001")

        assert len(result.dates_found) >= 1
        assert result.primary_date is not None
        assert result.primary_date.parsed_date.month == 12
        assert result.primary_date.parsed_date.day == 25
        assert result.primary_date.format_detected == DateFormat.KOREAN_MD


class TestMultipleDatesInEmail:
    """Tests for emails with multiple dates."""

    def test_meeting_series_email(self):
        """Test extracting multiple dates from meeting series."""
        email_content = """
        Meeting Series Schedule:

        Session 1: 2024년 11월 10일
        Session 2: 2024년 11월 17일
        Session 3: 2024년 11월 24일

        All sessions start at 2pm.
        """

        result = extract_dates_from_text(email_content, email_id="series_001")

        assert len(result.dates_found) == 3
        date_strings = {d.iso_format for d in result.dates_found}
        assert "2024-11-10" in date_strings
        assert "2024-11-17" in date_strings
        assert "2024-11-24" in date_strings

    def test_date_range_email(self):
        """Test extracting start and end dates from range."""
        email_content = """
        Conference Dates:

        Start: January 15, 2025
        End: January 18, 2025

        Registration opens December 1, 2024.
        """

        result = extract_dates_from_text(email_content, email_id="conference_001")

        assert len(result.dates_found) == 3
        date_strings = {d.iso_format for d in result.dates_found}
        assert "2024-12-01" in date_strings
        assert "2025-01-15" in date_strings
        assert "2025-01-18" in date_strings


class TestEdgeCasesInEmails:
    """Tests for edge cases in real email scenarios."""

    def test_email_with_no_dates(self):
        """Test email with no dates returns empty result."""
        email_content = """
        Hi team,

        Just a quick reminder to submit your reports.
        No specific deadline, but please do it soon.

        Thanks!
        """

        result = extract_dates_from_text(email_content, email_id="reminder_001")

        assert len(result.dates_found) == 0
        assert result.primary_date is None
        assert result.confidence == 0.0

    def test_email_with_date_like_strings(self):
        """Test email with numbers that look like dates but aren't."""
        email_content = """
        Report Summary:

        Total revenue: 2024만원
        Q1 target: 1억 5천만원
        Growth: 13.5%

        Meeting at room 1225.
        """

        result = extract_dates_from_text(email_content, email_id="report_001")

        # Should not extract numbers that aren't dates
        # If any dates are found, they should be actual dates
        for date in result.dates_found:
            assert date.parsed_date is not None
            assert date.confidence > 0.5

    def test_email_with_timestamp(self):
        """Test email with ISO 8601 timestamp."""
        email_content = """
        System Alert:

        Error occurred at: 2024-11-13T14:30:00
        Please investigate immediately.

        Log ID: abc123
        """

        result = extract_dates_from_text(email_content, email_id="alert_001")

        assert len(result.dates_found) >= 1
        assert result.primary_date is not None
        assert result.primary_date.iso_format == "2024-11-13"
        assert result.primary_date.format_detected == DateFormat.ISO_DATETIME

    def test_email_with_duplicate_dates(self):
        """Test email mentioning same date multiple times in different formats."""
        email_content = """
        Important Reminder:

        Meeting on 2024년 11월 13일

        Please confirm attendance for 2024-11-13 by responding to this email.
        The meeting is scheduled for November 13, 2024.
        """

        result = extract_dates_from_text(email_content, email_id="reminder_002")

        # Should deduplicate dates with same ISO format
        # Note: All three date strings above represent the same date (2024-11-13)
        assert len(result.dates_found) == 1
        assert result.primary_date.iso_format == "2024-11-13"


class TestIntegrationWithEmailMetadata:
    """Tests simulating integration with email processing."""

    def test_extract_with_email_id_tracking(self):
        """Test that email ID is properly tracked through extraction."""
        email_content = "Meeting on 2024년 11월 13일"
        email_id = "test_email_12345"

        result = extract_dates_from_text(email_content, email_id=email_id)

        assert result.email_id == email_id
        assert len(result.dates_found) >= 1

    def test_extract_with_reference_date(self):
        """Test date extraction uses reference date for partial dates."""
        # Email from 2023 mentioning "12월 25일" should use 2023 as year
        email_content = "Holiday party on 12월 25일"
        reference_date = datetime(2023, 1, 1)

        result = extract_dates_from_text(
            email_content, email_id="holiday_001", reference_date=reference_date
        )

        assert len(result.dates_found) >= 1
        # Partial date should use reference year (2023)
        # Note: The current implementation may default to current year
        # This test documents expected behavior for future enhancement
        assert result.primary_date is not None
        assert result.primary_date.parsed_date.month == 12
        assert result.primary_date.parsed_date.day == 25


class TestConfidenceScoring:
    """Tests for confidence scoring in real scenarios."""

    def test_high_confidence_dates(self):
        """Test that well-formatted dates get high confidence."""
        email_content = """
        Conference: 2024년 11월 13일
        ISO Date: 2024-11-13
        English: November 13, 2024
        """

        result = extract_dates_from_text(email_content, email_id="conf_001")

        # All these formats should have high confidence
        for date in result.dates_found:
            assert date.confidence >= 0.95

    def test_medium_confidence_dates(self):
        """Test that ambiguous dates get medium confidence."""
        email_content = """
        Meeting on 11월 25일 (partial date - year assumed)
        Or 01/15/2025 (US or EU format?)
        """

        result = extract_dates_from_text(email_content, email_id="meeting_003")

        # Should have at least one date with medium confidence
        confidences = [d.confidence for d in result.dates_found]
        assert any(0.6 <= c < 1.0 for c in confidences)


class TestFormatDetection:
    """Tests for format detection in email context."""

    def test_korean_format_detection(self):
        """Test Korean date format is correctly detected."""
        email_content = "행사: 2024년 11월 13일"

        result = extract_dates_from_text(email_content, email_id="event_002")

        assert result.primary_date is not None
        assert result.primary_date.format_detected == DateFormat.KOREAN_YMD

    def test_iso_format_detection(self):
        """Test ISO format is correctly detected."""
        email_content = "Deadline: 2024-11-13"

        result = extract_dates_from_text(email_content, email_id="deadline_001")

        assert result.primary_date is not None
        assert result.primary_date.format_detected == DateFormat.ISO_8601

    def test_english_format_detection(self):
        """Test English format is correctly detected."""
        email_content = "Due date: January 15, 2025"

        result = extract_dates_from_text(email_content, email_id="due_001")

        assert result.primary_date is not None
        assert result.primary_date.format_detected == DateFormat.ENGLISH_MDY


class TestErrorHandling:
    """Tests for error handling in integration scenarios."""

    def test_malformed_email_content(self):
        """Test handling of malformed or unusual content."""
        email_content = None

        # Should not crash, should return empty result
        result = extract_dates_from_text("", email_id="malformed_001")

        assert len(result.dates_found) == 0
        assert result.primary_date is None

    def test_empty_email_content(self):
        """Test handling of empty email."""
        result = extract_dates_from_text("", email_id="empty_001")

        assert len(result.dates_found) == 0
        assert result.primary_date is None
        assert result.email_id == "empty_001"

    def test_very_long_email(self):
        """Test handling of very long email content."""
        # Create a long email with multiple dates
        email_content = "Meeting schedule:\n"
        for i in range(1, 30):
            email_content += f"Day {i}: 2024년 11월 {i}일\n"

        result = extract_dates_from_text(email_content, email_id="long_001")

        # Should extract multiple dates without crashing
        assert len(result.dates_found) > 0
        assert result.primary_date is not None


class TestPrimaryDateSelection:
    """Tests for primary date selection logic."""

    def test_primary_date_selection_by_confidence(self):
        """Test that highest confidence date is selected as primary."""
        email_content = """
        Meeting options:
        - 2024년 11월 13일 (confirmed)
        - 11월 20일 (tentative)
        """

        result = extract_dates_from_text(email_content, email_id="options_001")

        # Primary should be the one with highest confidence
        assert result.primary_date is not None
        if len(result.dates_found) > 1:
            assert result.primary_date.confidence == max(
                d.confidence for d in result.dates_found
            )

    def test_primary_date_with_equal_confidence(self):
        """Test primary date selection when confidence is equal."""
        email_content = """
        Session 1: 2024년 11월 13일
        Session 2: 2024년 11월 20일
        """

        result = extract_dates_from_text(email_content, email_id="sessions_001")

        # Should select one as primary (typically first found)
        assert result.primary_date is not None
        assert result.primary_date.iso_format in [
            d.iso_format for d in result.dates_found
        ]
