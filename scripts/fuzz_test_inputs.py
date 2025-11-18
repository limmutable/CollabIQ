#!/usr/bin/env python3
"""Fuzz test execution script for CollabIQ system.

This script executes comprehensive fuzz testing campaigns against system components:
- Date parser fuzzing
- Email extraction fuzzing
- API integration fuzzing
- End-to-end pipeline fuzzing

Usage:
    python scripts/fuzz_test_inputs.py --target date_parser --count 100
    python scripts/fuzz_test_inputs.py --target llm_adapter --count 50
    python scripts/fuzz_test_inputs.py --target all --count 20
    python scripts/fuzz_test_inputs.py --generate-report
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, UTC
from typing import Dict, List, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from collabiq.test_utils.fuzz_generator import (
    FuzzConfig,
    generate_fuzz_emails,
    generate_fuzz_extraction_results,
    generate_fuzz_date_strings,
)
from collabiq.date_parser import parse_date


class FuzzTestRunner:
    """Runner for fuzz test campaigns."""

    def __init__(self, output_dir: Path = None):
        """Initialize fuzz test runner.

        Args:
            output_dir: Directory for test results
        """
        self.output_dir = output_dir or Path("data/test_metrics/fuzz_results")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.results = {
            "timestamp": datetime.now(UTC).isoformat(),
            "campaigns": [],
        }

    def run_date_parser_fuzzing(self, count: int = 100) -> Dict[str, Any]:
        """Run fuzz tests against date parser.

        Args:
            count: Number of fuzz inputs to generate

        Returns:
            Campaign results
        """
        print(f"Running date parser fuzzing ({count} inputs)...")

        config = FuzzConfig(seed=12345, include_valid=True, valid_ratio=0.1)
        results = {
            "target": "date_parser",
            "count": count,
            "successes": 0,
            "errors": 0,
            "crashes": 0,
            "error_types": {},
        }

        for i, date_str in enumerate(generate_fuzz_date_strings(count, config)):
            try:
                result = parse_date(date_str)
                if result is not None:
                    results["successes"] += 1
                else:
                    results["errors"] += 1
            except Exception as e:
                error_type = type(e).__name__
                results["errors"] += 1
                results["error_types"][error_type] = (
                    results["error_types"].get(error_type, 0) + 1
                )

            if (i + 1) % 10 == 0:
                print(f"  Progress: {i + 1}/{count}")

        success_rate = results["successes"] / count
        print(f"  Results: {results['successes']}/{count} success ({success_rate:.1%})")
        print(f"  Errors: {results['errors']}, Crashes: {results['crashes']}")

        return results

    def run_email_extraction_fuzzing(self, count: int = 50) -> Dict[str, Any]:
        """Run fuzz tests against email extraction.

        Args:
            count: Number of fuzz inputs to generate

        Returns:
            Campaign results
        """
        print(f"Running email extraction fuzzing ({count} inputs)...")

        config = FuzzConfig(seed=23456, include_valid=True, valid_ratio=0.1)
        results = {
            "target": "email_extraction",
            "count": count,
            "successes": 0,
            "errors": 0,
            "crashes": 0,
            "error_types": {},
        }

        try:
            from llm_adapters.gemini_adapter import GeminiAdapter

            adapter = GeminiAdapter()
        except Exception as e:
            print(f"  Could not initialize adapter: {e}")
            return results

        for i, email_text in enumerate(generate_fuzz_emails(count, config)):
            try:
                result = adapter.extract_entities(email_text)
                if result and isinstance(result, dict):
                    results["successes"] += 1
                else:
                    results["errors"] += 1
            except Exception as e:
                error_type = type(e).__name__
                results["errors"] += 1
                results["error_types"][error_type] = (
                    results["error_types"].get(error_type, 0) + 1
                )

            if (i + 1) % 5 == 0:
                print(f"  Progress: {i + 1}/{count}")

        success_rate = results["successes"] / count if count > 0 else 0
        print(f"  Results: {results['successes']}/{count} success ({success_rate:.1%})")
        print(f"  Errors: {results['errors']}, Crashes: {results['crashes']}")

        return results

    def run_extraction_result_fuzzing(self, count: int = 50) -> Dict[str, Any]:
        """Run fuzz tests against extraction result validation.

        Args:
            count: Number of fuzz inputs to generate

        Returns:
            Campaign results
        """
        print(f"Running extraction result fuzzing ({count} inputs)...")

        config = FuzzConfig(seed=34567, include_valid=True, valid_ratio=0.1)
        results = {
            "target": "extraction_validation",
            "count": count,
            "successes": 0,
            "errors": 0,
            "crashes": 0,
            "error_types": {},
        }

        for i, extraction in enumerate(generate_fuzz_extraction_results(count, config)):
            try:
                # Validate extraction structure
                if isinstance(extraction, dict):
                    # Check for expected fields
                    has_fields = any(
                        field in extraction
                        for field in [
                            "startup_name",
                            "person_in_charge",
                            "partner_org",
                            "details",
                            "date",
                        ]
                    )
                    if has_fields:
                        results["successes"] += 1
                    else:
                        results["errors"] += 1
                else:
                    results["errors"] += 1
            except Exception as e:
                error_type = type(e).__name__
                results["errors"] += 1
                results["error_types"][error_type] = (
                    results["error_types"].get(error_type, 0) + 1
                )

            if (i + 1) % 10 == 0:
                print(f"  Progress: {i + 1}/{count}")

        success_rate = results["successes"] / count
        print(f"  Results: {results['successes']}/{count} success ({success_rate:.1%})")
        print(f"  Errors: {results['errors']}, Crashes: {results['crashes']}")

        return results

    def run_all_campaigns(self, count: int = 20) -> List[Dict[str, Any]]:
        """Run all fuzz test campaigns.

        Args:
            count: Number of inputs per campaign

        Returns:
            List of campaign results
        """
        campaigns = [
            ("date_parser", self.run_date_parser_fuzzing),
            ("extraction_validation", self.run_extraction_result_fuzzing),
            # Email extraction requires API keys, skip by default
            # ("email_extraction", self.run_email_extraction_fuzzing),
        ]

        all_results = []

        for name, runner in campaigns:
            print(f"\n{'=' * 60}")
            print(f"Campaign: {name}")
            print(f"{'=' * 60}")

            result = runner(count)
            all_results.append(result)
            self.results["campaigns"].append(result)

        return all_results

    def generate_report(self) -> str:
        """Generate fuzz testing report.

        Returns:
            Markdown-formatted report
        """
        lines = [
            "# Fuzz Testing Report",
            "",
            f"**Timestamp**: {self.results['timestamp']}",
            "",
            "## Campaign Results",
            "",
        ]

        for campaign in self.results["campaigns"]:
            lines.extend(
                [
                    f"### {campaign['target']}",
                    "",
                    f"- **Total Inputs**: {campaign['count']}",
                    f"- **Successes**: {campaign['successes']}",
                    f"- **Errors**: {campaign['errors']}",
                    f"- **Crashes**: {campaign['crashes']}",
                    f"- **Success Rate**: {campaign['successes'] / campaign['count']:.1%}",
                    "",
                ]
            )

            if campaign["error_types"]:
                lines.append("**Error Types**:")
                for error_type, count in campaign["error_types"].items():
                    lines.append(f"- {error_type}: {count}")
                lines.append("")

        lines.extend(
            [
                "## Summary",
                "",
                f"- **Total Campaigns**: {len(self.results['campaigns'])}",
                f"- **Total Inputs Tested**: {sum(c['count'] for c in self.results['campaigns'])}",
                f"- **Total Successes**: {sum(c['successes'] for c in self.results['campaigns'])}",
                f"- **Total Errors**: {sum(c['errors'] for c in self.results['campaigns'])}",
                "",
            ]
        )

        return "\n".join(lines)

    def save_results(self):
        """Save fuzz test results to JSON file."""
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        output_path = self.output_dir / f"fuzz_results_{timestamp}.json"

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        print(f"\nResults saved to: {output_path}")

    def save_report(self):
        """Save fuzz test report to markdown file."""
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        report_path = self.output_dir / f"fuzz_report_{timestamp}.md"

        report = self.generate_report()

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)

        print(f"Report saved to: {report_path}")


def main():
    """Main entry point for fuzz test script."""
    parser = argparse.ArgumentParser(
        description="Execute fuzz tests against CollabIQ system"
    )
    parser.add_argument(
        "--target",
        choices=["date_parser", "email_extraction", "extraction_validation", "all"],
        default="all",
        help="Target component for fuzzing",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=20,
        help="Number of fuzz inputs to generate per campaign",
    )
    parser.add_argument(
        "--generate-report",
        action="store_true",
        help="Generate and save report only (no fuzzing)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory for results",
    )

    args = parser.parse_args()

    runner = FuzzTestRunner(output_dir=args.output_dir)

    if args.generate_report:
        # Load most recent results and generate report
        print("Generating report from most recent results...")
        # Implementation would load from JSON
        print("Report generation not yet implemented")
        return

    print("=" * 60)
    print("CollabIQ Fuzz Testing Campaign")
    print("=" * 60)
    print(f"Target: {args.target}")
    print(f"Count: {args.count}")
    print(f"Output: {runner.output_dir}")
    print("=" * 60)
    print()

    # Run selected campaign(s)
    if args.target == "all":
        runner.run_all_campaigns(args.count)
    elif args.target == "date_parser":
        result = runner.run_date_parser_fuzzing(args.count)
        runner.results["campaigns"].append(result)
    elif args.target == "email_extraction":
        result = runner.run_email_extraction_fuzzing(args.count)
        runner.results["campaigns"].append(result)
    elif args.target == "extraction_validation":
        result = runner.run_extraction_result_fuzzing(args.count)
        runner.results["campaigns"].append(result)

    # Save results
    print()
    runner.save_results()
    runner.save_report()

    # Print summary report
    print()
    print(runner.generate_report())


if __name__ == "__main__":
    main()
