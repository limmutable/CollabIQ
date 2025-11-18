"""Contract tests for Notion schema fetching in Phase 2c.

This module verifies:
- NotionIntegrator can fetch "협업형태" property from CollabIQ database
- Property has correct type (Select)
- Property options follow [X]* pattern format
- Schema caching works correctly
"""

import pytest
from unittest.mock import Mock


class TestNotionSchemaFetching:
    """Contract tests for Notion schema fetching."""

    @pytest.fixture
    def mock_notion_integrator(self, mocker):
        """Fixture providing mocked NotionIntegrator."""
        mock = mocker.AsyncMock()
        return mock

    @pytest.fixture
    def mock_database_schema(self):
        """Fixture providing mock database schema with 협업형태 property."""
        # Create option objects with .name attribute
        option_a = Mock()
        option_a.name = "[A]PortCoXSSG"

        option_b = Mock()
        option_b.name = "[B]Non-PortCoXSSG"

        option_c = Mock()
        option_c.name = "[C]PortCoXPortCo"

        option_d = Mock()
        option_d.name = "[D]Other"

        schema = Mock()
        schema.properties = {
            "협업형태": Mock(
                type="select",
                options=[option_a, option_b, option_c, option_d],
            )
        }
        return schema

    @pytest.mark.asyncio
    async def test_collaboration_type_property_exists(
        self, mock_notion_integrator, mock_database_schema
    ):
        """Verify 협업형태 property exists in CollabIQ database schema."""
        mock_notion_integrator.discover_database_schema.return_value = (
            mock_database_schema
        )

        schema = await mock_notion_integrator.discover_database_schema("test-db-id")
        collab_type_prop = schema.properties.get("협업형태")

        assert collab_type_prop is not None, (
            "협업형태 property must exist in database schema"
        )

    @pytest.mark.asyncio
    async def test_collaboration_type_property_is_select(
        self, mock_notion_integrator, mock_database_schema
    ):
        """Verify 협업형태 property has type 'select'."""
        mock_notion_integrator.discover_database_schema.return_value = (
            mock_database_schema
        )

        schema = await mock_notion_integrator.discover_database_schema("test-db-id")
        collab_type_prop = schema.properties.get("협업형태")

        assert collab_type_prop.type == "select", "협업형태 must be a Select property"

    @pytest.mark.asyncio
    async def test_collaboration_type_options_follow_pattern(
        self, mock_notion_integrator, mock_database_schema
    ):
        """Verify 협업형태 options follow [X]* pattern."""
        mock_notion_integrator.discover_database_schema.return_value = (
            mock_database_schema
        )

        schema = await mock_notion_integrator.discover_database_schema("test-db-id")
        collab_type_prop = schema.properties.get("협업형태")

        import re

        for option in collab_type_prop.options:
            assert re.match(r"^\[([A-Z0-9]+)\]", option.name), (
                f"Option '{option.name}' must follow [X]* pattern"
            )

    @pytest.mark.asyncio
    async def test_schema_fetching_caching(
        self, mock_notion_integrator, mock_database_schema
    ):
        """Verify schema is cached to avoid repeated API calls."""
        from models.classification_service import ClassificationService

        mock_gemini = Mock()
        mock_notion_integrator.discover_database_schema.return_value = (
            mock_database_schema
        )

        service = ClassificationService(
            notion_integrator=mock_notion_integrator,
            gemini_adapter=mock_gemini,
            collabiq_db_id="test-db-id",
        )

        # First call should fetch from Notion
        types1 = await service.get_collaboration_types()
        assert mock_notion_integrator.discover_database_schema.call_count == 1

        # Second call should use cache (no additional API call)
        types2 = await service.get_collaboration_types()
        assert (
            mock_notion_integrator.discover_database_schema.call_count == 1
        )  # Still 1, not 2

        # Results should be identical
        assert types1 == types2

    @pytest.mark.asyncio
    async def test_missing_collaboration_type_property_raises_error(
        self, mock_notion_integrator
    ):
        """Verify missing 협업형태 property raises ValueError."""
        from models.classification_service import ClassificationService

        # Schema without 협업형태 property
        schema = Mock()
        schema.properties = {"other_property": Mock()}
        mock_notion_integrator.discover_database_schema.return_value = schema

        mock_gemini = Mock()
        service = ClassificationService(
            notion_integrator=mock_notion_integrator,
            gemini_adapter=mock_gemini,
            collabiq_db_id="test-db-id",
        )

        with pytest.raises(ValueError, match="협업형태 property not found"):
            await service.get_collaboration_types()

    @pytest.mark.asyncio
    async def test_invalid_property_type_raises_error(self, mock_notion_integrator):
        """Verify 협업형태 property with wrong type raises ValueError."""
        from models.classification_service import ClassificationService

        # Schema with 협업형태 as text property instead of select
        schema = Mock()
        schema.properties = {
            "협업형태": Mock(type="text")  # Wrong type!
        }
        mock_notion_integrator.discover_database_schema.return_value = schema

        mock_gemini = Mock()
        service = ClassificationService(
            notion_integrator=mock_notion_integrator,
            gemini_adapter=mock_gemini,
            collabiq_db_id="test-db-id",
        )

        with pytest.raises(ValueError, match="협업형태 property has invalid type"):
            await service.get_collaboration_types()
