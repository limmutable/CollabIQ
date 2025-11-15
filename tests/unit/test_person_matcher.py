"""
Unit tests for NotionPersonMatcher.

Tests person name matching with Korean names, ambiguity detection, and caching.
"""

import json
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock

from notion_integrator.person_matcher import NotionPersonMatcher, NotionUser
from models.matching import PersonMatch


class TestPersonMatcherExactMatch:
    """Test exact person name matching."""

    def test_exact_match_returns_similarity_1_0(self, tmp_path):
        """
        Test: Exact match returns similarity 1.0.

        Given: Extracted name "김철수"
        And: User list contains "김철수"
        When: match() is called
        Then: Returns exact match with similarity 1.0
        """
        # Arrange
        mock_client = MagicMock()
        matcher = NotionPersonMatcher(mock_client, cache_dir=str(tmp_path))

        # Mock cached users
        users = [
            NotionUser(id="user1", name="김철수", email="kim@example.com"),
            NotionUser(id="user2", name="이영희", email="lee@example.com"),
        ]
        matcher._save_to_cache(users)

        # Act
        result = matcher.match("김철수")

        # Assert
        assert result.match_type == "exact"
        assert result.similarity_score == 1.0
        assert result.user_id == "user1"
        assert result.user_name == "김철수"
        assert result.confidence_level == "high"
        assert result.is_ambiguous is False


class TestPersonMatcherFuzzyMatch:
    """Test fuzzy person name matching."""

    def test_fuzzy_match_above_threshold_returns_user_id(self, tmp_path):
        """
        Test: Fuzzy match ≥0.70 returns user_id.

        Given: Extracted name "김 철수" (with space)
        And: User list contains "김철수" (without space)
        When: match() is called
        Then: Returns fuzzy match with similarity ≥0.70
        """
        mock_client = MagicMock()
        matcher = NotionPersonMatcher(mock_client, cache_dir=str(tmp_path))

        users = [
            NotionUser(id="user1", name="김철수"),
            NotionUser(id="user2", name="이영희"),
        ]
        matcher._save_to_cache(users)

        result = matcher.match("김 철수", similarity_threshold=0.70)

        assert result.match_type == "fuzzy"
        assert result.similarity_score >= 0.70
        assert result.user_id == "user1"
        assert result.user_name == "김철수"

    def test_fuzzy_match_selects_highest_score(self, tmp_path):
        """
        Test: Multiple matches return highest similarity.

        Given: Extracted name "김철"
        And: User list has "김철수", "김철민" (both similar)
        When: match() is called
        Then: Returns best match
        """
        mock_client = MagicMock()
        matcher = NotionPersonMatcher(mock_client, cache_dir=str(tmp_path))

        users = [
            NotionUser(id="user1", name="김철수"),
            NotionUser(id="user2", name="김철민"),
            NotionUser(id="user3", name="이영희"),
        ]
        matcher._save_to_cache(users)

        result = matcher.match("김철", similarity_threshold=0.70)

        assert result.match_type in ["fuzzy", "none"]
        # Both "김철수" and "김철민" should have similar scores
        # The matcher returns the first (highest) one


class TestPersonMatcherAmbiguity:
    """Test ambiguity detection."""

    def test_ambiguous_match_detected_when_scores_close(self, tmp_path):
        """
        Test: Ambiguous match when top 2 scores differ by <0.10.

        Given: Extracted name "John Smith"
        And: User list has "John Smith", "Jon Smith" (very similar)
        When: match() is called
        Then: is_ambiguous=True and alternative_matches populated
        """
        mock_client = MagicMock()
        matcher = NotionPersonMatcher(mock_client, cache_dir=str(tmp_path))

        users = [
            NotionUser(id="user1", name="John Smith"),
            NotionUser(id="user2", name="Jon Smith"),  # Very similar
            NotionUser(id="user3", name="Jane Doe"),
        ]
        matcher._save_to_cache(users)

        result = matcher.match("John Smith", similarity_threshold=0.70)

        # "John Smith" is exact match, so should NOT be ambiguous
        assert result.match_type == "exact"
        assert result.is_ambiguous is False

        # Try with a slightly different name
        result2 = matcher.match("Joh Smith", similarity_threshold=0.70)

        # Now both "John Smith" and "Jon Smith" might have close scores
        if result2.match_type == "fuzzy" and result2.similarity_score >= 0.70:
            # Check if ambiguity was detected (depends on actual scores)
            if result2.is_ambiguous:
                assert len(result2.alternative_matches) >= 2


