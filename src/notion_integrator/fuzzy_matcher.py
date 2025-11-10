"""
Fuzzy company name matching for Notion field population.

This module provides interfaces and implementations for matching extracted
company names to the Notion Companies database using fuzzy string matching.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from rapidfuzz import fuzz

from models.matching import CompanyMatch


def normalize_company_name(name: str) -> str:
    """
    Normalize company name for matching.

    Normalization rules:
    1. Trim leading/trailing whitespace
    2. No other transformations (preserve case, punctuation, internal spacing)

    Args:
        name: Raw company name (may have extra whitespace)

    Returns:
        Normalized company name

    Raises:
        ValueError: If name is empty or whitespace-only after normalization
    """
    normalized = name.strip()

    if not normalized:
        raise ValueError("Company name cannot be empty or whitespace-only")

    return normalized


def normalize_for_matching(name: str) -> str:
    """
    Additional normalization for fuzzy matching.

    Handles common Korean company name variations:
    1. Removes parentheticals: "웨이크(산스)" → "웨이크"
    2. Normalizes Korean character variants: "네트워크" ↔ "네트웍"

    Args:
        name: Normalized company name

    Returns:
        Name with normalization applied for better matching
    """
    import re

    # Remove parenthetical content like (산스), (주), etc.
    without_parens = re.sub(r'\([^)]*\)', '', name).strip()

    # Normalize Korean character variants
    # Common substitutions in Korean company names:
    # ㅓ vs ㅕ variants, ㅗ vs ㅜ variants, final consonant variants
    normalized = without_parens

    # 워크 (work) ↔ 웍 (same pronunciation, different spelling)
    # Common in "네트워크" (network) variations
    normalized = normalized.replace('워크', '웍')
    normalized = normalized.replace('웍스', '웍')  # 웍스 → 웍 for matching

    return normalized


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

    Uses rapidfuzz.fuzz.ratio() for Korean company name matching.
    Handles spelling variations, spacing, character substitutions.

    Does not handle: abbreviations (SSG), multi-language (Samsung/삼성), semantic.

    Note: This matcher signals when company creation is needed (returns match_type="none"
    with company_name set). The actual creation is handled by NotionWriter.create_company()
    which should be called by the integration layer (FieldMapper) when it detects this signal.
    """

    def _find_exact_match(
        self, normalized_name: str, candidates: List[tuple[str, str]]
    ) -> Optional[tuple[str, str]]:
        """
        Search for exact match (case-sensitive).

        Args:
            normalized_name: Normalized extracted company name
            candidates: List of (page_id, company_name) tuples

        Returns:
            (page_id, company_name) if exact match found, None otherwise
        """
        for page_id, candidate_name in candidates:
            normalized_candidate = normalize_company_name(candidate_name)
            if normalized_name == normalized_candidate:
                return (page_id, candidate_name)
        return None

    def _find_fuzzy_match(
        self,
        normalized_name: str,
        candidates: List[tuple[str, str]],
        threshold: float,
    ) -> Optional[tuple[str, str, float]]:
        """
        Search for fuzzy match using hybrid rapidfuzz approach.

        Uses multiple scoring strategies to handle Korean text variations:
        1. Standard fuzz.ratio() for general similarity
        2. partial_ratio() for parenthetical cases like "웨이크(산스)" → "웨이크"
        3. Parenthetical normalization for exact matching after removal

        Takes the maximum score across all strategies.

        Args:
            normalized_name: Normalized extracted company name
            candidates: List of (page_id, company_name) tuples
            threshold: Minimum similarity score (0.0-1.0)

        Returns:
            (page_id, company_name, similarity_score) if match found, None otherwise
        """
        best_match = None
        best_score = 0.0

        # Normalize for matching (remove parentheticals)
        matching_name = normalize_for_matching(normalized_name)

        for page_id, candidate_name in candidates:
            normalized_candidate = normalize_company_name(candidate_name)
            matching_candidate = normalize_for_matching(normalized_candidate)

            # Strategy 1: Standard ratio (handles spacing, minor variations)
            score_ratio = fuzz.ratio(normalized_name, normalized_candidate) / 100.0

            # Strategy 2: Partial ratio (ONLY for parentheticals)
            # Only use if one string has parentheses (indicates likely parenthetical case)
            # This prevents "스타트업" matching "스타트업A" at 1.0
            use_partial = '(' in normalized_name or ')' in normalized_name or '(' in normalized_candidate or ')' in normalized_candidate
            score_partial = fuzz.partial_ratio(normalized_name, normalized_candidate) / 100.0 if use_partial else 0.0

            # Strategy 3: Exact match after parenthetical removal
            score_normalized = 1.0 if matching_name == matching_candidate else 0.0

            # Strategy 4: Ratio on normalized forms (for Korean variants)
            score_normalized_fuzzy = fuzz.ratio(matching_name, matching_candidate) / 100.0

            # Take the maximum score across all strategies
            similarity = max(score_ratio, score_partial, score_normalized, score_normalized_fuzzy)

            if similarity > best_score:
                best_score = similarity
                best_match = (page_id, candidate_name, similarity)

        # Return best match if it meets threshold
        if best_match and best_score >= threshold:
            return best_match

        return None

    def _compute_confidence_level(self, similarity_score: float) -> str:
        """
        Compute confidence level from similarity score.

        Thresholds per data-model.md:
        - high: similarity ≥ 0.95 or exact/created
        - medium: 0.85 ≤ similarity < 0.95
        - low: 0.70 ≤ similarity < 0.85 (below company threshold but logged)
        - none: similarity < 0.70

        Args:
            similarity_score: Similarity score (0.0-1.0)

        Returns:
            Confidence level: "high", "medium", "low", or "none"
        """
        if similarity_score >= 0.95:
            return "high"
        elif similarity_score >= 0.85:
            return "medium"
        elif similarity_score >= 0.70:
            return "low"
        else:
            return "none"

    def match(
        self,
        company_name: str,
        candidates: List[tuple[str, str]],
        *,
        auto_create: bool = True,
        similarity_threshold: float = 0.85,
    ) -> CompanyMatch:
        """
        Match company name using rapidfuzz algorithm.

        Algorithm:
        1. Validate inputs
        2. Normalize company name (trim whitespace)
        3. Search exact match (case-sensitive) → return similarity 1.0
        4. Compute fuzzy similarity for all candidates
        5. If best match ≥ threshold → return CompanyMatch with page_id
        6. If best match < threshold and auto_create → signal creation needed
        7. Otherwise → return CompanyMatch with page_id=None, match_type='none'

        Args:
            company_name: Extracted company name (will be normalized: trim whitespace)
            candidates: List of (page_id, company_name) from Companies database
            auto_create: Create new company if no match found (default: True)
            similarity_threshold: Minimum similarity for match (default: 0.85)

        Returns:
            CompanyMatch with match_type:
            - 'exact': Exact match found (similarity 1.0)
            - 'fuzzy': Fuzzy match ≥ threshold (similarity 0.85-0.99)
            - 'created': No match, new company should be auto-created
                         (Note: Actual creation happens in Phase 4/T018)
            - 'none': No match and auto_create=False

        Raises:
            ValueError: If company_name is empty or threshold is invalid
        """
        # Validate threshold
        if not (0.0 <= similarity_threshold <= 1.0):
            raise ValueError(
                f"similarity_threshold must be between 0.0 and 1.0, got {similarity_threshold}"
            )

        # Normalize company name (raises ValueError if empty)
        normalized_name = normalize_company_name(company_name)

        # Step 1: Search for exact match
        exact_match = self._find_exact_match(normalized_name, candidates)
        if exact_match:
            page_id, matched_name = exact_match
            return CompanyMatch(
                page_id=page_id,
                company_name=matched_name,
                similarity_score=1.0,
                match_type="exact",
                confidence_level="high",
                was_created=False,
                match_method="character",
            )

        # Step 2: Search for fuzzy match
        fuzzy_match = self._find_fuzzy_match(
            normalized_name, candidates, similarity_threshold
        )
        if fuzzy_match:
            page_id, matched_name, similarity = fuzzy_match

            # If fuzzy matching found perfect match (1.0), treat as exact
            # This can happen when normalization (parenthetical removal, Korean variants) creates exact match
            if similarity == 1.0:
                return CompanyMatch(
                    page_id=page_id,
                    company_name=matched_name,
                    similarity_score=1.0,
                    match_type="exact",
                    confidence_level="high",
                    was_created=False,
                    match_method="character",
                )

            confidence = self._compute_confidence_level(similarity)
            return CompanyMatch(
                page_id=page_id,
                company_name=matched_name,
                similarity_score=similarity,
                match_type="fuzzy",
                confidence_level=confidence,
                was_created=False,
                match_method="character",
            )

        # Step 3: No match found
        if auto_create:
            # Signal that creation is needed
            # The actual Notion API call is handled by the caller (FieldMapper/integration layer)
            # which will call NotionWriter.create_company() and update the result
            return CompanyMatch(
                page_id=None,  # Will be set after creation by caller
                company_name=normalized_name,
                similarity_score=0.0,
                match_type="none",  # Caller will check this and create
                confidence_level="none",
                was_created=False,  # Will be True after caller creates
                match_method="character",
            )
        else:
            # No match and auto_create=False
            return CompanyMatch(
                page_id=None,
                company_name="",
                similarity_score=0.0,
                match_type="none",
                confidence_level="none",
                was_created=False,
                match_method="character",
            )
