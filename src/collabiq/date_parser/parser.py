"""Date parsing and normalization library for CollabIQ.

This module provides robust date parsing with format detection,
confidence scoring, and comprehensive error handling. It wraps
the existing date_utils functionality with enhanced validation
and reporting.

Features:
- Multi-format date parsing (ISO, English, Korean, relative)
- Format detection and confidence scoring
- Comprehensive error handling and reporting
- Korean date support (absolute and relative)
- Week notation support (Korean: "11월 1주")
"""

import re
from datetime import datetime
from typing import Optional

from collabiq.date_parser.models import DateFormat, DateExtractionResult, ParsedDate
from llm_provider.date_utils import parse_date as _parse_date_util


def parse_date(date_str: str, reference_date: Optional[datetime] = None) -> ParsedDate:
    """Parse date string with format detection and confidence scoring.

    Args:
        date_str: Date string to parse
        reference_date: Reference date for relative dates (default: now)

    Returns:
        ParsedDate object with parsing results and metadata

    Examples:
        >>> result = parse_date("2025-01-15")
        >>> result.parsed_date
        datetime(2025, 1, 15, 0, 0)
        >>> result.format_detected
        <DateFormat.ISO_8601: 'iso_8601'>

        >>> result = parse_date("2024년 11월 13일")
        >>> result.format_detected
        <DateFormat.KOREAN_YMD: 'korean_ymd'>

        >>> result = parse_date("invalid date")
        >>> result.parse_error
        'Failed to parse date string'
    """
    if not date_str or not isinstance(date_str, str):
        return ParsedDate(
            original_text=str(date_str),
            parsed_date=None,
            iso_format=None,
            format_detected=DateFormat.UNKNOWN,
            confidence=0.0,
            parse_error="Invalid or empty date string",
        )

    # Clean the date string
    date_str_clean = date_str.strip()

    # Detect format and confidence before parsing
    format_detected, confidence = detect_format(date_str_clean)

    # Attempt to parse using the utility function
    try:
        parsed = _parse_date_util(date_str_clean, reference_date)

        if parsed is None:
            return ParsedDate(
                original_text=date_str,
                parsed_date=None,
                iso_format=None,
                format_detected=format_detected,
                confidence=0.0,
                parse_error="Failed to parse date string",
            )

        return ParsedDate(
            original_text=date_str,
            parsed_date=parsed,
            iso_format=parsed.strftime("%Y-%m-%d"),
            format_detected=format_detected,
            confidence=confidence,
            parse_error=None,
        )

    except Exception as e:
        return ParsedDate(
            original_text=date_str,
            parsed_date=None,
            iso_format=None,
            format_detected=format_detected,
            confidence=0.0,
            parse_error=f"Parsing error: {str(e)}",
        )


def detect_format(date_str: str) -> tuple[DateFormat, float]:
    """Detect date format and confidence score.

    Args:
        date_str: Date string to analyze

    Returns:
        Tuple of (DateFormat enum, confidence score 0.0-1.0)

    Examples:
        >>> detect_format("2025-01-15")
        (<DateFormat.ISO_8601: 'iso_8601'>, 1.0)

        >>> detect_format("2024년 11월 13일")
        (<DateFormat.KOREAN_YMD: 'korean_ymd'>, 1.0)

        >>> detect_format("next Monday")
        (<DateFormat.RELATIVE: 'relative'>, 0.8)
    """
    date_str = date_str.strip()

    # ISO 8601 formats (highest confidence)
    if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        return DateFormat.ISO_8601, 1.0

    if re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", date_str):
        return DateFormat.ISO_DATETIME, 1.0

    # Korean formats (high confidence)
    if re.match(r"^\d{4}년\s*\d{1,2}월\s*\d{1,2}일$", date_str):
        return DateFormat.KOREAN_YMD, 1.0

    if re.match(r"^\d{1,2}월\s*\d{1,2}일$", date_str):
        return DateFormat.KOREAN_MD, 0.95  # Slightly lower (assumes current year)

    if re.match(r"^\d{1,2}월\s*\d{1}주$", date_str):
        return DateFormat.KOREAN_WEEK, 0.9

    # English formats (high confidence)
    if re.match(
        r"^(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}$",
        date_str,
        re.IGNORECASE,
    ):
        return DateFormat.ENGLISH_MDY, 0.95

    if re.match(
        r"^\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}$",
        date_str,
        re.IGNORECASE,
    ):
        return DateFormat.ENGLISH_DMY, 0.95

    # Short date formats (medium confidence - ambiguous)
    if re.match(r"^\d{1,2}/\d{1,2}/\d{4}$", date_str):
        # Could be either US (MM/DD/YYYY) or EU (DD/MM/YYYY)
        # Default to US format with lower confidence
        return DateFormat.US_SHORT, 0.7

    # Relative dates (medium-low confidence)
    relative_keywords = [
        "yesterday",
        "tomorrow",
        "today",
        "어제",
        "오늘",
        "내일",
        "next",
        "last",
        "this",
        "다음",
        "지난",
    ]
    if any(keyword in date_str.lower() for keyword in relative_keywords):
        return DateFormat.RELATIVE, 0.8

    # Unknown format
    return DateFormat.UNKNOWN, 0.0


