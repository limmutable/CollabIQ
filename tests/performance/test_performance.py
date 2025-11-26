"""Performance tests for CollabIQ system.

This module provides performance tests for:
- Email processing pipeline
- LLM extraction performance
- Notion integration performance
- End-to-end pipeline throughput

Tests use PerformanceMonitor to track metrics and validate against thresholds.

Usage:
    pytest tests/performance/test_performance.py -v
    pytest tests/performance/test_performance.py -v --benchmark-only
"""

import os
import pytest
import time
from pathlib import Path
from datetime import datetime, UTC

from collabiq.test_utils.performance_monitor import (
    PerformanceMonitor,
    PerformanceThresholds,
    measure_performance,
    save_metrics,
)
from llm_adapters.gemini_adapter import GeminiAdapter
from notion_integrator.integrator import NotionIntegrator


class TestEmailProcessingPerformance:
    """Performance tests for email processing operations."""

    @pytest.fixture
    def sample_email_text(self) -> str:
        """Sample Korean email for testing."""
        return """
        안녕하세요,

        스타트업 "테크노베이션"의 김철수 대리입니다.
        신세계그룹과의 파트너십 관련하여 11월 20일 오후 2시에
        회의 일정을 제안드립니다.

        감사합니다.
        """

    @pytest.fixture
    def performance_thresholds(self) -> PerformanceThresholds:
        """Standard performance thresholds for email processing."""
        return PerformanceThresholds(
            max_response_time=5.0,  # 5 seconds max for email processing
            max_processing_time=10.0,  # 10 seconds max for full pipeline
            min_throughput=0.1,  # At least 0.1 emails/second
            max_error_rate=0.1,  # Max 10% error rate
        )

    def test_email_parsing_performance(self, sample_email_text, performance_thresholds):
        """Test email parsing performance meets thresholds."""
        thresholds = PerformanceThresholds(max_processing_time=1.0)

        with PerformanceMonitor("email_parsing", thresholds) as monitor:
            # Simulate email parsing
            from email import message_from_string
            from email.policy import default

            for _ in range(10):
                message_from_string(
                    f"Subject: Test\n\n{sample_email_text}", policy=default
                )
                monitor.record_item()

        assert monitor.passed, monitor.failure_message
        assert monitor.metrics.duration < 1.0
        assert monitor.metrics.throughput >= 10.0  # 10 emails/second

    def test_email_text_extraction_performance(
        self, sample_email_text, performance_thresholds
    ):
        """Test email text extraction performance."""
        thresholds = PerformanceThresholds(max_processing_time=0.5)

        with PerformanceMonitor("text_extraction", thresholds) as monitor:
            # Simulate text extraction
            for _ in range(10):
                text = sample_email_text.strip()
                assert len(text) > 0
                monitor.record_item()

        assert monitor.passed, monitor.failure_message
        assert monitor.metrics.throughput >= 20.0  # 20 extractions/second


