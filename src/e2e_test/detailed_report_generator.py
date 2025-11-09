"""Detailed E2E Test Report Generator

Generates comprehensive, standardized reports for E2E test runs with sections:
1. Test Run Summary
2. Per-Email Processing Details
3. Extracted Values and Notion Field Mappings
4. Notion Database Write Results
5. Quality Metrics Summary
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class DetailedReportGenerator:
    """Generates standardized E2E test reports with detailed sections."""

    def __init__(self, base_dir: str = "data/e2e_test"):
        """Initialize report generator.

        Args:
            base_dir: Base directory for E2E test data
        """
        self.base_dir = Path(base_dir)
        self.runs_dir = self.base_dir / "runs"
        self.extractions_dir = self.base_dir / "extractions"
        self.reports_dir = self.base_dir / "reports"

    def generate_detailed_report(self, run_id: str) -> str:
        """Generate comprehensive detailed report for a test run.

        Args:
            run_id: Test run ID

        Returns:
            Markdown-formatted report content
        """
        # Load test run data
        run_file = self.runs_dir / f"{run_id}.json"
        if not run_file.exists():
            return f"ERROR: Run file not found: {run_file}"

        with run_file.open() as f:
            run_data = json.load(f)

        # Load extractions
        extractions = self._load_extractions(run_id)

        # Load quality metrics if available
        quality_metrics_file = self.reports_dir / f"{run_id}_quality_metrics.json"
        quality_metrics = {}
        if quality_metrics_file.exists():
            with quality_metrics_file.open() as f:
                quality_metrics = json.load(f)

        # Load error details
        errors = self._load_errors(run_id)

        # Generate report sections
        report = []
        report.append(self._generate_header(run_id, run_data))
        report.append(self._generate_test_summary(run_data))
        report.append(self._generate_email_details(run_data, extractions))
        report.append(self._generate_field_mappings())
        report.append(self._generate_notion_write_results(run_data, extractions))
        report.append(self._generate_quality_metrics(quality_metrics))

        # Add error details section if errors exist
        if errors:
            report.append(self._generate_error_details(errors))

        report.append(self._generate_footer(run_id))

        return "\n\n".join(report)

    def _load_extractions(self, run_id: str) -> Dict[str, dict]:
        """Load all extraction files for a run.

        Args:
            run_id: Test run ID

        Returns:
            Dictionary mapping email_id -> extraction data
        """
        extractions_run_dir = self.extractions_dir / run_id
        if not extractions_run_dir.exists():
            return {}

        extractions = {}
        for extraction_file in extractions_run_dir.glob("*.json"):
            email_id = extraction_file.stem
            with extraction_file.open() as f:
                extractions[email_id] = json.load(f)

        return extractions

    def _load_errors(self, run_id: str) -> Dict[str, List[dict]]:
        """Load all error files for a run organized by severity.

        Args:
            run_id: Test run ID

        Returns:
            Dictionary mapping severity -> list of error records
        """
        errors_dir = self.base_dir / "errors"
        errors_by_severity = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
        }

        for severity in errors_by_severity.keys():
            severity_dir = errors_dir / severity
            if not severity_dir.exists():
                continue

            # Load all error files for this run_id
            error_files = list(severity_dir.glob(f"{run_id}_*.json"))
            for error_file in error_files:
                with error_file.open("r", encoding="utf-8") as f:
                    error_data = json.load(f)
                    errors_by_severity[severity].append(error_data)

        return errors_by_severity

    def _generate_header(self, run_id: str, run_data: dict) -> str:
        """Generate report header."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status_emoji = "✅" if run_data["status"] == "completed" else "⚠️"

        return f"""# E2E Test Report - {run_id}

**Generated**: {timestamp}
**Status**: {status_emoji} {run_data["status"].upper()}
**Test Mode**: {"Enabled" if run_data.get("config", {}).get("test_mode", True) else "Disabled (Production Mode)"}

---"""

    def _generate_test_summary(self, run_data: dict) -> str:
        """Generate test run summary section."""
        duration = "N/A"
        if run_data.get("start_time") and run_data.get("end_time"):
            start = datetime.fromisoformat(run_data["start_time"])
            end = datetime.fromisoformat(run_data["end_time"])
            duration_seconds = (end - start).total_seconds()
            duration = f"{duration_seconds:.1f}s"

        success_rate = 0
        if run_data["emails_processed"] > 0:
            success_rate = (run_data["success_count"] / run_data["emails_processed"]) * 100

        return f"""## 1. Test Run Summary

| Metric | Value |
|--------|-------|
| **Run ID** | `{run_data["run_id"]}` |
| **Start Time** | {run_data.get("start_time", "N/A")} |
| **End Time** | {run_data.get("end_time", "N/A")} |
| **Duration** | {duration} |
| **Total Emails** | {run_data["email_count"]} |
| **Processed** | {run_data["emails_processed"]} |
| **✅ Successful** | {run_data["success_count"]} ({success_rate:.1f}%) |
| **❌ Failed** | {run_data["failure_count"]} |

### Error Summary

| Severity | Count |
|----------|-------|
| Critical | {run_data.get("error_summary", {}).get("critical", 0)} |
| High | {run_data.get("error_summary", {}).get("high", 0)} |
| Medium | {run_data.get("error_summary", {}).get("medium", 0)} |
| Low | {run_data.get("error_summary", {}).get("low", 0)} |

---"""

    def _generate_email_details(self, run_data: dict, extractions: Dict[str, dict]) -> str:
        """Generate per-email processing details."""
        section = [f"""## 2. Email Processing Details

Total emails processed: {len(run_data.get("test_email_ids", []))}

"""]

        for idx, email_id in enumerate(run_data.get("test_email_ids", []), 1):
            extraction = extractions.get(email_id, {})

            section.append(f"""### Email {idx}/{len(run_data["test_email_ids"])}: `{email_id}`

**Status**: {"✅ Success" if email_id in extractions else "❌ Failed"}
**Provider**: {extraction.get("provider_name", "N/A")}
**Extracted At**: {extraction.get("extracted_at", "N/A")}

#### Extracted Values

| Field | Value | Confidence |
|-------|-------|-----------|
| **Person in Charge** | {extraction.get("person_in_charge", "N/A")} | {extraction.get("confidence", {}).get("person", 0):.1%} |
| **Startup Name** | {extraction.get("startup_name", "N/A")} | {extraction.get("confidence", {}).get("startup", 0):.1%} |
| **Partner Org** | {extraction.get("partner_org", "N/A")} | {extraction.get("confidence", {}).get("partner", 0):.1%} |
| **Date** | {extraction.get("date", "N/A")} | {extraction.get("confidence", {}).get("date", 0):.1%} |

**Details** (Confidence: {extraction.get("confidence", {}).get("details", 0):.1%}):
```
{extraction.get("details", "N/A")}
```

**Average Confidence**: {self._calculate_avg_confidence(extraction.get("confidence", {})):.1%}

---
""")

        return "\n".join(section)

    def _generate_field_mappings(self) -> str:
        """Generate Notion field mapping reference."""
        return """## 3. Notion Database Field Mappings

Extracted values are mapped to Notion database properties as follows:

| Extracted Field | Notion Property | Property Type | Description |
|-----------------|-----------------|---------------|-------------|
| `person_in_charge` | 담당자 | Title | Person responsible for collaboration |
| `startup_name` | 스타트업명 | Rich Text | Name of startup company |
| `partner_org` | 협력기관 | Rich Text | Partner organization |
| `details` | 협업내용 | Rich Text | Collaboration description |
| `date` | 날짜 | Date | Collaboration date |
| `collaboration_type` | 협력유형 | Select | Type of collaboration (e.g., [A]PortCoXSSG) |
| `collaboration_intensity` | 협력강도 | Select | Intensity level (이해/협력/투자/인수) |

**Note**: Classification fields (type and intensity) are added during Stage 4.

---"""

    def _generate_notion_write_results(self, run_data: dict, extractions: Dict[str, dict]) -> str:
        """Generate Notion database write results."""
        section = [f"""## 4. Notion Database Write Results

"""]

        writes_attempted = len(run_data.get("test_email_ids", []))
        writes_successful = run_data.get("success_count", 0)
        writes_failed = run_data.get("failure_count", 0)

        section.append(f"""### Write Summary

| Metric | Count |
|--------|-------|
| **Total Writes Attempted** | {writes_attempted} |
| **✅ Successful Writes** | {writes_successful} |
| **❌ Failed Writes** | {writes_failed} |
| **Success Rate** | {(writes_successful / writes_attempted * 100) if writes_attempted > 0 else 0:.1f}% |

### Per-Email Write Status

| Email ID | Status | Details |
|----------|--------|---------|
""")

        for email_id in run_data.get("test_email_ids", []):
            if email_id in extractions:
                section.append(f"| `{email_id}` | ✅ Success | Written to Notion database |")
            else:
                section.append(f"| `{email_id}` | ❌ Failed | Check error report for details |")

        section.append("\n**Note**: Detailed error information available in `{run_id}_errors.md`")
        section.append("\n---")

        return "\n".join(section)

    def _generate_quality_metrics(self, quality_metrics: dict) -> str:
        """Generate quality metrics section."""
        if not quality_metrics:
            return """## 5. Quality Metrics Summary

No quality metrics available for this run.

---"""

        section = [f"""## 5. Quality Metrics Summary

Quality metrics collected across all LLM providers:

"""]

        # Sort providers by quality score
        providers_sorted = sorted(
            quality_metrics.items(),
            key=lambda x: (
                0.4 * x[1]["avg_confidence"]
                + 0.3 * (x[1]["field_completeness"] / 100)
                + 0.3 * (x[1]["validation_success_rate"] / 100)
            ),
            reverse=True
        )

        for idx, (provider, metrics) in enumerate(providers_sorted, 1):
            medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else ""
            quality_score = (
                0.4 * metrics["avg_confidence"]
                + 0.3 * (metrics["field_completeness"] / 100)
                + 0.3 * (metrics["validation_success_rate"] / 100)
            )

            section.append(f"""### {medal} {provider.upper()}

| Metric | Value |
|--------|-------|
| **Total Extractions** | {metrics["total_extractions"]} |
| **Avg Confidence** | {metrics["avg_confidence"]:.2%} |
| **Field Completeness** | {metrics["field_completeness"]:.1f}% |
| **Validation Rate** | {metrics["validation_success_rate"]:.1f}% |
| **Quality Score** | {quality_score:.2f} |

**Per-Field Confidence**:
""")

            for field, conf in metrics.get("per_field_confidence", {}).items():
                section.append(f"- {field.capitalize()}: {conf:.2%}")

            section.append("\n")

        section.append("**Quality Score Formula**: 40% confidence + 30% completeness + 30% validation")
        section.append("\n---")

        return "\n".join(section)

    def _generate_error_details(self, errors_by_severity: Dict[str, List[dict]]) -> str:
        """Generate detailed error section.

        Args:
            errors_by_severity: Dictionary mapping severity -> list of error records

        Returns:
            Markdown-formatted error details section
        """
        total_errors = sum(len(errors) for errors in errors_by_severity.values())
        if total_errors == 0:
            return ""

        section = [f"""## 6. Detailed Error Report

**Total Errors**: {total_errors}

"""]

        # Generate error details by severity
        for severity in ["critical", "high", "medium", "low"]:
            errors = errors_by_severity[severity]
            if len(errors) == 0:
                continue

            section.append(f"### {severity.upper()} Errors ({len(errors)})\n")

            for i, error in enumerate(errors, 1):
                section.append(f"""#### {i}. {error.get("error_type", "Unknown Error")}

- **Error ID**: `{error.get("error_id", "N/A")}`
- **Email ID**: `{error.get("email_id", "N/A")}`
- **Stage**: {error.get("stage", "N/A")}
- **Timestamp**: {error.get("timestamp", "N/A")}
- **Status**: {error.get("resolution_status", "unresolved")}

**Error Message**:
```
{error.get("error_message", "No message")}
```
""")

                if error.get("stack_trace"):
                    section.append(f"""<details>
<summary>Stack Trace</summary>

```python
{error["stack_trace"]}
```

</details>
""")

                if error.get("input_data_snapshot"):
                    section.append(f"""<details>
<summary>Input Data Snapshot</summary>

```json
{json.dumps(error["input_data_snapshot"], indent=2, ensure_ascii=False)}
```

</details>
""")

                if error.get("fix_commit"):
                    section.append(f"**Fix Commit**: `{error['fix_commit']}`\n")

                if error.get("notes"):
                    section.append(f"**Notes**: {error['notes']}\n")

                section.append("\n---\n")

        section.append("\n")
        return "\n".join(section)

    def _generate_footer(self, run_id: str) -> str:
        """Generate report footer."""
        return f"""## Test Artifacts

### Generated Files

```
data/e2e_test/
├── runs/{run_id}.json                     # Test run metadata
├── reports/{run_id}_summary.md            # Human-readable summary
├── reports/{run_id}_errors.md             # Detailed error report
├── reports/{run_id}_quality_metrics.json  # Quality metrics data
└── extractions/{run_id}/                  # Individual extraction files
    ├── {{email_id_1}}.json
    ├── {{email_id_2}}.json
    └── ...
```

### Viewing Results

```bash
# View this detailed report
cat data/e2e_test/reports/{run_id}_detailed.md

# View quality metrics
cat data/e2e_test/reports/{run_id}_quality_metrics.json | python3 -m json.tool

# View error details
cat data/e2e_test/reports/{run_id}_errors.md

# View extraction for specific email
cat data/e2e_test/extractions/{run_id}/{{email_id}}.json | python3 -m json.tool

# Generate extraction report
uv run python scripts/generate_extraction_report.py {run_id}

# Compare provider performance
collabiq llm compare --detailed
```

---

**Report Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Phase**: 013 - Quality Metrics & Intelligent Routing ✅
**System**: CollabIQ E2E Test Suite"""

    def _calculate_avg_confidence(self, confidence: dict) -> float:
        """Calculate average confidence from confidence dict.

        Args:
            confidence: Dict with per-field confidence scores

        Returns:
            Average confidence (0.0-1.0)
        """
        if not confidence:
            return 0.0

        values = list(confidence.values())
        return sum(values) / len(values) if values else 0.0

    def save_report(self, run_id: str) -> Path:
        """Generate and save detailed report.

        Args:
            run_id: Test run ID

        Returns:
            Path to saved report file
        """
        report_content = self.generate_detailed_report(run_id)

        # Create timestamped filename in format: YYYYMMDD_HHMMSS-e2e_test.md
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"{timestamp}-e2e_test.md"
        report_path = self.reports_dir / report_filename

        with report_path.open("w", encoding="utf-8") as f:
            f.write(report_content)

        logger.info(f"Detailed report saved to {report_path}")

        return report_path
