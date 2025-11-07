"""
Accuracy tests for signature removal (SC-002: 95%+ target).

This module tests signature removal accuracy against a diverse dataset
of 20+ emails to ensure the system meets the 95% success criteria.

Tasks:
- T060: test_signature_removal_accuracy_95_percent()
- T061: Create accuracy test dataset (20+ emails)
"""

from pathlib import Path

import pytest

try:
    from src.content_normalizer.normalizer import ContentNormalizer
except ImportError:
    from content_normalizer.normalizer import ContentNormalizer


# Accuracy test dataset (T061)
ACCURACY_TEST_DATASET = [
    # Korean signatures (8 samples)
    {
        "body": "안녕하세요,\n\n프로젝트 업데이트를 공유합니다.\n\n감사합니다.\n김철수 드림",
        "has_signature": True,
        "expected_content": "프로젝트 업데이트를 공유합니다",
        "description": "Korean thanks + name pattern",
    },
    {
        "body": "회의 일정 공유드립니다.\n\n감사드립니다.\n이영희 올림",
        "has_signature": True,
        "expected_content": "회의 일정 공유드립니다",
        "description": "Korean thanks variant + name",
    },
    {
        "body": "첨부 파일 확인 부탁드립니다.\n\n좋은 하루 보내세요.\n박민수 드림",
        "has_signature": True,
        "expected_content": "첨부 파일 확인 부탁드립니다",
        "description": "Korean greeting signature",
    },
    {
        "body": "보고서를 전달드립니다.\n\n고맙습니다.",
        "has_signature": True,
        "expected_content": "보고서를 전달드립니다",
        "description": "Korean closing without name",
    },
    {
        "body": "다음 주 일정입니다.\n\n---\n정수진 부장\n영업본부",
        "has_signature": True,
        "expected_content": "다음 주 일정입니다",
        "description": "Korean contact block with separator",
    },
    {
        "body": "제안서를 첨부합니다.\n\n수고하세요.",
        "has_signature": True,
        "expected_content": "제안서를 첨부합니다",
        "description": "Korean informal closing",
    },
    {
        "body": "회의록을 공유합니다.\n\n감사합니다\n최지훈 올림",
        "has_signature": True,
        "expected_content": "회의록을 공유합니다",
        "description": "Korean without period in closing",
    },
    {
        "body": "단순한 메시지입니다. 서명이 없습니다.",
        "has_signature": False,
        "expected_content": "단순한 메시지입니다. 서명이 없습니다.",
        "description": "Korean without signature",
    },
    # English signatures (12 samples)
    {
        "body": "Hi team,\n\nPlease review the attached proposal.\n\nBest regards,\nJohn Smith",
        "has_signature": True,
        "expected_content": "Please review the attached proposal",
        "description": "English formal closing",
    },
    {
        "body": "Hello,\n\nThe report is ready for your review.\n\nSincerely,\nSarah Johnson",
        "has_signature": True,
        "expected_content": "The report is ready for your review",
        "description": "English sincerely closing",
    },
    {
        "body": "Quick update on the project status.\n\nThanks,\nMike",
        "has_signature": True,
        "expected_content": "Quick update on the project status",
        "description": "English informal thanks",
    },
    {
        "body": "Meeting rescheduled to Tuesday.\n\nCheers,\nEmma",
        "has_signature": True,
        "expected_content": "Meeting rescheduled to Tuesday",
        "description": "English casual cheers",
    },
    {
        "body": "Attached is the quarterly report.\n\nKind regards,\nDavid Chen",
        "has_signature": True,
        "expected_content": "Attached is the quarterly report",
        "description": "English kind regards",
    },
    {
        "body": "Please find the updated timeline.\n\n---\nLisa Park\nDirector of Operations",
        "has_signature": True,
        "expected_content": "Please find the updated timeline",
        "description": "English contact block",
    },
    {
        "body": "Project kickoff is next Monday.\n\nRegards,\nTom Wilson",
        "has_signature": True,
        "expected_content": "Project kickoff is next Monday",
        "description": "English simple regards",
    },
    {
        "body": "Budget approved for Q4.\n\nBest,\nAnna",
        "has_signature": True,
        "expected_content": "Budget approved for Q4",
        "description": "English short best",
    },
    {
        "body": "Contract has been signed.\n\n---\nJames Lee\nPhone: 555-1234\nEmail: james@company.com",
        "has_signature": True,
        "expected_content": "Contract has been signed",
        "description": "English full contact block",
    },
    {
        "body": "New policy effective immediately.\n\nYours sincerely,\nRobert Brown",
        "has_signature": True,
        "expected_content": "New policy effective immediately",
        "description": "English yours sincerely",
    },
    {
        "body": "Please confirm receipt.\n\nThank you,\nJennifer",
        "has_signature": True,
        "expected_content": "Please confirm receipt",
        "description": "English thank you closing",
    },
    {
        "body": "This is a simple message without any signature at all.",
        "has_signature": False,
        "expected_content": "This is a simple message without any signature at all.",
        "description": "English without signature",
    },
    # Mixed/Edge cases (2 samples)
    {
        "body": "Update: Project on track.\n\nThanks for your patience.\n\nBest regards,\nAlex",
        "has_signature": True,
        "expected_content": "Thanks for your patience",
        "description": "Multiple paragraphs before signature",
    },
    {
        "body": "FYI",
        "has_signature": False,
        "expected_content": "FYI",
        "description": "Very short message",
    },
]


@pytest.fixture
def normalizer():
    """Create ContentNormalizer instance for accuracy testing."""
    return ContentNormalizer()


