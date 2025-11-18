"""
Comparative Evaluation: Rapidfuzz vs LLM vs Hybrid Matching

This module evaluates three company name matching approaches:
1. RapidfuzzMatcher: Fast character-based fuzzy matching
2. LLMMatcher: Semantic LLM-based matching
3. HybridMatcher: Rapidfuzz first, LLM fallback

Metrics:
- Accuracy: % of correct matches
- Precision: % of predicted matches that are correct
- Recall: % of actual matches that were found
- F1 Score: Harmonic mean of precision and recall
- Latency: Average time per match (ms)
- Cost: Estimated API cost per match

Ground Truth: tests/fixtures/evaluation/ground_truth.json
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict

import pytest

from notion_integrator.fuzzy_matcher import (
    RapidfuzzMatcher,
    LLMMatcher,
    HybridMatcher,
    CompanyMatcher,
)


@dataclass
class EvaluationMetrics:
    """Metrics for a single matcher evaluation."""

    matcher_name: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    avg_latency_ms: float
    total_latency_ms: float
    correct_matches: int
    incorrect_matches: int
    true_positives: int
    false_positives: int
    false_negatives: int
    test_cases: int
    estimated_cost_per_match: float = 0.0

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class MatchResult:
    """Result of a single match attempt."""

    test_case_id: str
    extracted_name: str
    expected_match: str
    predicted_match: str
    is_correct: bool
    similarity_score: float
    match_type: str
    latency_ms: float
    match_method: str


def load_ground_truth(
    file_path: str = "tests/fixtures/evaluation/ground_truth.json",
) -> List[Dict]:
    """
    Load ground truth test cases.

    Args:
        file_path: Path to ground truth JSON file

    Returns:
        List of test case dictionaries
    """
    path = Path(file_path)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data["test_cases"]


def load_candidates(
    file_path: str = "data/notion_cache/data_Companies.json",
) -> List[Tuple[str, str]]:
    """
    Load company candidates from Companies database cache.

    Args:
        file_path: Path to cached Companies data

    Returns:
        List of (page_id, company_name) tuples
    """
    path = Path(file_path)

    if not path.exists():
        # Return mock candidates for testing
        return [
            ("page1", "웨이크"),
            ("page2", "네트워크"),
            ("page3", "현대카드"),
            ("page4", "신세계푸드"),
            ("page5", "KDT다이아몬드"),
            ("page6", "채널톡"),
            ("page7", "에이블리"),
            ("page8", "시그나이트"),
            ("page9", "브레이크앤컴퍼니"),
            ("page10", "로보톰"),
            ("page11", "스위트스팟"),
            ("page12", "신세계백화점"),
            ("page13", "SFNW"),
            ("page14", "프랙시스"),
            ("page15", "네이버"),
            ("page16", "카카오"),
        ]

    with open(path, "r", encoding="utf-8") as f:
        cache_data = json.load(f)

    companies = cache_data.get("companies", [])
    return [(c["page_id"], c["title"]) for c in companies]


def evaluate_matcher(
    matcher: CompanyMatcher,
    matcher_name: str,
    test_cases: List[Dict],
    candidates: List[Tuple[str, str]],
    *,
    similarity_threshold: float = 0.85,
) -> Tuple[EvaluationMetrics, List[MatchResult]]:
    """
    Evaluate a single matcher against ground truth.

    Args:
        matcher: CompanyMatcher instance to evaluate
        matcher_name: Human-readable name for reporting
        test_cases: Ground truth test cases
        candidates: List of (page_id, company_name) tuples
        similarity_threshold: Threshold for matching

    Returns:
        Tuple of (EvaluationMetrics, List[MatchResult])
    """
    # Create name-to-page-id mapping for evaluation
    name_to_page = {name: pid for pid, name in candidates}

    results = []
    latencies = []

    # Metrics counters
    correct_matches = 0
    incorrect_matches = 0
    true_positives = 0  # Correctly predicted a match
    false_positives = 0  # Incorrectly predicted a match
    false_negatives = 0  # Failed to find a match that exists

    for test_case in test_cases:
        test_id = test_case["id"]
        extracted_name = test_case["extracted_name"]
        expected_match = test_case["correct_match"]

        # Time the match operation
        start_time = time.time()

        try:
            match_result = matcher.match(
                extracted_name,
                candidates,
                auto_create=False,  # Don't create for evaluation
                similarity_threshold=similarity_threshold,
            )
        except Exception as e:
            # Matcher failed - record as incorrect
            latency_ms = (time.time() - start_time) * 1000
            latencies.append(latency_ms)

            results.append(
                MatchResult(
                    test_case_id=test_id,
                    extracted_name=extracted_name,
                    expected_match=expected_match or "(no match)",
                    predicted_match=f"ERROR: {str(e)}",
                    is_correct=False,
                    similarity_score=0.0,
                    match_type="error",
                    latency_ms=latency_ms,
                    match_method="error",
                )
            )

            incorrect_matches += 1
            if expected_match is not None:
                false_negatives += 1

            continue

        latency_ms = (time.time() - start_time) * 1000
        latencies.append(latency_ms)

        # Determine predicted match
        if match_result.match_type in ["exact", "fuzzy"]:
            predicted_match = match_result.company_name
        else:
            predicted_match = None

        # Check correctness
        is_correct = predicted_match == expected_match

        if is_correct:
            correct_matches += 1
            if predicted_match is not None:
                true_positives += 1
        else:
            incorrect_matches += 1
            if predicted_match is not None and expected_match is None:
                false_positives += 1  # Predicted a match when there shouldn't be one
            elif predicted_match is None and expected_match is not None:
                false_negatives += 1  # Failed to find a match that exists
            elif predicted_match is not None and expected_match is not None:
                false_negatives += 1  # Found wrong match

        results.append(
            MatchResult(
                test_case_id=test_id,
                extracted_name=extracted_name,
                expected_match=expected_match or "(no match)",
                predicted_match=predicted_match or "(no match)",
                is_correct=is_correct,
                similarity_score=match_result.similarity_score,
                match_type=match_result.match_type,
                latency_ms=latency_ms,
                match_method=match_result.match_method,
            )
        )

    # Compute metrics
    total_cases = len(test_cases)
    accuracy = correct_matches / total_cases if total_cases > 0 else 0.0

    # Precision = TP / (TP + FP)
    precision = (
        true_positives / (true_positives + false_positives)
        if (true_positives + false_positives) > 0
        else 0.0
    )

    # Recall = TP / (TP + FN)
    recall = (
        true_positives / (true_positives + false_negatives)
        if (true_positives + false_negatives) > 0
        else 0.0
    )

    # F1 = 2 * (Precision * Recall) / (Precision + Recall)
    f1_score = (
        2 * (precision * recall) / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    avg_latency_ms = sum(latencies) / len(latencies) if latencies else 0.0
    total_latency_ms = sum(latencies)

    # Estimate cost (simplified - actual costs vary)
    if "LLM" in matcher_name or "Hybrid" in matcher_name:
        # Assume $0.001 per LLM call (rough estimate)
        llm_calls = sum(1 for r in results if "semantic" in r.match_method)
        estimated_cost_per_match = (
            (llm_calls / total_cases) * 0.001 if total_cases > 0 else 0.0
        )
    else:
        estimated_cost_per_match = 0.0  # Rapidfuzz is free

    metrics = EvaluationMetrics(
        matcher_name=matcher_name,
        accuracy=accuracy,
        precision=precision,
        recall=recall,
        f1_score=f1_score,
        avg_latency_ms=avg_latency_ms,
        total_latency_ms=total_latency_ms,
        correct_matches=correct_matches,
        incorrect_matches=incorrect_matches,
        true_positives=true_positives,
        false_positives=false_positives,
        false_negatives=false_negatives,
        test_cases=total_cases,
        estimated_cost_per_match=estimated_cost_per_match,
    )

    return metrics, results


def generate_comparison_report(
    all_metrics: List[EvaluationMetrics],
    all_results: Dict[str, List[MatchResult]],
    output_path: str = "specs/014-enhanced-field-mapping/evaluation-report.md",
) -> None:
    """
    Generate comprehensive comparison report in Markdown format.

    Args:
        all_metrics: List of EvaluationMetrics for each matcher
        all_results: Dictionary mapping matcher_name to List[MatchResult]
        output_path: Path to save report
    """
    # Sort by F1 score (descending)
    sorted_metrics = sorted(all_metrics, key=lambda m: m.f1_score, reverse=True)

    report = f"""# Algorithm Evaluation Report

