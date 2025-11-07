"""Contract tests for GeminiAdapter company matching extension (Phase 2b).

This module tests the API contract for GeminiAdapter.extract_entities() with
optional company_context parameter. Tests focus on interface compliance, not
accuracy (accuracy tested in integration tests).

Contract Requirements:
- MUST accept optional company_context parameter
- MUST maintain backward compatibility when company_context=None
- MUST populate matched_* fields when company_context provided
- MUST return valid ExtractedEntities in all cases
- MUST enforce confidence range (0.0-1.0)
"""

import json
import os
from pathlib import Path
from typing import Dict, List

import pytest

from src.llm_adapters.gemini_adapter import GeminiAdapter
from src.llm_provider.types import ExtractedEntities


# Fixture: Load mock Notion data
@pytest.fixture
def mock_notion_data() -> List[Dict]:
    """Load mock Notion company data for testing."""
    fixture_path = Path(__file__).parent.parent / "fixtures" / "mock_notion_data.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["companies"]


@pytest.fixture
def company_context_markdown(mock_notion_data: List[Dict]) -> str:
    """Format mock data as markdown for LLM context."""
    portfolio = [c for c in mock_notion_data if c["classification"] == "Portfolio"]
    ssg = [c for c in mock_notion_data if c["classification"] == "SSG Affiliate"]

    lines = ["## Portfolio Companies\n"]
    for company in portfolio:
        lines.append(
            f"- {company['name']} ({company['english_name']}, ID: {company['id']}) - {company['description']}\n"
        )

    lines.append("\n## SSG Affiliates\n")
    for company in ssg:
        lines.append(
            f"- {company['name']} ({company['english_name']}, ID: {company['id']}) - {company['description']}\n"
        )

    return "".join(lines)


class TestGeminiAdapterMatchingContract:
    """Contract tests for Phase 2b company matching extension."""

    def test_backward_compatibility_without_company_context(self):
        """MUST: Phase 1b mode works when company_context=None.

        Contract: When company_context is not provided, GeminiAdapter must:
        - Return valid ExtractedEntities
        - Set all matched_* fields to None
        - Set all *_match_confidence fields to None
        """
        # Skip if no API key (contract test requires real Gemini call)
        if not os.getenv("GEMINI_API_KEY"):
            pytest.skip("GEMINI_API_KEY not set")

        adapter = GeminiAdapter(api_key=os.getenv("GEMINI_API_KEY"))

        # Call without company_context (Phase 1b mode)
        entities = adapter.extract_entities("브레이크앤컴퍼니와 협업 진행 중")

        # Validate return type
        assert isinstance(entities, ExtractedEntities)

        # Validate backward compatibility - all matching fields should be None
        assert entities.matched_company_id is None
        assert entities.matched_partner_id is None
        assert entities.startup_match_confidence is None
        assert entities.partner_match_confidence is None

    def test_matching_enabled_with_company_context(self, company_context_markdown: str):
        """MUST: Phase 2b matching populates matched_* fields when company_context provided.

        Contract: When company_context is provided, GeminiAdapter must:
        - Accept the parameter without error
        - Populate matched_company_id if confident match found
        - Populate startup_match_confidence with valid range (0.0-1.0)
        - Return valid ExtractedEntities
        """
        if not os.getenv("GEMINI_API_KEY"):
            pytest.skip("GEMINI_API_KEY not set")

        adapter = GeminiAdapter(api_key=os.getenv("GEMINI_API_KEY"))

        # Call WITH company_context (Phase 2b mode)
        entities = adapter.extract_entities(
            email_text="브레이크앤컴퍼니와 협업 진행 중",
            company_context=company_context_markdown,
        )

        # Validate return type
        assert isinstance(entities, ExtractedEntities)

        # Validate matching fields are populated (at least one should be set)
        # Note: We don't assert specific IDs here (that's for integration tests)
        # We only verify the contract is respected
        assert (
            entities.matched_company_id is not None
            or entities.matched_partner_id is not None
        )
        assert (
            entities.startup_match_confidence is not None
            or entities.partner_match_confidence is not None
        )

        # Validate confidence ranges
        if entities.startup_match_confidence is not None:
            assert 0.0 <= entities.startup_match_confidence <= 1.0

        if entities.partner_match_confidence is not None:
            assert 0.0 <= entities.partner_match_confidence <= 1.0

    def test_confidence_threshold_enforcement(self, company_context_markdown: str):
        """MUST: Low confidence (<0.70) returns null matched_company_id.

        Contract: When LLM confidence is below threshold (0.70), adapter must:
        - Return None for matched_company_id/matched_partner_id
        - Still populate confidence score (showing low confidence)
        """
        if not os.getenv("GEMINI_API_KEY"):
            pytest.skip("GEMINI_API_KEY not set")

        adapter = GeminiAdapter(api_key=os.getenv("GEMINI_API_KEY"))

        # Test with unknown company (should have low confidence)
        entities = adapter.extract_entities(
            email_text="UnknownStartupXYZ와 협업 제안",
            company_context=company_context_markdown,
        )

        # Validate return type
        assert isinstance(entities, ExtractedEntities)

        # If confidence is low (<0.70), matched_id must be None
        if entities.startup_match_confidence is not None:
            if entities.startup_match_confidence < 0.70:
                assert entities.matched_company_id is None

    def test_return_type_validation(self):
        """MUST: Return value is always valid ExtractedEntities.

        Contract: GeminiAdapter.extract_entities() must:
        - Always return ExtractedEntities instance
        - Never return None or other types
        - Pass Pydantic validation
        """
        if not os.getenv("GEMINI_API_KEY"):
            pytest.skip("GEMINI_API_KEY not set")

        adapter = GeminiAdapter(api_key=os.getenv("GEMINI_API_KEY"))

        entities = adapter.extract_entities("테스트 이메일")

        # Validate return type
        assert isinstance(entities, ExtractedEntities)

        # Validate Pydantic model can be dumped and reloaded
        data = entities.model_dump()
        assert ExtractedEntities.model_validate(data)