def test_signature_removal_accuracy_95_percent(normalizer):
    """
    T060: Test signature removal achieves 95%+ accuracy (SC-002).

    Success criteria:
    - For emails WITH signatures: Signature must be removed AND main content preserved
    - For emails WITHOUT signatures: Content must remain unchanged
    - Overall accuracy: >= 95% (19/20 or better)

    This test uses the comprehensive 22-email dataset covering:
    - Korean patterns (8 samples)
    - English patterns (12 samples)
    - Edge cases (2 samples)
    """
    total_tests = len(ACCURACY_TEST_DATASET)
    successful_removals = 0
    failed_cases = []

    for i, test_case in enumerate(ACCURACY_TEST_DATASET):
        body = test_case["body"]
        has_signature = test_case["has_signature"]
        expected_content = test_case["expected_content"]
        description = test_case["description"]

        # Perform signature removal
        cleaned_body = normalizer.remove_signature(body)

        # Check if removal was successful
        success = False

        if has_signature:
            # For emails with signatures:
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
                        "cleaned_body": cleaned_body,
                    }
                )
        else:
            # For emails without signatures:
            # Content should remain exactly the same
            success = cleaned_body == body

            if not success:
                failed_cases.append(
                    {
                        "index": i,
                        "description": description,
                        "reason": "Content was modified when it shouldn't be",
                        "original": body,
                        "cleaned": cleaned_body,
                    }
                )

        if success:
            successful_removals += 1

    # Calculate accuracy
    accuracy = (successful_removals / total_tests) * 100

    # Print detailed results
    print(f"\n{'=' * 70}")
    print(f"SIGNATURE REMOVAL ACCURACY TEST RESULTS")
    print(f"{'=' * 70}")
    print(f"Total test cases: {total_tests}")
    print(f"Successful: {successful_removals}")
    print(f"Failed: {len(failed_cases)}")
    print(f"Accuracy: {accuracy:.1f}%")
    print(f"Target: 95.0%")
    print(f"Status: {'✓ PASS' if accuracy >= 95.0 else '✗ FAIL'}")
    print(f"{'=' * 70}")

    # Print failed cases for debugging
    if failed_cases:
        print(f"\nFailed test cases ({len(failed_cases)}):")
        for case in failed_cases:
            print(f"\n  [{case['index']}] {case['description']}")
            print(f"      Reason: {case['reason']}")
            if "cleaned_body" in case:
                print(f"      Expected content: {case['expected_content'][:50]}...")
                print(f"      Cleaned body: {case['cleaned_body'][:100]}...")

    # Assert 95%+ accuracy
    assert accuracy >= 95.0, (
        f"Signature removal accuracy {accuracy:.1f}% is below 95% target. "
        f"Failed {len(failed_cases)}/{total_tests} cases. See output for details."
    )


def test_dataset_quality():
    """
    Verify the accuracy test dataset meets requirements.

    Requirements:
    - At least 20 test cases (T061)
    - Mix of Korean and English
    - Mix of signatures present and absent
    - Representative of real-world patterns
    """
    total_cases = len(ACCURACY_TEST_DATASET)
    with_signature = sum(1 for case in ACCURACY_TEST_DATASET if case["has_signature"])
    without_signature = total_cases - with_signature

    korean_cases = sum(
        1
        for case in ACCURACY_TEST_DATASET
        if any(
            ord(c) >= 0xAC00 and ord(c) <= 0xD7A3  # Korean Hangul range
            for c in case["body"]
        )
    )
    english_cases = total_cases - korean_cases

    print(f"\nDataset composition:")
    print(f"  Total cases: {total_cases}")
    print(f"  With signature: {with_signature}")
    print(f"  Without signature: {without_signature}")
    print(f"  Korean: {korean_cases}")
    print(f"  English: {english_cases}")

    # Assert dataset quality
    assert total_cases >= 20, (
        f"Dataset should have at least 20 cases, got {total_cases}"
    )
    assert with_signature > 0, "Dataset should include cases with signatures"
    assert without_signature > 0, "Dataset should include cases without signatures"
    assert korean_cases > 0, "Dataset should include Korean cases"
    assert english_cases > 0, "Dataset should include English cases"


def test_individual_pattern_coverage():
    """
    Test that each major pattern type is covered in the dataset.

    Pattern types:
    - Korean: thanks_name, greeting_signature, closing_only, contact_block
    - English: formal_closing, informal_closing, contact_block
    - Edge cases: no signature, very short
    """
    pattern_coverage = {
        "korean_thanks_name": 0,
        "korean_greeting": 0,
        "korean_closing_only": 0,
        "korean_contact_block": 0,
        "english_formal": 0,
        "english_informal": 0,
        "english_contact_block": 0,
        "no_signature": 0,
    }

    for case in ACCURACY_TEST_DATASET:
        desc = case["description"].lower()
        if "korean" in desc:
            if "thanks" in desc or "name" in desc:
                pattern_coverage["korean_thanks_name"] += 1
            if "greeting" in desc:
                pattern_coverage["korean_greeting"] += 1
            if "closing without" in desc or "informal closing" in desc:
                pattern_coverage["korean_closing_only"] += 1
            if "contact block" in desc:
                pattern_coverage["korean_contact_block"] += 1
        if "english" in desc:
            if "formal" in desc or "sincerely" in desc or "regards" in desc:
                pattern_coverage["english_formal"] += 1
            if "informal" in desc or "thanks" in desc or "cheers" in desc:
                pattern_coverage["english_informal"] += 1
            if "contact block" in desc:
                pattern_coverage["english_contact_block"] += 1
        if not case["has_signature"]:
            pattern_coverage["no_signature"] += 1

    print(f"\nPattern coverage:")
    for pattern, count in pattern_coverage.items():
        print(f"  {pattern}: {count}")

    # All major patterns should be covered
    for pattern, count in pattern_coverage.items():
        assert count > 0, f"Pattern '{pattern}' is not covered in dataset"