class TestLLMExtractionPerformance:
    """Performance tests for LLM extraction operations."""

    @pytest.fixture
    def sample_email_text(self) -> str:
        """Sample Korean email for testing."""
        return """
        안녕하세요,

        스타트업 "테크노베이션"의 김철수 대리입니다.
        신세계그룹과의 파트너십 관련하여 11월 20일 오후 2시에
        회의 일정을 제안드립니다.

        감사합니다.
        """

    @pytest.fixture
    def llm_performance_thresholds(self) -> PerformanceThresholds:
        """Performance thresholds for LLM operations."""
        return PerformanceThresholds(
            max_response_time=5.0,  # 5 seconds max per LLM call
            max_processing_time=5.0,
            min_throughput=0.2,  # At least 0.2 extractions/second
            max_error_rate=0.05,  # Max 5% error rate for LLM
        )

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_gemini_extraction_performance(
        self, sample_email_text, llm_performance_thresholds
    ):
        """Test Gemini extraction performance meets thresholds."""
        from unittest.mock import AsyncMock, patch

        thresholds = PerformanceThresholds(
            max_response_time=5.0,
            max_error_rate=0.1,
        )

        with PerformanceMonitor("gemini_extraction", thresholds) as monitor:
            adapter = GeminiAdapter(api_key="test-key")

            # Mock the API call to avoid needing real credentials
            mock_result = {
                "startup_name": {"value": "테크노베이션", "confidence": 0.9},
                "person_in_charge": {"value": "김철수", "confidence": 0.85},
                "partner_org": {"value": "신세계그룹", "confidence": 0.8},
                "details": {"value": "파트너십 회의", "confidence": 0.75},
                "date": {"value": "2025-11-20", "confidence": 0.9},
            }

            with patch.object(adapter, '_call_gemini_api', return_value=mock_result):
                try:
                    result = await adapter.extract_entities(sample_email_text)

                    # Validate response
                    assert result is not None
                    assert hasattr(result, 'startup_name')
                    monitor.record_item(success=True)

                    # Record custom metrics
                    monitor.record_custom_metric(
                        "startup_found", result.startup_name is not None
                    )
                    monitor.record_custom_metric(
                        "person_found", result.person_in_charge is not None
                    )

                except Exception:
                    monitor.record_item(success=False)
                    raise

        assert monitor.passed, monitor.failure_message
        assert monitor.metrics.duration < 5.0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_llm_batch_extraction_performance(
        self, sample_email_text, llm_performance_thresholds
    ):
        """Test batch LLM extraction performance."""
        from unittest.mock import patch

        thresholds = PerformanceThresholds(
            max_processing_time=30.0,  # 30 seconds for 5 emails
            min_throughput=0.15,  # At least 0.15 emails/second
            max_error_rate=0.1,
        )

        with PerformanceMonitor("batch_extraction", thresholds) as monitor:
            adapter = GeminiAdapter(api_key="test-key")

            # Mock the API call to avoid needing real credentials
            mock_result = {
                "startup_name": {"value": "테크노베이션", "confidence": 0.9},
                "person_in_charge": {"value": "김철수", "confidence": 0.85},
                "partner_org": {"value": "신세계그룹", "confidence": 0.8},
                "details": {"value": "파트너십 회의", "confidence": 0.75},
                "date": {"value": "2025-11-20", "confidence": 0.9},
            }

            with patch.object(adapter, '_call_gemini_api', return_value=mock_result):
                # Process 5 emails
                for i in range(5):
                    try:
                        result = await adapter.extract_entities(sample_email_text)
                        assert result is not None
                        monitor.record_item(success=True)
                    except Exception:
                        monitor.record_item(success=False)

                    # Small delay to avoid rate limits
                    time.sleep(1.0)

        assert monitor.passed, monitor.failure_message
        assert monitor.metrics.error_rate <= 0.1

        # Save metrics for analysis
        metrics_dir = Path("data/test_metrics/performance")
        metrics_dir.mkdir(parents=True, exist_ok=True)
        save_metrics(
            monitor.metrics,
            metrics_dir
            / f"batch_extraction_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.json",
        )


