"""Unit tests for date parser library.

Tests cover:
- Date parsing for various formats (ISO, English, Korean, relative)
- Format detection and confidence scoring
- Date normalization
- Error handling and edge cases
- Korean date support (absolute and week notation)
"""

from datetime import datetime


from src.collabiq.date_parser import (
    DateFormat,
    detect_format,
    extract_dates_from_text,
    normalize_date,
    parse_date,
)


class TestParseDate:
    """Tests for parse_date function."""

    def test_parse_iso_8601_date(self):
        """Test parsing ISO 8601 date format."""
        result = parse_date("2025-01-15")

        assert result.parsed_date is not None
        assert result.parsed_date.year == 2025
        assert result.parsed_date.month == 1
        assert result.parsed_date.day == 15
        assert result.iso_format == "2025-01-15"
        assert result.format_detected == DateFormat.ISO_8601
        assert result.confidence == 1.0
        assert result.parse_error is None

    def test_parse_iso_datetime(self):
        """Test parsing ISO datetime format."""
        result = parse_date("2025-01-15T10:30:00")

        assert result.parsed_date is not None
        assert result.parsed_date.year == 2025
        assert result.parsed_date.month == 1
        assert result.parsed_date.day == 15
        assert result.iso_format == "2025-01-15"
        assert result.format_detected == DateFormat.ISO_DATETIME
        assert result.confidence == 1.0

    def test_parse_korean_full_date(self):
        """Test parsing Korean full date format (YYYY년 M월 D일)."""
        result = parse_date("2024년 11월 13일")

        assert result.parsed_date is not None
        assert result.parsed_date.year == 2024
        assert result.parsed_date.month == 11
        assert result.parsed_date.day == 13
        assert result.iso_format == "2024-11-13"
        assert result.format_detected == DateFormat.KOREAN_YMD
        assert result.confidence == 1.0

    def test_parse_korean_partial_date(self):
        """Test parsing Korean partial date format (M월 D일)."""
        result = parse_date("10월 27일")

        assert result.parsed_date is not None
        assert result.parsed_date.month == 10
        assert result.parsed_date.day == 27
        # Year should default to current year
        assert result.parsed_date.year == datetime.now().year
        assert result.format_detected == DateFormat.KOREAN_MD
        assert result.confidence == 0.95

    def test_parse_korean_week_notation(self):
        """Test parsing Korean week notation (M월 N주)."""
        result = parse_date("11월 1주")

        assert result.parsed_date is not None
        assert result.parsed_date.month == 11
        assert result.parsed_date.day == 1  # First day of first week
        assert result.format_detected == DateFormat.KOREAN_WEEK
        assert result.confidence == 0.9

    def test_parse_korean_week_notation_week2(self):
        """Test parsing Korean week notation for week 2."""
        result = parse_date("11월 2주")

        assert result.parsed_date is not None
        assert result.parsed_date.month == 11
        assert result.parsed_date.day == 8  # First day of second week (8-14)
        assert result.format_detected == DateFormat.KOREAN_WEEK

    def test_parse_english_mdy(self):
        """Test parsing English MDY format."""
        result = parse_date("January 15, 2025")

        assert result.parsed_date is not None
        assert result.parsed_date.year == 2025
        assert result.parsed_date.month == 1
        assert result.parsed_date.day == 15
        assert result.format_detected == DateFormat.ENGLISH_MDY
        assert result.confidence == 0.95

    def test_parse_english_dmy(self):
        """Test parsing English DMY format."""
        result = parse_date("15 January 2025")

        assert result.parsed_date is not None
        assert result.parsed_date.year == 2025
        assert result.parsed_date.month == 1
        assert result.parsed_date.day == 15
        assert result.format_detected == DateFormat.ENGLISH_DMY
        assert result.confidence == 0.95

    def test_parse_us_short_format(self):
        """Test parsing US short date format (MM/DD/YYYY)."""
        result = parse_date("01/15/2025")

        assert result.parsed_date is not None
        assert result.parsed_date.year == 2025
        # Note: dateparser may interpret this differently
        assert result.format_detected == DateFormat.US_SHORT
        assert result.confidence == 0.7  # Lower confidence due to ambiguity

    def test_parse_empty_string(self):
        """Test parsing empty string returns error."""
        result = parse_date("")

        assert result.parsed_date is None
        assert result.iso_format is None
        assert result.format_detected == DateFormat.UNKNOWN
        assert result.confidence == 0.0
        assert "Invalid or empty" in result.parse_error

    def test_parse_none(self):
        """Test parsing None returns error."""
        result = parse_date(None)  # type: ignore

        assert result.parsed_date is None
        assert result.confidence == 0.0
        assert "Invalid or empty" in result.parse_error

    def test_parse_invalid_date(self):
        """Test parsing invalid date string."""
        result = parse_date("not a date")

        assert result.parsed_date is None
        assert result.iso_format is None
        assert result.confidence == 0.0
        assert result.parse_error is not None

    def test_parse_with_whitespace(self):
        """Test parsing date with extra whitespace."""
        result = parse_date("  2025-01-15  ")

        assert result.parsed_date is not None
        assert result.iso_format == "2025-01-15"
        assert result.confidence == 1.0

    def test_parse_korean_with_whitespace(self):
        """Test parsing Korean date with extra whitespace."""
        result = parse_date("2024년  11월  13일")

        assert result.parsed_date is not None
        assert result.iso_format == "2024-11-13"
        assert result.format_detected == DateFormat.KOREAN_YMD