**Date**: {time.strftime("%Y-%m-%d")}
**Feature**: 014-enhanced-field-mapping
**Evaluation**: Comparative Analysis of Company Name Matching Algorithms

---

## Executive Summary

This report compares three approaches for fuzzy company name matching:

1. **RapidfuzzMatcher**: Character-based fuzzy matching (Jaro-Winkler algorithm)
2. **LLMMatcher**: Semantic LLM-based matching
3. **HybridMatcher**: Rapidfuzz first (fast path), LLM fallback (accuracy)

**Test Dataset**: {sorted_metrics[0].test_cases} test cases from real email data

---

## Overall Results

| Rank | Matcher | Accuracy | Precision | Recall | F1 Score | Avg Latency | Cost/Match |
|------|---------|----------|-----------|--------|----------|-------------|------------|
"""

    for i, metrics in enumerate(sorted_metrics, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
        report += f"| {medal} | **{metrics.matcher_name}** | {metrics.accuracy:.1%} | {metrics.precision:.1%} | {metrics.recall:.1%} | {metrics.f1_score:.3f} | {metrics.avg_latency_ms:.1f}ms | ${metrics.estimated_cost_per_match:.4f} |\n"

    report += """

---

## Detailed Metrics

"""

    for metrics in sorted_metrics:
        status_icon = (
            "✅"
            if metrics.f1_score >= 0.90
            else "⚠️"
            if metrics.f1_score >= 0.80
            else "❌"
        )

        report += f"""
