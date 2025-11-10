"""
Fuzzy company name matching for Notion field population.

This module provides interfaces and implementations for matching extracted
company names to the Notion Companies database using fuzzy string matching.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from src.models.matching import CompanyMatch


class CompanyMatcher(ABC):
    """
    Abstract interface for company name matching algorithms.

    This interface enables dependency injection and algorithm swapping
    (e.g., character-based rapidfuzz, LLM-based semantic, hybrid).
    """

    @abstractmethod
    def match(
        self,
        company_name: str,
        candidates: List[tuple[str, str]],
        *,
        auto_create: bool = True,
        similarity_threshold: float = 0.85,
    ) -> CompanyMatch:
        """
        Match extracted company name to Companies database.

        Args:
            company_name: Extracted company name from LLM (may have variations)
            candidates: List of (page_id, company_name) tuples from Companies database
            auto_create: Whether to auto-create company if no match found
            similarity_threshold: Minimum similarity score for match (default: 0.85)

        Returns:
            CompanyMatch: Result with page_id, similarity score, match type, confidence

        Raises:
            ValueError: If company_name is empty or threshold is invalid
            NotionAPIError: If Notion API calls fail during matching or creation
        """
        pass


class RapidfuzzMatcher(CompanyMatcher):
    """
    Character-based fuzzy matcher using rapidfuzz library (MVP implementation).

    Uses Jaro-Winkler similarity algorithm for Korean company name matching.
    Handles spelling variations, spacing, character substitutions.

    Does not handle: abbreviations (SSG), multi-language (Samsung/삼성), semantic.
    """

    def match(
        self,
        company_name: str,
        candidates: List[tuple[str, str]],
        *,
        auto_create: bool = True,
        similarity_threshold: float = 0.85,
    ) -> CompanyMatch:
        """
        Match company name using rapidfuzz Jaro-Winkler algorithm.

        Algorithm:
        1. Search exact match (case-sensitive) → return similarity 1.0
        2. Compute Jaro-Winkler similarity for all candidates
        3. If best match ≥ threshold → return CompanyMatch with page_id
        4. If best match < threshold and auto_create → create new company
        5. Otherwise → return CompanyMatch with page_id=None, match_type='none'

        Args:
            company_name: Extracted company name (will be normalized: trim whitespace)
            candidates: List of (page_id, company_name) from Companies database
            auto_create: Create new company if no match found (default: True)
            similarity_threshold: Minimum similarity for match (default: 0.85)

        Returns:
            CompanyMatch with match_type:
            - 'exact': Exact match found (similarity 1.0)
            - 'fuzzy': Fuzzy match ≥ threshold (similarity 0.85-0.99)
            - 'created': No match, new company auto-created
            - 'none': No match and auto_create=False
        """
        # Implementation will be added in T010-T013
        raise NotImplementedError("RapidfuzzMatcher.match() not yet implemented")
