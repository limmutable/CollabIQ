"""
Contract tests for FuzzyCompanyMatcher service.

These tests verify the API contract defined in:
specs/014-enhanced-field-mapping/contracts/fuzzy_company_matcher.yaml

Test coverage:
- T006: Exact match returns similarity 1.0
- T007: Fuzzy match (≥0.85) returns valid page_id
- T015 (US2): New entry creation returns valid page_id
"""

import pytest

from src.models.matching import CompanyMatch
from src.notion_integrator.fuzzy_matcher import RapidfuzzMatcher


class TestExactMatch:
    """Test exact company name matching (case-sensitive)."""

    def test_exact_match_returns_similarity_1_0(self):
        """
        Contract: Exact match must return similarity 1.0 and match_type='exact'.

        Given: Extracted company name "웨이크"
        And: Companies database contains exact match "웨이크" with page_id "abc123"
        When: FuzzyCompanyMatcher.match() is called
        Then: Returns CompanyMatch with similarity=1.0, match_type='exact', page_id='abc123'
        """
        # Arrange
        matcher = RapidfuzzMatcher()
        extracted_name = "웨이크"
        candidates = [
            ("abc123def456789012345678901234", "웨이크"),
            ("xyz789abc012345678901234567890", "네트워크"),
        ]

        # Act
        result = matcher.match(extracted_name, candidates)

        # Assert
        assert isinstance(result, CompanyMatch)
        assert result.similarity_score == 1.0
        assert result.match_type == "exact"
        assert result.page_id == "abc123def456789012345678901234"
        assert result.company_name == "웨이크"
        assert result.confidence_level == "high"
        assert result.was_created is False
        assert result.match_method == "character"

    def test_exact_match_case_sensitive(self):
        """
        Contract: Exact match is case-sensitive for accuracy.

        Given: Extracted name "Wake" (English)
        And: Database has "wake" (lowercase) and "WAKE" (uppercase)
        When: match() is called
        Then: No exact match (will fall through to fuzzy matching)
        """
        matcher = RapidfuzzMatcher()
        extracted_name = "Wake"
        candidates = [
            ("page1" + "0" * 26, "wake"),  # 32 chars
            ("page2" + "0" * 26, "WAKE"),
        ]

        result = matcher.match(extracted_name, candidates, auto_create=False)

        # Should not be exact match (case mismatch)
        assert result.match_type in ["fuzzy", "none"]  # depends on similarity score

    def test_exact_match_ignores_trailing_whitespace(self):
        """
        Contract: Exact match should normalize whitespace (trim).

        Given: Extracted name "웨이크 " (trailing space)
        And: Database has "웨이크" (no trailing space)
        When: match() is called
        Then: Returns exact match after normalization
        """
        matcher = RapidfuzzMatcher()
        extracted_name = "웨이크 "  # trailing space
        candidates = [
            ("abc123def456789012345678901234", "웨이크"),
        ]

        result = matcher.match(extracted_name, candidates)

        assert result.match_type == "exact"
        assert result.similarity_score == 1.0
        assert result.page_id == "abc123def456789012345678901234"


