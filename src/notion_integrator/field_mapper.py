"""FieldMapper - Maps ExtractedEntitiesWithClassification to Notion property format.

This module provides schema-aware field mapping functionality to convert
Pydantic models to Notion API property format.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime


logger = logging.getLogger(__name__)


class FieldMapper:
    """Maps ExtractedEntitiesWithClassification to Notion property format."""

    def __init__(
        self,
        schema,
        company_matcher=None,
        person_matcher=None,
        companies_cache=None,
        notion_writer=None,
        companies_db_id: Optional[str] = None,
    ):
        """Initialize FieldMapper with database schema and optional matchers.

        Args:
            schema: DatabaseSchema from NotionIntegrator.discover_database_schema()
            company_matcher: Optional CompanyMatcher for fuzzy matching company names
            person_matcher: Optional PersonMatcher for matching person names to users
            companies_cache: Optional CompaniesCache for loading company candidates
            notion_writer: Optional NotionWriter for creating companies when no match
            companies_db_id: Companies database ID (required if company_matcher provided)
        """
        self.schema = schema
        self.company_matcher = company_matcher
        self.person_matcher = person_matcher
        self.companies_cache = companies_cache
        self.notion_writer = notion_writer
        self.companies_db_id = companies_db_id

        # Build property type map for quick lookups
        # DatabaseSchema.database.properties contains the actual property definitions
        properties_dict = (
            schema.database.properties
            if hasattr(schema, "database")
            else schema.properties
            if hasattr(schema, "properties")
            else {}
        )
        self.property_types = {
            name: prop.type if hasattr(prop, "type") else prop.get("type")
            for name, prop in properties_dict.items()
        }

    async def map_to_notion_properties_async(self, extracted_data) -> Dict[str, Any]:
        """Map ExtractedEntitiesWithClassification to Notion properties format with async fuzzy matching.

        This async version performs fuzzy matching for company names and person names before mapping.
        Use this when company_matcher/person_matcher and companies_cache are provided.

        Args:
            extracted_data: ExtractedEntitiesWithClassification instance

        Returns:
            Dict of Notion properties ready for API submission
        """
        # Perform fuzzy matching for companies if matcher is available
        if self.company_matcher and self.companies_cache:
            await self._match_and_populate_companies(extracted_data)

        # Perform person matching if matcher is available
        if self.person_matcher:
            self._match_and_populate_person(extracted_data)

        # Use sync version for the actual mapping
        return self.map_to_notion_properties(extracted_data)

    async def _match_and_populate_companies(self, extracted_data) -> None:
        """Match extracted company names to Companies database and populate IDs.

        Args:
            extracted_data: ExtractedEntitiesWithClassification instance (modified in place)
        """
        # Get company candidates from cache
        candidates = await self.companies_cache.get_companies()

        # Match startup_name to 스타트업명
        if extracted_data.startup_name and not extracted_data.matched_company_id:
            match_result = self.company_matcher.match(
                company_name=extracted_data.startup_name,
                candidates=candidates,
                auto_create=True,
                similarity_threshold=0.85,
            )

            # Handle match result
            if match_result.match_type in ["exact", "fuzzy"]:
                # Match found
                extracted_data.matched_company_id = match_result.page_id
                logger.info(
                    f"Company matched: '{extracted_data.startup_name}' → '{match_result.company_name}' "
                    f"(similarity: {match_result.similarity_score:.2f}, type: {match_result.match_type})"
                )

                # Log low-confidence matches (T038)
                if match_result.confidence_level in ["low", "medium"]:
                    logger.warning(
                        f"Low-confidence company match: '{extracted_data.startup_name}' → '{match_result.company_name}' "
                        f"(similarity: {match_result.similarity_score:.2f}, confidence: {match_result.confidence_level}). "
                        f"Manual review recommended."
                    )

            elif match_result.match_type == "none" and match_result.company_name:
                # No match found - auto-create new company
                logger.info(
                    f"No match found for '{extracted_data.startup_name}'. Creating new company entry."
                )

                if self.notion_writer and self.companies_db_id:
                    new_page_id = await self.notion_writer.create_company(
                        company_name=match_result.company_name,
                        companies_db_id=self.companies_db_id,
                    )

                    if new_page_id:
                        extracted_data.matched_company_id = new_page_id
                        logger.info(
                            f"New company created: '{match_result.company_name}' (page_id: {new_page_id})"
                        )

                        # Invalidate cache so next fetch includes new company
                        self.companies_cache.invalidate_cache()
                    else:
                        logger.error(
                            f"Failed to create company: '{match_result.company_name}'"
                        )
                else:
                    logger.warning(
                        f"Cannot auto-create company '{match_result.company_name}': "
                        f"notion_writer or companies_db_id not configured"
                    )

        # Match partner_org to 협업기관 (same logic)
        if extracted_data.partner_org and not extracted_data.matched_partner_id:
            match_result = self.company_matcher.match(
                company_name=extracted_data.partner_org,
                candidates=candidates,
                auto_create=True,
                similarity_threshold=0.85,
            )

            if match_result.match_type in ["exact", "fuzzy"]:
                extracted_data.matched_partner_id = match_result.page_id
                logger.info(
                    f"Partner matched: '{extracted_data.partner_org}' → '{match_result.company_name}' "
                    f"(similarity: {match_result.similarity_score:.2f}, type: {match_result.match_type})"
                )

                # Log low-confidence matches (T038)
                if match_result.confidence_level in ["low", "medium"]:
                    logger.warning(
                        f"Low-confidence partner match: '{extracted_data.partner_org}' → '{match_result.company_name}' "
                        f"(similarity: {match_result.similarity_score:.2f}, confidence: {match_result.confidence_level}). "
                        f"Manual review recommended."
                    )

            elif match_result.match_type == "none" and match_result.company_name:
                logger.info(
                    f"No match found for '{extracted_data.partner_org}'. Creating new company entry."
                )

                if self.notion_writer and self.companies_db_id:
                    new_page_id = await self.notion_writer.create_company(
                        company_name=match_result.company_name,
                        companies_db_id=self.companies_db_id,
                    )

                    if new_page_id:
                        extracted_data.matched_partner_id = new_page_id
                        logger.info(
                            f"New partner created: '{match_result.company_name}' (page_id: {new_page_id})"
                        )
                        self.companies_cache.invalidate_cache()
                    else:
                        logger.error(
                            f"Failed to create partner: '{match_result.company_name}'"
                        )

    def _match_and_populate_person(self, extracted_data) -> None:
        """Match extracted person name to Notion workspace users and populate ID.

        Args:
            extracted_data: ExtractedEntitiesWithClassification instance (modified in place)
        """
        # Match person_in_charge to 담당자
        if extracted_data.person_in_charge and not extracted_data.matched_person_id:
            match_result = self.person_matcher.match(
                person_name=extracted_data.person_in_charge,
                similarity_threshold=0.70,
            )

            # Handle match result
            if match_result.match_type in ["exact", "fuzzy"]:
                # Match found
                extracted_data.matched_person_id = match_result.user_id
                logger.info(
                    f"Person matched: '{extracted_data.person_in_charge}' → '{match_result.user_name}' "
                    f"(similarity: {match_result.similarity_score:.2f}, type: {match_result.match_type})"
                )

                # Log low-confidence or ambiguous matches for manual review
                if (
                    match_result.confidence_level in ["low", "medium"]
                    or match_result.is_ambiguous
                ):
                    warning_msg = (
                        f"Person match requires review: '{extracted_data.person_in_charge}' → '{match_result.user_name}' "
                        f"(similarity: {match_result.similarity_score:.2f}, confidence: {match_result.confidence_level}"
                    )
                    if match_result.is_ambiguous:
                        warning_msg += f", ambiguous: {len(match_result.alternative_matches)} alternatives"
                        # Log alternative matches
                        for alt in match_result.alternative_matches:
                            logger.info(
                                f"  Alternative: {alt.get('user_name')} (similarity: {alt.get('similarity_score')})"
                            )
                    warning_msg += "). Manual review recommended."
                    logger.warning(warning_msg)
            else:
                # No match found
                logger.warning(
                    f"No match found for person: '{extracted_data.person_in_charge}' "
                    f"(best similarity: {match_result.similarity_score:.2f}). "
                    f"담당자 field will be left empty."
                )

    def map_to_notion_properties(self, extracted_data) -> Dict[str, Any]:
        """Map ExtractedEntitiesWithClassification to Notion properties format.

        This is the synchronous version that maps already-matched company IDs.
        Use map_to_notion_properties_async() if you need fuzzy matching.

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

        # People field: 담당자
        if extracted_data.matched_person_id:
            properties["담당자"] = self._format_people(extracted_data.matched_person_id)

        # Rich text fields
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

        # Date field (using Korean name as it appears in Notion DB)
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
        properties["Email ID"] = self._format_rich_text(extracted_data.email_id)

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

    def _format_people(self, user_id: str) -> Dict[str, Any]:
        """Format user ID as Notion people property.

        Args:
            user_id: Notion user UUID (32-36 character UUID)

        Returns:
            Notion people property format
        """
        return {"people": [{"id": user_id}]}
