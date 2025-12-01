#!/usr/bin/env python3
"""Generate markdown report of extracted entities from E2E test run."""

import json
import sys
from pathlib import Path


def generate_report(run_id: str):
    """Generate extraction report for a test run.

    Args:
        run_id: Test run ID
    """
    extractions_dir = Path(f"data/e2e_test/extractions/{run_id}")

    if not extractions_dir.exists():
        print(f"ERROR: Extractions directory not found: {extractions_dir}")
        sys.exit(1)

    extraction_files = sorted(extractions_dir.glob("*.json"))

    if not extraction_files:
        print(f"ERROR: No extraction files found in {extractions_dir}")
        sys.exit(1)

    print(f"\n{'=' * 120}")
    print(f"E2E Test Extraction Report - Run ID: {run_id}")
    print(f"{'=' * 120}\n")
    print(f"Total Emails Processed: {len(extraction_files)}\n")

    for idx, extraction_file in enumerate(extraction_files, 1):
        with extraction_file.open() as f:
            data = json.load(f)

        email_id = extraction_file.stem

        print(f"\n{'-' * 120}")
        print(f"Email {idx}/{len(extraction_files)}: {email_id}")
        print(f"{'-' * 120}\n")

        # Display extracted fields
        print(f"{'Field':<20} {'Value':<60} {'Confidence':<15}")
        print(f"{'-' * 95}")

        fields = [
            (
                "Person in Charge",
                data.get("person_in_charge", "N/A"),
                data["confidence"]["person"],
            ),
            (
                "Startup Name",
                data.get("startup_name", "N/A"),
                data["confidence"]["startup"],
            ),
            (
                "Partner Org",
                data.get("partner_org", "N/A"),
                data["confidence"]["partner"],
            ),
            ("Date", data.get("date", "N/A"), data["confidence"]["date"]),
        ]

        for field_name, value, confidence in fields:
            # Truncate long values
            display_value = value[:55] + "..." if len(value) > 55 else value
            conf_display = f"{confidence:.1%}"
            print(f"{field_name:<20} {display_value:<60} {conf_display:<15}")

        # Details on separate line (can be long)
        details = data.get("details", "N/A")
        details_conf = data["confidence"]["details"]
        print(f"\n{'Details':<20} (Confidence: {details_conf:.1%})")
        print(f"  {details}")

        # Provider info
        provider = data.get("provider_name", "unknown")
        print(f"\n{'Provider':<20} {provider}")

        # Average confidence
        avg_conf = sum(data["confidence"].values()) / len(data["confidence"])
        print(f"{'Avg Confidence':<20} {avg_conf:.1%}")

    # Summary statistics
    print(f"\n{'=' * 120}")
    print("Summary Statistics")
    print(f"{'=' * 120}\n")

    all_data = []
    for extraction_file in extraction_files:
        with extraction_file.open() as f:
            all_data.append(json.load(f))

    # Count providers
    provider_counts = {}
    for data in all_data:
        provider = data.get("provider_name", "unknown")
        provider_counts[provider] = provider_counts.get(provider, 0) + 1

    print("Emails Processed by Provider:")
    for provider, count in sorted(
        provider_counts.items(), key=lambda x: x[1], reverse=True
    ):
        print(f"  {provider}: {count}")

    # Average confidence by field
    print("\nAverage Confidence by Field:")
    field_confidences = {
        "person": [],
        "startup": [],
        "partner": [],
        "details": [],
        "date": [],
    }

    for data in all_data:
        for field, conf_list in field_confidences.items():
            conf_list.append(data["confidence"][field])

    for field, conf_list in field_confidences.items():
        avg = sum(conf_list) / len(conf_list) if conf_list else 0
        print(f"  {field.capitalize()}: {avg:.1%}")

    # Overall average
    all_confidences = []
    for data in all_data:
        all_confidences.extend(data["confidence"].values())

    overall_avg = sum(all_confidences) / len(all_confidences) if all_confidences else 0
    print(f"\nOverall Average Confidence: {overall_avg:.1%}")

    print(f"\n{'=' * 120}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Use most recent run
        runs_dir = Path("data/e2e_test/extractions")
        if not runs_dir.exists():
            print("ERROR: No E2E test extractions found")
            sys.exit(1)

        run_dirs = sorted([d for d in runs_dir.iterdir() if d.is_dir()], reverse=True)
        if not run_dirs:
            print("ERROR: No E2E test extractions found")
            sys.exit(1)

        run_id = run_dirs[0].name
        print(f"Using most recent run: {run_id}\n")
    else:
        run_id = sys.argv[1]

    generate_report(run_id)
