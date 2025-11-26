"""
Integration tests for Validators

Tests validate:
- validate_notion_entry method (check required fields, Korean text, date formats)
- Korean text validation (detect mojibake, ensure UTF-8 preservation)
- Field format checks (dates, collabor ation types, company IDs)
"""

from e2e_test.validators import Validator


class TestValidateNotionEntry:
    """Test validate_notion_entry method"""

    def test_validate_valid_notion_entry(self):
        """Test validation passes for properly formatted entry"""
        validator = Validator()

        # Valid Notion entry with all required fields
        notion_entry = {
            "properties": {
                "Email ID": {"rich_text": [{"text": {"content": "msg_001"}}]},
                "담당자": {"title": [{"text": {"content": "김철수"}}]},
                "스타트업명": {
                    "rich_text": [{"text": {"content": "브레이크앤컴퍼니"}}]
                },
                "협업기관": {"rich_text": [{"text": {"content": "신세계푸드"}}]},
                "협업형태": {"select": {"name": "[A] 포트폴리오 x SSG"}},
                "날짜": {"date": {"start": "2025-10-28"}},
                "Company ID": {"rich_text": [{"text": {"content": "comp_123"}}]},
            }
        }

        result = validator.validate_notion_entry(notion_entry)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_missing_required_field(self):
        """Test validation fails when required field is missing"""
        validator = Validator()

        # Missing "스타트업명" field
        notion_entry = {
            "properties": {
                "Email ID": {"rich_text": [{"text": {"content": "msg_002"}}]},
                # Missing 스타트업명
            }
        }

        result = validator.validate_notion_entry(notion_entry)

        assert result.is_valid is False
        assert any("스타트업명" in error for error in result.errors)

    def test_validate_empty_field_value(self):
        """Test validation fails when required field has empty value"""
        validator = Validator()

        notion_entry = {
            "properties": {
                "Email ID": {"rich_text": [{"text": {"content": "msg_003"}}]},
                "스타트업명": {"rich_text": [{"text": {"content": ""}}]},  # Empty string
            }
        }

        result = validator.validate_notion_entry(notion_entry)

        assert result.is_valid is False
        assert any("empty" in error.lower() for error in result.errors)

    def test_validate_invalid_date_format(self):
        """Test validation fails for invalid date format"""
        validator = Validator()

        notion_entry = {
            "properties": {
                "Email ID": {"rich_text": [{"text": {"content": "msg_004"}}]},
                "담당자": {"title": [{"text": {"content": "김철수"}}]},
                "스타트업명": {"rich_text": [{"text": {"content": "Test Corp"}}]},
                "날짜": {"date": {"start": "invalid-date"}},  # Invalid format
            }
        }

        result = validator.validate_notion_entry(notion_entry)

        assert result.is_valid is False
        assert any("date" in error.lower() for error in result.errors)


class TestKoreanTextValidation:
    """Test Korean text preservation and corruption detection"""

    def test_korean_text_preserved_correctly(self):
        """Test that Korean text is identical between input and Notion entry"""
        validator = Validator()

        original_text = "담당자: 김철수, 스타트업명: 브레이크앤컴퍼니"

        notion_entry = {
            "properties": {
                "담당자": {"title": [{"text": {"content": "김철수"}}]},
                "스타트업명": {
                    "rich_text": [{"text": {"content": "브레이크앤컴퍼니"}}]
                },
            }
        }

        result = validator.validate_korean_text(original_text, notion_entry)

        assert result.is_valid is True
        assert len(result.corruption_detected) == 0

    def test_detect_mojibake_corruption(self):
        """Test detection of Korean text corruption (mojibake)"""
        validator = Validator()

        original_text = "담당자: 김철수"

        # Corrupted Notion entry with mojibake
        notion_entry = {
            "properties": {
                "담당자": {
                    "title": [{"text": {"content": "ë‹´ë‹¹ìž: ê¹€ì²ì"}}]
                },  # Mojibake
            }
        }

        result = validator.validate_korean_text(original_text, notion_entry)

        assert result.is_valid is False
        assert len(result.corruption_detected) > 0
        assert "mojibake" in result.corruption_detected[0].lower()

    def test_korean_with_emojis_preserved(self):
        """Test that Korean text with emojis is preserved"""
        validator = Validator()

        original_text = "브레이크앤컴퍼니 🚀"

        notion_entry = {
            "properties": {
                "스타트업명": {
                    "rich_text": [{"text": {"content": "브레이크앤컴퍼니 🚀"}}]
                },
            }
        }

        result = validator.validate_korean_text(original_text, notion_entry)

        assert result.is_valid is True

    def test_mixed_korean_english_preserved(self):
        """Test mixed Korean-English text is preserved"""
        validator = Validator()

        original_text = "브레이크앤컴퍼니 x 신세계푸드 (Collaboration Type A)"

        notion_entry = {
            "properties": {
                "협업기관": {
                    "rich_text": [
                        {
                            "text": {
                                "content": "브레이크앤컴퍼니 x 신세계푸드 (Collaboration Type A)"
                            }
                        }
                    ]
                },
            }
        }

        result = validator.validate_korean_text(original_text, notion_entry)

        assert result.is_valid is True


