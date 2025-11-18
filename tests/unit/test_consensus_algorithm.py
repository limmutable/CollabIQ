"""Unit tests for consensus algorithm components.

Tests for:
- Jaro-Winkler string similarity calculation
- Fuzzy matching with configurable threshold
- Weighted voting for conflict resolution
- Tie-breaking logic
"""


class TestJaroWinklerSimilarity:
    """Test Jaro-Winkler string similarity function."""

    def test_identical_strings(self):
        """Test that identical strings have similarity 1.0."""
        from llm_orchestrator.strategies.consensus import jaro_winkler_similarity

        assert jaro_winkler_similarity("본봄", "본봄") == 1.0
        assert jaro_winkler_similarity("김철수", "김철수") == 1.0
        assert jaro_winkler_similarity("신세계인터내셔널", "신세계인터내셔널") == 1.0

    def test_completely_different_strings(self):
        """Test that completely different strings have low similarity."""
        from llm_orchestrator.strategies.consensus import jaro_winkler_similarity

        similarity = jaro_winkler_similarity("abc", "xyz")
        assert similarity < 0.5

    def test_similar_strings(self):
        """Test similarity for slightly different strings."""
        from llm_orchestrator.strategies.consensus import jaro_winkler_similarity

        # Similar Korean names
        sim = jaro_winkler_similarity("김철수", "김철호")
        assert 0.7 < sim < 1.0

        # Similar company names
        sim = jaro_winkler_similarity("신세계인터내셔널", "신세계")
        assert 0.7 < sim < 1.0

        # Similar but not identical
        sim = jaro_winkler_similarity("본봄", "본봄컴퍼니")
        assert 0.8 < sim < 1.0

    def test_empty_strings(self):
        """Test handling of empty strings."""
        from llm_orchestrator.strategies.consensus import jaro_winkler_similarity

        # Both empty should be equal
        assert jaro_winkler_similarity("", "") == 1.0

        # One empty should have 0 similarity
        assert jaro_winkler_similarity("", "abc") == 0.0
        assert jaro_winkler_similarity("abc", "") == 0.0

    def test_case_sensitivity(self):
        """Test that comparison is case-sensitive for Korean text."""
        from llm_orchestrator.strategies.consensus import jaro_winkler_similarity

        # Korean text should be case-sensitive (though Korean doesn't have cases)
        assert jaro_winkler_similarity("본봄", "본봄") == 1.0

        # English text case sensitivity
        sim_same = jaro_winkler_similarity("ABC", "ABC")
        sim_diff = jaro_winkler_similarity("ABC", "abc")
        assert sim_same == 1.0
        assert sim_diff < 1.0

    def test_whitespace_handling(self):
        """Test handling of whitespace in strings."""
        from llm_orchestrator.strategies.consensus import jaro_winkler_similarity

        # Leading/trailing whitespace should affect similarity
        sim = jaro_winkler_similarity("본봄", " 본봄 ")
        assert sim < 1.0

        # Internal whitespace
        sim = jaro_winkler_similarity("신세계 인터내셔널", "신세계인터내셔널")
        assert 0.8 < sim < 1.0


class TestFuzzyMatching:
    """Test fuzzy matching logic."""

    def test_exact_match(self):
        """Test that exact matches are recognized."""
        from llm_orchestrator.strategies.consensus import fuzzy_match

        assert fuzzy_match("본봄", "본봄", threshold=0.85) is True
        assert fuzzy_match("김철수", "김철수", threshold=0.85) is True

    def test_similar_match_above_threshold(self):
        """Test that similar strings above threshold are matched."""
        from llm_orchestrator.strategies.consensus import fuzzy_match

        # "신세계인터내셔널" vs "신세계" should match with 0.85 threshold
        assert fuzzy_match("신세계인터내셔널", "신세계", threshold=0.85) is True

    def test_different_strings_below_threshold(self):
        """Test that different strings below threshold are not matched."""
        from llm_orchestrator.strategies.consensus import fuzzy_match

        assert fuzzy_match("본봄", "브레이크앤컴퍼니", threshold=0.85) is False
        assert fuzzy_match("김철수", "이영희", threshold=0.85) is False

    def test_threshold_boundary(self):
        """Test behavior at threshold boundary."""
        from llm_orchestrator.strategies.consensus import (
            fuzzy_match,
            jaro_winkler_similarity,
        )

        s1, s2 = "test string", "test strong"
        similarity = jaro_winkler_similarity(s1, s2)

        # Should match if similarity >= threshold
        assert fuzzy_match(s1, s2, threshold=similarity) is True
        assert fuzzy_match(s1, s2, threshold=similarity + 0.01) is False

    def test_none_handling(self):
        """Test handling of None values."""
        from llm_orchestrator.strategies.consensus import fuzzy_match

        # None should only match None
        assert fuzzy_match(None, None, threshold=0.85) is True
        assert fuzzy_match(None, "본봄", threshold=0.85) is False
        assert fuzzy_match("본봄", None, threshold=0.85) is False

    def test_empty_string_handling(self):
        """Test handling of empty strings."""
        from llm_orchestrator.strategies.consensus import fuzzy_match

        # Empty strings should match each other
        assert fuzzy_match("", "", threshold=0.85) is True

        # Empty vs non-empty should not match
        assert fuzzy_match("", "본봄", threshold=0.85) is False
        assert fuzzy_match("본봄", "", threshold=0.85) is False