class TestFuzzyMatch:
    """Test fuzzy company name matching with similarity threshold."""

    def test_fuzzy_match_above_threshold_returns_page_id(self):
        """
        Contract: Fuzzy match ≥0.85 returns valid page_id and match_type='fuzzy'.

        Given: Extracted name "스타트업 A" (with space)
        And: Database contains "스타트업A" (without space) - scores ≈0.90
        When: match() is called with threshold=0.85
        Then: Returns CompanyMatch with page_id, similarity≥0.85, match_type='fuzzy'

        Note: Using spacing variation case which reliably scores above 0.85.
        Cases like "웨이크(산스)" → "웨이크" only score 0.60 (below threshold).
        """
        matcher = RapidfuzzMatcher()
        extracted_name = "스타트업 A"  # With space
        candidates = [
            ("abc123def456789012345678901234", "스타트업A"),  # Without space
            ("xyz789abc012345678901234567890", "네트워크"),
        ]

        result = matcher.match(extracted_name, candidates, similarity_threshold=0.85)

        assert isinstance(result, CompanyMatch)
        assert result.match_type == "fuzzy"
        assert result.similarity_score >= 0.85
        assert result.similarity_score < 1.0
        assert result.page_id == "abc123def456789012345678901234"
        assert result.company_name == "스타트업A"
        assert result.confidence_level in ["medium", "high"]
        assert result.was_created is False
        assert result.match_method == "character"

    def test_fuzzy_match_selects_highest_score(self):
        """
        Contract: When multiple candidates match, return highest similarity score.

        Given: Extracted name "스타트업A"
        And: Database has "스타트업 A" (spacing), "스타트업" (partial)
        When: match() is called
        Then: Returns best match (highest similarity)
        """
        matcher = RapidfuzzMatcher()
        extracted_name = "스타트업A"
        candidates = [
            ("page1" + "0" * 26, "스타트업 A"),  # spacing variation
            ("page2" + "0" * 26, "스타트업"),  # partial match
            ("page3" + "0" * 26, "다른회사"),  # unrelated
        ]

        result = matcher.match(extracted_name, candidates, similarity_threshold=0.85)

        # Should match "스타트업 A" (highest similarity)
        assert result.match_type in ["exact", "fuzzy"]
        assert result.page_id == "page1" + "0" * 26
        assert result.company_name == "스타트업 A"

    def test_fuzzy_match_below_threshold_triggers_no_match(self):
        """
        Contract: Fuzzy match <0.85 with auto_create=False returns match_type='none'.

        Given: Extracted name "CompleteMismatch"
        And: Database contains Korean company names (very low similarity)
        When: match() is called with auto_create=False
        Then: Returns CompanyMatch with page_id=None, match_type='none'
        """
        matcher = RapidfuzzMatcher()
        extracted_name = "CompleteMismatch"
        candidates = [
            ("page1" + "0" * 26, "웨이크"),
            ("page2" + "0" * 26, "네트워크"),
        ]

        result = matcher.match(
            extracted_name, candidates, auto_create=False, similarity_threshold=0.85
        )

        assert result.match_type == "none"
        assert result.page_id is None
        assert result.similarity_score < 0.85
        assert result.confidence_level == "none"
        assert result.was_created is False

    def test_fuzzy_match_with_korean_character_alternatives(self):
        """
        Contract: Korean character alternatives score below threshold (known limitation).

        Given: Extracted name "스마트푸드네트워크"
        And: Database has "스마트푸드네트웍스" (워크 → 웍, 스 appended)
        When: match() is called with threshold=0.85
        Then: Returns no match (similarity ≈0.78, below 0.85)

        Note: This is a known limitation of character-based matching.
        Cases like this score ≈0.78 and will trigger auto-creation.
        The hybrid approach (P4) with LLM may handle this better.
        """
        matcher = RapidfuzzMatcher()
        extracted_name = "스마트푸드네트워크"
        candidates = [
            ("page1" + "0" * 26, "스마트푸드네트웍스"),
        ]

        # Use default threshold 0.85 (scores ≈0.78, below threshold)
        result = matcher.match(extracted_name, candidates, auto_create=False)

        # Should NOT match (below 0.85 threshold)
        assert result.match_type == "none"
        assert result.similarity_score < 0.85
        assert result.page_id is None


