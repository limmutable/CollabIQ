from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime, timedelta

class TestCategoryMetrics(BaseModel):
    total: int = Field(..., description="Total tests in this category.")
    passed: int = Field(..., description="Number of passed tests in this category.")
    failed: int = Field(..., description="Number of failed tests in this category.")
    skipped: int = Field(0, description="Number of skipped tests in this category.")

class QualityMetricsComparison(BaseModel):
    metric_name: str = Field(..., description="Name of the quality metric (e.g., person_assignment_rate).")
    before_phase_017: Optional[float] = Field(None, description="Metric value before Phase 017 implementation.")
    after_phase_017: Optional[float] = Field(None, description="Metric value after Phase 017 implementation.")
    improvement: Optional[float] = Field(None, description="Improvement in metric value.")

class TestExecutionReport(BaseModel):
    """
    Represents a comprehensive report of test execution results.
    """
    report_id: str = Field(..., description="Unique ID for the test report.")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp of when the report was generated.")
    total_tests_executed: int = Field(..., description="Total number of tests executed.")
    pass_count: int = Field(..., description="Total number of tests that passed.")
    fail_count: int = Field(..., description="Total number of tests that failed.")
    skip_count: int = Field(0, description="Total number of tests that were skipped.")
    test_duration: timedelta = Field(..., description="Total duration of the test execution.")
    coverage_percentage: Optional[float] = Field(None, ge=0.0, le=100.0, description="Code coverage percentage.")
    pass_rate: float = Field(..., ge=0.0, le=1.0, description="Overall pass rate of the test suite.")
    test_categories: Dict[str, TestCategoryMetrics] = Field(default_factory=dict, description="Metrics broken down by test category.")
    detailed_failure_logs: List[str] = Field(default_factory=list, description="List of detailed logs for failed tests.")
    quality_metrics_comparison: List[QualityMetricsComparison] = Field(default_factory=list, description="Comparison of quality metrics before and after Phase 017.")
