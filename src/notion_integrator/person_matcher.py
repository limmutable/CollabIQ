"""
Person name matching for Notion people field population.

This module provides interfaces and implementations for matching extracted
person names to Notion workspace users.
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from rapidfuzz import fuzz

from models.matching import PersonMatch


logger = logging.getLogger(__name__)


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

    def __init__(
        self,
        notion_client,
        cache_dir: Optional[str] = None,
        cache_ttl_hours: int = 24,
    ):
        """
        Initialize NotionPersonMatcher.

        Args:
            notion_client: NotionClient instance for API access
            cache_dir: Cache directory (defaults to data/notion_cache)
            cache_ttl_hours: Cache TTL in hours (default: 24)
        """
        self.notion_client = notion_client
        self.cache_dir = Path(cache_dir or "data/notion_cache")
        self.cache_ttl_hours = cache_ttl_hours
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            "NotionPersonMatcher initialized",
            extra={
                "cache_dir": str(self.cache_dir),
                "cache_ttl_hours": cache_ttl_hours,
            },
        )

    def list_users(self, *, force_refresh: bool = False) -> List[NotionUser]:
        """
        List Notion workspace users with caching (synchronous version).

        Cache Location: data/notion_cache/users_list.json
        Cache TTL: 24 hours (86400 seconds)

        Args:
            force_refresh: Bypass cache and fetch fresh from API

        Returns:
            List of NotionUser objects

        Note: This is a sync wrapper. Use list_users_async() from async contexts.
        """
        # Try cache first unless force refresh
        if not force_refresh:
            cached_users = self._get_from_cache()
            if cached_users is not None:
                logger.info(
                    "Users loaded from cache", extra={"user_count": len(cached_users)}
                )
                return cached_users

        # Cache miss or force refresh - fetch from API
        logger.info("Fetching users from Notion API")

        # Run async fetch
        try:
            users = asyncio.run(self._fetch_from_api_async())
        except RuntimeError:
            # Already in async context - this shouldn't be called from async
            raise RuntimeError(
                "list_users() called from async context. Use list_users_async() instead."
            )

        # Save to cache
        self._save_to_cache(users)

        return users

    async def list_users_async(
        self, *, force_refresh: bool = False
    ) -> List[NotionUser]:
        """
        List Notion workspace users with caching (async version).

        Cache Location: data/notion_cache/users_list.json
        Cache TTL: 24 hours (86400 seconds)

        Args:
            force_refresh: Bypass cache and fetch fresh from API

        Returns:
            List of NotionUser objects
        """
        # Try cache first unless force refresh
        if not force_refresh:
            cached_users = self._get_from_cache()
            if cached_users is not None:
                logger.info(
                    "Users loaded from cache", extra={"user_count": len(cached_users)}
                )
                return cached_users

        # Cache miss or force refresh - fetch from API
        logger.info("Fetching users from Notion API")
        users = await self._fetch_from_api_async()

        # Save to cache
        self._save_to_cache(users)

        return users

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
        # Validate inputs
        if not (0.0 <= similarity_threshold <= 1.0):
            raise ValueError(
                f"similarity_threshold must be between 0.0 and 1.0, got {similarity_threshold}"
            )

        normalized_name = person_name.strip()
        if not normalized_name:
            raise ValueError("Person name cannot be empty or whitespace-only")

        # Load users from cache
        users = self.list_users()

        # Convert to candidates format
        candidates = [(user.id, user.name) for user in users]

        # Step 1: Search for exact match
        exact_match = self._find_exact_match(normalized_name, candidates)
        if exact_match:
            user_id, matched_name = exact_match
            return PersonMatch(
                user_id=user_id,
                user_name=matched_name,
                similarity_score=1.0,
                match_type="exact",
                confidence_level="high",
                is_ambiguous=False,
                alternative_matches=[],
                match_method="character",
            )

        # Step 2: Compute fuzzy similarity for all candidates
        scored_matches = []
        for user_id, user_name in candidates:
            similarity = fuzz.ratio(normalized_name, user_name) / 100.0
            scored_matches.append((user_id, user_name, similarity))

        # Sort by similarity (descending)
        scored_matches.sort(key=lambda x: x[2], reverse=True)

        # Step 3: Check if best match meets threshold
        if not scored_matches or scored_matches[0][2] < similarity_threshold:
            # No match found
            return PersonMatch(
                user_id=None,
                user_name="",
                similarity_score=scored_matches[0][2] if scored_matches else 0.0,
                match_type="none",
                confidence_level="none",
                is_ambiguous=False,
                alternative_matches=[],
                match_method="character",
            )

        # Step 4: Check for ambiguity
        best_match = scored_matches[0]
        user_id, matched_name, similarity = best_match

        is_ambiguous = False
        alternative_matches = []

        if len(scored_matches) >= 2:
            second_best = scored_matches[1]
            score_difference = similarity - second_best[2]

            # Ambiguous if top 2 scores differ by < 0.10
            if score_difference < 0.10:
                is_ambiguous = True
                # Include top matches as alternatives
                alternative_matches = [
                    {
                        "user_id": uid,
                        "user_name": uname,
                        "similarity_score": f"{sim:.2f}",  # Convert to string
                    }
                    for uid, uname, sim in scored_matches[:3]  # Top 3
                    if sim >= similarity_threshold
                ]

        # Compute confidence level
        confidence = self._compute_confidence_level(similarity, is_ambiguous)

        return PersonMatch(
            user_id=user_id,
            user_name=matched_name,
            similarity_score=similarity,
            match_type="fuzzy" if similarity < 1.0 else "exact",
            confidence_level=confidence,
            is_ambiguous=is_ambiguous,
            alternative_matches=alternative_matches,
            match_method="character",
        )

    def _find_exact_match(
        self, normalized_name: str, candidates: List[Tuple[str, str]]
    ) -> Optional[Tuple[str, str]]:
        """Search for exact match (case-sensitive)."""
        for user_id, user_name in candidates:
            if normalized_name == user_name:
                return (user_id, user_name)
        return None

    def _compute_confidence_level(
        self, similarity_score: float, is_ambiguous: bool
    ) -> str:
        """
        Compute confidence level from similarity score and ambiguity.

        Thresholds:
        - high: similarity ≥ 0.95 and not ambiguous
        - medium: 0.85 ≤ similarity < 0.95 or ambiguous
        - low: 0.70 ≤ similarity < 0.85
        - none: similarity < 0.70
        """
        if is_ambiguous:
            return "medium"  # Ambiguous matches are medium confidence

        if similarity_score >= 0.95:
            return "high"
        elif similarity_score >= 0.85:
            return "medium"
        elif similarity_score >= 0.70:
            return "low"
        else:
            return "none"

    async def _fetch_from_api_async(self) -> List[NotionUser]:
        """Fetch users from Notion API asynchronously.

        Note: This uses the Notion SDK's async users.list() API.
        The notion_client parameter should be a NotionClient instance.

        Returns:
            List of NotionUser objects
        """
        try:
            # Access the underlying Notion SDK client
            # NotionClient wraps the official notion-client SDK
            sdk_client = self.notion_client.client

            # Call Notion SDK users.list() API (async)
            # Returns: {"results": [{"id": "...", "name": "...", "person": {"email": "..."}, "type": "person"}]}
            response = await sdk_client.users.list()

            # Extract users from response
            users = []
            for user_data in response.get("results", []):
                user_id = user_data.get("id")
                user_type = user_data.get("type", "person")

                # Get name from name field
                name = user_data.get("name", "")

                # Get email from person.email
                email = None
                if user_type == "person":
                    person_data = user_data.get("person", {})
                    email = person_data.get("email")

                if user_id:
                    users.append(
                        NotionUser(
                            id=user_id,
                            name=name,
                            email=email,
                            type=user_type,
                        )
                    )

            logger.info(
                "Users fetched from API",
                extra={"user_count": len(users)},
            )

            return users

        except Exception as e:
            logger.error(
                "Failed to fetch users from API",
                extra={"error": str(e)},
                exc_info=True,
            )
            raise

    def _get_from_cache(self) -> Optional[List[NotionUser]]:
        """
        Get users from cache if valid.

        Returns:
            List of NotionUser objects or None if cache invalid
        """
        cache_path = self.cache_dir / "users_list.json"

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cache_data = json.load(f)

            # Validate cache structure
            if not isinstance(cache_data, dict):
                logger.warning("Invalid cache format (not a dict)")
                return None

            # Check expiration
            cached_at_str = cache_data.get("cached_at")
            if not cached_at_str:
                logger.warning("Cache missing cached_at timestamp")
                return None

            cached_at = datetime.fromisoformat(cached_at_str)
            age_hours = (datetime.now() - cached_at).total_seconds() / 3600

            if age_hours > self.cache_ttl_hours:
                logger.info(
                    "Cache expired",
                    extra={"age_hours": age_hours, "ttl_hours": self.cache_ttl_hours},
                )
                return None

            # Extract users
            users_data = cache_data.get("users", [])
            if not isinstance(users_data, list):
                logger.warning("Invalid cache format (users not a list)")
                return None

            users = [
                NotionUser(
                    id=user["id"],
                    name=user["name"],
                    email=user.get("email"),
                    type=user.get("type", "person"),
                )
                for user in users_data
                if "id" in user and "name" in user
            ]

            if not users:
                logger.warning("Cache contains no valid users")
                return None

            return users

        except Exception as e:
            logger.warning("Error reading users from cache", extra={"error": str(e)})
            return None

    def _save_to_cache(self, users: List[NotionUser]) -> None:
        """
        Save users to cache.

        Args:
            users: List of NotionUser objects
        """
        cache_path = self.cache_dir / "users_list.json"

        try:
            cache_data = {
                "version": 1,
                "cached_at": datetime.now().isoformat(),
                "ttl_seconds": self.cache_ttl_hours * 3600,
                "users": [
                    {
                        "id": user.id,
                        "name": user.name,
                        "email": user.email,
                        "type": user.type,
                    }
                    for user in users
                ],
            }

            # Write atomically using temp file
            temp_path = cache_path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)

            # Atomic rename
            temp_path.replace(cache_path)

            logger.info("Users saved to cache", extra={"user_count": len(users)})

        except Exception as e:
            logger.warning("Failed to save users to cache", extra={"error": str(e)})
            # Don't raise - cache write failure is not critical

    def invalidate_cache(self) -> None:
        """Invalidate user cache without fetching new data."""
        cache_path = self.cache_dir / "users_list.json"

        if cache_path.exists():
            cache_path.unlink()
            logger.info("User cache invalidated")