### {status_icon} {metrics.matcher_name}

| Metric | Value |
|--------|-------|
| **Accuracy** | {metrics.accuracy:.2%} ({metrics.correct_matches}/{metrics.test_cases}) |
| **Precision** | {metrics.precision:.2%} (TP: {metrics.true_positives}, FP: {metrics.false_positives}) |
| **Recall** | {metrics.recall:.2%} (TP: {metrics.true_positives}, FN: {metrics.false_negatives}) |
| **F1 Score** | {metrics.f1_score:.3f} |
| **Avg Latency** | {metrics.avg_latency_ms:.1f}ms |
| **Total Latency** | {metrics.total_latency_ms:.1f}ms |
| **Est. Cost/Match** | ${metrics.estimated_cost_per_match:.4f} |

**Correct Matches**: {metrics.correct_matches}
**Incorrect Matches**: {metrics.incorrect_matches}

"""

    # Add failure analysis
    report += """
---

## Failure Analysis

### Cases Where Matchers Disagreed

"""

    # Find cases where predictions differ
    matcher_names = list(all_results.keys())
    if len(matcher_names) >= 2:
        results_by_id = {}
        for matcher_name, results in all_results.items():
            for result in results:
                if result.test_case_id not in results_by_id:
                    results_by_id[result.test_case_id] = {}
                results_by_id[result.test_case_id][matcher_name] = result

        disagreements = []
        for test_id, results_dict in results_by_id.items():
            predictions = set(r.predicted_match for r in results_dict.values())
            if len(predictions) > 1:  # Matchers disagree
                disagreements.append((test_id, results_dict))

        if disagreements:
            report += (
                f"\nFound {len(disagreements)} cases where matchers disagreed:\n\n"
            )

            for test_id, results_dict in disagreements[:10]:  # Show top 10
                first_result = list(results_dict.values())[0]
                report += f"#### Test Case: {test_id}\n\n"
                report += f"- **Extracted Name**: {first_result.extracted_name}\n"
                report += f"- **Expected Match**: {first_result.expected_match}\n\n"

                report += "| Matcher | Predicted | Correct? | Similarity |\n"
                report += "|---------|-----------|----------|------------|\n"

                for matcher_name in sorted(results_dict.keys()):
                    result = results_dict[matcher_name]
                    correct_icon = "✅" if result.is_correct else "❌"
                    report += f"| {matcher_name} | {result.predicted_match} | {correct_icon} | {result.similarity_score:.2f} |\n"

                report += "\n"
        else:
            report += "\nNo disagreements found - all matchers produced identical predictions.\n\n"

    # Add recommendations
    report += """
---

## Recommendations

### Production Algorithm Selection

"""

    best = sorted_metrics[0]

    if best.matcher_name == "RapidfuzzMatcher":
        report += f"""
**✅ RECOMMEND: RapidfuzzMatcher**

Rationale:
- Highest F1 score ({best.f1_score:.3f}) meets 90% threshold
- Fastest latency ({best.avg_latency_ms:.1f}ms average)
- Zero cost (no API calls)
- Simple implementation
- Excellent performance on character-based variations

**Use Case**: Primary matcher for production
"""

    elif best.matcher_name == "HybridMatcher":
        report += f"""
**✅ RECOMMEND: HybridMatcher**

