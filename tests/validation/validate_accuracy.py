#!/usr/bin/env python3
"""Validate entity extraction accuracy against ground truth.

This script:
1. Reads ground truth from tests/fixtures/ground_truth/GROUND_TRUTH.md
2. Runs CLI extraction on each test email
3. Compares results against expected values
4. Calculates accuracy metrics (SC-001, SC-002, SC-003)
5. Generates accuracy report

Usage:
    uv run python tests/validation/validate_accuracy.py
    uv run python tests/validation/validate_accuracy.py --verbose
    uv run python tests/validation/validate_accuracy.py --output report.md
"""

import argparse
import json
import logging
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# Ground truth data (parsed from GROUND_TRUTH.md)
GROUND_TRUTH = {
    "korean_001.txt": {
        "person_in_charge": "김철수",
        "startup_name": "본봄",
        "partner_org": "신세계인터내셔널",
        "details_keywords": ["파일럿", "킥오프", "테이블 예약", "PoC", "11월"],
        "date": "2025-11-01",
        "date_tolerance_days": 7,  # First week of November
    },
    "korean_002.txt": {
        "person_in_charge": "이영희",
        "startup_name": "TableManager",
        "partner_org": "신세계푸드",
        "details_keywords": ["레스토랑", "예약 시스템", "협의", "파일럿", "11월"],
        "date": "2025-10-27",
        "date_tolerance_days": 1,
    },
    "english_001.txt": {
        "person_in_charge": "John Kim",
        "startup_name": "TableManager",
        "partner_org": "Shinsegae Food",
        "details_keywords": ["pilot", "kickoff", "restaurant", "reservation", "trial"],
        "date": "2025-10-31",  # Yesterday relative to 2025-11-01
        "date_tolerance_days": 1,
    },
    "english_002.txt": {
        "person_in_charge": None,  # Missing in email
        "startup_name": "BonBom",
        "partner_org": "Shinsegae International",
        "details_keywords": ["kickoff", "PoC", "November", "table reservation"],
        "date": "2025-11-01",
        "date_tolerance_days": 7,  # First week of November
    },
}


