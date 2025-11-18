"""Unit tests for best-match aggregate confidence calculation.

Tests the aggregate confidence calculation algorithm that computes
a weighted average across all entity fields.
"""

import pytest

from llm_provider.types import ConfidenceScores
from llm_orchestrator.strategies.best_match import calculate_aggregate_confidence


class TestCalculateAggregateConfidence:
    """Test aggregate confidence calculation with weighted averaging."""

    def test_default_weights_calculation(self):
        """Test aggregate confidence with default weights."""
        # Default weights: person=1.5, startup=1.5, partner=1.0, details=0.8, date=0.5
        confidence = ConfidenceScores(
            person=0.9, startup=0.8, partner=0.7, details=0.6, date=0.5
        )

        # Expected: (0.9*1.5 + 0.8*1.5 + 0.7*1.0 + 0.6*0.8 + 0.5*0.5) / (1.5+1.5+1.0+0.8+0.5)
        # = (1.35 + 1.20 + 0.70 + 0.48 + 0.25) / 5.3
        # = 3.98 / 5.3 = 0.7509434
        expected = 3.98 / 5.3

        result = calculate_aggregate_confidence(confidence)

        assert pytest.approx(result, abs=0.001) == expected

    def test_all_perfect_confidence(self):
        """Test aggregate confidence when all scores are 1.0."""
        confidence = ConfidenceScores(
            person=1.0, startup=1.0, partner=1.0, details=1.0, date=1.0
        )

        result = calculate_aggregate_confidence(confidence)

        # Should be 1.0 regardless of weights
        assert result == 1.0

    def test_all_zero_confidence(self):
        """Test aggregate confidence when all scores are 0.0."""
        confidence = ConfidenceScores(
            person=0.0, startup=0.0, partner=0.0, details=0.0, date=0.0
        )

        result = calculate_aggregate_confidence(confidence)

        # Should be 0.0 regardless of weights
        assert result == 0.0

    def test_high_confidence_in_weighted_fields(self):
        """Test that high confidence in heavily weighted fields increases aggregate."""
        # High confidence in person and startup (weight=1.5 each)
        high_weighted = ConfidenceScores(
            person=1.0, startup=1.0, partner=0.5, details=0.5, date=0.5
        )

        # High confidence in details and date (weight=0.8 and 0.5)
        low_weighted = ConfidenceScores(
            person=0.5, startup=0.5, partner=0.5, details=1.0, date=1.0
        )

        high_result = calculate_aggregate_confidence(high_weighted)
        low_result = calculate_aggregate_confidence(low_weighted)

        # High-weighted fields should have higher aggregate confidence
        assert high_result > low_result

    def test_custom_weights(self):
        """Test aggregate confidence with custom weights."""
        confidence = ConfidenceScores(
            person=0.9, startup=0.8, partner=0.7, details=0.6, date=0.5
        )

        custom_weights = {
            "person": 2.0,
            "startup": 2.0,
            "partner": 1.5,
            "details": 1.0,
            "date": 0.1,
        }

        # Expected: (0.9*2.0 + 0.8*2.0 + 0.7*1.5 + 0.6*1.0 + 0.5*0.1) / (2.0+2.0+1.5+1.0+0.1)
        # = (1.8 + 1.6 + 1.05 + 0.6 + 0.05) / 6.6
        # = 5.1 / 6.6 = 0.7727272
        expected = 5.1 / 6.6

        result = calculate_aggregate_confidence(confidence, weights=custom_weights)

        assert pytest.approx(result, abs=0.001) == expected

    def test_equal_weights(self):
        """Test aggregate confidence with equal weights (simple average)."""
        confidence = ConfidenceScores(
            person=0.9, startup=0.8, partner=0.7, details=0.6, date=0.5
        )

        equal_weights = {
            "person": 1.0,
            "startup": 1.0,
            "partner": 1.0,
            "details": 1.0,
            "date": 1.0,
        }

        result = calculate_aggregate_confidence(confidence, weights=equal_weights)

        # Should be simple average: (0.9 + 0.8 + 0.7 + 0.6 + 0.5) / 5 = 0.7
        expected = 0.7

        assert pytest.approx(result, abs=0.001) == expected

    def test_result_within_valid_range(self):
        """Test that aggregate confidence is always between 0.0 and 1.0."""
        # Test various combinations
        test_cases = [
            ConfidenceScores(
                person=0.1, startup=0.2, partner=0.3, details=0.4, date=0.5
            ),
            ConfidenceScores(
                person=0.99, startup=0.98, partner=0.97, details=0.96, date=0.95
            ),
            ConfidenceScores(
                person=0.5, startup=0.5, partner=0.5, details=0.5, date=0.5
            ),
            ConfidenceScores(
                person=0.0, startup=1.0, partner=0.0, details=1.0, date=0.5
            ),
        ]

        for confidence in test_cases:
            result = calculate_aggregate_confidence(confidence)
            assert 0.0 <= result <= 1.0, (
                f"Result {result} out of range for {confidence}"
            )

    def test_weighted_average_formula(self):
        """Test that the weighted average formula is correct."""
        confidence = ConfidenceScores(
            person=0.8, startup=0.7, partner=0.6, details=0.5, date=0.4
        )

        weights = {
            "person": 2.0,
            "startup": 1.5,
            "partner": 1.0,
            "details": 0.5,
            "date": 0.25,
        }

        # Manual calculation
        numerator = 0.8 * 2.0 + 0.7 * 1.5 + 0.6 * 1.0 + 0.5 * 0.5 + 0.4 * 0.25  # 3.8
        denominator = 2.0 + 1.5 + 1.0 + 0.5 + 0.25  # 5.25
        expected = numerator / denominator  # 0.7238095

        result = calculate_aggregate_confidence(confidence, weights=weights)

        assert pytest.approx(result, abs=0.001) == expected

    def test_single_high_confidence_field(self):
        """Test aggregate with one high confidence field and others low."""
        # Only person has high confidence (heavily weighted)
        confidence = ConfidenceScores(
            person=1.0, startup=0.1, partner=0.1, details=0.1, date=0.1
        )

        result = calculate_aggregate_confidence(confidence)

        # Result should be between 0.1 and 1.0, closer to middle due to weighting
        # Expected: (1.0*1.5 + 0.1*1.5 + 0.1*1.0 + 0.1*0.8 + 0.1*0.5) / 5.3
        # = (1.5 + 0.15 + 0.1 + 0.08 + 0.05) / 5.3 = 1.88 / 5.3 = 0.3547
        expected = 1.88 / 5.3

        assert pytest.approx(result, abs=0.001) == expected

    def test_missing_weights_uses_defaults(self):
        """Test that missing weight keys use default values."""
        confidence = ConfidenceScores(
            person=0.9, startup=0.8, partner=0.7, details=0.6, date=0.5
        )

        # Only provide some weights, others should use defaults
        partial_weights = {"person": 2.0, "startup": 2.0}

        result = calculate_aggregate_confidence(confidence, weights=partial_weights)

        # Expected: person and startup use 2.0, others use defaults
        # (0.9*2.0 + 0.8*2.0 + 0.7*1.0 + 0.6*0.8 + 0.5*0.5) / (2.0+2.0+1.0+0.8+0.5)
        expected = (1.8 + 1.6 + 0.7 + 0.48 + 0.25) / 6.3

        assert pytest.approx(result, abs=0.001) == expected

    def test_zero_weight_excludes_field(self):
        """Test that zero weight effectively excludes a field."""
        confidence = ConfidenceScores(
            person=0.9, startup=0.8, partner=0.7, details=0.6, date=0.0
        )

        # Give date zero weight
        weights = {
            "person": 1.0,
            "startup": 1.0,
            "partner": 1.0,
            "details": 1.0,
            "date": 0.0,
        }

        result = calculate_aggregate_confidence(confidence, weights=weights)

        # Should be average of first 4 fields only
        # (0.9 + 0.8 + 0.7 + 0.6) / 4 = 0.75
        expected = 3.0 / 4.0

        assert pytest.approx(result, abs=0.001) == expected

    def test_negative_weights_not_allowed(self):
        """Test that negative weights raise an error."""
        confidence = ConfidenceScores(
            person=0.9, startup=0.8, partner=0.7, details=0.6, date=0.5
        )

        invalid_weights = {
            "person": -1.0,
            "startup": 1.0,
            "partner": 1.0,
            "details": 1.0,
            "date": 1.0,
        }

        with pytest.raises(ValueError, match="Weights must be non-negative"):
            calculate_aggregate_confidence(confidence, weights=invalid_weights)

    def test_all_zero_weights_raises_error(self):
        """Test that all zero weights raise an error."""
        confidence = ConfidenceScores(
            person=0.9, startup=0.8, partner=0.7, details=0.6, date=0.5
        )

        zero_weights = {
            "person": 0.0,
            "startup": 0.0,
            "partner": 0.0,
            "details": 0.0,
            "date": 0.0,
        }

        with pytest.raises(ValueError, match="Sum of weights must be positive"):
            calculate_aggregate_confidence(confidence, weights=zero_weights)
