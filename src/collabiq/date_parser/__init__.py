"""
Date Parser Library - Standalone library for date parsing and normalization.

This library handles diverse date formats including Korean dates, providing
both programmatic API and CLI interface per constitution principle II.

Usage (Python API):
    from src.collabiq.date_parser import parse_date, normalize_date

    result = parse_date("2024년 11월 13일")
    # Returns: ParsedDate(date="2024-11-13", format="korean_ymd", confidence=0.95)

Usage (CLI):
    python -m src.collabiq.date_parser.cli "2024년 11월 13일"
    # Output: {"parsed_date": "2024-11-13", "format_detected": "korean_ymd", "confidence": 0.95}
"""

__version__ = "0.1.0"

# Library exports will be added as modules are implemented
# from .parser import parse_date, normalize_date
# from .models import ParsedDate, DateFormat
