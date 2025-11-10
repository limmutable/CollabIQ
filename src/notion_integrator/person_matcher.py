"""
Person name matching for Notion people field population.

This module provides interfaces and implementations for matching extracted
person names to Notion workspace users.
"""

from abc import ABC, abstractmethod
from typing import List

from src.models.matching import PersonMatch


class NotionUser:
    """
    Notion workspace user for person matching.

    Attributes:
        id: Notion user UUID
        name: Full name as appears in Notion
        email: Email address (if available)
        type: User type ('person' or 'bot')
    """

    def __init__(
        self,
        id: str,
        name: str,
        email: str | None = None,
        type: str = "person",
    ):
        self.id = id
        self.name = name
        self.email = email
        self.type = type


class PersonMatcher(ABC):
    """
    Abstract interface for person name matching algorithms.

    This interface enables dependency injection and algorithm swapping.
    """

    @abstractmethod
    def list_users(self, *, force_refresh: bool = False) -> List[NotionUser]:
        """
        List all Notion workspace users.

        Results are cached with 24h TTL in data/notion_cache/users_list.json
        to minimize API calls during person matching.

        Args:
            force_refresh: Bypass cache and fetch fresh from Notion API

        Returns:
            List of NotionUser objects with id, name, email, type

        Raises:
            NotionAPIError: If Notion API call fails
        """
        pass

    @abstractmethod
    def match(
        self,
        person_name: str,
        *,
        similarity_threshold: float = 0.70,
    ) -> PersonMatch:
        """
        Match extracted person name to Notion workspace users.

        Args:
            person_name: Extracted person name from LLM
            similarity_threshold: Minimum similarity score for match (default: 0.70)

        Returns:
            PersonMatch: Result with user_id, similarity score, match type, confidence,
                        ambiguity indicators

        Raises:
            ValueError: If person_name is empty or threshold is invalid
            NotionAPIError: If Notion API calls fail
        """
        pass


class NotionPersonMatcher(PersonMatcher):
    """
    Fuzzy person name matcher for Notion workspace users.

    Uses rapidfuzz for fuzzy matching with Korean name handling.
    Detects ambiguous matches when multiple users have similar scores.

    Features:
    - Caches user list for 24h to minimize API calls
    - Handles Korean names (family name + given name variations)
    - Detects ambiguity (top 2 scores differ by <0.10)
    - More lenient threshold (0.70) than company matching
    """

    def list_users(self, *, force_refresh: bool = False) -> List[NotionUser]:
        """
        List Notion workspace users with caching.

        Cache Location: data/notion_cache/users_list.json
        Cache TTL: 24 hours (86400 seconds)

        Args:
            force_refresh: Bypass cache and fetch fresh from API

        Returns:
            List of NotionUser objects
        """
        # Implementation will be added in T024
        raise NotImplementedError("NotionPersonMatcher.list_users() not yet implemented")

    def match(
        self,
        person_name: str,
        *,
        similarity_threshold: float = 0.70,
    ) -> PersonMatch:
        """
        Match person name using fuzzy matching with ambiguity detection.

        Algorithm:
        1. Load cached user list (or fetch if stale)
        2. Search exact match → return similarity 1.0
        3. Compute Jaro-Winkler similarity for all users
        4. Check ambiguity: If top 2 scores differ by <0.10 → mark ambiguous
        5. If best match ≥ threshold → return PersonMatch with user_id
        6. Otherwise → return PersonMatch with user_id=None, match_type='none'

        Args:
            person_name: Extracted person name (will be normalized)
            similarity_threshold: Minimum similarity for match (default: 0.70)

        Returns:
            PersonMatch with match_type:
            - 'exact': Exact match found (similarity 1.0)
            - 'fuzzy': Fuzzy match ≥ threshold (similarity 0.70-0.99)
            - 'none': No match found (similarity < 0.70)

            is_ambiguous=True if multiple users have similar scores
        """
        # Implementation will be added in T025
        raise NotImplementedError("NotionPersonMatcher.match() not yet implemented")