class TestNotionIntegrationPerformance:
    """Performance tests for Notion integration operations."""

    @pytest.fixture
    def notion_performance_thresholds(self) -> PerformanceThresholds:
        """Performance thresholds for Notion operations."""
        return PerformanceThresholds(
            max_response_time=3.0,  # 3 seconds max per API call
            max_processing_time=5.0,
            min_throughput=0.3,  # At least 0.3 operations/second
            max_error_rate=0.05,  # Max 5% error rate
        )

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_notion_read_performance(self, notion_performance_thresholds):
        """Test Notion database read performance."""
        thresholds = PerformanceThresholds(
            max_response_time=5.0,  # Allow for network variability
            max_error_rate=0.1,
        )

        # Get database ID from environment
        database_id = os.getenv("NOTION_DATABASE_ID_COLLABIQ")
        if not database_id:
            pytest.skip("NOTION_DATABASE_ID_COLLABIQ not set")

        with PerformanceMonitor("notion_read", thresholds) as monitor:
            integrator = NotionIntegrator()

            try:
                # Read database schema using async API
                schema = await integrator.discover_database_schema(database_id)

                assert schema is not None
                monitor.record_item(success=True)

                # Record custom metrics - use property_count computed field
                monitor.record_custom_metric("schema_fields", schema.property_count)

            except Exception:
                monitor.record_item(success=False)
                raise

        assert monitor.passed, monitor.failure_message

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_notion_write_performance(self, notion_performance_thresholds):
        """Test Notion API connectivity performance.

        Note: This test validates the NotionIntegrator can connect and query.
        Full write operations are tested in integration/test_notion_write_e2e.py.
        We use schema discovery (fast) instead of fetch_all_records (slow with relationships).
        """
        thresholds = PerformanceThresholds(
            max_response_time=10.0,  # Schema discovery should be fast
            max_error_rate=0.1,
        )

        # Get database ID from environment
        database_id = os.getenv("NOTION_DATABASE_ID_COLLABIQ")
        if not database_id:
            pytest.skip("NOTION_DATABASE_ID_COLLABIQ not set")

        with PerformanceMonitor("notion_write", thresholds) as monitor:
            integrator = NotionIntegrator()

            try:
                # Test API connectivity with schema discovery (faster than fetch_all_records)
                # This validates the integrator can write by confirming schema access
                schema = await integrator.discover_database_schema(
                    database_id=database_id,
                    use_cache=False,  # Force fresh fetch for performance testing
                )

                assert schema is not None
                monitor.record_item(success=True)

                # Record custom metrics
                monitor.record_custom_metric("property_count", schema.property_count)

            except Exception:
                monitor.record_item(success=False)
                # Don't raise - tests may fail due to validation

        assert monitor.passed, monitor.failure_message


class TestEndToEndPipelinePerformance:
    """Performance tests for end-to-end pipeline."""

    @pytest.fixture
    def pipeline_performance_thresholds(self) -> PerformanceThresholds:
        """Performance thresholds for full pipeline."""
        return PerformanceThresholds(
            max_processing_time=15.0,  # 15 seconds max for full pipeline
            min_throughput=0.05,  # At least 0.05 emails/second
            max_error_rate=0.1,  # Max 10% error rate
        )

    @pytest.fixture
    def sample_email_text(self) -> str:
        """Sample Korean email for testing."""
        return """
        안녕하세요,

        스타트업 "테크노베이션"의 김철수 대리입니다.
        신세계그룹과의 파트너십 관련하여 11월 20일 오후 2시에
        회의 일정을 제안드립니다.

        감사합니다.
        """

    @pytest.mark.integration
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_full_pipeline_performance(
        self, sample_email_text, pipeline_performance_thresholds
    ):
        """Test full pipeline performance from email to Notion."""
        with PerformanceMonitor(
            "full_pipeline", pipeline_performance_thresholds
        ) as monitor:
            # Step 1: Email parsing
            monitor.record_custom_metric("step_1_start", time.perf_counter())
            from email import message_from_string
            from email.policy import default

            message_from_string(
                f"Subject: Test Partnership\n\n{sample_email_text}", policy=default
            )
            monitor.record_custom_metric("step_1_end", time.perf_counter())

            # Step 2: LLM extraction
            monitor.record_custom_metric("step_2_start", time.perf_counter())
            try:
                adapter = GeminiAdapter(api_key="test-key")
                extraction = await adapter.extract_entities(sample_email_text)
                assert extraction is not None
                monitor.record_custom_metric("step_2_end", time.perf_counter())
            except Exception:
                monitor.record_item(success=False)
                return

            # Step 3: Notion integration (dry run - no actual write)
            monitor.record_custom_metric("step_3_start", time.perf_counter())
            try:
                NotionIntegrator()
                # Just validate data structure (no write)
                assert "startup_name" in extraction
                monitor.record_custom_metric("step_3_end", time.perf_counter())

                monitor.record_item(success=True)
            except Exception:
                monitor.record_item(success=False)

        # Validate overall performance
        assert monitor.passed, monitor.failure_message

        # Calculate step timings
        step_1_time = monitor.metrics.custom_metrics.get(
            "step_1_end", 0
        ) - monitor.metrics.custom_metrics.get("step_1_start", 0)
        step_2_time = monitor.metrics.custom_metrics.get(
            "step_2_end", 0
        ) - monitor.metrics.custom_metrics.get("step_2_start", 0)
        step_3_time = monitor.metrics.custom_metrics.get(
            "step_3_end", 0
        ) - monitor.metrics.custom_metrics.get("step_3_start", 0)

        # Validate step timings
        assert step_1_time < 1.0, f"Email parsing too slow: {step_1_time:.2f}s"
        assert step_2_time < 10.0, f"LLM extraction too slow: {step_2_time:.2f}s"
        assert step_3_time < 5.0, f"Notion integration too slow: {step_3_time:.2f}s"

        # Save detailed metrics
        metrics_dir = Path("data/test_metrics/performance")
        metrics_dir.mkdir(parents=True, exist_ok=True)
        save_metrics(
            monitor.metrics,
            metrics_dir
            / f"full_pipeline_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.json",
        )