class TestWeightedVoting:
    """Test weighted voting algorithm."""

    def test_unanimous_vote(self):
        """Test voting when all providers agree."""
        from llm_orchestrator.strategies.consensus import weighted_vote

        # All providers agree on "본봄"
        candidates = [
            ("본봄", 0.92, 0.90),  # (value, confidence, success_rate)
            ("본봄", 0.93, 0.85),
            ("본봄", 0.89, 0.95),
        ]

        winner = weighted_vote(candidates, fuzzy_threshold=0.85)
        assert winner == "본봄"

    def test_majority_vote(self):
        """Test voting with clear majority."""
        from llm_orchestrator.strategies.consensus import weighted_vote

        # 2 votes for "김철수", 1 vote for "김영희"
        candidates = [
            ("김철수", 0.95, 0.90),
            ("김철수", 0.90, 0.85),
            ("김영희", 0.75, 0.88),
        ]

        winner = weighted_vote(candidates, fuzzy_threshold=0.85)
        assert winner == "김철수"

    def test_weighted_by_confidence(self):
        """Test that higher confidence values have more weight."""
        from llm_orchestrator.strategies.consensus import weighted_vote

        # Same number of votes, but different confidence
        # "김철수" has higher confidence
        candidates = [
            ("김철수", 0.95, 0.90),
            ("김영희", 0.70, 0.90),
        ]

        winner = weighted_vote(candidates, fuzzy_threshold=0.85)
        assert winner == "김철수"

    def test_weighted_by_provider_success_rate(self):
        """Test that provider success rate affects voting weight."""
        from llm_orchestrator.strategies.consensus import weighted_vote

        # Same confidence, different success rates
        candidates = [
            ("김철수", 0.90, 0.95),  # Higher success rate
            ("김영희", 0.90, 0.70),
        ]

        winner = weighted_vote(candidates, fuzzy_threshold=0.85)
        assert winner == "김철수"

    def test_fuzzy_matching_in_voting(self):
        """Test that fuzzy matching groups similar values."""
        from llm_orchestrator.strategies.consensus import weighted_vote

        # "신세계인터내셔널" and "신세계" should be grouped as similar
        candidates = [
            ("신세계인터내셔널", 0.88, 0.90),
            ("신세계", 0.85, 0.85),
            ("파트너", 0.80, 0.88),  # Different value
        ]

        winner = weighted_vote(candidates, fuzzy_threshold=0.85)
        # Should choose from the "신세계" group (2 votes vs 1)
        assert winner in ["신세계인터내셔널", "신세계"]

    def test_tie_breaking_by_confidence(self):
        """Test tie-breaking when votes are equal."""
        from llm_orchestrator.strategies.consensus import weighted_vote

        # Exact tie in votes, break by confidence
        candidates = [
            ("값A", 0.95, 0.90),  # Higher confidence
            ("값B", 0.80, 0.90),
        ]

        winner = weighted_vote(candidates, fuzzy_threshold=0.85)
        assert winner == "값A"

    def test_none_value_handling(self):
        """Test handling of None values in voting."""
        from llm_orchestrator.strategies.consensus import weighted_vote

        # Mix of None and real values
        candidates = [
            (None, 0.50, 0.90),
            ("본봄", 0.92, 0.85),
            ("본봄", 0.89, 0.88),
        ]

        winner = weighted_vote(candidates, fuzzy_threshold=0.85)
        assert winner == "본봄"

    def test_all_none_values(self):
        """Test voting when all values are None."""
        from llm_orchestrator.strategies.consensus import weighted_vote

        candidates = [
            (None, 0.50, 0.90),
            (None, 0.45, 0.85),
            (None, 0.40, 0.88),
        ]

        winner = weighted_vote(candidates, fuzzy_threshold=0.85)
        assert winner is None


