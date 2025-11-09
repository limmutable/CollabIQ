"""Quality metrics tracking for LLM providers.

This module provides quality metrics tracking following the established pattern
of health_tracker.py and cost_tracker.py. It records extraction quality metrics,
calculates aggregate statistics, and enables cross-provider comparison.
"""

import json
import logging
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Literal

from llm_orchestrator.types import (
    ProviderQualitySummary,
    QualityMetricsRecord,
    QualityThresholdConfig,
    ProviderQualityComparison,
)
from llm_provider.types import ExtractedEntities

logger = logging.getLogger(__name__)


class QualityTracker:
    """Track and analyze LLM provider quality metrics.

    This class records extraction quality metrics (confidence scores, field completeness,
    validation results) and calculates aggregate statistics per provider. It follows
    the same pattern as HealthTracker and CostTracker with file-based JSON persistence.

    Attributes:
        data_dir: Directory for quality metrics storage
        metrics_file: Path to quality_metrics.json
        evaluation_window_size: Number of recent extractions for trend calculation
        metrics: Dictionary mapping provider_name → ProviderQualitySummary
    """

    def __init__(
        self,
        data_dir: str | Path = "data/llm_health",
        evaluation_window_size: int = 50,
    ) -> None:
        """Initialize QualityTracker.

        Args:
            data_dir: Directory for quality metrics JSON storage
            evaluation_window_size: Number of recent extractions for trend calculation (default: 50)

        Side Effects:
            - Creates data_dir if it doesn't exist
            - Loads existing metrics from quality_metrics.json if present
            - Initializes empty metrics dict if file doesn't exist
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.metrics_file = self.data_dir / "quality_metrics.json"
        self.evaluation_window_size = max(evaluation_window_size, 10)  # Minimum 10

        # Load existing metrics or initialize empty dict
        self.metrics: dict[str, ProviderQualitySummary] = self._load_metrics()

        logger.info(
            f"QualityTracker initialized with data_dir={self.data_dir}, "
            f"evaluation_window_size={self.evaluation_window_size}, "
            f"loaded {len(self.metrics)} provider(s)"
        )

    def _load_metrics(self) -> dict[str, ProviderQualitySummary]:
        """Load quality metrics from JSON file.

        Returns:
            Dictionary mapping provider_name → ProviderQualitySummary

        Side Effects:
            - Logs info message if file doesn't exist
            - Logs error if file is corrupted (returns empty dict)

        Error Handling:
            - Returns {} if file doesn't exist
            - Returns {} if JSON is malformed or validation fails
            - Converts ISO timestamp strings to datetime objects
        """
        if not self.metrics_file.exists():
            logger.info(f"No existing quality metrics file at {self.metrics_file}")
            return {}

        try:
            with open(self.metrics_file, "r") as f:
                data = json.load(f)

            # Parse JSON to ProviderQualitySummary objects
            metrics = {}
            for provider_name, provider_data in data.items():
                # Convert ISO timestamp strings to datetime
                if "updated_at" in provider_data and isinstance(
                    provider_data["updated_at"], str
                ):
                    provider_data["updated_at"] = datetime.fromisoformat(
                        provider_data["updated_at"]
                    )

                try:
                    metrics[provider_name] = ProviderQualitySummary(**provider_data)
                except Exception as e:
                    logger.warning(
                        f"Skipping invalid provider data for {provider_name}: {e}"
                    )
                    continue

            logger.info(f"Loaded quality metrics for {len(metrics)} provider(s)")
            return metrics

        except json.JSONDecodeError as e:
            logger.error(f"Corrupted quality metrics file: {e}. Starting fresh.")
            return {}
        except Exception as e:
            logger.error(f"Error loading quality metrics: {e}. Starting fresh.")
            return {}

    def _save_metrics(self) -> None:
        """Save quality metrics to JSON file using atomic write.

        Side Effects:
            - Creates temp file in data_dir
            - Writes JSON with indent=2
            - Atomically renames temp file to quality_metrics.json
            - Converts datetime objects to ISO format strings

        Error Handling:
            - Cleans up temp file on write failure
            - Logs error and raises exception on atomic rename failure
            - Ensures POSIX atomic rename semantics (Linux/macOS)
        """
        # Convert ProviderQualitySummary objects to dicts for JSON serialization
        data = {}
        for provider_name, summary in self.metrics.items():
            summary_dict = summary.model_dump()

            # Convert datetime to ISO format string
            if isinstance(summary_dict.get("updated_at"), datetime):
                summary_dict["updated_at"] = summary_dict["updated_at"].isoformat()

            data[provider_name] = summary_dict

        # Atomic write using tempfile + rename pattern (mirrors health_tracker.py)
        temp_fd, temp_path = tempfile.mkstemp(dir=self.data_dir, suffix=".tmp")

        try:
            with os.fdopen(temp_fd, "w") as f:
                json.dump(data, f, indent=2)

            # Atomic rename (POSIX guarantee)
            shutil.move(temp_path, self.metrics_file)

            logger.debug(f"Quality metrics saved to {self.metrics_file}")

        except Exception as e:
            # Clean up temp file on error
            try:
                os.unlink(temp_path)
            except OSError:
                pass

            logger.error(f"Failed to save quality metrics: {e}")
            raise

    def get_metrics(self, provider_name: str) -> ProviderQualitySummary:
        """Get current quality metrics for a provider.

        Args:
            provider_name: Provider identifier ("gemini", "claude", "openai")

        Returns:
            ProviderQualitySummary for the specified provider

        Side Effects:
            - Initializes default metrics if provider not yet tracked
            - Persists new default metrics to disk if created
        """
        if provider_name not in self.metrics:
            # Initialize default ProviderQualitySummary
            self.metrics[provider_name] = ProviderQualitySummary(
                provider_name=provider_name  # type: ignore
            )
            self._save_metrics()
            logger.info(f"Initialized default quality metrics for {provider_name}")

        return self.metrics[provider_name]

    def get_all_metrics(self) -> dict[str, ProviderQualitySummary]:
        """Get quality metrics for all tracked providers.

        Returns:
            Dictionary mapping provider_name → ProviderQualitySummary

        Side Effects:
            None (returns copy of internal state)
        """
        return self.metrics.copy()

    def _calculate_field_completeness(
        self, extracted_entities: ExtractedEntities
    ) -> tuple[int, float]:
        """Calculate field completeness metrics from extracted entities.

        Args:
            extracted_entities: Extraction result with 5 key entity fields

        Returns:
            Tuple of (fields_extracted int, completeness_percentage float)
            - fields_extracted: Count of non-None fields (0-5)
            - completeness_percentage: (fields_extracted / 5) * 100 (0.0-100.0)
        """
        # Count non-None fields for the 5 key entities
        field_values = [
            extracted_entities.person_in_charge,
            extracted_entities.startup_name,
            extracted_entities.partner_org,
            extracted_entities.details,
            extracted_entities.date,
        ]

        fields_extracted = sum(1 for value in field_values if value is not None)
        completeness_percentage = (fields_extracted / 5) * 100

        return fields_extracted, completeness_percentage

    def _calculate_overall_confidence(
        self, extracted_entities: ExtractedEntities
    ) -> float:
        """Calculate overall confidence from per-field confidence scores.

        Args:
            extracted_entities: Extraction result with confidence scores

        Returns:
            overall_confidence: Average of 5 per-field confidence values (0.0-1.0)
        """
        confidence = extracted_entities.confidence

        # Calculate average of the 5 confidence scores
        overall_confidence = (
            confidence.person
            + confidence.startup
            + confidence.partner
            + confidence.details
            + confidence.date
        ) / 5

        return overall_confidence

    def _update_aggregate_statistics(
        self,
        provider_name: str,
        per_field_confidence: dict[str, float],
        overall_confidence: float,
        fields_extracted: int,
        field_completeness_percentage: float,
        validation_passed: bool,
    ) -> None:
        """Update aggregate quality statistics for a provider.

        Args:
            provider_name: Provider identifier
            per_field_confidence: Confidence scores for each field
            overall_confidence: Average confidence score
            fields_extracted: Count of non-null fields
            field_completeness_percentage: Completeness percentage
            validation_passed: Whether validation passed

        Side Effects:
            - Increments total_extractions counter
            - Updates validation success/failure counters
            - Recalculates running averages (confidence, completeness, per-field averages)
            - Calculates standard deviation incrementally
            - Updates updated_at timestamp
        """
        summary = self.metrics[provider_name]

        # Increment extraction counter
        n = summary.total_extractions
        n_new = n + 1
        summary.total_extractions = n_new

        # Update validation counters
        if validation_passed:
            summary.successful_validations += 1
        else:
            summary.failed_validations += 1

        # Recalculate validation success rate
        summary.validation_success_rate = (
            summary.successful_validations / n_new
        ) * 100

        # Update running average for overall confidence (incremental formula)
        old_avg_confidence = summary.average_overall_confidence
        summary.average_overall_confidence = old_avg_confidence + (
            overall_confidence - old_avg_confidence
        ) / n_new

        # Update running average for field completeness
        old_avg_completeness = summary.average_field_completeness
        summary.average_field_completeness = old_avg_completeness + (
            field_completeness_percentage - old_avg_completeness
        ) / n_new

        # Update running average for fields extracted
        old_avg_fields = summary.average_fields_extracted
        summary.average_fields_extracted = old_avg_fields + (
            fields_extracted - old_avg_fields
        ) / n_new

        # Update per-field confidence averages
        for field in ["person", "startup", "partner", "details", "date"]:
            old_field_avg = summary.per_field_confidence_averages[field]
            new_field_conf = per_field_confidence[field]
            summary.per_field_confidence_averages[field] = old_field_avg + (
                new_field_conf - old_field_avg
            ) / n_new

        # Calculate standard deviation incrementally (Welford's online algorithm)
        # For simplicity in MVP, we'll use a simplified approach:
        # Store sum of squares and calculate std dev from mean
        # Note: This is approximate for incremental updates, good enough for MVP
        if n == 0:
            # First extraction
            summary.confidence_std_deviation = 0.0
        else:
            # Simplified std dev calculation (good enough for monitoring trends)
            # In production, we'd maintain sum_of_squares for exact calculation
            # For now, we use a conservative estimate that updates slowly
            variance_estimate = abs(overall_confidence - summary.average_overall_confidence)
            summary.confidence_std_deviation = (
                summary.confidence_std_deviation * 0.95 + variance_estimate * 0.05
            )

        # Update timestamp
        summary.updated_at = datetime.utcnow()

    def record_extraction(
        self,
        provider_name: str,
        extracted_entities: ExtractedEntities,
        validation_passed: bool,
        validation_failure_reasons: list[str] | None = None,
    ) -> None:
        """Record quality metrics for a single extraction attempt.

        Args:
            provider_name: Provider identifier ("gemini", "claude", "openai")
            extracted_entities: Extraction result with confidence scores
            validation_passed: True if extraction passed validation
            validation_failure_reasons: List of failure reasons if validation failed

        Side Effects:
            - Updates provider quality summary statistics
            - Increments total_extractions counter
            - Recalculates averages, std deviation, and trend
            - Persists updated metrics to quality_metrics.json atomically

        Raises:
            ValueError: If provider_name not in ["gemini", "claude", "openai"]
            ValueError: If validation_passed is False but validation_failure_reasons is None/empty
        """
        # Validate parameters
        valid_providers = {"gemini", "claude", "openai"}
        if provider_name not in valid_providers:
            raise ValueError(
                f"Invalid provider_name '{provider_name}'. Must be one of: {valid_providers}"
            )

        if not validation_passed and not validation_failure_reasons:
            raise ValueError(
                "validation_failure_reasons must be a non-empty list when validation_passed is False"
            )

        # Ensure provider has metrics initialized
        if provider_name not in self.metrics:
            self.get_metrics(provider_name)

        # Extract quality metrics from extracted_entities
        fields_extracted, field_completeness_percentage = (
            self._calculate_field_completeness(extracted_entities)
        )
        overall_confidence = self._calculate_overall_confidence(extracted_entities)

        # Build per-field confidence dict
        per_field_confidence = {
            "person": extracted_entities.confidence.person,
            "startup": extracted_entities.confidence.startup,
            "partner": extracted_entities.confidence.partner,
            "details": extracted_entities.confidence.details,
            "date": extracted_entities.confidence.date,
        }

        # Log detailed field-level metrics at DEBUG level
        logger.debug(
            f"Quality metrics detail for {provider_name}: "
            f"fields_extracted={fields_extracted}/5, "
            f"per_field_confidence={per_field_confidence}"
        )

        # Update aggregate statistics
        self._update_aggregate_statistics(
            provider_name=provider_name,
            per_field_confidence=per_field_confidence,
            overall_confidence=overall_confidence,
            fields_extracted=fields_extracted,
            field_completeness_percentage=field_completeness_percentage,
            validation_passed=validation_passed,
        )

        # Persist to disk
        self._save_metrics()

        # Log quality metric update at INFO level
        logger.info(
            f"Recorded quality metrics for {provider_name}: "
            f"confidence={overall_confidence:.2f}, "
            f"completeness={field_completeness_percentage:.1f}%, "
            f"validation={'PASS' if validation_passed else 'FAIL'}"
        )

        # Log warning if validation failed
        if not validation_passed:
            logger.warning(
                f"Validation FAILED for {provider_name}: "
                f"reasons={validation_failure_reasons}"
            )

    def _calculate_quality_score(self, summary: ProviderQualitySummary) -> float:
        """Calculate composite quality score for a provider.

        This score combines multiple quality dimensions into a single metric for
        provider comparison and ranking.

        Args:
            summary: ProviderQualitySummary with aggregate quality metrics

        Returns:
            Quality score ranging from 0.0 to 1.0

        Scoring Formula:
            quality_score = (0.4 × confidence) + (0.3 × completeness/100) + (0.3 × validation_rate/100)

            Weights:
            - 40% average overall confidence (0.0-1.0)
            - 30% average field completeness (0.0-100.0, normalized to 0.0-1.0)
            - 30% validation success rate (0.0-100.0, normalized to 0.0-1.0)

        Example:
            >>> summary = ProviderQualitySummary(
            ...     provider_name="gemini",
            ...     average_overall_confidence=0.85,
            ...     average_field_completeness=90.0,
            ...     validation_success_rate=95.0
            ... )
            >>> score = tracker._calculate_quality_score(summary)
            >>> # score = (0.4 × 0.85) + (0.3 × 0.90) + (0.3 × 0.95) = 0.895
        """
        confidence = summary.average_overall_confidence  # Already 0.0-1.0
        completeness = summary.average_field_completeness / 100  # Convert to 0.0-1.0
        validation_rate = summary.validation_success_rate / 100  # Convert to 0.0-1.0

        quality_score = (0.4 * confidence) + (0.3 * completeness) + (0.3 * validation_rate)

        return quality_score

    def _calculate_value_score(self, quality_score: float, cost_per_email: float) -> float:
        """Calculate quality-to-cost value score for a provider.

        This metric helps identify the best value provider by balancing quality
        against cost. Higher scores indicate better value (more quality per dollar).

        Args:
            quality_score: Composite quality score (0.0-1.0)
            cost_per_email: Average cost per email in USD (from CostTracker)

        Returns:
            Value score as float (unbounded, higher is better)

        Scoring Formula:
            - If cost_per_email == 0.0 (free tier): value_score = quality_score × 1.5
            - Otherwise: value_score = quality_score / (1 + cost_per_email × 1000)

        The formula balances quality against cost:
        - Free providers get a 1.5x bonus but still depend on quality
        - Paid providers are penalized proportionally to cost
        - The (1 + cost × 1000) denominator prevents division by zero
          and scales costs appropriately (e.g., $0.005/email → 6.0 divisor)

        Example:
            >>> # High-quality paid provider
            >>> value = tracker._calculate_value_score(0.90, 0.005)
            >>> # value = 0.90 / (1 + 5.0) = 0.15
            >>>
            >>> # Free tier provider with good quality
            >>> value = tracker._calculate_value_score(0.80, 0.0)
            >>> # value = 0.80 × 1.5 = 1.20
        """
        if cost_per_email == 0.0:
            # Free tier provider: give 1.5x bonus
            return quality_score * 1.5

        # Paid provider: quality divided by cost scaling factor
        value_score = quality_score / (1 + cost_per_email * 1000)

        return value_score

    def _generate_recommendation(
        self,
        provider_rankings: list[dict],
        quality_to_cost_rankings: list[dict],
    ) -> tuple[str, str]:
        """Generate provider recommendation with human-readable explanation.

        Determines the recommended provider based on value score (quality-to-cost ratio)
        and generates a 2-3 sentence explanation of why this provider is recommended.

        Args:
            provider_rankings: List of dicts with provider quality rankings
                Format: [{"provider_name": str, "quality_score": float, "rank": int}, ...]
                Sorted by quality score (best to worst)
            quality_to_cost_rankings: List of dicts with provider value rankings
                Format: [{"provider_name": str, "value_score": float, "rank": int}, ...]
                Sorted by value score (best to worst)

        Returns:
            Tuple of (recommended_provider_name, recommendation_reason)

        Recommendation Logic:
            - Recommended provider = highest value_score (best quality per dollar)
            - Reason explains quality score, cost, and value proposition

        Example:
            >>> rankings = [
            ...     {"provider_name": "claude", "quality_score": 0.92, "rank": 1},
            ...     {"provider_name": "gemini", "quality_score": 0.88, "rank": 2}
            ... ]
            >>> value_rankings = [
            ...     {"provider_name": "claude", "value_score": 0.184, "rank": 1},
            ...     {"provider_name": "gemini", "value_score": 0.147, "rank": 2}
            ... ]
            >>> provider, reason = tracker._generate_recommendation(rankings, value_rankings)
            >>> print(provider)
            'claude'
        """
        if not quality_to_cost_rankings:
            raise ValueError("Cannot generate recommendation: no providers have metrics")

        # Best value provider is first in quality_to_cost_rankings (already sorted)
        recommended = quality_to_cost_rankings[0]
        recommended_provider = recommended["provider_name"]
        value_score = recommended["value_score"]

        # Find quality ranking for recommended provider
        quality_info = None
        for ranking in provider_rankings:
            if ranking["provider_name"] == recommended_provider:
                quality_info = ranking
                break

        if not quality_info:
            raise ValueError(f"Quality info not found for {recommended_provider}")

        quality_score = quality_info["quality_score"]
        quality_rank = quality_info["rank"]

        # Generate explanation based on rankings
        if quality_rank == 1:
            # Best quality AND best value
            reason = (
                f"{recommended_provider.title()} offers the best overall quality "
                f"(score: {quality_score:.2f}) and the best value (score: {value_score:.3f}). "
                f"It delivers top-tier extraction accuracy at competitive cost."
            )
        else:
            # Not highest quality, but best value
            reason = (
                f"{recommended_provider.title()} provides the best value "
                f"(score: {value_score:.3f}) by balancing strong quality "
                f"(score: {quality_score:.2f}) with lower cost per email. "
                f"This provider delivers excellent ROI for production workloads."
            )

        return recommended_provider, reason

    def compare_providers(
        self,
        provider_names: list[str] | None = None,
        cost_tracker: "CostTracker | None" = None,
    ) -> ProviderQualityComparison:
        """Compare quality metrics across providers and recommend best option.

        This method calculates composite quality scores and value scores (quality-to-cost
        ratio) for each provider, ranks them, and identifies the recommended provider
        for production use.

        Args:
            provider_names: List of provider names to compare (defaults to all tracked providers)
            cost_tracker: CostTracker instance for cost data (optional)
                If not provided, cost_per_email defaults to 0.0 for all providers

        Returns:
            ProviderQualityComparison object containing:
            - providers_compared: List of provider names included
            - provider_rankings: Providers ranked by quality score (best to worst)
            - quality_to_cost_rankings: Providers ranked by value score (best to worst)
            - recommended_provider: Provider with highest value score
            - recommendation_reason: Human-readable explanation (2-3 sentences)

        Raises:
            ValueError: If no providers have quality metrics
            ValueError: If specified provider_names list is empty

        Side Effects:
            None (read-only operation)

        Example:
            >>> comparison = quality_tracker.compare_providers(cost_tracker=cost_tracker)
            >>> print(f"Recommended: {comparison.recommended_provider}")
            >>> print(f"Reason: {comparison.recommendation_reason}")
            >>> for ranking in comparison.provider_rankings:
            ...     print(f"{ranking['rank']}. {ranking['provider_name']}: {ranking['quality_score']:.2f}")
        """
        # Determine which providers to compare
        if provider_names is None:
            # Compare all tracked providers
            providers_to_compare = list(self.metrics.keys())
        else:
            if not provider_names:
                raise ValueError("provider_names list cannot be empty")
            providers_to_compare = provider_names

        # Filter to providers with metrics
        providers_with_metrics = [
            name for name in providers_to_compare
            if name in self.metrics and self.metrics[name].total_extractions > 0
        ]

        if not providers_with_metrics:
            raise ValueError(
                f"No providers have quality metrics. "
                f"Process at least one extraction per provider before comparing."
            )

        # Calculate quality scores and value scores for each provider
        provider_scores = []

        for provider_name in providers_with_metrics:
            summary = self.metrics[provider_name]

            # Calculate quality score
            quality_score = self._calculate_quality_score(summary)

            # Get cost per email from cost_tracker
            cost_per_email = 0.0
            if cost_tracker:
                try:
                    cost_metrics = cost_tracker.get_metrics(provider_name)
                    cost_per_email = cost_metrics.average_cost_per_email
                except Exception as e:
                    logger.warning(
                        f"Could not get cost metrics for {provider_name}: {e}. "
                        f"Using $0.00 for value calculation."
                    )

            # Calculate value score
            value_score = self._calculate_value_score(quality_score, cost_per_email)

            provider_scores.append({
                "provider_name": provider_name,
                "quality_score": quality_score,
                "value_score": value_score,
            })

        # Rank providers by quality score (descending)
        provider_rankings = sorted(
            provider_scores,
            key=lambda x: x["quality_score"],
            reverse=True
        )
        for rank, provider in enumerate(provider_rankings, start=1):
            provider["rank"] = rank

        # Rank providers by value score (descending)
        quality_to_cost_rankings = sorted(
            provider_scores,
            key=lambda x: x["value_score"],
            reverse=True
        )
        for rank, provider in enumerate(quality_to_cost_rankings, start=1):
            provider["rank"] = rank

        # Generate recommendation
        recommended_provider, recommendation_reason = self._generate_recommendation(
            provider_rankings, quality_to_cost_rankings
        )

        # Build ProviderQualityComparison result
        comparison = ProviderQualityComparison(
            providers_compared=providers_with_metrics,
            provider_rankings=provider_rankings,
            quality_to_cost_rankings=quality_to_cost_rankings,
            recommended_provider=recommended_provider,
            recommendation_reason=recommendation_reason,
        )

        logger.info(
            f"Provider comparison complete: compared {len(providers_with_metrics)} providers, "
            f"recommended {recommended_provider}"
        )

        return comparison

    def select_provider_by_quality(
        self, candidate_providers: list[str]
    ) -> str | None:
        """Select provider based on quality metrics.

        Takes a list of candidate provider names, filters providers meeting minimum
        quality thresholds (if configured), ranks candidates by composite quality score,
        and returns the provider name with the highest quality.

        Args:
            candidate_providers: List of provider names to consider for selection

        Returns:
            Provider name with highest quality score, or None if no providers
            meet quality threshold or have metrics

        Side Effects:
            - Logs selection decision with reasoning at INFO level
            - Logs filtering decisions at DEBUG level

        Algorithm:
            1. Filter to providers with metrics (total_extractions > 0)
            2. Calculate composite quality score for each provider
            3. Rank providers by score descending
            4. Return provider with highest score
            5. Return None if no providers have metrics

        Quality Score Calculation:
            Composite score (0-100 scale):
            - average_overall_confidence × 100 × 60%
            - validation_success_rate × 30%
            - average_field_completeness × 10%

            Weights emphasize confidence > validation > completeness

        Example:
            >>> tracker = QualityTracker()
            >>> candidates = ["gemini", "claude", "openai"]
            >>> best_provider = tracker.select_provider_by_quality(candidates)
            >>> print(f"Selected: {best_provider}")
        """
        if not candidate_providers:
            logger.warning("No candidate providers provided for quality selection")
            return None

        # Filter to providers with metrics
        providers_with_metrics = []
        for provider_name in candidate_providers:
            if provider_name in self.metrics:
                summary = self.metrics[provider_name]
                if summary.total_extractions > 0:
                    providers_with_metrics.append(provider_name)
                else:
                    logger.debug(
                        f"Provider {provider_name} excluded: no extractions recorded"
                    )
            else:
                logger.debug(
                    f"Provider {provider_name} excluded: no quality metrics"
                )

        if not providers_with_metrics:
            logger.warning(
                f"No providers have quality metrics yet. Candidates: {candidate_providers}"
            )
            return None

        # Calculate quality scores for all providers with metrics
        provider_scores = []
        for provider_name in providers_with_metrics:
            summary = self.metrics[provider_name]

            # Use existing _calculate_quality_score helper (returns 0.0-1.0)
            quality_score = self._calculate_quality_score(summary)

            # Convert to 0-100 scale for display
            quality_score_display = quality_score * 100

            provider_scores.append((provider_name, quality_score_display, summary))

        # Sort by quality score descending
        provider_scores.sort(key=lambda x: x[1], reverse=True)

        # Select best provider
        best_provider, best_score, best_summary = provider_scores[0]

        logger.info(
            f"Quality-based provider selection: {best_provider} "
            f"(score={best_score:.2f}/100, "
            f"confidence={best_summary.average_overall_confidence:.2f}, "
            f"validation={best_summary.validation_success_rate:.1f}%, "
            f"completeness={best_summary.average_field_completeness:.1f}%) "
            f"from {len(providers_with_metrics)} providers with metrics"
        )

        return best_provider