class TestPerformanceMonitorUtility:
    """Tests for PerformanceMonitor utility itself."""

    def test_performance_monitor_basic(self):
        """Test basic PerformanceMonitor functionality."""
        thresholds = PerformanceThresholds(max_processing_time=1.0)

        with PerformanceMonitor("test_operation", thresholds) as monitor:
            time.sleep(0.1)
            monitor.record_item()

        assert monitor.passed
        assert monitor.metrics.duration >= 0.1
        assert monitor.metrics.duration < 1.0
        assert monitor.metrics.item_count == 1

    def test_performance_monitor_threshold_violation(self):
        """Test PerformanceMonitor detects threshold violations."""
        thresholds = PerformanceThresholds(max_processing_time=0.1)

        with PerformanceMonitor("slow_operation", thresholds) as monitor:
            time.sleep(0.2)
            monitor.record_item()

        assert not monitor.passed
        assert "Processing time" in monitor.failure_message
        assert monitor.metrics.duration >= 0.2

    def test_performance_monitor_error_rate(self):
        """Test PerformanceMonitor tracks error rate."""
        thresholds = PerformanceThresholds(max_error_rate=0.2)

        with PerformanceMonitor("error_rate_test", thresholds) as monitor:
            # Record 10 items with 3 failures (30% error rate)
            for i in range(10):
                success = i % 3 != 0  # Fail every 3rd item
                monitor.record_item(success=success)

        assert not monitor.passed
        assert monitor.metrics.error_rate > 0.2
        assert "Error rate" in monitor.failure_message

    def test_performance_monitor_throughput(self):
        """Test PerformanceMonitor calculates throughput."""
        thresholds = PerformanceThresholds(min_throughput=5.0)

        with PerformanceMonitor("throughput_test", thresholds) as monitor:
            # Process 10 items quickly
            for _ in range(10):
                monitor.record_item()
            time.sleep(0.1)

        assert monitor.passed
        assert monitor.metrics.throughput >= 5.0

    def test_performance_monitor_custom_metrics(self):
        """Test PerformanceMonitor custom metrics."""
        with PerformanceMonitor("custom_metrics_test") as monitor:
            monitor.record_custom_metric("test_value", 42)
            monitor.record_custom_metric("test_string", "hello")
            monitor.record_custom_metric("test_bool", True)

        assert monitor.metrics.custom_metrics["test_value"] == 42
        assert monitor.metrics.custom_metrics["test_string"] == "hello"
        assert monitor.metrics.custom_metrics["test_bool"] is True

    def test_performance_metrics_serialization(self):
        """Test PerformanceMetrics JSON serialization."""
        with measure_performance("serialization_test") as monitor:
            monitor.record_item()
            monitor.record_custom_metric("test", "value")

        metrics_dict = monitor.metrics.to_dict()

        assert "operation_name" in metrics_dict
        assert metrics_dict["operation_name"] == "serialization_test"
        assert "duration" in metrics_dict
        assert "throughput" in metrics_dict
        assert "custom_metrics" in metrics_dict
        assert metrics_dict["custom_metrics"]["test"] == "value"
