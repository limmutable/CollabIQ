"""
Accuracy tests for quoted thread removal (SC-003: 95%+ target).

This module tests quoted thread removal accuracy against a diverse dataset
of 20+ emails to ensure the system meets the 95% success criteria.

Tasks:
- T074: test_quote_removal_accuracy_95_percent()
- T075: Create accuracy test dataset (20+ emails)
"""

import pytest

try:
    from content_normalizer.normalizer import ContentNormalizer
except ImportError:
    from content_normalizer.normalizer import ContentNormalizer


# Accuracy test dataset (T075)
ACCURACY_TEST_DATASET = [
    # Angle bracket quotes (6 samples)
    {
        "body": "Thanks for the update!\n\n> On Oct 30, John wrote:\n> Previous message here.",
        "has_quotes": True,
        "expected_content": "Thanks for the update!",
        "description": "Simple angle bracket quote",
    },
    {
        "body": "I agree with this approach.\n\n> Original message\n> with multiple lines\n> of quoted content",
        "has_quotes": True,
        "expected_content": "I agree with this approach",
        "description": "Multi-line angle bracket quotes",
    },
    {
        "body": "Let's proceed.\n\n> Level 1\n> > Level 2\n> > > Level 3",
        "has_quotes": True,
        "expected_content": "Let's proceed",
        "description": "Nested angle bracket quotes",
    },
    {
        "body": "안녕하세요,\n\n동의합니다.\n\n> 원본 메시지\n> 여러 줄의 인용 내용",
        "has_quotes": True,
        "expected_content": "동의합니다",
        "description": "Korean with angle bracket quotes",
    },
    {
        "body": "Perfect! Will do.\n\n> Here's what I think\n> about the proposal",
        "has_quotes": True,
        "expected_content": "Perfect! Will do",
        "description": "Short response with quotes",
    },
    {
        "body": "Acknowledged.\n\n> > Previous previous\n> Previous",
        "has_quotes": True,
        "expected_content": "Acknowledged",
        "description": "Reverse nested quotes",
    },
    # Gmail reply headers (5 samples)
    {
        "body": "Sounds good!\n\nOn Mon, Oct 30, 2025 at 2:30 PM, John Smith wrote:\nOriginal message content here.",
        "has_quotes": True,
        "expected_content": "Sounds good!",
        "description": "Gmail reply header with time",
    },
    {
        "body": "I'll review this tomorrow.\n\nOn Tuesday, Nov 1, 2025, Sarah Johnson wrote:\nPlease review the attached proposal.",
        "has_quotes": True,
        "expected_content": "I'll review this tomorrow",
        "description": "Gmail reply header without time",
    },
    {
        "body": "Great work!\n\nOn Wed, Oct 30, 2025, Mike Chen wrote:\nThe feature is complete.",
        "has_quotes": True,
        "expected_content": "Great work!",
        "description": "Gmail reply header short form",
    },
    {
        "body": "프로젝트 진행하겠습니다.\n\n2025년 10월 30일 화요일, 김철수님이 작성:\n일정을 조정해야 합니다.",
        "has_quotes": True,
        "expected_content": "프로젝트 진행하겠습니다",
        "description": "Korean date format reply header",
    },
    {
        "body": "Let's schedule a meeting.\n\nOn Friday, Nov 3, 2025 at 9:00 AM, Lisa Park wrote:\nI have some concerns about the timeline.",
        "has_quotes": True,
        "expected_content": "Let's schedule a meeting",
        "description": "Gmail reply with specific time",
    },
    # Outlook-style headers (3 samples)
    {
        "body": "Thanks for clarifying.\n\nFrom: John Smith\nSent: Monday, October 30, 2025\nTo: Team\nSubject: Project Update\n\nOriginal message.",
        "has_quotes": True,
        "expected_content": "Thanks for clarifying",
        "description": "Outlook From/Sent header",
    },
    {
        "body": "Got it.\n\nFrom: Sarah Johnson\nSent: Tuesday, October 31, 2025 3:45 PM\n\nPrevious email content.",
        "has_quotes": True,
        "expected_content": "Got it",
        "description": "Outlook header with time",
    },
    {
        "body": "Will do.\n\nFrom: Mike Chen\nSent: Wednesday, November 1, 2025\n\nHere's the update.",
        "has_quotes": True,
        "expected_content": "Will do",
        "description": "Outlook simple format",
    },
    # Mixed patterns (4 samples)
    {
        "body": "Agreed on all points.\n\nOn Mon, Oct 30, 2025, John wrote:\n> Original message\n> > Even older message",
        "has_quotes": True,
        "expected_content": "Agreed on all points",
        "description": "Header + nested angle brackets",
    },
    {
        "body": "I'll handle this.\n\nOn Tuesday, Nov 1, 2025, Team Lead wrote:\n> Please review\n> the attached document",
        "has_quotes": True,
        "expected_content": "I'll handle this",
        "description": "Header with angle bracket content",
    },
    {
        "body": "동의합니다.\n\n2025년 10월 30일, 팀장님이 작성:\n> 검토 부탁드립니다",
        "has_quotes": True,
        "expected_content": "동의합니다",
        "description": "Korean header + angle brackets",
    },
    {
        "body": "Perfect timing!\n\nOn Wed, Oct 30, 2025, Alice wrote:\nFrom: Bob\nSent: Tuesday\n> Original",
        "has_quotes": True,
        "expected_content": "Perfect timing!",
        "description": "Multiple quote patterns",
    },
    # No quotes (3 samples)
    {
        "body": "Project update: Phase 1 complete, starting Phase 2 next week.",
        "has_quotes": False,
        "expected_content": "Project update: Phase 1 complete, starting Phase 2 next week.",
        "description": "Fresh email, no quotes",
    },
    {
        "body": "프로젝트 상황 보고입니다.\n\n1단계 완료\n2단계 시작 예정",
        "has_quotes": False,
        "expected_content": "프로젝트 상황 보고입니다",
        "description": "Korean fresh email",
    },
    {
        "body": "The value is x > y where x and y are positive integers.",
        "has_quotes": False,
        "expected_content": "The value is x > y where x and y are positive integers.",
        "description": "Fake > symbol (not quote)",
    },
]


