"""Date parsing utilities for multi-format date handling.

This module provides utilities for parsing dates in various formats:
- English absolute dates: "2025-01-15", "January 15, 2025"
- Korean dates: "2025년 1월 15일", "10월 27일"
- Relative dates: "yesterday", "next Monday", "last week"
- Korean week notation: "11월 1주" (November 1st week) - requires custom handler

Uses dateparser library for robust multi-format parsing.
"""

import re
from datetime import datetime, timedelta
from typing import Optional

import dateparser


def parse_date(date_str: str, reference_date: Optional[datetime] = None) -> Optional[datetime]:
    """Parse date string in various formats to datetime object.

    Handles:
    - English absolute: "2025-01-15", "January 15, 2025"
    - Korean: "2025년 1월 15일", "10월 27일"
    - Relative: "yesterday", "next Monday"
    - Korean week notation: "11월 1주" (November 1st week)

    Args:
        date_str: Date string to parse
        reference_date: Reference date for relative dates (default: now)

    Returns:
        datetime object (UTC) or None if parsing fails

    Examples:
        >>> parse_date("2025-01-15")
        datetime(2025, 1, 15, 0, 0)

        >>> parse_date("어제")  # yesterday
        datetime(2025, 10, 31, 0, 0)  # (if today is 2025-11-01)

        >>> parse_date("11월 1주")  # November 1st week
        datetime(2025, 11, 1, 0, 0)  # First day of November 1st week
    """
    if not date_str:
        return None

    # Set reference date (default to now)
    if reference_date is None:
        reference_date = datetime.utcnow()

    # Handle Korean week notation: "11월 1주" (November 1st week)
    week_match = re.match(r"(\d{1,2})월\s*(\d{1})주", date_str)
    if week_match:
        month = int(week_match.group(1))
        week_num = int(week_match.group(2))
        return _parse_korean_week(month, week_num, reference_date.year)

    # Handle Korean date formats with regex (dateparser doesn't support these)
    # Format: "YYYY년 M월 D일" (e.g., "2025년 1월 15일")
    korean_full_match = re.match(r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일", date_str)
    if korean_full_match:
        year = int(korean_full_match.group(1))
        month = int(korean_full_match.group(2))
        day = int(korean_full_match.group(3))
        return datetime(year, month, day)

    # Format: "M월 D일" (e.g., "10월 27일") - assume current year
    korean_partial_match = re.match(r"(\d{1,2})월\s*(\d{1,2})일", date_str)
    if korean_partial_match:
        month = int(korean_partial_match.group(1))
        day = int(korean_partial_match.group(2))
        year = reference_date.year
        return datetime(year, month, day)

    # Use dateparser for all other formats (English dates, relative dates)
    parsed = dateparser.parse(
        date_str,
        settings={
            "RELATIVE_BASE": reference_date,
            "PREFER_DATES_FROM": "future",  # Prefer future dates for relative dates
            "TIMEZONE": "UTC",
            "RETURN_AS_TIMEZONE_AWARE": False,
        },
        languages=["ko", "en"],  # Korean and English
    )

    return parsed


def _parse_korean_week(month: int, week_num: int, year: int) -> Optional[datetime]:
    """Parse Korean week notation to datetime.

    Korean week notation: "11월 1주" means "November 1st week"
    Week 1 = days 1-7, Week 2 = days 8-14, Week 3 = days 15-21, Week 4 = days 22-end

    Args:
        month: Month number (1-12)
        week_num: Week number (1-4)
        year: Year (default: current year)

    Returns:
        datetime object representing the first day of that week, or None if invalid

    Examples:
        >>> _parse_korean_week(11, 1, 2025)
        datetime(2025, 11, 1, 0, 0)

        >>> _parse_korean_week(11, 2, 2025)
        datetime(2025, 11, 8, 0, 0)
    """
    if not (1 <= month <= 12 and 1 <= week_num <= 4):
        return None

    # Calculate the first day of the week
    # Week 1 starts on day 1, Week 2 starts on day 8, etc.
    day = 1 + (week_num - 1) * 7

    try:
        return datetime(year, month, day, 0, 0, 0)
    except ValueError:
        # Invalid date (e.g., February 30)
        return None
