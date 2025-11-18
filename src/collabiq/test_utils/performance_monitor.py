"""Performance monitoring utilities for testing.

This module provides utilities for:
- Collecting performance metrics during test execution
- Defining performance thresholds
- Asserting against performance expectations
- Tracking response times, processing times, and throughput

Usage:
    from collabiq.test_utils.performance_monitor import (
        PerformanceMonitor,
        PerformanceThresholds,
        measure_performance
    )

    # Define thresholds
    thresholds = PerformanceThresholds(
        max_response_time=3.0,  # seconds
        max_processing_time=5.0,  # seconds
        min_throughput=10.0  # items/second
    )

    # Measure performance
    with PerformanceMonitor("email_processing", thresholds) as monitor:
        # Your code here
        process_email(email_text)

    # Check results
    assert monitor.passed, monitor.failure_message
"""

import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, UTC
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class PerformanceThresholds:
    """Performance thresholds for testing.

    Attributes:
        max_response_time: Maximum acceptable response time in seconds
        max_processing_time: Maximum acceptable processing time in seconds
        min_throughput: Minimum acceptable throughput (items/second)
        max_memory_mb: Maximum acceptable memory usage in MB
        max_error_rate: Maximum acceptable error rate (0.0-1.0)
    """

    max_response_time: Optional[float] = None  # seconds
    max_processing_time: Optional[float] = None  # seconds
    min_throughput: Optional[float] = None  # items/second
    max_memory_mb: Optional[float] = None  # MB
    max_error_rate: Optional[float] = None  # 0.0-1.0

    def validate(self) -> List[str]:
        """Validate threshold values.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        if self.max_response_time is not None and self.max_response_time <= 0:
            errors.append("max_response_time must be positive")

        if self.max_processing_time is not None and self.max_processing_time <= 0:
            errors.append("max_processing_time must be positive")

        if self.min_throughput is not None and self.min_throughput <= 0:
            errors.append("min_throughput must be positive")

        if self.max_memory_mb is not None and self.max_memory_mb <= 0:
            errors.append("max_memory_mb must be positive")

        if self.max_error_rate is not None:
            if not (0.0 <= self.max_error_rate <= 1.0):
                errors.append("max_error_rate must be between 0.0 and 1.0")

        return errors


@dataclass
class PerformanceMetrics:
    """Performance metrics collected during execution.

    Attributes:
        operation_name: Name of the operation being measured
        start_time: Start timestamp
        end_time: End timestamp (None if not finished)
        duration: Duration in seconds (None if not finished)
        item_count: Number of items processed
        error_count: Number of errors encountered
        memory_peak_mb: Peak memory usage in MB (if tracked)
        custom_metrics: Additional custom metrics
    """

    operation_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None  # seconds
    item_count: int = 0
    error_count: int = 0
    memory_peak_mb: Optional[float] = None
    custom_metrics: Dict[str, Any] = field(default_factory=dict)

    @property
    def throughput(self) -> Optional[float]:
        """Calculate throughput (items/second).

        Returns:
            Items per second, or None if duration is 0 or not finished
        """
        if self.duration and self.duration > 0:
            return self.item_count / self.duration
        return None

    @property
    def error_rate(self) -> float:
        """Calculate error rate.

        Returns:
            Error rate (0.0-1.0)
        """
        if self.item_count == 0:
            return 0.0
        return self.error_count / self.item_count

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "operation_name": self.operation_name,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration,
            "item_count": self.item_count,
            "error_count": self.error_count,
            "throughput": self.throughput,
            "error_rate": self.error_rate,
            "memory_peak_mb": self.memory_peak_mb,
            "custom_metrics": self.custom_metrics,
        }


class PerformanceMonitor:
    """Context manager for monitoring performance metrics.

    Example:
        >>> thresholds = PerformanceThresholds(max_processing_time=5.0)
        >>> with PerformanceMonitor("test_op", thresholds) as monitor:
        ...     # Your code here
        ...     monitor.record_item()
        >>> assert monitor.passed
    """

    def __init__(
        self,
        operation_name: str,
        thresholds: Optional[PerformanceThresholds] = None,
        auto_start: bool = True,
    ):
        """Initialize performance monitor.

        Args:
            operation_name: Name of the operation being monitored
            thresholds: Performance thresholds to check against
            auto_start: Whether to start timing automatically
        """
        self.operation_name = operation_name
        self.thresholds = thresholds or PerformanceThresholds()
        self.metrics = PerformanceMetrics(
            operation_name=operation_name, start_time=datetime.now(UTC)
        )
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None
        self._passed: Optional[bool] = None
        self._failures: List[str] = []

        if auto_start:
            self.start()

    def start(self):
        """Start timing."""
        self._start_time = time.perf_counter()
        self.metrics.start_time = datetime.now(UTC)
        logger.debug(f"Performance monitoring started for '{self.operation_name}'")

    def stop(self):
        """Stop timing and calculate metrics."""
        if self._start_time is None:
            raise RuntimeError("Monitor not started")

        self._end_time = time.perf_counter()
        self.metrics.end_time = datetime.now(UTC)
        self.metrics.duration = self._end_time - self._start_time

        logger.debug(
            f"Performance monitoring stopped for '{self.operation_name}' "
            f"(duration: {self.metrics.duration:.3f}s)"
        )

    def record_item(self, success: bool = True):
        """Record a processed item.

        Args:
            success: Whether the item was processed successfully
        """
        self.metrics.item_count += 1
        if not success:
            self.metrics.error_count += 1

    def record_custom_metric(self, name: str, value: Any):
        """Record a custom metric.

        Args:
            name: Metric name
            value: Metric value
        """
        self.metrics.custom_metrics[name] = value

    def check_thresholds(self) -> bool:
        """Check if metrics meet defined thresholds.

        Returns:
            True if all thresholds are met, False otherwise
        """
        self._failures = []

        # Validate thresholds first
        validation_errors = self.thresholds.validate()
        if validation_errors:
            self._failures.extend(validation_errors)
            self._passed = False
            return False

        # Check response time (use duration as proxy)
        if (
            self.thresholds.max_response_time is not None
            and self.metrics.duration is not None
        ):
            if self.metrics.duration > self.thresholds.max_response_time:
                self._failures.append(
                    f"Response time {self.metrics.duration:.3f}s exceeds "
                    f"threshold {self.thresholds.max_response_time:.3f}s"
                )

        # Check processing time
        if (
            self.thresholds.max_processing_time is not None
            and self.metrics.duration is not None
        ):
            if self.metrics.duration > self.thresholds.max_processing_time:
                self._failures.append(
                    f"Processing time {self.metrics.duration:.3f}s exceeds "
                    f"threshold {self.thresholds.max_processing_time:.3f}s"
                )

        # Check throughput
        if self.thresholds.min_throughput is not None and self.metrics.throughput:
            if self.metrics.throughput < self.thresholds.min_throughput:
                self._failures.append(
                    f"Throughput {self.metrics.throughput:.2f} items/s below "
                    f"threshold {self.thresholds.min_throughput:.2f} items/s"
                )

        # Check memory
        if (
            self.thresholds.max_memory_mb is not None
            and self.metrics.memory_peak_mb is not None
        ):
            if self.metrics.memory_peak_mb > self.thresholds.max_memory_mb:
                self._failures.append(
                    f"Memory usage {self.metrics.memory_peak_mb:.1f}MB exceeds "
                    f"threshold {self.thresholds.max_memory_mb:.1f}MB"
                )

        # Check error rate
        if self.thresholds.max_error_rate is not None:
            if self.metrics.error_rate > self.thresholds.max_error_rate:
                self._failures.append(
                    f"Error rate {self.metrics.error_rate:.2%} exceeds "
                    f"threshold {self.thresholds.max_error_rate:.2%}"
                )

        self._passed = len(self._failures) == 0
        return self._passed

    @property
    def passed(self) -> bool:
        """Check if performance thresholds were met.

        Returns:
            True if thresholds met, False otherwise
        """
        if self._passed is None:
            self.check_thresholds()
        return self._passed

    @property
    def failure_message(self) -> str:
        """Get failure message if thresholds not met.

        Returns:
            Formatted failure message
        """
        if self._passed is None:
            self.check_thresholds()

        if self._passed:
            return ""

        return (
            f"Performance thresholds not met for '{self.operation_name}':\n"
            + "\n".join(f"  - {failure}" for failure in self._failures)
        )

    def __enter__(self):
        """Enter context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager and check thresholds."""
        self.stop()
        self.check_thresholds()

        if self._failures:
            logger.warning(self.failure_message)

        return False  # Don't suppress exceptions


@contextmanager
def measure_performance(
    operation_name: str, thresholds: Optional[PerformanceThresholds] = None
):
    """Context manager for measuring performance.

    Args:
        operation_name: Name of the operation
        thresholds: Optional performance thresholds

    Yields:
        PerformanceMonitor instance

    Example:
        >>> with measure_performance("test", PerformanceThresholds(max_processing_time=5.0)) as monitor:
        ...     # Your code here
        ...     monitor.record_item()
    """
    monitor = PerformanceMonitor(operation_name, thresholds)
    try:
        yield monitor
    finally:
        monitor.stop()


def save_metrics(metrics: PerformanceMetrics, output_path: Path):
    """Save metrics to JSON file.

    Args:
        metrics: Performance metrics to save
        output_path: Path to output file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metrics.to_dict(), f, indent=2, ensure_ascii=False)
    logger.info(f"Performance metrics saved to {output_path}")


def load_metrics(input_path: Path) -> PerformanceMetrics:
    """Load metrics from JSON file.

    Args:
        input_path: Path to input file

    Returns:
        Loaded performance metrics
    """
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return PerformanceMetrics(
        operation_name=data["operation_name"],
        start_time=datetime.fromisoformat(data["start_time"])
        if data.get("start_time")
        else datetime.now(UTC),
        end_time=datetime.fromisoformat(data["end_time"])
        if data.get("end_time")
        else None,
        duration=data.get("duration"),
        item_count=data.get("item_count", 0),
        error_count=data.get("error_count", 0),
        memory_peak_mb=data.get("memory_peak_mb"),
        custom_metrics=data.get("custom_metrics", {}),
    )
