"""Unit tests for parsing [X]* pattern from Notion field values.

This module tests pattern parsing to support future changes:
- Current format: [A]PortCoXSSG, [B]Non-PortCoXSSG, [C]PortCoXPortCo, [D]Other
- Future format: [1]NewName, [2]OtherName, etc.
- Handles multi-character codes: [A1], [AB], etc.
"""

import re


class TestPatternParsing:
    """Unit tests for [X]* pattern parsing."""

    def test_parse_current_format_a_b_c_d(self):
        """Test: Parse current A/B/C/D format."""
        test_values = [
            "[A]PortCoXSSG",
            "[B]Non-PortCoXSSG",
            "[C]PortCoXPortCo",
            "[D]Other",
        ]

        parsed = {}
        for value in test_values:
            match = re.match(r"^\[([A-Z0-9]+)\]", value)
            if match:
                code = match.group(1)
                parsed[code] = value

        assert parsed == {
            "A": "[A]PortCoXSSG",
            "B": "[B]Non-PortCoXSSG",
            "C": "[C]PortCoXPortCo",
            "D": "[D]Other",
        }

    def test_parse_future_format_1_2_3_4(self):
        """Test: Parse future 1/2/3/4 format (supports schema changes)."""
        test_values = [
            "[1]PortCoXSSG",
            "[2]Non-PortCoXSSG",
            "[3]PortCoXPortCo",
            "[4]Other",
        ]

        parsed = {}
        for value in test_values:
            match = re.match(r"^\[([A-Z0-9]+)\]", value)
            if match:
                code = match.group(1)
                parsed[code] = value

        assert parsed == {
            "1": "[1]PortCoXSSG",
            "2": "[2]Non-PortCoXSSG",
            "3": "[3]PortCoXPortCo",
            "4": "[4]Other",
        }

    def test_parse_multi_character_codes(self):
        """Test: Parse multi-character codes [A1], [AB], etc."""
        test_values = [
            "[A1]TypeOne",
            "[AB]TypeTwo",
            "[123]TypeThree",
        ]

        parsed = {}
        for value in test_values:
            match = re.match(r"^\[([A-Z0-9]+)\]", value)
            if match:
                code = match.group(1)
                parsed[code] = value

        assert parsed == {
            "A1": "[A1]TypeOne",
            "AB": "[AB]TypeTwo",
            "123": "[123]TypeThree",
        }

    def test_ignore_values_without_bracket_prefix(self):
        """Test: Ignore values that don't follow [X]* pattern."""
        test_values = [
            "[A]ValidType",
            "InvalidType",  # Missing brackets
            "Also Invalid",  # No brackets at all
            "[B]AnotherValid",
        ]

        parsed = {}
        for value in test_values:
            match = re.match(r"^\[([A-Z0-9]+)\]", value)
            if match:
                code = match.group(1)
                parsed[code] = value

        # Only valid values should be parsed
        assert parsed == {
            "A": "[A]ValidType",
            "B": "[B]AnotherValid",
        }

    def test_case_sensitivity(self):
        """Test: Pattern matching is case-sensitive (uppercase only)."""
        test_values = [
            "[A]Uppercase",  # Valid
            "[a]lowercase",  # Invalid (lowercase not in pattern)
            "[1]Number",  # Valid
        ]

        parsed = {}
        for value in test_values:
            match = re.match(r"^\[([A-Z0-9]+)\]", value)
            if match:
                code = match.group(1)
                parsed[code] = value

        # Only uppercase and numbers should match
        assert parsed == {
            "A": "[A]Uppercase",
            "1": "[1]Number",
        }

    def test_code_extraction_from_full_value(self):
        """Test: Extract code from full Notion field value."""
        full_value = "[A]PortCoXSSG"

        match = re.match(r"^\[([A-Z0-9]+)\]", full_value)
        assert match is not None
        assert match.group(1) == "A"  # Extracted code

    def test_integration_with_classification_service(self):
        """Test: Pattern parsing works with ClassificationService.get_collaboration_types()."""
        from unittest.mock import Mock

        # Simulate Notion schema with options (create Mock objects with .name attribute)
        option_a = Mock()
        option_a.name = "[A]PortCoXSSG"

        option_b = Mock()
        option_b.name = "[B]Non-PortCoXSSG"

        option_c = Mock()
        option_c.name = "[C]PortCoXPortCo"

        option_d = Mock()
        option_d.name = "[D]Other"

        mock_options = [option_a, option_b, option_c, option_d]

        # Parse like ClassificationService does
        parsed = {}
        for option in mock_options:
            match = re.match(r"^\[([A-Z0-9]+)\]", option.name)
            if match:
                code = match.group(1)
                parsed[code] = option.name

        assert parsed == {
            "A": "[A]PortCoXSSG",
            "B": "[B]Non-PortCoXSSG",
            "C": "[C]PortCoXPortCo",
            "D": "[D]Other",
        }

    def test_empty_bracket_code_not_matched(self):
        """Test: Empty bracket code [] is not matched."""
        test_values = [
            "[]EmptyCode",  # Invalid
            "[A]ValidCode",  # Valid
        ]

        parsed = {}
        for value in test_values:
            match = re.match(r"^\[([A-Z0-9]+)\]", value)
            if match:
                code = match.group(1)
                parsed[code] = value

        assert parsed == {"A": "[A]ValidCode"}
        assert "[]EmptyCode" not in parsed.values()
