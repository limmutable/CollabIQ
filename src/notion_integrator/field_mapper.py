"""FieldMapper - Maps ExtractedEntitiesWithClassification to Notion property format.

This module provides schema-aware field mapping functionality to convert
Pydantic models to Notion API property format.
"""

from typing import Dict, Any, Optional
from datetime import datetime


class FieldMapper:
    """Maps ExtractedEntitiesWithClassification to Notion property format."""

    def __init__(self, schema):
        """Initialize FieldMapper with database schema.

        Args:
            schema: DatabaseSchema from NotionIntegrator.discover_database_schema()
        """
        self.schema = schema
        # Build property type map for quick lookups
        self.property_types = {
            name: prop["type"] for name, prop in schema.properties.items()
        }

    def map_to_notion_properties(self, extracted_data) -> Dict[str, Any]:
        """Map ExtractedEntitiesWithClassification to Notion properties format.

        Args:
            extracted_data: ExtractedEntitiesWithClassification instance

        Returns:
            Dict of Notion properties ready for API submission
        """
        properties = {}

        # Title field: 협력주체 (auto-generated: startup-partner)
        collaboration_subject = (
            f"{extracted_data.startup_name}-{extracted_data.partner_org}"
        )
        properties["협력주체"] = self._format_title(collaboration_subject)

        # Rich text fields
        if extracted_data.person_in_charge:
            properties["담당자"] = self._format_rich_text(
                extracted_data.person_in_charge
            )

        if extracted_data.details:
            properties["협업내용"] = self._format_rich_text(extracted_data.details)

        if extracted_data.collaboration_summary:
            properties["요약"] = self._format_rich_text(
                extracted_data.collaboration_summary
            )

        # Relation fields (company IDs)
        if extracted_data.matched_company_id:
            properties["스타트업명"] = self._format_relation(
                extracted_data.matched_company_id
            )

        if extracted_data.matched_partner_id:
            properties["협업기관"] = self._format_relation(
                extracted_data.matched_partner_id
            )

        # Select fields
        if extracted_data.collaboration_type:
            properties["협업형태"] = self._format_select(
                extracted_data.collaboration_type
            )

        if extracted_data.collaboration_intensity:
            properties["협업강도"] = self._format_select(
                extracted_data.collaboration_intensity
            )

        # Date field
        if extracted_data.date:
            properties["날짜"] = self._format_date(extracted_data.date)

        # Number fields (confidence scores)
        if extracted_data.type_confidence is not None:
            properties["type_confidence"] = self._format_number(
                extracted_data.type_confidence
            )

        if extracted_data.intensity_confidence is not None:
            properties["intensity_confidence"] = self._format_number(
                extracted_data.intensity_confidence
            )

        # Metadata fields
        properties["email_id"] = self._format_rich_text(extracted_data.email_id)

        if extracted_data.classification_timestamp:
            properties["classification_timestamp"] = self._format_date(
                extracted_data.classification_timestamp
            )

        return properties

    def _format_title(self, text: str) -> Dict[str, Any]:
        """Format text as Notion title property.

        Args:
            text: Title text (will be truncated to 2000 chars)

        Returns:
            Notion title property format
        """
        truncated = text[:2000] if len(text) > 2000 else text
        return {"title": [{"text": {"content": truncated}}]}

    def _format_rich_text(self, text: str) -> Dict[str, Any]:
        """Format text as Notion rich_text property with Korean text support.

        Args:
            text: Rich text content (will be truncated to 2000 chars)

        Returns:
            Notion rich_text property format
        """
        truncated = text[:2000] if len(text) > 2000 else text
        return {"rich_text": [{"text": {"content": truncated}}]}

    def _format_select(self, value: str) -> Dict[str, Any]:
        """Format value as Notion select property.

        Args:
            value: Select option name

        Returns:
            Notion select property format
        """
        return {"select": {"name": value}}

    def _format_relation(self, page_id: Optional[str]) -> Dict[str, Any]:
        """Format page ID as Notion relation property.

        Args:
            page_id: Notion page ID to link (or None for empty relation)

        Returns:
            Notion relation property format
        """
        if page_id is None:
            return {"relation": []}

        return {"relation": [{"id": page_id}]}

    def _format_date(self, date_value) -> Dict[str, Any]:
        """Format date as Notion date property (date only, no time).

        Args:
            date_value: datetime object or ISO 8601 string

        Returns:
            Notion date property format with YYYY-MM-DD only
        """
        # Handle datetime objects
        if isinstance(date_value, datetime):
            date_str = date_value.strftime("%Y-%m-%d")
        # Handle ISO 8601 strings
        elif isinstance(date_value, str):
            # Extract date portion (YYYY-MM-DD) from ISO 8601
            date_str = date_value[:10]
        else:
            raise ValueError(f"Invalid date_value type: {type(date_value)}")

        return {"date": {"start": date_str}}

    def _format_number(self, value: float) -> Dict[str, Any]:
        """Format number as Notion number property.

        Args:
            value: Numeric value (e.g., confidence score 0.0-1.0)

        Returns:
            Notion number property format
        """
        return {"number": value}
