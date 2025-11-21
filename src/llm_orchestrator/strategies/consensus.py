"""Consensus orchestration strategy.

This module implements the consensus strategy which queries multiple providers
in parallel and merges results using fuzzy matching and weighted voting to
improve extraction accuracy.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Optional

from llm_adapters.health_tracker import HealthTracker
from llm_orchestrator.exceptions import AllProvidersFailedError
from llm_provider.base import LLMProvider
from llm_provider.exceptions import LLMAPIError
from llm_provider.types import ConfidenceScores, ExtractedEntities

logger = logging.getLogger(__name__)


def jaro_winkler_similarity(s1: str | None, s2: str | None) -> float:
    """Calculate Jaro-Winkler similarity between two strings.

    Args:
        s1: First string (or None)
        s2: Second string (or None)

    Returns:
        Similarity score between 0.0 and 1.0
        - 1.0 for identical strings
        - 0.0 for completely different strings
        - None values: return 1.0 if both None, 0.0 if only one is None

    Algorithm:
        Jaro-Winkler similarity gives higher scores to strings with common prefixes.
        It's particularly effective for names and short strings.

    Example:
        >>> jaro_winkler_similarity("본봄", "본봄")
        1.0
        >>> jaro_winkler_similarity("신세계인터내셔널", "신세계")
        0.87
    """
    # Handle None values
    if s1 is None and s2 is None:
        return 1.0
    if s1 is None or s2 is None:
        return 0.0

    # Handle empty strings
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0

    # If identical, return 1.0
    if s1 == s2:
        return 1.0

    # Calculate Jaro similarity first
    len1, len2 = len(s1), len(s2)

    # Maximum allowed distance for matching characters
    match_distance = max(len1, len2) // 2 - 1
    if match_distance < 0:
        match_distance = 0

    # Track which characters match
    s1_matches = [False] * len1
    s2_matches = [False] * len2

    matches = 0
    transpositions = 0

    # Find matching characters
    for i in range(len1):
        start = max(0, i - match_distance)
        end = min(i + match_distance + 1, len2)

        for j in range(start, end):
            if s2_matches[j] or s1[i] != s2[j]:
                continue
            s1_matches[i] = True
            s2_matches[j] = True
            matches += 1
            break

    if matches == 0:
        return 0.0

    # Count transpositions
    k = 0
    for i in range(len1):
        if not s1_matches[i]:
            continue
        while not s2_matches[k]:
            k += 1
        if s1[i] != s2[k]:
            transpositions += 1
        k += 1

    # Calculate Jaro similarity
    jaro = (
        matches / len1 + matches / len2 + (matches - transpositions / 2) / matches
    ) / 3.0

    # Calculate common prefix length (up to 4 characters)
    prefix_len = 0
    for i in range(min(len1, len2, 4)):
        if s1[i] == s2[i]:
            prefix_len += 1
        else:
            break

    # Calculate Jaro-Winkler similarity
    # Winkler modification: bonus for common prefix (p=0.1 is standard)
    p = 0.1
    jaro_winkler = jaro + prefix_len * p * (1 - jaro)

    return jaro_winkler


def fuzzy_match(
    value1: str | None, value2: str | None, threshold: float = 0.85
) -> bool:
    """Check if two values match using fuzzy string matching.

    Args:
        value1: First value to compare
        value2: Second value to compare
        threshold: Minimum Jaro-Winkler similarity required for match (default: 0.85)

    Returns:
        True if values match (similarity >= threshold), False otherwise

    Example:
        >>> fuzzy_match("신세계인터내셔널", "신세계", threshold=0.85)
        True
        >>> fuzzy_match("본봄", "브레이크앤컴퍼니", threshold=0.85)
        False
    """
    similarity = jaro_winkler_similarity(value1, value2)
    return similarity >= threshold


def weighted_vote(
    candidates: list[tuple[Any, float, float]],
    fuzzy_threshold: float = 0.85,
    abstention_threshold: float = 0.25,
) -> Any:
    """Perform weighted voting to select the best value from multiple candidates.

    Args:
        candidates: List of (value, confidence, success_rate) tuples
                   - value: The candidate value
                   - confidence: Confidence score for this value (0.0-1.0)
                   - success_rate: Provider's historical success rate (0.0-1.0)
        fuzzy_threshold: Jaro-Winkler threshold for grouping similar values
        abstention_threshold: If all candidates have confidence below this, return None

    Returns:
        Winning value based on weighted voting, or None if abstention

    Voting Algorithm:
        1. Group similar values using fuzzy matching
        2. Calculate weight for each candidate = confidence * success_rate
        3. Sum weights for each group (fuzzy-matched values)
        4. Select group with highest total weight
        5. Within winning group, select value with highest individual weight
        6. Tie-breaking: majority → highest weight → first encountered

    Example:
        >>> candidates = [
        ...     ("본봄", 0.92, 0.90),
        ...     ("본봄", 0.93, 0.85),
        ...     ("본봄컴퍼니", 0.89, 0.95)  # Similar, will be grouped
        ... ]
        >>> weighted_vote(candidates)
        "본봄"
    """
    if not candidates:
        return None

    # Check for abstention (all candidates have very low confidence)
    if all(conf < abstention_threshold for _, conf, _ in candidates):
        logger.info(
            f"Abstaining from vote: all candidates below threshold {abstention_threshold}"
        )
        return None

    # Group similar values using fuzzy matching
    # groups: {representative_value: [(value, weight, count), ...]}
    groups: dict[Any, list[tuple[Any, float, int]]] = {}

    for value, confidence, success_rate in candidates:
        # Calculate weight for this candidate
        weight = confidence * success_rate

        # Find matching group
        matched_group = None
        for group_key in groups.keys():
            if isinstance(value, str) and isinstance(group_key, str):
                if fuzzy_match(value, group_key, threshold=fuzzy_threshold):
                    matched_group = group_key
                    break
            elif value == group_key:
                matched_group = group_key
                break

        # Add to existing group or create new group
        if matched_group is not None:
            groups[matched_group].append((value, weight, 1))
        else:
            groups[value] = [(value, weight, 1)]

    # Calculate total weight for each group
    group_scores: list[tuple[Any, float, int, float]] = []
    for group_key, members in groups.items():
        total_weight = sum(w for _, w, _ in members)
        count = len(members)
        # Find highest individual weight in group
        max_individual_weight = max(w for _, w, _ in members)
        group_scores.append((group_key, total_weight, count, max_individual_weight))

    # Sort by: total weight (desc), count (desc), max individual weight (desc)
    group_scores.sort(key=lambda x: (x[1], x[2], x[3]), reverse=True)

    # Winner is the group with highest score
    winning_group_key = group_scores[0][0]

    # Within winning group, select value with highest individual weight
    winning_group_members = groups[winning_group_key]
    winning_group_members.sort(key=lambda x: x[1], reverse=True)

    winner_value = winning_group_members[0][0]

    logger.debug(
        f"Weighted vote: {len(candidates)} candidates → {len(groups)} groups, "
        f"winner='{winner_value}' (weight={winning_group_members[0][1]:.3f})"
    )

    return winner_value


def recalculate_confidence(
    field_values: list[tuple[Any, float]],
    fuzzy_threshold: float = 0.85,
    total_providers: int = 3,
) -> float:
    """Recalculate confidence score based on provider agreement.

    Args:
        field_values: List of (value, original_confidence) tuples
        fuzzy_threshold: Threshold for fuzzy matching
        total_providers: Total number of providers queried

    Returns:
        New confidence score (0.0-1.0) based on agreement and original confidence

    Algorithm:
        1. Calculate agreement rate (% of providers that agree on winning value)
        2. Calculate average original confidence for agreeing providers
        3. Boost confidence if agreement is high, reduce if low
        4. Formula: base_confidence * agreement_factor
           - agreement_factor = 0.8 + (agreement_rate * 0.4)
           - Range: [0.8, 1.2] → [80% to 120% of base confidence]

    Example:
        >>> field_values = [("본봄", 0.92), ("본봄", 0.93), ("본봄", 0.89)]
        >>> recalculate_confidence(field_values, total_providers=3)
        0.98  # High agreement boosts confidence
    """
    if not field_values:
        return 0.0

    # Find winning value using simple majority
    value_groups: dict[Any, list[float]] = {}

    for value, conf in field_values:
        matched = False
        for group_key in value_groups.keys():
            if isinstance(value, str) and isinstance(group_key, str):
                if fuzzy_match(value, group_key, threshold=fuzzy_threshold):
                    value_groups[group_key].append(conf)
                    matched = True
                    break
            elif value == group_key:
                value_groups[group_key].append(conf)
                matched = True
                break

        if not matched:
            value_groups[value] = [conf]

    # Find group with most votes
    winning_group = max(value_groups.items(), key=lambda x: len(x[1]))
    winning_confidences = winning_group[1]

    # Calculate agreement rate
    agreement_count = len(winning_confidences)
    agreement_rate = agreement_count / total_providers

    # Calculate base confidence (average of agreeing providers)
    base_confidence = sum(winning_confidences) / len(winning_confidences)

    # Apply agreement factor
    # High agreement (3/3 = 1.0) → factor = 1.2 → boost confidence
    # Medium agreement (2/3 = 0.67) → factor = 1.07 → slight boost
    # Low agreement (1/3 = 0.33) → factor = 0.93 → reduce confidence
    agreement_factor = 0.8 + (agreement_rate * 0.4)

    new_confidence = base_confidence * agreement_factor

    # Clamp to valid range [0.0, 1.0]
    new_confidence = max(0.0, min(1.0, new_confidence))

    logger.debug(
        f"Confidence recalc: {agreement_count}/{total_providers} agree, "
        f"base={base_confidence:.3f}, factor={agreement_factor:.3f}, "
        f"new={new_confidence:.3f}"
    )

    return new_confidence


class ConsensusStrategy:
    """Consensus orchestration strategy.

    Queries multiple providers in parallel and merges results using fuzzy matching
    and weighted voting. Improves accuracy by leveraging agreement across providers.

    Attributes:
        provider_names: List of provider names to query
        fuzzy_threshold: Jaro-Winkler threshold for fuzzy matching (default: 0.85)
        min_agreement: Minimum number of provider responses required (default: 2)
        abstention_threshold: Min confidence to avoid abstention (default: 0.25)

    Example:
        >>> strategy = ConsensusStrategy(
        ...     provider_names=["gemini", "claude", "openai"],
        ...     fuzzy_threshold=0.85,
        ...     min_agreement=2
        ... )
        >>> providers = {"gemini": gemini_adapter, "claude": claude_adapter, ...}
        >>> tracker = HealthTracker()
        >>> result, provider_used = await strategy.execute(providers, "email text", tracker)
    """

    def __init__(
        self,
        provider_names: list[str],
        fuzzy_threshold: float = 0.85,
        min_agreement: int = 2,
        abstention_threshold: float = 0.25,
    ):
        """Initialize consensus strategy.

        Args:
            provider_names: List of provider names to query (e.g., ["gemini", "claude"])
            fuzzy_threshold: Jaro-Winkler threshold for fuzzy matching (default: 0.85)
            min_agreement: Minimum provider responses required (default: 2)
            abstention_threshold: Min confidence to avoid abstention (default: 0.25)
        """
        self.provider_names = provider_names
        self.fuzzy_threshold = fuzzy_threshold
        self.min_agreement = min_agreement
        self.abstention_threshold = abstention_threshold

        logger.info(
            f"Initialized ConsensusStrategy with providers: {provider_names}, "
            f"fuzzy_threshold={fuzzy_threshold}, min_agreement={min_agreement}"
        )

    async def execute(
        self,
        providers: dict[str, LLMProvider],
        email_text: str,
        health_tracker: HealthTracker,
        company_context: Optional[str] = None,
        email_id: Optional[str] = None,
    ) -> tuple[ExtractedEntities, str]:
        """Execute consensus strategy across providers.

        Queries all healthy providers in parallel and merges results.

        Args:
            providers: Dictionary mapping provider_name → LLMProvider instance
            email_text: Email text to extract entities from
            health_tracker: HealthTracker for monitoring provider health
            company_context: Optional company context for matching
            email_id: Optional email ID

        Returns:
            Tuple of (merged ExtractedEntities, "consensus")

        Raises:
            AllProvidersFailedError: If insufficient providers respond (< min_agreement)

        Contract:
            - MUST query providers in parallel using asyncio.gather()
            - MUST skip unhealthy providers
            - MUST require at least min_agreement responses
            - MUST merge results using fuzzy matching and weighted voting
            - MUST recalculate confidence scores based on agreement
            - MUST record successes/failures in health tracker
        """
        # Filter to healthy providers
        available_providers = []
        for provider_name in self.provider_names:
            if provider_name not in providers:
                logger.warning(f"Provider '{provider_name}' not configured, skipping")
                continue

            if not health_tracker.is_healthy(provider_name):
                logger.info(
                    f"Skipping unhealthy provider: {provider_name} "
                    f"(circuit_breaker={health_tracker.get_metrics(provider_name).circuit_breaker_state})"
                )
                continue

            available_providers.append(provider_name)

        if len(available_providers) < self.min_agreement:
            error_msg = (
                f"Insufficient healthy providers: {len(available_providers)} available, "
                f"{self.min_agreement} required"
            )
            logger.error(error_msg)
            raise AllProvidersFailedError(error_msg)

        # Query all providers in parallel
        logger.info(
            f"Querying {len(available_providers)} providers in parallel: {available_providers}"
        )

        tasks = []
        for provider_name in available_providers:
            task = self._query_provider(
                provider_name=provider_name,
                provider=providers[provider_name],
                email_text=email_text,
                health_tracker=health_tracker,
                company_context=company_context,
                email_id=email_id,
            )
            tasks.append(task)

        # Gather results
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Separate successful results from failures
        successful_results: list[tuple[str, ExtractedEntities]] = []
        for provider_name, result in zip(available_providers, results):
            if isinstance(result, Exception):
                logger.warning(
                    f"Provider {provider_name} failed: {type(result).__name__}: {str(result)[:100]}"
                )
                # Failure already recorded in _query_provider
            elif result is not None:
                successful_results.append((provider_name, result))

        # Validate minimum responses
        if len(successful_results) < self.min_agreement:
            error_msg = (
                f"Insufficient provider responses: {len(successful_results)} succeeded, "
                f"{self.min_agreement} required. "
                f"Attempted: {available_providers}"
            )
            logger.error(error_msg)
            raise AllProvidersFailedError(error_msg)

        logger.info(
            f"Received {len(successful_results)} successful responses, merging results"
        )

        # Merge results using consensus algorithm
        merged_entities = self._merge_results(
            successful_results, health_tracker, email_id or "unknown"
        )

        return merged_entities, "consensus"

    async def _query_provider(
        self,
        provider_name: str,
        provider: LLMProvider,
        email_text: str,
        health_tracker: HealthTracker,
        company_context: Optional[str] = None,
        email_id: Optional[str] = None,
    ) -> Optional[ExtractedEntities]:
        """Query a single provider and record result in health tracker.

        Args:
            provider_name: Provider identifier
            provider: LLMProvider instance
            email_text: Email text to extract from
            health_tracker: Health tracker instance
            company_context: Optional company context
            email_id: Optional email ID

        Returns:
            ExtractedEntities on success, None on failure
        """
        import time

        start_time = time.time()

        try:
            # Call provider's extract_entities (now an async method)
            entities = await provider.extract_entities(
                email_text=email_text,
                company_context=company_context,
                email_id=email_id,
            )

            # Calculate response time
            response_time_ms = (time.time() - start_time) * 1000

            # Record success
            health_tracker.record_success(provider_name, response_time_ms)

            logger.info(
                f"Provider {provider_name} succeeded "
                f"(response_time={response_time_ms:.1f}ms)"
            )

            return entities

        except LLMAPIError as e:
            # Record failure
            health_tracker.record_failure(provider_name, str(e))
            logger.warning(f"Provider {provider_name} failed: {type(e).__name__}")
            return None

        except Exception as e:
            # Unexpected error - still record as failure
            health_tracker.record_failure(provider_name, f"Unexpected: {str(e)}")
            logger.error(
                f"Unexpected error from provider {provider_name}: {e}", exc_info=True
            )
            return None

    def _merge_results(
        self,
        results: list[tuple[str, ExtractedEntities]],
        health_tracker: HealthTracker,
        email_id: str,
    ) -> ExtractedEntities:
        """Merge multiple extraction results using fuzzy matching and weighted voting.

        Args:
            results: List of (provider_name, ExtractedEntities) tuples
            health_tracker: Health tracker for provider success rates
            email_id: Email ID for the merged result

        Returns:
            Merged ExtractedEntities with recalculated confidence scores
        """
        if not results:
            raise AllProvidersFailedError("No results to merge")

        logger.info(f"Merging {len(results)} extraction results")

        # Collect candidates for each field
        person_candidates = []
        startup_candidates = []
        partner_candidates = []
        details_candidates = []
        date_candidates = []

        for provider_name, entities in results:
            # Get provider's historical success rate
            metrics = health_tracker.get_metrics(provider_name)
            success_rate = metrics.success_rate if metrics.success_count > 0 else 0.5

            # Add candidates with (value, confidence, success_rate)
            person_candidates.append(
                (entities.person_in_charge, entities.confidence.person, success_rate)
            )
            startup_candidates.append(
                (entities.startup_name, entities.confidence.startup, success_rate)
            )
            partner_candidates.append(
                (entities.partner_org, entities.confidence.partner, success_rate)
            )
            details_candidates.append(
                (entities.details, entities.confidence.details, success_rate)
            )
            date_candidates.append(
                (entities.date, entities.confidence.date, success_rate)
            )

        # Perform weighted voting for each field
        person_value = weighted_vote(
            person_candidates, self.fuzzy_threshold, self.abstention_threshold
        )
        startup_value = weighted_vote(
            startup_candidates, self.fuzzy_threshold, self.abstention_threshold
        )
        partner_value = weighted_vote(
            partner_candidates, self.fuzzy_threshold, self.abstention_threshold
        )
        details_value = weighted_vote(
            details_candidates, self.fuzzy_threshold, self.abstention_threshold
        )
        date_value = weighted_vote(
            date_candidates, self.fuzzy_threshold, self.abstention_threshold
        )

        # Recalculate confidence scores based on agreement
        person_conf = recalculate_confidence(
            [(v, c) for v, c, _ in person_candidates],
            self.fuzzy_threshold,
            len(results),
        )
        startup_conf = recalculate_confidence(
            [(v, c) for v, c, _ in startup_candidates],
            self.fuzzy_threshold,
            len(results),
        )
        partner_conf = recalculate_confidence(
            [(v, c) for v, c, _ in partner_candidates],
            self.fuzzy_threshold,
            len(results),
        )
        details_conf = recalculate_confidence(
            [(v, c) for v, c, _ in details_candidates],
            self.fuzzy_threshold,
            len(results),
        )
        date_conf = recalculate_confidence(
            [(v, c) for v, c, _ in date_candidates],
            self.fuzzy_threshold,
            len(results),
        )

        # Create merged result
        merged = ExtractedEntities(
            person_in_charge=person_value,
            startup_name=startup_value,
            partner_org=partner_value,
            details=details_value,
            date=date_value,
            confidence=ConfidenceScores(
                person=person_conf,
                startup=startup_conf,
                partner=partner_conf,
                details=details_conf,
                date=date_conf,
            ),
            email_id=email_id,
            extracted_at=datetime.now(),
        )

        logger.info(
            f"Merged result: person={person_value}, startup={startup_value}, "
            f"avg_confidence={(person_conf + startup_conf + partner_conf + details_conf + date_conf) / 5:.3f}"
        )

        return merged
