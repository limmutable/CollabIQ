#!/usr/bin/env python3
"""Compare gemini-3-pro-preview vs gemini-2.5-flash performance on real email extraction."""

import os
import sys
from pathlib import Path
import time
from typing import Dict, List

# Add src to path
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from llm_adapters.gemini_adapter import GeminiAdapter

# Test emails (mix of Korean and English)
TEST_EMAILS = [
    "어제 신세계와 본봄 파일럿 킥오프 미팅이 있었습니다. 담당자는 김민수님입니다.",
    "Pilot kickoff meeting with Shinsegae and Bonbom yesterday. Contact: Kim Min-soo.",
    "내일 오전 10시에 카카오와 파트너십 논의 예정. 담당: 이영희 (yhlee@kakao.com)",
    "Meeting scheduled for tomorrow 10am with Kakao for partnership discussion. Contact: Lee Young-hee (yhlee@kakao.com)",
    "2025년 1월 15일 네이버클라우드와 데모 세션. 참석자: 박철수 이사",
    "Demo session with Naver Cloud on January 15, 2025. Attendee: Director Park Chul-soo",
    "토스페이먼츠와 2024년 12월 3일 통합 논의. 연락처: 정현우 팀장 (hw.jung@tosspayments.com)",
    "Integration discussion with Toss Payments on December 3, 2024. Contact: Team Lead Jung Hyun-woo (hw.jung@tosspayments.com)"
]

def benchmark_model(model_name: str, api_key: str) -> Dict:
    """Run benchmark for a specific model."""
    print(f"\n{'='*80}")
    print(f"Benchmarking: {model_name}")
    print(f"{'='*80}\n")

    adapter = GeminiAdapter(api_key=api_key, model=model_name)

    results = {
        "model": model_name,
        "tests": len(TEST_EMAILS),
        "successes": 0,
        "failures": 0,
        "total_time": 0,
        "response_times": [],
        "field_accuracy": {
            "partner_org": 0,
            "date": 0,
            "startup_name": 0,
            "person_in_charge": 0,
            "details": 0
        },
        "confidence_scores": []
    }

    for i, email in enumerate(TEST_EMAILS, 1):
        print(f"Test {i}/{len(TEST_EMAILS)}: ", end="", flush=True)
        start = time.time()
        try:
            entities = adapter.extract_entities(email)
            elapsed = time.time() - start
            results["response_times"].append(elapsed)
            results["successes"] += 1

            # Check field accuracy
            if entities.partner_org:
                results["field_accuracy"]["partner_org"] += 1
            if entities.date:
                results["field_accuracy"]["date"] += 1
            if entities.startup_name:
                results["field_accuracy"]["startup_name"] += 1
            if entities.person_in_charge:
                results["field_accuracy"]["person_in_charge"] += 1
            if entities.details:
                results["field_accuracy"]["details"] += 1

            # Track confidence
            if hasattr(entities, 'confidence_scores') and entities.confidence_scores:
                avg_confidence = sum(entities.confidence_scores.values()) / len(entities.confidence_scores)
                results["confidence_scores"].append(avg_confidence)

            print(f"✅ ({elapsed:.2f}s)")
        except Exception as e:
            elapsed = time.time() - start
            results["failures"] += 1
            print(f"❌ ({elapsed:.2f}s) - {str(e)[:50]}")

    results["total_time"] = sum(results["response_times"])

    # Print results
    print(f"\n{'='*80}")
    print(f"RESULTS: {model_name}")
    print(f"{'='*80}")
    print(f"Tests:          {results['tests']}")
    print(f"Successes:      {results['successes']} ({results['successes']/results['tests']*100:.0f}%)")
    print(f"Failures:       {results['failures']}")
    print(f"\nTiming:")
    print(f"  Total Time:   {results['total_time']:.2f}s")
    print(f"  Avg Time:     {results['total_time']/len(TEST_EMAILS):.2f}s")
    if results["response_times"]:
        print(f"  Min Time:     {min(results['response_times']):.2f}s")
        print(f"  Max Time:     {max(results['response_times']):.2f}s")

    print(f"\nField Accuracy (out of {results['tests']} tests):")
    for field, count in results["field_accuracy"].items():
        pct = (count / results['tests']) * 100
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        print(f"  {field:20s}: {count}/{results['tests']} ({pct:5.1f}%) {bar}")

    if results["confidence_scores"]:
        avg_conf = sum(results["confidence_scores"]) / len(results["confidence_scores"])
        print(f"\nAvg Confidence: {avg_conf:.2f}")

    return results