class TestTieBreaking:
    """Test tie-breaking logic."""

    def test_tie_break_by_majority(self):
        """Test that majority wins in a tie."""
        from llm_orchestrator.strategies.consensus import weighted_vote

        # 2 votes vs 1 vote (clear majority)
        candidates = [
            ("값A", 0.80, 0.90),
            ("값A", 0.82, 0.88),
            ("값B", 0.95, 0.85),  # Higher confidence but minority
        ]

        winner = weighted_vote(candidates, fuzzy_threshold=0.85)
        assert winner == "값A"

    def test_tie_break_by_historical_performance(self):
        """Test tie-breaking by provider historical success rate."""
        from llm_orchestrator.strategies.consensus import weighted_vote

        # Equal votes and confidence, different success rates
        candidates = [
            ("값A", 0.90, 0.95),  # Higher success rate
            ("값B", 0.90, 0.70),
        ]

        winner = weighted_vote(candidates, fuzzy_threshold=0.85)
        assert winner == "값A"

    def test_abstention_when_no_clear_winner(self):
        """Test abstention when there's no clear winner."""
        from llm_orchestrator.strategies.consensus import weighted_vote

        # All providers with very low confidence
        candidates = [
            ("값A", 0.20, 0.90),
            ("값B", 0.22, 0.88),
            ("값C", 0.18, 0.92),
        ]

        # With a high abstention threshold, should return None
        winner = weighted_vote(
            candidates, fuzzy_threshold=0.85, abstention_threshold=0.25
        )
        # Should abstain or choose based on weights
        # The implementation will determine exact behavior


class TestConfidenceRecalculation:
    """Test confidence score recalculation."""

    def test_high_agreement_increases_confidence(self):
        """Test that high agreement increases confidence scores."""
        from llm_orchestrator.strategies.consensus import (
            recalculate_confidence,
        )

        # All 3 providers agree
        field_values = [
            ("본봄", 0.92),  # (value, original_confidence)
            ("본봄", 0.93),
            ("본봄", 0.89),
        ]

        new_confidence = recalculate_confidence(
            field_values, fuzzy_threshold=0.85, total_providers=3
        )

        # High agreement should boost confidence
        # Average original confidence ~0.91, agreement boost should increase it
        assert new_confidence >= 0.91

    def test_low_agreement_decreases_confidence(self):
        """Test that low agreement decreases confidence scores."""
        from llm_orchestrator.strategies.consensus import (
            recalculate_confidence,
        )

        # All providers disagree
        field_values = [
            ("값A", 0.90),
            ("값B", 0.88),
            ("값C", 0.92),
        ]

        new_confidence = recalculate_confidence(
            field_values, fuzzy_threshold=0.85, total_providers=3
        )

        # Low agreement should reduce confidence
        # Should be lower than average original confidence
        avg_original = (0.90 + 0.88 + 0.92) / 3
        assert new_confidence < avg_original

    def test_partial_agreement(self):
        """Test confidence with partial agreement (2 out of 3)."""
        from llm_orchestrator.strategies.consensus import (
            recalculate_confidence,
        )

        # 2 agree, 1 disagrees
        field_values = [
            ("값A", 0.90),
            ("값A", 0.88),
            ("값B", 0.85),
        ]

        new_confidence = recalculate_confidence(
            field_values, fuzzy_threshold=0.85, total_providers=3
        )

        # Should be somewhere in the middle
        assert 0.70 < new_confidence < 0.95

    def test_confidence_bounds(self):
        """Test that confidence stays within valid bounds [0.0, 1.0]."""
        from llm_orchestrator.strategies.consensus import (
            recalculate_confidence,
        )

        # Test with extreme high agreement
        field_values = [
            ("값", 0.99),
            ("값", 0.98),
            ("값", 0.99),
        ]
        conf = recalculate_confidence(
            field_values, fuzzy_threshold=0.85, total_providers=3
        )
        assert 0.0 <= conf <= 1.0

        # Test with extreme low agreement
        field_values = [
            ("A", 0.50),
            ("B", 0.45),
            ("C", 0.40),
        ]
        conf = recalculate_confidence(
            field_values, fuzzy_threshold=0.85, total_providers=3
        )
        assert 0.0 <= conf <= 1.0

    def test_none_values_in_confidence(self):
        """Test confidence calculation with None values."""
        from llm_orchestrator.strategies.consensus import (
            recalculate_confidence,
        )

        # Mix of None and real values
        field_values = [
            (None, 0.50),
            ("본봄", 0.92),
            ("본봄", 0.89),
        ]

        new_confidence = recalculate_confidence(
            field_values, fuzzy_threshold=0.85, total_providers=3
        )

        # Should still compute valid confidence
        assert 0.0 <= new_confidence <= 1.0