@pytest.fixture
def normalizer():
    """Create ContentNormalizer instance for accuracy testing."""
    return ContentNormalizer()


def test_quote_removal_accuracy_95_percent(normalizer):
    """
    T074: Test quoted thread removal achieves 95%+ accuracy (SC-003).

    Success criteria:
    - For emails WITH quotes: Quotes must be removed AND main content preserved
    - For emails WITHOUT quotes: Content must remain unchanged
    - Overall accuracy: >= 95% (19/20 or better)

    This test uses the comprehensive 20-email dataset covering:
    - Angle bracket quotes (6 samples)
    - Gmail reply headers (5 samples)
    - Outlook headers (3 samples)
    - Mixed patterns (4 samples)
    - No quotes (3 samples)
    """
    total_tests = len(ACCURACY_TEST_DATASET)
    successful_removals = 0
    failed_cases = []

    for i, test_case in enumerate(ACCURACY_TEST_DATASET):
        body = test_case["body"]
        has_quotes = test_case["has_quotes"]
        expected_content = test_case["expected_content"]
        description = test_case["description"]

        # Perform quote removal
        cleaned_body = normalizer.remove_quoted_thread(body)

        # Check if removal was successful
        success = False

        if has_quotes:
            # For emails with quotes:
            # 1. Expected content should be preserved
            # 2. Cleaned body should be shorter than original
            content_preserved = expected_content in cleaned_body
            size_reduced = len(cleaned_body) < len(body)
            success = content_preserved and size_reduced

            if not success:
                failed_cases.append(
                    {
                        "index": i,
                        "description": description,
                        "reason": f"Content preserved: {content_preserved}, Size reduced: {size_reduced}",
                        "original_length": len(body),
                        "cleaned_length": len(cleaned_body),
                        "expected_content": expected_content,
                        "cleaned_body": cleaned_body[:100],
                    }
                )
        else:
            # For emails without quotes:
            # Content should remain exactly the same
            success = cleaned_body == body

            if not success:
                failed_cases.append(
                    {
                        "index": i,
                        "description": description,
                        "reason": "Content was modified when it shouldn't be",
                        "original": body[:100],
                        "cleaned": cleaned_body[:100],
                    }
                )

        if success:
            successful_removals += 1

    # Calculate accuracy
    accuracy = (successful_removals / total_tests) * 100

    # Print detailed results
    print(f"\n{'=' * 70}")
    print("QUOTED THREAD REMOVAL ACCURACY TEST RESULTS")
    print(f"{'=' * 70}")
    print(f"Total test cases: {total_tests}")
    print(f"Successful: {successful_removals}")
    print(f"Failed: {len(failed_cases)}")
    print(f"Accuracy: {accuracy:.1f}%")
    print("Target: 95.0%")
    print(f"Status: {'✓ PASS' if accuracy >= 95.0 else '✗ FAIL'}")
    print(f"{'=' * 70}")

    # Print failed cases for debugging
    if failed_cases:
        print(f"\nFailed test cases ({len(failed_cases)}):")
        for case in failed_cases:
            print(f"\n  [{case['index']}] {case['description']}")
            print(f"      Reason: {case['reason']}")
            if "cleaned_body" in case:
                print(f"      Expected: {case['expected_content'][:50]}...")
                print(f"      Got: {case['cleaned_body'][:80]}...")

    # Assert 95%+ accuracy
    assert accuracy >= 95.0, (
        f"Quote removal accuracy {accuracy:.1f}% is below 95% target. "
        f"Failed {len(failed_cases)}/{total_tests} cases. See output for details."
    )