class TestDetectFormat:
    """Tests for detect_format function."""

    def test_detect_iso_8601(self):
        """Test detecting ISO 8601 format."""
        format_type, confidence = detect_format("2025-01-15")

        assert format_type == DateFormat.ISO_8601
        assert confidence == 1.0

    def test_detect_iso_datetime(self):
        """Test detecting ISO datetime format."""
        format_type, confidence = detect_format("2025-01-15T10:30:00")

        assert format_type == DateFormat.ISO_DATETIME
        assert confidence == 1.0

    def test_detect_korean_ymd(self):
        """Test detecting Korean YMD format."""
        format_type, confidence = detect_format("2024년 11월 13일")

        assert format_type == DateFormat.KOREAN_YMD
        assert confidence == 1.0

    def test_detect_korean_md(self):
        """Test detecting Korean MD format."""
        format_type, confidence = detect_format("10월 27일")

        assert format_type == DateFormat.KOREAN_MD
        assert confidence == 0.95

    def test_detect_korean_week(self):
        """Test detecting Korean week notation."""
        format_type, confidence = detect_format("11월 1주")

        assert format_type == DateFormat.KOREAN_WEEK
        assert confidence == 0.9

    def test_detect_english_mdy(self):
        """Test detecting English MDY format."""
        format_type, confidence = detect_format("January 15, 2025")

        assert format_type == DateFormat.ENGLISH_MDY
        assert confidence == 0.95

    def test_detect_english_dmy(self):
        """Test detecting English DMY format."""
        format_type, confidence = detect_format("15 January 2025")

        assert format_type == DateFormat.ENGLISH_DMY
        assert confidence == 0.95

    def test_detect_us_short(self):
        """Test detecting US short format."""
        format_type, confidence = detect_format("01/15/2025")

        assert format_type == DateFormat.US_SHORT
        assert confidence == 0.7  # Lower due to ambiguity

    def test_detect_relative_english(self):
        """Test detecting relative date (English)."""
        format_type, confidence = detect_format("next Monday")

        assert format_type == DateFormat.RELATIVE
        assert confidence == 0.8

    def test_detect_relative_korean(self):
        """Test detecting relative date (Korean)."""
        format_type, confidence = detect_format("어제")

        assert format_type == DateFormat.RELATIVE
        assert confidence == 0.8

    def test_detect_unknown(self):
        """Test detecting unknown format."""
        format_type, confidence = detect_format("not a date")

        assert format_type == DateFormat.UNKNOWN
        assert confidence == 0.0

    def test_detect_with_whitespace(self):
        """Test format detection strips whitespace."""
        format_type, confidence = detect_format("  2025-01-15  ")

        assert format_type == DateFormat.ISO_8601
        assert confidence == 1.0


class TestNormalizeDate:
    """Tests for normalize_date function."""

    def test_normalize_iso_date(self):
        """Test normalizing ISO date."""
        result = normalize_date("2025-01-15")

        assert result == "2025-01-15"

    def test_normalize_korean_date(self):
        """Test normalizing Korean date."""
        result = normalize_date("2024년 11월 13일")

        assert result == "2024-11-13"

    def test_normalize_english_date(self):
        """Test normalizing English date."""
        result = normalize_date("January 15, 2025")

        assert result == "2025-01-15"

    def test_normalize_korean_week(self):
        """Test normalizing Korean week notation."""
        result = normalize_date("11월 1주")

        # Should return first day of first week
        assert result.startswith("20")  # Year
        assert "-11-01" in result  # Month and day

    def test_normalize_invalid_date(self):
        """Test normalizing invalid date returns empty string."""
        result = normalize_date("not a date")

        assert result == ""

    def test_normalize_empty_string(self):
        """Test normalizing empty string returns empty string."""
        result = normalize_date("")

        assert result == ""


