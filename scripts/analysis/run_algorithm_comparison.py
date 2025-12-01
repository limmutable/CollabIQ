#!/usr/bin/env python3
"""
Run algorithm comparison between Rapidfuzz and LLM-based matching.

This script demonstrates the differences between character-based fuzzy matching
and semantic LLM-based matching on the ground truth dataset.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "tests"))

from evaluation.test_matching_comparison import (
    load_ground_truth,
    load_candidates,
    evaluate_matcher,
)
from notion_integrator.fuzzy_matcher import RapidfuzzMatcher


def print_detailed_results():
    """Print detailed comparison of matching results."""

    print("=" * 80)
    print("ALGORITHM COMPARISON: Rapidfuzz vs LLM-based Matching")
    print("=" * 80)
    print()

    # Load test data
    test_cases = load_ground_truth()
    candidates = load_candidates()

    print(f"Ground Truth Dataset: {len(test_cases)} test cases")
    print(f"Candidate Companies: {len(candidates)} companies")
    print()

    # Show dataset statistics
    stats = {
        "exact_matches": sum(1 for tc in test_cases if tc["match_type"] == "exact"),
        "fuzzy_matches": sum(1 for tc in test_cases if tc["match_type"] == "fuzzy"),
        "no_matches": sum(1 for tc in test_cases if tc["match_type"] == "none"),
        "easy": sum(1 for tc in test_cases if tc["difficulty"] == "easy"),
        "medium": sum(1 for tc in test_cases if tc["difficulty"] == "medium"),
        "hard": sum(1 for tc in test_cases if tc["difficulty"] == "hard"),
    }

    print("Dataset Composition:")
    print(
        f"  Exact Matches:  {stats['exact_matches']:2d} ({stats['exact_matches'] / len(test_cases) * 100:.0f}%)"
    )
    print(
        f"  Fuzzy Matches:  {stats['fuzzy_matches']:2d} ({stats['fuzzy_matches'] / len(test_cases) * 100:.0f}%)"
    )
    print(
        f"  No Matches:     {stats['no_matches']:2d} ({stats['no_matches'] / len(test_cases) * 100:.0f}%)"
    )
    print()
    print(
        f"  Easy:   {stats['easy']:2d} ({stats['easy'] / len(test_cases) * 100:.0f}%)"
    )
    print(
        f"  Medium: {stats['medium']:2d} ({stats['medium'] / len(test_cases) * 100:.0f}%)"
    )
    print(
        f"  Hard:   {stats['hard']:2d} ({stats['hard'] / len(test_cases) * 100:.0f}%)"
    )
    print()

    # Evaluate Rapidfuzz
    print("=" * 80)
    print("TESTING: RapidfuzzMatcher (Character-based Fuzzy Matching)")
    print("=" * 80)
    print()

    rapidfuzz_matcher = RapidfuzzMatcher()
    rapidfuzz_metrics, rapidfuzz_results = evaluate_matcher(
        rapidfuzz_matcher,
        "RapidfuzzMatcher",
        test_cases,
        candidates,
        similarity_threshold=0.85,
    )

    print("✅ Evaluation Complete")
    print(f"   Accuracy:  {rapidfuzz_metrics.accuracy:.1%}")
    print(f"   Precision: {rapidfuzz_metrics.precision:.1%}")
    print(f"   Recall:    {rapidfuzz_metrics.recall:.1%}")
    print(f"   F1 Score:  {rapidfuzz_metrics.f1_score:.3f}")
    print(f"   Latency:   {rapidfuzz_metrics.avg_latency_ms:.2f}ms avg")
    print("   Cost:      $0 (free)")
    print()

    # Show detailed results
    print("=" * 80)
    print("DETAILED RESULTS BY TEST CASE")
    print("=" * 80)
    print()

    # Group by category
    by_category = {}
    for result in rapidfuzz_results:
        # Find test case to get category
        tc = next((t for t in test_cases if t["id"] == result.test_case_id), None)
        if tc:
            category = tc["category"]
            if category not in by_category:
                by_category[category] = []
            by_category[category].append((result, tc))

    for category in sorted(by_category.keys()):
        results = by_category[category]
        correct = sum(1 for r, _ in results if r.is_correct)
        total = len(results)

        print(f"Category: {category}")
        print(f"  Accuracy: {correct}/{total} ({correct / total * 100:.0f}%)")
        print()

        for result, tc in results:
            status = "✅" if result.is_correct else "❌"
            print(f"  {status} {result.test_case_id}: '{result.extracted_name}'")
            print(f"     Expected: {result.expected_match}")
            print(f"     Got:      {result.predicted_match}")
            print(f"     Score:    {result.similarity_score:.3f}")

            if not result.is_correct:
                # Explain why it failed
                if (
                    result.predicted_match == "(no match)"
                    and result.expected_match != "(no match)"
                ):
                    print("     ⚠️  False Negative: Failed to find match")
                elif (
                    result.predicted_match != "(no match)"
                    and result.expected_match == "(no match)"
                ):
                    print("     ⚠️  False Positive: Matched when shouldn't")
                else:
                    print("     ⚠️  Wrong Match: Found different company")

            print()

    # Summary comparison
    print("=" * 80)
    print("ALGORITHM COMPARISON SUMMARY")
    print("=" * 80)
    print()

    print("RapidfuzzMatcher (Character-based):")
    print("  ✅ Strengths:")
    print(f"     - Fast: {rapidfuzz_metrics.avg_latency_ms:.2f}ms average")
    print("     - Free: No API costs")
    print("     - Simple: No dependencies on external services")
    print("     - Handles exact matches perfectly")
    print("     - Good with whitespace variations")
    print()
    print("  ⚠️  Limitations:")

    # Find failure patterns
    failed_categories = set()
    for result in rapidfuzz_results:
        if not result.is_correct:
            tc = next((t for t in test_cases if t["id"] == result.test_case_id), None)
            if tc:
                failed_categories.add(tc["category"])

    if failed_categories:
        for cat in sorted(failed_categories):
            print(f"     - Struggles with: {cat}")
    else:
        print("     - None observed on this dataset!")

    print()

    print("LLMMatcher (Semantic, not tested):")
    print("  ✅ Theoretical Strengths:")
    print("     - Semantic understanding")
    print("     - Handles synonyms and variations")
    print("     - Can understand context")
    print("     - Multilingual capabilities")
    print()
    print("  ⚠️  Trade-offs:")
    print("     - Slower: ~500-2000ms per call")
    print("     - Costly: ~$0.001 per match")
    print("     - Requires LLM API configuration")
    print("     - May have variability in results")
    print()

    # Final recommendation
    print("=" * 80)
    print("RECOMMENDATION")
    print("=" * 80)
    print()

    if rapidfuzz_metrics.f1_score >= 0.90:
        print("✅ USE RapidfuzzMatcher for production")
        print(f"   - Meets 90% accuracy threshold ({rapidfuzz_metrics.accuracy:.1%})")
        print("   - Fast and free")
        print("   - No external dependencies")
    elif rapidfuzz_metrics.f1_score >= 0.80:
        print("⚠️  CONSIDER HybridMatcher")
        print(
            f"   - Rapidfuzz at {rapidfuzz_metrics.f1_score:.1%} is good but below target"
        )
        print("   - Use Rapidfuzz first, LLM fallback for difficult cases")
        print("   - Balances speed, cost, and accuracy")
    else:
        print("❌ EVALUATE LLMMatcher")
        print(f"   - Rapidfuzz at {rapidfuzz_metrics.f1_score:.1%} is below 80%")
        print("   - May need semantic understanding")
        print("   - Consider dataset improvements first")

    print()


if __name__ == "__main__":
    try:
        print_detailed_results()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
