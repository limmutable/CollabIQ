"""Pydantic models for date parsing results.

This module defines data models for date parsing operations,
including parsed date results and format detection.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DateFormat(str, Enum):
    """Detected date format types."""

    # ISO formats
    ISO_8601 = "iso_8601"  # 2025-01-15
    ISO_DATETIME = "iso_datetime"  # 2025-01-15T10:30:00

    # English formats
    ENGLISH_MDY = "english_mdy"  # January 15, 2025
    ENGLISH_DMY = "english_dmy"  # 15 January 2025
    US_SHORT = "us_short"  # 01/15/2025
    EU_SHORT = "eu_short"  # 15/01/2025

    # Korean formats
    KOREAN_YMD = "korean_ymd"  # 2025년 1월 15일
    KOREAN_MD = "korean_md"  # 1월 15일
    KOREAN_WEEK = "korean_week"  # 11월 1주

    # Relative formats
    RELATIVE = "relative"  # yesterday, tomorrow, next Monday

    # Unknown/unsupported
    UNKNOWN = "unknown"


class ParsedDate(BaseModel):
    """Result of date parsing operation.

    Attributes:
        original_text: Original date string provided
        parsed_date: Parsed datetime object (None if parsing failed)
        iso_format: ISO 8601 format string (YYYY-MM-DD) for easy storage
        format_detected: Type of date format detected
        confidence: Confidence score (0.0-1.0) for parsing accuracy
        parse_error: Error message if parsing failed
    """

    original_text: str = Field(..., description="Original date string")
    parsed_date: Optional[datetime] = Field(None, description="Parsed datetime object")
    iso_format: Optional[str] = Field(
        None, description="ISO 8601 date string (YYYY-MM-DD)"
    )
    format_detected: DateFormat = Field(
        DateFormat.UNKNOWN, description="Detected format type"
    )
    confidence: float = Field(
        1.0, ge=0.0, le=1.0, description="Confidence score (0.0-1.0)"
    )
    parse_error: Optional[str] = Field(
        None, description="Error message if parsing failed"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "original_text": "2024년 11월 13일",
                "parsed_date": "2024-11-13T00:00:00",
                "iso_format": "2024-11-13",
                "format_detected": "korean_ymd",
                "confidence": 1.0,
                "parse_error": None,
            }
        }
    )


class DateExtractionResult(BaseModel):
    """Result of date extraction from email content.

    Attributes:
        email_id: Email ID for tracking
        dates_found: List of parsed dates found in email
        primary_date: The most likely relevant date (e.g., meeting date)
        extraction_method: Method used for extraction (llm, regex, hybrid)
        confidence: Overall confidence in extraction accuracy
    """

    email_id: str = Field(..., description="Email ID")
    dates_found: list[ParsedDate] = Field(
        default_factory=list, description="All dates found"
    )
    primary_date: Optional[ParsedDate] = Field(
        None, description="Primary/most relevant date"
    )
    extraction_method: str = Field("regex", description="Extraction method used")
    confidence: float = Field(
        1.0, ge=0.0, le=1.0, description="Overall confidence score"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email_id": "abc123",
                "dates_found": [
                    {
                        "original_text": "2024년 11월 13일",
                        "parsed_date": "2024-11-13T00:00:00",
                        "iso_format": "2024-11-13",
                        "format_detected": "korean_ymd",
                        "confidence": 1.0,
                        "parse_error": None,
                    }
                ],
                "primary_date": {
                    "original_text": "2024년 11월 13일",
                    "parsed_date": "2024-11-13T00:00:00",
                    "iso_format": "2024-11-13",
                    "format_detected": "korean_ymd",
                    "confidence": 1.0,
                    "parse_error": None,
                },
                "extraction_method": "regex",
                "confidence": 0.95,
            }
        }
    )