class TestFieldFormatValidation:
    """Test field-specific format validation"""

    def test_valid_collaboration_type_format(self):
        """Test validation of collaboration type format [A/B/C/D]"""
        validator = Validator()

        for collab_type in ["[A]", "[B]", "[C]", "[D]"]:
            result = validator.validate_collaboration_type(collab_type)
            assert result.is_valid is True, f"{collab_type} should be valid"

    def test_invalid_collaboration_type_format(self):
        """Test validation rejects invalid collaboration types"""
        validator = Validator()

        invalid_types = ["[E]", "A", "[a]", "[1]", ""]

        for invalid_type in invalid_types:
            result = validator.validate_collaboration_type(invalid_type)
            assert result.is_valid is False, f"{invalid_type} should be invalid"

    def test_valid_date_formats(self):
        """Test validation accepts valid ISO 8601 dates"""
        validator = Validator()

        valid_dates = [
            "2025-10-28",
            "2025-01-01",
            "2024-12-31",
        ]

        for date_str in valid_dates:
            result = validator.validate_date_format(date_str)
            assert result.is_valid is True, f"{date_str} should be valid"

    def test_invalid_date_formats(self):
        """Test validation rejects invalid date formats"""
        validator = Validator()

        invalid_dates = [
            "10/28/2025",  # US format
            "28-10-2025",  # DD-MM-YYYY
            "2025/10/28",  # Wrong separator
            "invalid-date",
            "",
        ]

        for date_str in invalid_dates:
            result = validator.validate_date_format(date_str)
            assert result.is_valid is False, f"{date_str} should be invalid"

    def test_valid_company_id_format(self):
        """Test validation of company ID format"""
        validator = Validator()

        valid_ids = [
            "comp_123",
            "comp_abc456",
            "comp_test_company_1",
        ]

        for company_id in valid_ids:
            result = validator.validate_company_id(company_id)
            assert result.is_valid is True, f"{company_id} should be valid"

    def test_empty_company_id_allowed(self):
        """Test that empty company ID is allowed (for manual fallback)"""
        validator = Validator()

        result = validator.validate_company_id("")

        # Empty company_id is acceptable (routes to manual review)
        assert result.is_valid is True


class TestValidationResult:
    """Test ValidationResult data structure"""

    def test_validation_result_with_errors(self):
        """Test ValidationResult captures multiple errors"""
        validator = Validator()

        # Entry with multiple issues
        notion_entry = {
            "properties": {
                "Email ID": {"rich_text": [{"text": {"content": "msg_005"}}]},
                # Missing multiple required fields
            }
        }

        result = validator.validate_notion_entry(notion_entry)

        assert result.is_valid is False
        assert len(result.errors) > 0
        assert isinstance(result.errors, list)

    def test_validation_result_success(self):
        """Test ValidationResult for successful validation"""
        validator = Validator()

        notion_entry = {
            "properties": {
                "Email ID": {"rich_text": [{"text": {"content": "msg_006"}}]},
                "담당자": {"title": [{"text": {"content": "김철수"}}]},
                "스타트업명": {"rich_text": [{"text": {"content": "Test Corp"}}]},
                "협업기관": {"rich_text": [{"text": {"content": "신세계"}}]},
                "협업형태": {"select": {"name": "[A]"}},
                "날짜": {"date": {"start": "2025-10-28"}},
                "Company ID": {"rich_text": [{"text": {"content": "comp_123"}}]},
            }
        }

        result = validator.validate_notion_entry(notion_entry)

        assert result.is_valid is True
        assert len(result.errors) == 0
        assert result.warnings is not None  # May have warnings even if valid