def run_cli_extraction(email_file: Path) -> Optional[Dict[str, Any]]:
    """Run CLI extraction on email file.

    Args:
        email_file: Path to email file

    Returns:
        dict: Extracted entities (parsed JSON), or None if extraction failed
    """
    try:
        result = subprocess.run(
            [sys.executable, "src/cli/extract_entities.py", "--email", str(email_file)],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            logger.error(f"CLI extraction failed for {email_file.name}: {result.stderr}")
            return None

        # Parse JSON output
        return json.loads(result.stdout)

    except subprocess.TimeoutExpired:
        logger.error(f"CLI extraction timeout for {email_file.name}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON output for {email_file.name}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error extracting {email_file.name}: {e}")
        return None


def compare_exact_field(
    actual: Optional[str], expected: Optional[str], field_name: str
) -> Tuple[bool, str]:
    """Compare exact match fields (person, startup, partner).

    Args:
        actual: Actual extracted value
        expected: Expected value from ground truth
        field_name: Field name for logging

    Returns:
        tuple: (is_correct, reason)
    """
    # Handle None cases
    if expected is None and actual is None:
        return True, "Both null (correct)"
    if expected is None and actual is not None:
        return False, f"Expected null, got '{actual}'"
    if expected is not None and actual is None:
        return False, f"Expected '{expected}', got null"

    # Exact match
    if actual == expected:
        return True, "Exact match"
    else:
        return False, f"Expected '{expected}', got '{actual}'"


def compare_details_field(actual: Optional[str], keywords: List[str]) -> Tuple[bool, str, int]:
    """Compare details field using keyword matching.

    Args:
        actual: Actual extracted details
        keywords: List of expected keywords

    Returns:
        tuple: (is_correct, reason, num_matched_keywords)
    """
    if not actual:
        return False, "Details field is null", 0

    # Count matched keywords (case-insensitive)
    actual_lower = actual.lower()
    matched = sum(1 for kw in keywords if kw.lower() in actual_lower)

    # Consider correct if ≥60% keywords matched
    threshold = len(keywords) * 0.6
    is_correct = matched >= threshold

    reason = f"Matched {matched}/{len(keywords)} keywords ({matched/len(keywords)*100:.0f}%)"
    return is_correct, reason, matched


def compare_date_field(
    actual: Optional[str], expected: str, tolerance_days: int
) -> Tuple[bool, str]:
    """Compare date field with tolerance.

    Args:
        actual: Actual extracted date (ISO format string)
        expected: Expected date (ISO format string)
        tolerance_days: Tolerance in days

    Returns:
        tuple: (is_correct, reason)
    """
    if not actual:
        return False, "Date field is null"

    try:
        # Parse dates
        actual_date = datetime.fromisoformat(actual.replace("Z", "+00:00"))
        expected_date = datetime.fromisoformat(expected)

        # Calculate difference
        diff_days = abs((actual_date - expected_date).days)

        is_correct = diff_days <= tolerance_days
        reason = f"Date diff: {diff_days} days (tolerance: ±{tolerance_days} days)"

        return is_correct, reason

    except (ValueError, TypeError) as e:
        return False, f"Date parsing error: {e}"


def validate_single_email(
    email_file: Path, ground_truth: Dict[str, Any]
) -> Dict[str, Any]:
    """Validate extraction for a single email.

    Args:
        email_file: Path to email file
        ground_truth: Expected extraction results

    Returns:
        dict: Validation results with scores and details
    """
    logger.info(f"Validating {email_file.name}...")

    # Run extraction
    extracted = run_cli_extraction(email_file)
    if extracted is None:
        return {
            "email": email_file.name,
            "status": "FAILED",
            "error": "CLI extraction failed",
            "score": 0.0,
            "total_fields": 5,
            "correct_fields": 0,
        }

    # Compare each field
    results = {}
    correct_count = 0

    # 1. Person in charge
    person_correct, person_reason = compare_exact_field(
        extracted.get("person_in_charge"),
        ground_truth.get("person_in_charge"),
        "person_in_charge",
    )
    results["person_in_charge"] = {
        "correct": person_correct,
        "reason": person_reason,
        "actual": extracted.get("person_in_charge"),
        "expected": ground_truth.get("person_in_charge"),
    }
    if person_correct:
        correct_count += 1

    # 2. Startup name
    startup_correct, startup_reason = compare_exact_field(
        extracted.get("startup_name"),
        ground_truth.get("startup_name"),
        "startup_name",
    )
    results["startup_name"] = {
        "correct": startup_correct,
        "reason": startup_reason,
        "actual": extracted.get("startup_name"),
        "expected": ground_truth.get("startup_name"),
    }
    if startup_correct:
        correct_count += 1

    # 3. Partner org
    partner_correct, partner_reason = compare_exact_field(
        extracted.get("partner_org"),
        ground_truth.get("partner_org"),
        "partner_org",
    )
    results["partner_org"] = {
        "correct": partner_correct,
        "reason": partner_reason,
        "actual": extracted.get("partner_org"),
        "expected": ground_truth.get("partner_org"),
    }
    if partner_correct:
        correct_count += 1

    # 4. Details (keyword matching)
    details_correct, details_reason, matched_kw = compare_details_field(
        extracted.get("details"), ground_truth.get("details_keywords", [])
    )
    results["details"] = {
        "correct": details_correct,
        "reason": details_reason,
        "actual": extracted.get("details"),
        "expected_keywords": ground_truth.get("details_keywords", []),
        "matched_keywords": matched_kw,
    }
    if details_correct:
        correct_count += 1

    # 5. Date
    date_correct, date_reason = compare_date_field(
        extracted.get("date"),
        ground_truth.get("date"),
        ground_truth.get("date_tolerance_days", 1),
    )
    results["date"] = {
        "correct": date_correct,
        "reason": date_reason,
        "actual": extracted.get("date"),
        "expected": ground_truth.get("date"),
    }
    if date_correct:
        correct_count += 1

    # Calculate score
    score = (correct_count / 5) * 100

    # Check confidence scores
    confidence = extracted.get("confidence", {})
    low_confidence_fields = []
    for field in ["person", "startup", "partner", "details", "date"]:
        if confidence.get(field, 0.0) < 0.85:
            low_confidence_fields.append(field)

    return {
        "email": email_file.name,
        "status": "PASSED" if score >= 85 else "FAILED",
        "score": score,
        "total_fields": 5,
        "correct_fields": correct_count,
        "field_results": results,
        "confidence": confidence,
        "low_confidence_fields": low_confidence_fields,
    }


def generate_report(
    results: List[Dict[str, Any]], output_file: Optional[Path] = None
) -> str:
    """Generate accuracy validation report.

    Args:
        results: List of validation results
        output_file: Optional output file path

    Returns:
        str: Report content
    """
    # Separate Korean and English results
    korean_results = [r for r in results if r["email"].startswith("korean_")]
    english_results = [r for r in results if r["email"].startswith("english_")]

    # Calculate overall metrics
    total_correct = sum(r["correct_fields"] for r in results)
    total_fields = sum(r["total_fields"] for r in results)
    overall_accuracy = (total_correct / total_fields * 100) if total_fields > 0 else 0

    korean_correct = sum(r["correct_fields"] for r in korean_results)
    korean_fields = sum(r["total_fields"] for r in korean_results)
    korean_accuracy = (korean_correct / korean_fields * 100) if korean_fields > 0 else 0

    english_correct = sum(r["correct_fields"] for r in english_results)
    english_fields = sum(r["total_fields"] for r in english_results)
    english_accuracy = (
        (english_correct / english_fields * 100) if english_fields > 0 else 0
    )

    # Build report
    report_lines = [
        "# Entity Extraction Accuracy Validation Report",
        "",
        f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Test Dataset**: {len(results)} emails ({len(korean_results)} Korean, {len(english_results)} English)",
        "",
        "## Summary",
        "",
        f"- **Overall Accuracy**: {overall_accuracy:.1f}% ({total_correct}/{total_fields} fields correct)",
        f"- **Korean Accuracy (SC-001)**: {korean_accuracy:.1f}% ({korean_correct}/{korean_fields} fields) - Target: ≥85%",
        f"- **English Accuracy (SC-002)**: {english_accuracy:.1f}% ({english_correct}/{english_fields} fields) - Target: ≥85%",
        "",
        "### Success Criteria",
        "",
        f"- {'✅' if korean_accuracy >= 85 else '❌'} **SC-001**: Korean email accuracy ≥85% ({korean_accuracy:.1f}%)",
        f"- {'✅' if english_accuracy >= 85 else '❌'} **SC-002**: English email accuracy ≥85% ({english_accuracy:.1f}%)",
        "",
        "## Detailed Results",
        "",
    ]

    # Add detailed results for each email
    for result in results:
        status_icon = "✅" if result["status"] == "PASSED" else "❌"
        report_lines.extend(
            [
                f"### {status_icon} {result['email']} - {result['score']:.1f}%",
                "",
                f"**Score**: {result['correct_fields']}/{result['total_fields']} fields correct ({result['score']:.1f}%)",
                "",
            ]
        )

        if result.get("error"):
            report_lines.extend([f"**Error**: {result['error']}", ""])
            continue

        # Field-by-field breakdown
        field_results = result.get("field_results", {})
        for field_name, field_data in field_results.items():
            field_icon = "✅" if field_data["correct"] else "❌"
            report_lines.append(f"- {field_icon} **{field_name}**: {field_data['reason']}")

            if not field_data["correct"]:
                report_lines.append(
                    f"  - Expected: `{field_data.get('expected', 'N/A')}`"
                )
                report_lines.append(f"  - Actual: `{field_data.get('actual', 'N/A')}`")

        # Confidence warnings
        low_conf = result.get("low_confidence_fields", [])
        if low_conf:
            report_lines.extend(
                [
                    "",
                    f"⚠️  **Low Confidence**: {', '.join(low_conf)}",
                ]
            )

        report_lines.append("")

    # Add recommendations
    report_lines.extend(
        [
            "## Recommendations",
            "",
        ]
    )

    if korean_accuracy < 85:
        report_lines.append(
            f"- ⚠️  Korean accuracy ({korean_accuracy:.1f}%) is below target (85%). Consider improving few-shot examples for Korean emails."
        )
    if english_accuracy < 85:
        report_lines.append(
            f"- ⚠️  English accuracy ({english_accuracy:.1f}%) is below target (85%). Consider improving few-shot examples for English emails."
        )
    if overall_accuracy >= 85:
        report_lines.append("- ✅ Overall accuracy meets target. System is ready for MVP.")

    # Check if we have enough test emails
    if len(results) < 30:
        report_lines.append(
            f"- 📝 Only {len(results)} test emails available. Target is 30 emails (20 Korean + 10 English) for comprehensive validation."
        )

    report_lines.append("")

    report_content = "\n".join(report_lines)

    # Save to file if requested
    if output_file:
        output_file.write_text(report_content, encoding="utf-8")
        logger.info(f"Report saved to: {output_file}")

    return report_content


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate entity extraction accuracy against ground truth"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Output report file (default: print to stdout)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Find test email files
    fixtures_dir = Path("tests/fixtures/sample_emails")
    test_emails = sorted(
        [
            f
            for f in fixtures_dir.glob("*.txt")
            if f.name in GROUND_TRUTH and f.name.startswith(("korean_", "english_"))
        ]
    )

    if not test_emails:
        logger.error("No test emails found in tests/fixtures/sample_emails/")
        return 1

    logger.info(f"Found {len(test_emails)} test emails with ground truth")

    # Validate each email
    results = []
    for email_file in test_emails:
        ground_truth = GROUND_TRUTH.get(email_file.name)
        if ground_truth:
            result = validate_single_email(email_file, ground_truth)
            results.append(result)
        else:
            logger.warning(f"No ground truth for {email_file.name}, skipping")

    # Generate report
    report = generate_report(results, args.output)

    if not args.output:
        print(report)

    # Exit code based on overall pass/fail
    failed_count = sum(1 for r in results if r["status"] == "FAILED")
    if failed_count > 0:
        logger.warning(f"Validation completed with {failed_count} failures")
        return 1
    else:
        logger.info("✅ All validations passed!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
