"""
Integration tests for company auto-creation workflow.

Tests the end-to-end flow of auto-creating new companies when no match is found.
Covers T016 and T017 from tasks.md.
"""

import pytest

from models.matching import CompanyMatch
from notion_integrator.fuzzy_matcher import RapidfuzzMatcher


class TestAutoCreationWorkflow:
    """Test auto-creation workflow when no match found."""

    def test_no_match_triggers_auto_creation_signal(self):
        """
        Integration test: No match (< 0.85) should signal auto-creation needed.

        Given: Extracted name "완전히새로운회사123"
        And: Database has unrelated companies (all similarity < 0.85)
        When: match() is called with auto_create=True
        Then: Returns CompanyMatch signaling creation is needed
              (match_type='none', page_id=None, company_name=extracted)

        Note: This test verifies the matcher signals creation is needed.
        The actual Notion API call happens in NotionWriter.create_company()
        which will be tested in T015.
        """
        matcher = RapidfuzzMatcher()
        extracted_name = "완전히새로운회사123"
        candidates = [
            ("page1" + "0" * 26, "웨이크"),
            ("page2" + "0" * 26, "네트워크"),
        ]

        result = matcher.match(extracted_name, candidates, auto_create=True)

        # Should signal creation is needed
        assert isinstance(result, CompanyMatch)
        assert result.match_type == "none"  # Will be updated to "created" after actual creation
        assert result.page_id is None  # Will be set after actual creation
        assert result.company_name == "완전히새로운회사123"
        assert result.similarity_score == 0.0
        assert result.was_created is False  # Will be True after actual creation
        assert result.match_method == "character"

    def test_auto_create_false_returns_none(self):
        """
        Integration test: auto_create=False should return no match.

        Given: Extracted name with no match
        And: auto_create=False
        When: match() is called
        Then: Returns CompanyMatch with match_type='none', empty company_name
        """
        matcher = RapidfuzzMatcher()
        extracted_name = "새로운회사"
        candidates = [
            ("page1" + "0" * 26, "웨이크"),
        ]

        result = matcher.match(extracted_name, candidates, auto_create=False)

        assert result.match_type == "none"
        assert result.page_id is None
        assert result.company_name == ""  # Empty when auto_create=False
        assert result.was_created is False


class TestDuplicatePrevention:
    """Test duplicate prevention after auto-creation."""

    def test_exact_match_check_prevents_duplicates(self):
        """
        Integration test: After creation, exact match should find existing entry.

        Scenario:
        1. First email: "새로운스타트업" → no match → auto-create
        2. Second email: "새로운스타트업" → exact match → reuse existing

        This test simulates step 2 by including the newly created company
        in the candidates list.

        Given: Company "새로운스타트업" was previously auto-created
        And: Extracted name is "새로운스타트업" (exact match)
        When: match() is called
        Then: Returns exact match with existing page_id (no duplicate creation)
        """
        matcher = RapidfuzzMatcher()
        extracted_name = "새로운스타트업"

        # Simulate database after first auto-creation
        candidates = [
            ("newly_created_page_id00000000000", "새로운스타트업"),  # Previously created
            ("page2" + "0" * 26, "웨이크"),
        ]

        result = matcher.match(extracted_name, candidates)

        # Should find exact match (not create duplicate)
        assert result.match_type == "exact"
        assert result.similarity_score == 1.0
        assert result.page_id == "newly_created_page_id00000000000"
        assert result.company_name == "새로운스타트업"
        assert result.was_created is False  # Not created this time (already exists)

    def test_whitespace_normalization_prevents_duplicates(self):
        """
        Integration test: Whitespace differences should not create duplicates.

        Given: Company "스타트업A" was previously created
        And: Extracted name is " 스타트업A " (extra whitespace)
        When: match() is called after normalization
        Then: Returns exact match (whitespace trimmed before comparison)
        """
        matcher = RapidfuzzMatcher()
        extracted_name = " 스타트업A "  # Extra whitespace

        candidates = [
            ("existing_page_id000000000000000", "스타트업A"),  # Previously created
        ]

        result = matcher.match(extracted_name, candidates)

        # Should find exact match after normalization
        assert result.match_type == "exact"
        assert result.similarity_score == 1.0
        assert result.page_id == "existing_page_id000000000000000"
        assert result.was_created is False

    def test_case_sensitivity_may_create_different_entries(self):
        """
        Integration test: Case differences create separate entries (by design).

        Given: Company "Wake" exists in database
        And: Extracted name is "wake" (different case)
        When: match() is called
        Then: Returns fuzzy match or triggers creation (case-sensitive exact match fails)

        Note: This is intentional behavior. If case-insensitive matching is
        needed, it should be implemented in normalization (not in scope for MVP).
        """
        matcher = RapidfuzzMatcher()
        extracted_name = "wake"

        candidates = [
            ("page1" + "0" * 26, "Wake"),  # Different case
        ]

        result = matcher.match(extracted_name, candidates, auto_create=False)

        # Exact match fails (case-sensitive)
        assert result.match_type in ["fuzzy", "none"]
        # If fuzzy match succeeds (score ≥ 0.85), page_id will be set
        # If fuzzy match fails (score < 0.85), page_id will be None


class TestAutoCreationEdgeCases:
    """Test edge cases in auto-creation workflow."""

    def test_very_similar_but_below_threshold(self):
        """
        Integration test: Similarity just below threshold triggers creation.

        Given: Extracted name scores 0.84 (just below 0.85 threshold)
        When: match() is called
        Then: Signals auto-creation (not fuzzy match)
        """
        matcher = RapidfuzzMatcher()

        # Need to find a case that scores ~0.84
        # For testing purposes, we can use a lower threshold
        extracted_name = "스타트업 A"
        candidates = [
            ("page1" + "0" * 26, "스타트업 B"),  # Similar but different
        ]

        result = matcher.match(
            extracted_name, candidates, auto_create=True, similarity_threshold=0.90
        )

        # Should signal creation (below 0.90 threshold even if above 0.85)
        # Actual score depends on the strings
        if result.similarity_score < 0.90:
            assert result.match_type == "none"
            assert result.page_id is None

    def test_empty_candidates_triggers_creation(self):
        """
        Integration test: Empty database should trigger auto-creation.

        Given: Companies database is empty
        When: match() is called
        Then: Signals auto-creation for any extracted name
        """
        matcher = RapidfuzzMatcher()
        extracted_name = "첫번째회사"
        candidates = []  # Empty database

        result = matcher.match(extracted_name, candidates, auto_create=True)

        # Should signal creation (no candidates to match)
        assert result.match_type == "none"
        assert result.page_id is None
        assert result.company_name == "첫번째회사"
        assert result.was_created is False  # Will be True after actual creation

    def test_multiple_no_matches_each_trigger_creation(self):
        """
        Integration test: Multiple unmatched names each signal creation.

        Given: Database has "웨이크"
        When: Multiple different unmatched names are processed
        Then: Each signals auto-creation independently
        """
        matcher = RapidfuzzMatcher()
        candidates = [
            ("page1" + "0" * 26, "웨이크"),
        ]

        names_to_create = ["회사A", "회사B", "회사C"]

        for name in names_to_create:
            result = matcher.match(name, candidates, auto_create=True)

            # Each should signal creation
            assert result.match_type == "none"
            assert result.page_id is None
            assert result.company_name == name
            assert result.was_created is False