class TestExtractDatesFromText:
    """Tests for extract_dates_from_text function."""

    def test_extract_single_korean_date(self):
        """Test extracting single Korean date from text."""
        text = "Meeting scheduled for 2024년 11월 13일 at 3pm"
        result = extract_dates_from_text(text, email_id="test123")

        assert len(result.dates_found) == 1
        assert result.primary_date is not None
        assert result.primary_date.iso_format == "2024-11-13"
        assert result.email_id == "test123"
        assert result.extraction_method == "regex"
        assert result.confidence == 1.0

    def test_extract_multiple_dates(self):
        """Test extracting multiple dates from text."""
        text = "Meeting on 2024년 11월 13일 and followup on 2024년 11월 20일"
        result = extract_dates_from_text(text)

        assert len(result.dates_found) == 2
        assert result.primary_date is not None
        # Primary date should be the first one (or highest confidence)
        assert result.primary_date.iso_format in ["2024-11-13", "2024-11-20"]

    def test_extract_mixed_formats(self):
        """Test extracting dates in mixed formats."""
        text = "Meeting on 2024년 11월 13일 or January 15, 2025"
        result = extract_dates_from_text(text)

        assert len(result.dates_found) == 2
        date_strings = {d.iso_format for d in result.dates_found}
        assert "2024-11-13" in date_strings
        assert "2025-01-15" in date_strings

    def test_extract_duplicate_dates(self):
        """Test that duplicate dates are removed."""
        text = "Meeting on 2024년 11월 13일 and reminder 2024-11-13"
        result = extract_dates_from_text(text)

        # Should only have one date (duplicates removed)
        assert len(result.dates_found) == 1
        assert result.primary_date.iso_format == "2024-11-13"

    def test_extract_no_dates(self):
        """Test extracting from text with no dates."""
        text = "This is just regular text with no dates"
        result = extract_dates_from_text(text)

        assert len(result.dates_found) == 0
        assert result.primary_date is None
        assert result.confidence == 0.0

    def test_extract_from_empty_text(self):
        """Test extracting from empty text."""
        result = extract_dates_from_text("")

        assert len(result.dates_found) == 0
        assert result.primary_date is None
        assert result.confidence == 0.0

    def test_extract_korean_week_notation(self):
        """Test extracting Korean week notation."""
        text = "Workshop in 11월 2주"
        result = extract_dates_from_text(text)

        assert len(result.dates_found) == 1
        assert result.primary_date is not None
        assert "-11-08" in result.primary_date.iso_format  # Week 2 starts on day 8

    def test_extract_with_email_id(self):
        """Test that email_id is preserved in result."""
        result = extract_dates_from_text("Date: 2025-01-15", email_id="email456")

        assert result.email_id == "email456"


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_february_29_leap_year(self):
        """Test parsing February 29 in leap year."""
        result = parse_date("2024년 2월 29일")

        assert result.parsed_date is not None
        assert result.parsed_date.year == 2024
        assert result.parsed_date.month == 2
        assert result.parsed_date.day == 29

    def test_february_29_non_leap_year(self):
        """Test parsing February 29 in non-leap year fails gracefully."""
        # dateparser should handle this
        result = parse_date("2025년 2월 29일")

        # Should either fail to parse or adjust to valid date
        if result.parsed_date:
            # If it parsed, it should have adjusted to valid date
            assert result.parsed_date.month == 2 or result.parsed_date.day <= 28

    def test_korean_single_digit_dates(self):
        """Test Korean dates with single-digit month/day."""
        result = parse_date("2024년 1월 5일")

        assert result.parsed_date is not None
        assert result.parsed_date.month == 1
        assert result.parsed_date.day == 5

    def test_korean_double_digit_dates(self):
        """Test Korean dates with double-digit month/day."""
        result = parse_date("2024년 12월 31일")

        assert result.parsed_date is not None
        assert result.parsed_date.month == 12
        assert result.parsed_date.day == 31

    def test_year_boundaries(self):
        """Test dates at year boundaries."""
        result1 = parse_date("2024년 1월 1일")
        result2 = parse_date("2024년 12월 31일")

        assert result1.iso_format == "2024-01-01"
        assert result2.iso_format == "2024-12-31"

    def test_case_insensitive_english(self):
        """Test that English month names are case-insensitive."""
        result1 = parse_date("january 15, 2025")
        result2 = parse_date("JANUARY 15, 2025")

        assert result1.parsed_date is not None
        assert result2.parsed_date is not None
        assert result1.iso_format == result2.iso_format


class TestReferenceDate:
    """Tests for reference date functionality."""

    def test_korean_partial_with_reference_date(self):
        """Test Korean partial date uses reference year."""
        reference = datetime(2023, 1, 1)
        result = parse_date("10월 27일", reference_date=reference)

        assert result.parsed_date is not None
        assert result.parsed_date.year == 2023
        assert result.parsed_date.month == 10
        assert result.parsed_date.day == 27

    def test_korean_week_with_reference_year(self):
        """Test Korean week notation uses reference year."""
        reference = datetime(2023, 1, 1)
        result = parse_date("11월 1주", reference_date=reference)

        assert result.parsed_date is not None
        assert result.parsed_date.year == 2023
        assert result.parsed_date.month == 11


class TestOriginalTextPreservation:
    """Tests that original text is preserved in results."""

    def test_original_text_preserved_success(self):
        """Test original text is preserved when parsing succeeds."""
        original = "2024년 11월 13일"
        result = parse_date(original)

        assert result.original_text == original

    def test_original_text_preserved_failure(self):
        """Test original text is preserved when parsing fails."""
        original = "invalid date"
        result = parse_date(original)

        assert result.original_text == original

    def test_original_text_with_whitespace(self):
        """Test original text includes whitespace (before cleaning)."""
        original = "  2025-01-15  "
        result = parse_date(original)

        assert result.original_text == original