Rationale:
- Best F1 score ({best.f1_score:.3f}) across all approaches
- Balances speed and accuracy
- Uses LLM only when needed (cost-effective)
- Handles both simple and complex cases

**Use Case**: Production matcher when accuracy is critical
"""

    elif best.matcher_name == "LLMMatcher":
        report += f"""
**⚠️ CONSIDER: LLMMatcher**

Rationale:
- Highest F1 score ({best.f1_score:.3f})
- Best semantic understanding
- Handles complex name variations

**Trade-offs**:
- Higher latency ({best.avg_latency_ms:.1f}ms average)
- Higher cost (${best.estimated_cost_per_match:.4f} per match)

**Use Case**: Fallback matcher for difficult cases
"""

    # Add acceptance criteria check
    report += """

### Acceptance Criteria Validation

| Criterion | Target | Result | Status |
|-----------|--------|--------|--------|
"""

    for metrics in sorted_metrics:
        accuracy_status = "✅" if metrics.accuracy >= 0.90 else "❌"
        f1_status = "✅" if metrics.f1_score >= 0.90 else "❌"
        latency_status = "✅" if metrics.avg_latency_ms < 2000 else "❌"

        report += f"| **{metrics.matcher_name}** | | | |\n"
        report += f"| Accuracy (SC-001) | ≥90% | {metrics.accuracy:.1%} | {accuracy_status} |\n"
        report += f"| F1 Score | ≥0.90 | {metrics.f1_score:.3f} | {f1_status} |\n"
        report += f"| Latency (SC-007) | <2000ms | {metrics.avg_latency_ms:.1f}ms | {latency_status} |\n"

    report += """

---

## Conclusion

"""

    if best.f1_score >= 0.90:
        report += f"""
✅ **SUCCESS**: {best.matcher_name} meets all success criteria with {best.f1_score:.1%} F1 score.

**Recommended Action**: Deploy {best.matcher_name} to production.
"""
    else:
        report += f"""
⚠️ **REVIEW NEEDED**: Best F1 score is {best.f1_score:.1%}, below 90% target.

**Recommended Actions**:
1. Review failure cases in detail
2. Improve normalization rules
3. Add more training data if using LLM
4. Consider ensemble approach
"""

    report += f"""

---