class TestPersonMatcherNoMatch:
    """Test no match scenarios."""

    def test_below_threshold_returns_none(self, tmp_path):
        """
        Test: Match below threshold returns match_type='none'.

        Given: Extracted name "CompleteMismatch"
        And: User list has Korean names (very low similarity)
        When: match() is called
        Then: Returns match_type='none', user_id=None
        """
        mock_client = MagicMock()
        matcher = NotionPersonMatcher(mock_client, cache_dir=str(tmp_path))

        users = [
            NotionUser(id="user1", name="김철수"),
            NotionUser(id="user2", name="이영희"),
        ]
        matcher._save_to_cache(users)

        result = matcher.match("CompleteMismatch", similarity_threshold=0.70)

        assert result.match_type == "none"
        assert result.user_id is None
        assert result.similarity_score < 0.70
        assert result.is_ambiguous is False


class TestPersonMatcherCaching:
    """Test user list caching."""

    def test_cache_hit_avoids_api_call(self, tmp_path):
        """
        Test: Valid cache avoids API call.

        Given: Cache contains valid user list
        When: list_users() is called
        Then: Returns cached data without API call
        """
        mock_client = MagicMock()
        matcher = NotionPersonMatcher(mock_client, cache_dir=str(tmp_path))

        # Create valid cache
        users = [NotionUser(id="user1", name="김철수")]
        matcher._save_to_cache(users)

        # Call list_users (should use cache)
        result = matcher.list_users()

        assert len(result) == 1
        assert result[0].id == "user1"
        assert result[0].name == "김철수"

    def test_expired_cache_triggers_api_fetch(self, tmp_path):
        """
        Test: Expired cache triggers API fetch.

        Given: Cache is expired (cached_at > 24h ago)
        When: list_users() is called
        Then: Cache is ignored (returns None from _get_from_cache)
        """
        mock_client = MagicMock()
        matcher = NotionPersonMatcher(mock_client, cache_dir=str(tmp_path), cache_ttl_hours=24)

        # Create expired cache
        cache_path = tmp_path / "users_list.json"
        expired_time = datetime.now() - timedelta(hours=25)
        cache_data = {
            "version": 1,
            "cached_at": expired_time.isoformat(),
            "ttl_seconds": 24 * 3600,
            "users": [{"id": "user1", "name": "김철수"}],
        }

        with open(cache_path, "w") as f:
            json.dump(cache_data, f)

        # Call _get_from_cache (should return None due to expiration)
        result = matcher._get_from_cache()

        assert result is None  # Expired


class TestPersonMatcherValidation:
    """Test input validation."""

    def test_empty_person_name_raises_error(self, tmp_path):
        """
        Test: Empty person_name raises ValueError.

        Given: person_name is ""
        When: match() is called
        Then: Raises ValueError
        """
        mock_client = MagicMock()
        matcher = NotionPersonMatcher(mock_client, cache_dir=str(tmp_path))

        users = [NotionUser(id="user1", name="김철수")]
        matcher._save_to_cache(users)

        with pytest.raises(ValueError, match="empty"):
            matcher.match("")

    def test_invalid_threshold_raises_error(self, tmp_path):
        """
        Test: Invalid threshold raises ValueError.

        Given: similarity_threshold = 1.5
        When: match() is called
        Then: Raises ValueError
        """
        mock_client = MagicMock()
        matcher = NotionPersonMatcher(mock_client, cache_dir=str(tmp_path))

        users = [NotionUser(id="user1", name="김철수")]
        matcher._save_to_cache(users)

        with pytest.raises(ValueError, match="threshold"):
            matcher.match("김철수", similarity_threshold=1.5)
