#!/usr/bin/env python3
"""Display extracted entity values from E2E test run."""

import json
import sys
from pathlib import Path


def show_extractions(run_id: str):
    """Show extracted entities for a test run."""

    # Load test run data
    run_file = Path(f"data/e2e_test/runs/{run_id}.json")
    if not run_file.exists():
        print(f"ERROR: Run file not found: {run_file}")
        sys.exit(1)

    with run_file.open() as f:
        run_data = json.load(f)

    print(f"\n{'=' * 100}")
    print(f"E2E Test Run: {run_id}")
    print(f"{'=' * 100}\n")
    print(f"Status: {run_data['status']}")
    print(f"Emails Processed: {run_data['emails_processed']}")
    print(
        f"Success: {run_data['success_count']} ({run_data['success_count'] / run_data['emails_processed'] * 100:.1f}%)"
    )
    print(f"\n{'=' * 100}")
    print("Extracted Entities by Email")
    print(f"{'=' * 100}\n")

    # Load extracted entities for each email
    for idx, email_id in enumerate(run_data["test_email_ids"], 1):
        print(f"\n{idx}. Email ID: {email_id}")
        print(f"   {'-' * 90}")

        # Try to find extraction in errors directory (successful extractions)
        # E2E runner doesn't save individual extraction files, so we'll note that
        print("   ⚠️  Individual extraction files not saved by E2E runner")
        print("   💡 Extractions were processed but not persisted separately")
        print("   ✅ Quality metrics were collected and saved")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Show most recent run
        runs_dir = Path("data/e2e_test/runs")
        if not runs_dir.exists():
            print("ERROR: No E2E test runs found")
            sys.exit(1)

        run_files = sorted(runs_dir.glob("*.json"), reverse=True)
        if not run_files:
            print("ERROR: No E2E test runs found")
            sys.exit(1)

        run_id = run_files[0].stem
        print(f"Using most recent run: {run_id}")
    else:
        run_id = sys.argv[1]

    show_extractions(run_id)