class TestValidation:
    """Test input validation and error handling."""

    def test_empty_company_name_raises_error(self):
        """
        Contract: Empty company_name must raise ValueError.

        Given: company_name is empty string ""
        When: match() is called
        Then: Raises ValueError with message about empty input
        """
        matcher = RapidfuzzMatcher()
        candidates = [("page1" + "0" * 26, "웨이크")]

        with pytest.raises(ValueError, match="empty"):
            matcher.match("", candidates)

    def test_whitespace_only_company_name_raises_error(self):
        """
        Contract: Whitespace-only company_name must raise ValueError.

        Given: company_name is "   " (spaces only)
        When: match() is called
        Then: Raises ValueError
        """
        matcher = RapidfuzzMatcher()
        candidates = [("page1" + "0" * 26, "웨이크")]

        with pytest.raises(ValueError):
            matcher.match("   ", candidates)

    def test_invalid_threshold_below_0_raises_error(self):
        """
        Contract: similarity_threshold < 0.0 must raise ValueError.

        Given: similarity_threshold = -0.1
        When: match() is called
        Then: Raises ValueError
        """
        matcher = RapidfuzzMatcher()
        candidates = [("page1" + "0" * 26, "웨이크")]

        with pytest.raises(ValueError, match="threshold"):
            matcher.match("웨이크", candidates, similarity_threshold=-0.1)

    def test_invalid_threshold_above_1_raises_error(self):
        """
        Contract: similarity_threshold > 1.0 must raise ValueError.

        Given: similarity_threshold = 1.5
        When: match() is called
        Then: Raises ValueError
        """
        matcher = RapidfuzzMatcher()
        candidates = [("page1" + "0" * 26, "웨이크")]

        with pytest.raises(ValueError, match="threshold"):
            matcher.match("웨이크", candidates, similarity_threshold=1.5)


class TestPerformance:
    """Test performance requirements from spec."""

    def test_match_completes_in_under_2_seconds_for_1000_companies(self):
        """
        Contract: Must complete in <2 seconds for 1000+ companies (SC-007).

        Given: 1000 candidates in database
        When: match() is called
        Then: Completes in <2 seconds
        """
        import time

        matcher = RapidfuzzMatcher()
        extracted_name = "TestCompany"

        # Generate 1000 candidate companies
        candidates = [
            (f"page{i:04d}" + "0" * 24, f"Company{i:04d}") for i in range(1000)
        ]

        start = time.time()
        result = matcher.match(extracted_name, candidates, auto_create=False)
        elapsed = time.time() - start

        assert elapsed < 2.0, f"Match took {elapsed:.2f}s, expected <2s"
        assert isinstance(result, CompanyMatch)


class TestCompanyCreation:
    """Test company creation in Companies database (T015 - US2)."""

    @pytest.mark.asyncio
    async def test_create_company_returns_valid_page_id(self):
        """
        Contract: NotionWriter.create_company() must create new entry and return valid page_id.

        Given: Company name "신규회사" does not exist in Companies database
        When: NotionWriter.create_company("신규회사") is called
        Then: Returns valid page_id (32-character UUID)
        And: Company entry is created with title property set to "신규회사"

        Note: This is a contract test that requires actual Notion API access.
        It will be marked as @pytest.mark.integration and requires:
        - NOTION_API_KEY environment variable
        - NOTION_DATABASE_ID_COMPANIES environment variable
        - Valid Notion integration with write access to Companies database
        """
        pytest.skip(
            "Contract test for NotionWriter.create_company() requires Notion API credentials. "
            "Implementation pending: T019 will add the async create_company() method. "
            "This test serves as specification for the expected behavior."
        )

        # Expected implementation (to be tested when T019 is complete):
        # from src.notion_integrator.writer import NotionWriter
        # from src.notion_integrator.integrator import NotionIntegrator
        # from src.config.settings import Settings
        #
        # settings = Settings()
        # integrator = NotionIntegrator(...)
        # writer = NotionWriter(integrator, collabiq_db_id="...")
        # companies_db_id = settings.get_notion_companies_db_id()
        #
        # # Create new company
        # page_id = await writer.create_company(
        #     company_name="신규회사",
        #     companies_db_id=companies_db_id
        # )
        #
        # # Verify page_id format (32-character UUID without hyphens)
        # assert page_id is not None
        # assert isinstance(page_id, str)
        # assert len(page_id) == 32
        # assert page_id.replace("-", "").isalnum()  # UUID format
        #
        # # Verify entry exists in Notion (optional - could query back)
        # # response = await integrator.client.query_database(
        # #     database_id=companies_db_id,
        # #     filter_conditions={"property": "Name", "title": {"equals": "신규회사"}}
        # # )
        # # assert len(response["results"]) == 1
        # # assert response["results"][0]["id"] == page_id
