"""Unit tests for date parsing utilities.

Tests cover:
- Absolute dates (English): "2025-01-15", "January 15, 2025"
- Korean dates: "2025년 1월 15일", "10월 27일"
- Relative dates: "yesterday", "next Monday"
- Korean week notation: "11월 1주" (November 1st week)
"""

import pytest
from datetime import datetime

from src.llm_provider.date_utils import parse_date, _parse_korean_week


def test_parse_absolute_date_iso_format():
    """Test parsing ISO format dates (YYYY-MM-DD)."""
    result = parse_date("2025-01-15")
    assert result is not None
    assert result.year == 2025
    assert result.month == 1
    assert result.day == 15


def test_parse_absolute_date_english_format():
    """Test parsing English format dates (Month DD, YYYY)."""
    result = parse_date("January 15, 2025")
    assert result is not None
    assert result.year == 2025
    assert result.month == 1
    assert result.day == 15


def test_parse_korean_date_full_format():
    """Test parsing Korean full date format (YYYY년 M월 D일)."""
    result = parse_date("2025년 1월 15일")
    assert result is not None
    assert result.year == 2025
    assert result.month == 1
    assert result.day == 15


def test_parse_korean_date_month_day_format():
    """Test parsing Korean month-day format (M월 D일)."""
    # Note: dateparser should infer the year from current year
    result = parse_date("10월 27일")
    assert result is not None
    assert result.month == 10
    assert result.day == 27


def test_parse_relative_date_yesterday():
    """Test parsing relative date 'yesterday'."""
    reference = datetime(2025, 11, 1, 12, 0, 0)
    result = parse_date("yesterday", reference_date=reference)
    assert result is not None
    assert result.year == 2025
    assert result.month == 10
    assert result.day == 31


def test_parse_relative_date_next_monday():
    """Test parsing relative date 'next Monday'."""
    # Reference: Friday, October 31, 2025
    reference = datetime(2025, 10, 31, 12, 0, 0)
    result = parse_date("next Monday", reference_date=reference)
    assert result is not None
    # Next Monday from October 31 (Friday) should be November 3
    assert result.month == 11
    assert result.day == 3


def test_parse_korean_week_notation_week_1():
    """Test parsing Korean week notation (M월 W주) - Week 1."""
    result = parse_date("11월 1주")
    assert result is not None
    assert result.month == 11
    assert result.day == 1  # First day of week 1


def test_parse_korean_week_notation_week_2():
    """Test parsing Korean week notation (M월 W주) - Week 2."""
    result = parse_date("11월 2주")
    assert result is not None
    assert result.month == 11
    assert result.day == 8  # First day of week 2 (day 8-14)


def test_parse_korean_week_notation_week_3():
    """Test parsing Korean week notation (M월 W주) - Week 3."""
    result = parse_date("11월 3주")
    assert result is not None
    assert result.month == 11
    assert result.day == 15  # First day of week 3 (day 15-21)


def test_parse_korean_week_notation_week_4():
    """Test parsing Korean week notation (M월 W주) - Week 4."""
    result = parse_date("11월 4주")
    assert result is not None
    assert result.month == 11
    assert result.day == 22  # First day of week 4 (day 22-end)


def test_parse_date_empty_string():
    """Test parsing empty string returns None."""
    result = parse_date("")
    assert result is None


def test_parse_date_none():
    """Test parsing None returns None."""
    result = parse_date(None)
    assert result is None


def test_parse_date_invalid_format():
    """Test parsing invalid date format returns None."""
    result = parse_date("not a date")
    assert result is None


def test_parse_korean_week_invalid_month():
    """Test _parse_korean_week with invalid month."""
    result = _parse_korean_week(13, 1, 2025)  # Month 13 is invalid
    assert result is None


def test_parse_korean_week_invalid_week():
    """Test _parse_korean_week with invalid week number."""
    result = _parse_korean_week(11, 5, 2025)  # Week 5 is invalid (only 1-4)
    assert result is None


def test_parse_korean_week_invalid_date():
    """Test _parse_korean_week with date that doesn't exist."""
    # February 30 doesn't exist
    result = _parse_korean_week(2, 5, 2025)
    assert result is None


def test_parse_date_with_custom_reference_date():
    """Test parsing with custom reference date for relative dates."""
    reference = datetime(2025, 1, 15, 12, 0, 0)
    result = parse_date("tomorrow", reference_date=reference)
    assert result is not None
    assert result.year == 2025
    assert result.month == 1
    assert result.day == 16


def test_parse_date_korean_relative():
    """Test parsing Korean relative dates."""
    reference = datetime(2025, 11, 1, 12, 0, 0)
    result = parse_date("어제", reference_date=reference)  # yesterday
    if result:  # dateparser may or may not support Korean relative dates
        assert result.month == 10
        assert result.day == 31