def print_comparison(results_1: Dict, results_2: Dict):
    """Print side-by-side comparison."""
    model1 = results_1["model"]
    model2 = results_2["model"]

    print(f"\n{'='*100}")
    print("COMPARISON SUMMARY")
    print(f"{'='*100}")

    print(f"\n{'Metric':<30} {model1:<30} {model2:<30} {'Winner'}")
    print(f"{'-'*100}")

    # Success rate
    sr1 = f"{results_1['successes']}/{results_1['tests']} ({results_1['successes']/results_1['tests']*100:.0f}%)"
    sr2 = f"{results_2['successes']}/{results_2['tests']} ({results_2['successes']/results_2['tests']*100:.0f}%)"
    winner_sr = model1 if results_1['successes'] > results_2['successes'] else model2 if results_2['successes'] > results_1['successes'] else "TIE"
    print(f"{'Success Rate':<30} {sr1:<30} {sr2:<30} {winner_sr}")

    # Avg response time
    avg1 = results_1['total_time'] / results_1['tests']
    avg2 = results_2['total_time'] / results_2['tests']
    winner_time = model1 if avg1 < avg2 else model2
    speedup = max(avg1, avg2) / min(avg1, avg2)
    print(f"{'Avg Response Time':<30} {avg1:.2f}s{'':<26} {avg2:.2f}s{'':<26} {winner_time} ({speedup:.1f}x faster)")

    # Total time
    print(f"{'Total Time':<30} {results_1['total_time']:.2f}s{'':<26} {results_2['total_time']:.2f}s{'':<26}")

    # Field accuracy comparison
    print(f"\n{'Field Accuracy:':<30}")
    print(f"{'-'*100}")
    for field in results_1["field_accuracy"].keys():
        count1 = results_1["field_accuracy"][field]
        count2 = results_2["field_accuracy"][field]
        pct1 = count1 / results_1['tests'] * 100
        pct2 = count2 / results_2['tests'] * 100
        winner = model1 if count1 > count2 else model2 if count2 > count1 else "TIE"
        print(f"  {field:<28} {count1}/{results_1['tests']} ({pct1:5.1f}%){'':<18} {count2}/{results_2['tests']} ({pct2:5.1f}%){'':<18} {winner}")

    # Confidence scores
    if results_1["confidence_scores"] and results_2["confidence_scores"]:
        avg_conf1 = sum(results_1["confidence_scores"]) / len(results_1["confidence_scores"])
        avg_conf2 = sum(results_2["confidence_scores"]) / len(results_2["confidence_scores"])
        winner_conf = model1 if avg_conf1 > avg_conf2 else model2
        print(f"\n{'Avg Confidence':<30} {avg_conf1:.2f}{'':<26} {avg_conf2:.2f}{'':<26} {winner_conf}")

    # Overall winner
    print(f"\n{'='*100}")

    # Calculate overall score
    score1 = (results_1['successes'] / results_1['tests']) + (1 / avg1) * 0.1
    score2 = (results_2['successes'] / results_2['tests']) + (1 / avg2) * 0.1

    overall_winner = model1 if score1 > score2 else model2
    print(f"Overall Winner: {overall_winner}")
    print(f"  - Better accuracy/completeness and speed balance")
    print(f"{'='*100}")

if __name__ == "__main__":
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment")
        sys.exit(1)

    print("="*100)
    print("GEMINI MODEL COMPARISON: gemini-3-pro-preview vs gemini-2.5-flash")
    print("="*100)
    print(f"Test Dataset: {len(TEST_EMAILS)} emails (mix of Korean and English)")
    print("="*100)

    # Benchmark both models
    results_3_pro = benchmark_model("gemini-3-pro-preview", api_key)
    results_25_flash = benchmark_model("gemini-2.5-flash", api_key)

    # Print comparison
    print_comparison(results_3_pro, results_25_flash)