def test_dataset_quality():
    """
    Verify the accuracy test dataset meets requirements.

    Requirements:
    - At least 20 test cases (T075)
    - Mix of quote types (angle brackets, headers)
    - Mix of quotes present and absent
    - Representative of real-world patterns
    """
    total_cases = len(ACCURACY_TEST_DATASET)
    with_quotes = sum(1 for case in ACCURACY_TEST_DATASET if case["has_quotes"])
    without_quotes = total_cases - with_quotes

    korean_cases = sum(
        1
        for case in ACCURACY_TEST_DATASET
        if any(
            ord(c) >= 0xAC00 and ord(c) <= 0xD7A3  # Korean Hangul range
            for c in case["body"]
        )
    )
    english_cases = total_cases - korean_cases

    print("\nDataset composition:")
    print(f"  Total cases: {total_cases}")
    print(f"  With quotes: {with_quotes}")
    print(f"  Without quotes: {without_quotes}")
    print(f"  Korean: {korean_cases}")
    print(f"  English: {english_cases}")

    # Assert dataset quality
    assert total_cases >= 20, (
        f"Dataset should have at least 20 cases, got {total_cases}"
    )
    assert with_quotes > 0, "Dataset should include cases with quotes"
    assert without_quotes > 0, "Dataset should include cases without quotes"
    assert korean_cases > 0, "Dataset should include Korean cases"
    assert english_cases > 0, "Dataset should include English cases"


def test_individual_pattern_coverage():
    """
    Test that each major pattern type is covered in the dataset.

    Pattern types:
    - Angle bracket quotes
    - Gmail reply headers
    - Outlook headers
    - Korean patterns
    - No quotes
    """
    pattern_coverage = {
        "angle_bracket": 0,
        "gmail_header": 0,
        "outlook_header": 0,
        "korean_patterns": 0,
        "mixed_patterns": 0,
        "no_quotes": 0,
    }

    for case in ACCURACY_TEST_DATASET:
        desc = case["description"].lower()
        if "angle bracket" in desc:
            pattern_coverage["angle_bracket"] += 1
        if "gmail" in desc or ("reply header" in desc and "outlook" not in desc):
            pattern_coverage["gmail_header"] += 1
        if "outlook" in desc:
            pattern_coverage["outlook_header"] += 1
        if "korean" in desc:
            pattern_coverage["korean_patterns"] += 1
        if "mixed" in desc or "multiple" in desc:
            pattern_coverage["mixed_patterns"] += 1
        if not case["has_quotes"]:
            pattern_coverage["no_quotes"] += 1

    print("\nPattern coverage:")
    for pattern, count in pattern_coverage.items():
        print(f"  {pattern}: {count}")

    # All major patterns should be covered
    for pattern, count in pattern_coverage.items():
        assert count > 0, f"Pattern '{pattern}' is not covered in dataset"
