"""
Validators: Data integrity checks for E2E testing

Responsibilities:
- Validate Notion entries have all required fields
- Check Korean text preservation (detect mojibake)
- Validate field formats (dates, collaboration types, company IDs)
- Return structured ValidationResult with errors and warnings
"""

import re
from datetime import datetime
from typing import Optional


class ValidationResult:
    """Result of a validation check"""

    def __init__(self, is_valid: bool = True):
        self.is_valid = is_valid
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.corruption_detected: list[str] = []

    def add_error(self, message: str):
        """Add an error and mark validation as failed"""
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str):
        """Add a warning (doesn't fail validation)"""
        self.warnings.append(message)

    def add_corruption(self, message: str):
        """Add Korean text corruption detection"""
        self.corruption_detected.append(message)
        self.is_valid = False


class Validator:
    """
    Validates Notion entries and data integrity

    Checks:
    - All required fields present and non-empty
    - Korean text preserved without mojibake
    - Date formats are valid ISO 8601
    - Collaboration types match [A/B/C/D] pattern
    - Company IDs follow expected format
    """

    # Required fields in Notion entry (names match actual Notion DB properties)
    REQUIRED_FIELDS = [
        "Email ID",  # Added as text field for duplicate detection
        "담당자",  # people
        "스타트업명",  # relation
        "협력기관",  # relation
        "협력유형",  # select
        "날짜",  # date (Korean name in actual DB, not "Date")
    ]

    def validate_notion_entry(self, notion_entry: dict) -> ValidationResult:
        """
        Validate that Notion entry has all required fields with valid formats

        Args:
            notion_entry: Notion page object with properties

        Returns:
            ValidationResult: Validation result with errors if any
        """
        result = ValidationResult()

        properties = notion_entry.get("properties", {})

        # Check all required fields are present
        for field_name in self.REQUIRED_FIELDS:
            if field_name not in properties:
                result.add_error(f"Required field missing: {field_name}")
                continue

            # Check field value is not empty
            # Special handling for 날짜 (date) field
            if field_name == "날짜":
                field_value = self._extract_date_value(properties[field_name])
            else:
                field_value = self._extract_field_value(properties[field_name])

            if not field_value or (
                isinstance(field_value, str) and field_value.strip() == ""
            ):
                result.add_error(f"Required field is empty: {field_name}")

        # Validate 날짜 (date) field format if present
        if "날짜" in properties:
            date_value = self._extract_date_value(properties["날짜"])
            if date_value:
                date_result = self.validate_date_format(date_value)
                if not date_result.is_valid:
                    result.errors.extend(date_result.errors)
                    result.is_valid = False

        # Validate collaboration type format if present
        if "협력유형" in properties:
            collab_type = self._extract_field_value(properties["협력유형"])
            if collab_type:
                collab_result = self.validate_collaboration_type(collab_type)
                if not collab_result.is_valid:
                    result.errors.extend(collab_result.errors)
                    result.is_valid = False

        return result

    def validate_korean_text(
        self, original_text: str, notion_entry: dict
    ) -> ValidationResult:
        """
        Validate that Korean text is preserved correctly (detect mojibake)

        Args:
            original_text: Original Korean text from email
            notion_entry: Notion page object with properties

        Returns:
            ValidationResult: Validation result with corruption detection
        """
        result = ValidationResult()

        properties = notion_entry.get("properties", {})

        # Extract all text from Notion entry
        notion_text = ""
        for field_name, field_data in properties.items():
            field_value = self._extract_field_value(field_data)
            if isinstance(field_value, str):
                notion_text += field_value + " "

        # Check for mojibake patterns (Korean text corrupted to Latin-1)
        mojibake_patterns = [
            r"ë‹´ë‹¹",  # 담당 corrupted
            r"ê¹€ì²",  # 김철 corrupted
            r"ì íƒ",  # 스타 corrupted
            r"ë¸ë ì´",  # 브레이 corrupted
        ]

        for pattern in mojibake_patterns:
            if re.search(pattern, notion_text):
                result.add_corruption(
                    f"Mojibake detected: Korean text corruption pattern '{pattern}' found"
                )

        # Check that Notion entry contains Korean characters (if original had them)
        # This is a basic check - if original text had Korean, Notion should too
        original_has_korean = any(
            "\uac00" <= char <= "\ud7a3" for char in original_text
        )
        notion_has_korean = any("\uac00" <= char <= "\ud7a3" for char in notion_text)

        if original_has_korean and not notion_has_korean:
            result.add_corruption(
                "Original text contains Korean characters but Notion entry has none"
            )

        return result

    def validate_collaboration_type(self, collab_type: str) -> ValidationResult:
        """
        Validate collaboration type format [A/B/C/D]

        Args:
            collab_type: Collaboration type string

        Returns:
            ValidationResult: Validation result
        """
        result = ValidationResult()

        valid_types = ["[A]", "[B]", "[C]", "[D]"]

        # Extract just the [X] part if there's additional text
        match = re.search(r"\[([ABCD])\]", collab_type)

        if not match:
            result.add_error(
                f"Invalid collaboration type format: '{collab_type}' (expected [A], [B], [C], or [D])"
            )
        else:
            extracted_type = f"[{match.group(1)}]"
            if extracted_type not in valid_types:
                result.add_error(f"Invalid collaboration type: {extracted_type}")

        return result

    def validate_date_format(self, date_str: str) -> ValidationResult:
        """
        Validate date format is ISO 8601 (YYYY-MM-DD)

        Args:
            date_str: Date string to validate

        Returns:
            ValidationResult: Validation result
        """
        result = ValidationResult()

        # Check ISO 8601 format (YYYY-MM-DD)
        iso_pattern = r"^\d{4}-\d{2}-\d{2}$"

        if not re.match(iso_pattern, date_str):
            result.add_error(f"Invalid date format: '{date_str}' (expected YYYY-MM-DD)")
            return result

        # Try parsing to ensure it's a valid date
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError as e:
            result.add_error(f"Invalid date: '{date_str}' ({str(e)})")

        return result

    def validate_company_id(self, company_id: str) -> ValidationResult:
        """
        Validate company ID format

        Args:
            company_id: Company ID string

        Returns:
            ValidationResult: Validation result
        """
        result = ValidationResult()

        # Empty company_id is acceptable (manual review fallback)
        if company_id == "" or company_id is None:
            return result

        # Check format: comp_xxx or similar prefix pattern
        if not company_id.startswith("comp_"):
            result.add_warning(
                f"Company ID '{company_id}' doesn't follow expected format (comp_xxx)"
            )

        return result

    def _extract_field_value(self, field_data: dict) -> Optional[str]:
        """
        Extract text value from Notion field data structure

        Args:
            field_data: Notion field object

        Returns:
            str | None: Extracted text value or None
        """
        # Handle different Notion field types
        if "title" in field_data and field_data["title"]:
            return field_data["title"][0]["text"]["content"]

        if "rich_text" in field_data and field_data["rich_text"]:
            return field_data["rich_text"][0]["text"]["content"]

        if "select" in field_data and field_data["select"]:
            return field_data["select"]["name"]

        return None

    def _extract_date_value(self, field_data: dict) -> Optional[str]:
        """
        Extract date value from Notion date field

        Args:
            field_data: Notion date field object

        Returns:
            str | None: ISO date string or None
        """
        if "date" in field_data and field_data["date"]:
            return field_data["date"]["start"]

        return None