**Report Generated**: {time.strftime("%Y-%m-%d %H:%M:%S")}
**Evaluation Duration**: {sum(m.total_latency_ms for m in all_metrics):.1f}ms total
**Test Framework**: pytest + rapidfuzz + LLM orchestrator
"""

    # Write report to file
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    output_path_obj.write_text(report, encoding="utf-8")

    print(f"\n✅ Evaluation report saved to: {output_path}")


@pytest.mark.skip(reason="Evaluation test - run manually with pytest --run-evaluation")
def test_rapidfuzz_matcher_evaluation():
    """Evaluate RapidfuzzMatcher against ground truth."""
    test_cases = load_ground_truth()
    candidates = load_candidates()

    matcher = RapidfuzzMatcher()
    metrics, results = evaluate_matcher(
        matcher,
        "RapidfuzzMatcher",
        test_cases,
        candidates,
        similarity_threshold=0.85,
    )

    # Assert minimum performance
    assert metrics.accuracy >= 0.80, (
        f"Accuracy {metrics.accuracy:.1%} below 80% threshold"
    )
    assert metrics.f1_score >= 0.80, (
        f"F1 score {metrics.f1_score:.3f} below 0.80 threshold"
    )

    print(f"\n{metrics.matcher_name} Results:")
    print(f"  Accuracy: {metrics.accuracy:.2%}")
    print(f"  F1 Score: {metrics.f1_score:.3f}")
    print(f"  Avg Latency: {metrics.avg_latency_ms:.1f}ms")


@pytest.mark.skip(reason="Evaluation test - run manually, requires LLM")
def test_llm_matcher_evaluation():
    """Evaluate LLMMatcher against ground truth."""
    from llm_orchestrator.orchestrator import LLMOrchestrator

    test_cases = load_ground_truth()
    candidates = load_candidates()

    orchestrator = LLMOrchestrator()
    matcher = LLMMatcher(orchestrator)

    metrics, results = evaluate_matcher(
        matcher,
        "LLMMatcher",
        test_cases,
        candidates,
        similarity_threshold=0.70,
    )

    assert metrics.accuracy >= 0.80, (
        f"Accuracy {metrics.accuracy:.1%} below 80% threshold"
    )

    print(f"\n{metrics.matcher_name} Results:")
    print(f"  Accuracy: {metrics.accuracy:.2%}")
    print(f"  F1 Score: {metrics.f1_score:.3f}")
    print(f"  Avg Latency: {metrics.avg_latency_ms:.1f}ms")


@pytest.mark.skip(reason="Evaluation test - run manually, requires LLM")
def test_hybrid_matcher_evaluation():
    """Evaluate HybridMatcher against ground truth."""
    from llm_orchestrator.orchestrator import LLMOrchestrator

    test_cases = load_ground_truth()
    candidates = load_candidates()

    orchestrator = LLMOrchestrator()
    matcher = HybridMatcher(orchestrator)

    metrics, results = evaluate_matcher(
        matcher,
        "HybridMatcher",
        test_cases,
        candidates,
        similarity_threshold=0.85,
    )

    assert metrics.accuracy >= 0.80, (
        f"Accuracy {metrics.accuracy:.1%} below 80% threshold"
    )

    print(f"\n{metrics.matcher_name} Results:")
    print(f"  Accuracy: {metrics.accuracy:.2%}")
    print(f"  F1 Score: {metrics.f1_score:.3f}")
    print(f"  Avg Latency: {metrics.avg_latency_ms:.1f}ms")


@pytest.mark.skip(reason="Comparative evaluation - run manually")
def test_comparative_evaluation():
    """Run comparative evaluation of all matchers and generate report."""
    test_cases = load_ground_truth()
    candidates = load_candidates()

    all_metrics = []
    all_results = {}

    # Evaluate RapidfuzzMatcher
    print("\n" + "=" * 70)
    print("Evaluating RapidfuzzMatcher...")
    print("=" * 70)

    rapidfuzz_matcher = RapidfuzzMatcher()
    rapidfuzz_metrics, rapidfuzz_results = evaluate_matcher(
        rapidfuzz_matcher,
        "RapidfuzzMatcher",
        test_cases,
        candidates,
        similarity_threshold=0.85,
    )
    all_metrics.append(rapidfuzz_metrics)
    all_results["RapidfuzzMatcher"] = rapidfuzz_results

    print(f"✅ Accuracy: {rapidfuzz_metrics.accuracy:.2%}")
    print(f"✅ F1 Score: {rapidfuzz_metrics.f1_score:.3f}")
    print(f"✅ Avg Latency: {rapidfuzz_metrics.avg_latency_ms:.1f}ms")

    # Evaluate LLMMatcher (optional - requires LLM)
    try:
        print("\n" + "=" * 70)
        print("Evaluating LLMMatcher...")
        print("=" * 70)

        from llm_orchestrator.orchestrator import LLMOrchestrator

        orchestrator = LLMOrchestrator()

        llm_matcher = LLMMatcher(orchestrator)
        llm_metrics, llm_results = evaluate_matcher(
            llm_matcher,
            "LLMMatcher",
            test_cases,
            candidates,
            similarity_threshold=0.70,
        )
        all_metrics.append(llm_metrics)
        all_results["LLMMatcher"] = llm_results

        print(f"✅ Accuracy: {llm_metrics.accuracy:.2%}")
        print(f"✅ F1 Score: {llm_metrics.f1_score:.3f}")
        print(f"✅ Avg Latency: {llm_metrics.avg_latency_ms:.1f}ms")

        # Evaluate HybridMatcher
        print("\n" + "=" * 70)
        print("Evaluating HybridMatcher...")
        print("=" * 70)

        hybrid_matcher = HybridMatcher(orchestrator)
        hybrid_metrics, hybrid_results = evaluate_matcher(
            hybrid_matcher,
            "HybridMatcher",
            test_cases,
            candidates,
            similarity_threshold=0.85,
        )
        all_metrics.append(hybrid_metrics)
        all_results["HybridMatcher"] = hybrid_results

        print(f"✅ Accuracy: {hybrid_metrics.accuracy:.2%}")
        print(f"✅ F1 Score: {hybrid_metrics.f1_score:.3f}")
        print(f"✅ Avg Latency: {hybrid_metrics.avg_latency_ms:.1f}ms")

    except Exception as e:
        print(f"\n⚠️  LLM evaluation skipped: {str(e)}")
        print("    (LLM matchers require LLM orchestrator configuration)")

    # Generate comparison report
    print("\n" + "=" * 70)
    print("Generating comparison report...")
    print("=" * 70)

    generate_comparison_report(all_metrics, all_results)

    print("\n✅ Evaluation complete!")
