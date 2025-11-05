"""
ReportGenerator: Generate test run summaries and error reports

Responsibilities:
- Generate human-readable markdown test run summaries
- Create detailed error reports organized by severity
- Format success rates and performance metrics
- Provide actionable insights for error resolution
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.e2e_test.models import ErrorRecord, TestRun

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Generate markdown reports for E2E test runs

    Creates two types of reports:
    1. Test Run Summary - Overall success rates and error counts
    2. Detailed Error Report - Full error details organized by severity

    Attributes:
        output_dir: Base directory for E2E test outputs
    """

    def __init__(self, output_dir: str = "data/e2e_test"):
        """
        Initialize ReportGenerator

        Args:
            output_dir: Base directory for E2E test outputs
        """
        self.output_dir = Path(output_dir)
        self.runs_dir = self.output_dir / "runs"
        self.errors_dir = self.output_dir / "errors"
        self.reports_dir = self.output_dir / "reports"

        # Ensure reports directory exists
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"ReportGenerator initialized with output_dir={output_dir}")

    def generate_summary(self, test_run: TestRun) -> str:
        """
        Generate test run summary report in markdown format

        Creates a concise report with:
        - Overall success rate
        - Processing time
        - Error count by severity
        - Failed email details

        Args:
            test_run: TestRun object with completed test data

        Returns:
            str: Markdown-formatted summary report
        """
        # Calculate metrics
        success_rate = (
            (test_run.success_count / test_run.emails_processed * 100)
            if test_run.emails_processed > 0
            else 0.0
        )

        duration = (test_run.end_time - test_run.start_time) if test_run.end_time else None
        duration_str = self._format_duration(duration) if duration else "N/A"

        avg_time_per_email = (
            duration.total_seconds() / test_run.emails_processed
            if duration and test_run.emails_processed > 0
            else None
        )
        avg_time_str = f"{avg_time_per_email:.1f}s" if avg_time_per_email else "N/A"

        # Build markdown report
        lines = [
            f"# Test Run Summary: {test_run.run_id}",
            "",
            f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Overview",
            "",
            f"- **Run ID**: `{test_run.run_id}`",
            f"- **Status**: {test_run.status}",
            f"- **Start Time**: {test_run.start_time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"- **End Time**: {test_run.end_time.strftime('%Y-%m-%d %H:%M:%S') if test_run.end_time else 'In Progress'}",
            f"- **Duration**: {duration_str}",
            "",
            "## Processing Results",
            "",
            f"- **Emails Processed**: {test_run.emails_processed}",
            f"- **Success Count**: {test_run.success_count} ({success_rate:.1f}%)",
            f"- **Failure Count**: {test_run.failure_count}",
            f"- **Average Time per Email**: {avg_time_str}",
            "",
        ]

        # Success rate assessment
        if success_rate >= 95:
            lines.extend([
                "**✅ SUCCESS CRITERIA MET**: Success rate ≥95% (SC-001)",
                "",
            ])
        else:
            lines.extend([
                f"**⚠️ SUCCESS CRITERIA NOT MET**: Success rate {success_rate:.1f}% < 95% (SC-001)",
                "",
            ])

        # Error summary
        lines.extend([
            "## Errors by Severity",
            "",
            f"- **Critical**: {test_run.error_summary.get('critical', 0)}",
            f"- **High**: {test_run.error_summary.get('high', 0)}",
            f"- **Medium**: {test_run.error_summary.get('medium', 0)}",
            f"- **Low**: {test_run.error_summary.get('low', 0)}",
            "",
        ])

        # Critical error assessment
        if test_run.error_summary.get("critical", 0) == 0:
            lines.extend([
                "**✅ NO CRITICAL ERRORS** (SC-003)",
                "",
            ])
        else:
            lines.extend([
                f"**❌ CRITICAL ERRORS DETECTED**: {test_run.error_summary.get('critical', 0)} errors must be fixed (SC-003)",
                "",
            ])

        # Failed emails
        if test_run.failure_count > 0:
            lines.extend([
                "## Failed Emails",
                "",
            ])

            # Calculate failed email IDs (all emails - successful emails)
            # Note: This requires loading test_email_ids.json to get all email IDs
            # For now, show failure count only
            lines.extend([
                f"**Total Failures**: {test_run.failure_count}",
                "",
                "For detailed error information, see the error report:",
                f"```bash",
                f"cat data/e2e_test/reports/{test_run.run_id}_errors.md",
                f"```",
                "",
            ])

        # Processing details
        if test_run.processed_emails:
            lines.extend([
                "## Successfully Processed Emails",
                "",
            ])

            for email_id in test_run.processed_emails:
                lines.append(f"- ✅ {email_id}")

            lines.append("")

        # Next steps
        lines.extend([
            "## Next Steps",
            "",
        ])

        if success_rate >= 95 and test_run.error_summary.get("critical", 0) == 0:
            lines.extend([
                "1. **Verify Notion Entries**: Manually check Notion database for data accuracy (SC-002)",
                "2. **Validate Korean Text**: Ensure all Korean text is preserved without corruption (SC-007)",
                "3. **Review Error Logs**: Check medium/low severity errors for improvements",
                "4. **Run Cleanup**: Clean up test entries from Notion database",
                "   ```bash",
                "   uv run python scripts/cleanup_test_entries.py --dry-run",
                "   ```",
            ])
        else:
            lines.extend([
                "1. **Review Error Report**: Analyze failed emails and error patterns",
                "   ```bash",
                "   cat data/e2e_test/reports/{}_errors.md".format(test_run.run_id),
                "   ```",
                "2. **Fix Critical/High Errors**: Address critical and high severity errors first (SC-003, SC-004)",
                "3. **Re-run Tests**: Execute tests again after fixes",
                "   ```bash",
                "   uv run python scripts/run_e2e_tests.py --all",
                "   ```",
            ])

        lines.append("")

        # Footer
        lines.extend([
            "---",
            "",
            f"*Generated by E2E Test Suite*",
            f"*Report saved to: `data/e2e_test/reports/{test_run.run_id}_summary.md`*",
        ])

        return "\n".join(lines)

    def generate_error_report(self, run_id: str) -> str:
        """
        Generate detailed error report organized by severity

        Creates a comprehensive report with:
        - Error counts by severity
        - Full error details (stack traces, input data, stage)
        - Actionable recommendations for each error

        Args:
            run_id: Test run ID to generate report for

        Returns:
            str: Markdown-formatted error report
        """
        lines = [
            f"# Error Report: {run_id}",
            "",
            f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ]

        # Collect errors by severity
        errors_by_severity = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
        }

        for severity in ["critical", "high", "medium", "low"]:
            severity_dir = self.errors_dir / severity

            if not severity_dir.exists():
                continue

            # Load all error files for this run_id
            error_files = list(severity_dir.glob(f"{run_id}_*.json"))

            for error_file in error_files:
                with error_file.open("r", encoding="utf-8") as f:
                    error_data = json.load(f)
                    errors_by_severity[severity].append(ErrorRecord(**error_data))

        # Summary
        total_errors = sum(len(errors) for errors in errors_by_severity.values())
        lines.extend([
            "## Error Summary",
            "",
            f"- **Total Errors**: {total_errors}",
            f"- **Critical**: {len(errors_by_severity['critical'])}",
            f"- **High**: {len(errors_by_severity['high'])}",
            f"- **Medium**: {len(errors_by_severity['medium'])}",
            f"- **Low**: {len(errors_by_severity['low'])}",
            "",
        ])

        if total_errors == 0:
            lines.extend([
                "**✅ NO ERRORS DETECTED**",
                "",
                "All emails processed successfully!",
            ])
            return "\n".join(lines)

        # Detailed errors by severity
        for severity in ["critical", "high", "medium", "low"]:
            errors = errors_by_severity[severity]

            if len(errors) == 0:
                continue

            lines.extend([
                f"## {severity.upper()} Errors ({len(errors)})",
                "",
            ])

            for i, error in enumerate(errors, 1):
                lines.extend(self._format_error(error, i))
                lines.append("")

        # Recommendations
        lines.extend([
            "## Recommendations",
            "",
        ])

        if len(errors_by_severity["critical"]) > 0:
            lines.extend([
                "### Critical Errors (MUST FIX)",
                "",
                "Critical errors block MVP deployment. Fix these immediately:",
                "",
            ])

            for error in errors_by_severity["critical"]:
                recommendation = self._get_recommendation(error)
                lines.append(f"- **{error.email_id}** ({error.stage}): {recommendation}")

            lines.append("")

        if len(errors_by_severity["high"]) > 0:
            lines.extend([
                "### High Priority Errors (SHOULD FIX)",
                "",
                "High severity errors impact data quality and user experience:",
                "",
            ])

            for error in errors_by_severity["high"]:
                recommendation = self._get_recommendation(error)
                lines.append(f"- **{error.email_id}** ({error.stage}): {recommendation}")

            lines.append("")

        # Footer
        lines.extend([
            "---",
            "",
            f"*Generated by E2E Test Suite*",
            f"*Report saved to: `data/e2e_test/reports/{run_id}_errors.md`*",
        ])

        return "\n".join(lines)

    def _format_error(self, error: ErrorRecord, index: int) -> list[str]:
        """Format a single error as markdown"""
        lines = [
            f"### {index}. {error.error_type}",
            "",
            f"- **Error ID**: `{error.error_id}`",
            f"- **Email ID**: `{error.email_id}`",
            f"- **Stage**: {error.stage}",
            f"- **Timestamp**: {error.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"- **Status**: {error.resolution_status}",
            "",
            "**Error Message**:",
            "```",
            error.error_message or "No message",
            "```",
            "",
        ]

        if error.stack_trace:
            lines.extend([
                "<details>",
                "<summary>Stack Trace</summary>",
                "",
                "```python",
                error.stack_trace,
                "```",
                "",
                "</details>",
                "",
            ])

        if error.input_data_snapshot:
            lines.extend([
                "<details>",
                "<summary>Input Data Snapshot</summary>",
                "",
                "```json",
                json.dumps(error.input_data_snapshot, indent=2, ensure_ascii=False),
                "```",
                "",
                "</details>",
                "",
            ])

        if error.fix_commit:
            lines.extend([
                f"**Fix Commit**: `{error.fix_commit}`",
                "",
            ])

        if error.notes:
            lines.extend([
                f"**Notes**: {error.notes}",
                "",
            ])

        return lines

    def _get_recommendation(self, error: ErrorRecord) -> str:
        """Get actionable recommendation for error"""
        # Provide stage-specific recommendations
        if error.stage == "reception":
            return "Check Gmail API authentication and email ID validity"
        elif error.stage == "extraction":
            return "Review Gemini API logs and prompt engineering"
        elif error.stage == "matching":
            return "Verify company database and matching logic"
        elif error.stage == "classification":
            return "Check classification rules and LLM responses"
        elif error.stage == "write":
            return "Verify Notion API credentials and database schema"
        elif error.stage == "validation":
            if "korean" in error.error_type.lower() or "mojibake" in error.error_type.lower():
                return "Fix Korean text encoding issues (check UTF-8 preservation)"
            return "Check Notion entry structure and required fields"
        else:
            return "Review error details and implement appropriate fix"

    def _format_duration(self, duration) -> str:
        """Format timedelta as human-readable string"""
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