def normalize_date(date_str: str, reference_date: Optional[datetime] = None) -> str:
    """Normalize date string to ISO 8601 format (YYYY-MM-DD).

    Convenience function for getting just the normalized date string.

    Args:
        date_str: Date string to normalize
        reference_date: Reference date for relative dates (default: now)

    Returns:
        ISO 8601 date string (YYYY-MM-DD) or empty string if parsing fails

    Examples:
        >>> normalize_date("2024년 11월 13일")
        '2024-11-13'

        >>> normalize_date("January 15, 2025")
        '2025-01-15'

        >>> normalize_date("invalid")
        ''
    """
    result = parse_date(date_str, reference_date)
    return result.iso_format or ""


def extract_dates_from_text(
    text: str, email_id: str = "unknown", reference_date: Optional[datetime] = None
) -> DateExtractionResult:
    """Extract all dates from text content.

    Scans text for date patterns and returns all found dates with metadata.

    Args:
        text: Text content to scan for dates
        email_id: Email ID for tracking (optional)
        reference_date: Reference date for relative dates (default: now)

    Returns:
        DateExtractionResult with all found dates and primary date selection

    Examples:
        >>> result = extract_dates_from_text(
        ...     "Meeting on 2024년 11월 13일 at 3pm",
        ...     email_id="email123"
        ... )
        >>> len(result.dates_found)
        1
        >>> result.primary_date.iso_format
        '2024-11-13'
    """
    if not text:
        return DateExtractionResult(
            email_id=email_id,
            dates_found=[],
            primary_date=None,
            extraction_method="regex",
            confidence=0.0,
        )

    dates_found: list[ParsedDate] = []
    matched_positions: set[tuple[int, int]] = set()  # Track matched text positions

    # Define date patterns to search for (order matters - most specific first)
    patterns = [
        # Korean formats (specific before general)
        (r"\d{4}년\s*\d{1,2}월\s*\d{1,2}일", DateFormat.KOREAN_YMD),
        (r"\d{1,2}월\s*\d{1}주", DateFormat.KOREAN_WEEK),
        (r"\d{1,2}월\s*\d{1,2}일", DateFormat.KOREAN_MD),
        # ISO formats (specific before general)
        (r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", DateFormat.ISO_DATETIME),
        (r"\d{4}-\d{2}-\d{2}", DateFormat.ISO_8601),
        # English formats
        (
            r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}",
            DateFormat.ENGLISH_MDY,
        ),
        # US/EU short formats
        (r"\d{1,2}/\d{1,2}/\d{4}", DateFormat.US_SHORT),
    ]

    # Search for each pattern
    for pattern, expected_format in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            # Check if this position overlaps with an already matched date
            match_pos = (match.start(), match.end())
            if any(
                start <= match.start() < end or start < match.end() <= end
                for start, end in matched_positions
            ):
                continue  # Skip overlapping matches

            date_str = match.group(0)
            parsed = parse_date(date_str, reference_date)

            # Only include successfully parsed dates
            if parsed.parsed_date is not None:
                dates_found.append(parsed)
                matched_positions.add(match_pos)

    # Remove duplicates (same ISO date)
    unique_dates: dict[str, ParsedDate] = {}
    for date in dates_found:
        if date.iso_format and date.iso_format not in unique_dates:
            unique_dates[date.iso_format] = date

    dates_found = list(unique_dates.values())

    # Select primary date (highest confidence, or first if tied)
    primary_date = None
    if dates_found:
        primary_date = max(dates_found, key=lambda d: d.confidence)

    # Calculate overall confidence
    confidence = primary_date.confidence if primary_date else 0.0

    return DateExtractionResult(
        email_id=email_id,
        dates_found=dates_found,
        primary_date=primary_date,
        extraction_method="regex",
        confidence=confidence,
    )


# Public API exports
__all__ = [
    "parse_date",
    "normalize_date",
    "detect_format",
    "extract_dates_from_text",
    "ParsedDate",
    "DateFormat",
    "DateExtractionResult",
]
