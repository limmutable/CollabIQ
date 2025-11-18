"""Performance threshold definitions for CollabIQ system.

This module defines standard performance thresholds for different components
of the CollabIQ system. These thresholds are used by performance tests to
validate that the system meets acceptable performance criteria.

Usage:
    from collabiq.test_utils.performance_thresholds import (
        EMAIL_PROCESSING_THRESHOLDS,
        LLM_EXTRACTION_THRESHOLDS,
        NOTION_INTEGRATION_THRESHOLDS,
        PIPELINE_THRESHOLDS,
    )

    with PerformanceMonitor("operation", EMAIL_PROCESSING_THRESHOLDS) as monitor:
        # Your code here
        pass
"""

from collabiq.test_utils.performance_monitor import PerformanceThresholds


# Email Processing Thresholds
EMAIL_PROCESSING_THRESHOLDS = PerformanceThresholds(
    max_response_time=5.0,  # 5 seconds max for email processing
    max_processing_time=10.0,  # 10 seconds max for full email pipeline
    min_throughput=0.1,  # At least 0.1 emails/second (6 emails/minute)
    max_error_rate=0.1,  # Max 10% error rate
)

# Email Parsing Thresholds (subset of email processing)
EMAIL_PARSING_THRESHOLDS = PerformanceThresholds(
    max_processing_time=1.0,  # 1 second max for parsing
    min_throughput=10.0,  # At least 10 emails/second
    max_error_rate=0.05,  # Max 5% error rate
)

# Email Text Extraction Thresholds
EMAIL_TEXT_EXTRACTION_THRESHOLDS = PerformanceThresholds(
    max_processing_time=0.5,  # 0.5 seconds max for text extraction
    min_throughput=20.0,  # At least 20 extractions/second
    max_error_rate=0.01,  # Max 1% error rate
)


# LLM Extraction Thresholds
LLM_EXTRACTION_THRESHOLDS = PerformanceThresholds(
    max_response_time=5.0,  # 5 seconds max per LLM call
    max_processing_time=5.0,  # 5 seconds max for extraction
    min_throughput=0.2,  # At least 0.2 extractions/second (12/minute)
    max_error_rate=0.05,  # Max 5% error rate for LLM
)

# LLM Batch Extraction Thresholds
LLM_BATCH_EXTRACTION_THRESHOLDS = PerformanceThresholds(
    max_processing_time=30.0,  # 30 seconds for 5 emails
    min_throughput=0.15,  # At least 0.15 emails/second
    max_error_rate=0.1,  # Max 10% error rate (1 failure per 10 emails)
)


# Notion Integration Thresholds
NOTION_INTEGRATION_THRESHOLDS = PerformanceThresholds(
    max_response_time=3.0,  # 3 seconds max per API call
    max_processing_time=5.0,  # 5 seconds max for full operation
    min_throughput=0.3,  # At least 0.3 operations/second (18/minute)
    max_error_rate=0.05,  # Max 5% error rate
)

# Notion Read Thresholds
NOTION_READ_THRESHOLDS = PerformanceThresholds(
    max_response_time=3.0,  # 3 seconds max per read
    max_error_rate=0.1,  # Max 10% error rate
)

# Notion Write Thresholds
NOTION_WRITE_THRESHOLDS = PerformanceThresholds(
    max_response_time=5.0,  # 5 seconds max per write
    max_error_rate=0.1,  # Max 10% error rate
)


# End-to-End Pipeline Thresholds
PIPELINE_THRESHOLDS = PerformanceThresholds(
    max_processing_time=15.0,  # 15 seconds max for full pipeline
    min_throughput=0.05,  # At least 0.05 emails/second (3 emails/minute)
    max_error_rate=0.1,  # Max 10% error rate
)


# Component Step Thresholds (for pipeline breakdown)
class PipelineStepThresholds:
    """Individual step thresholds within the pipeline."""

    EMAIL_PARSING_MAX_TIME = 1.0  # seconds
    LLM_EXTRACTION_MAX_TIME = 10.0  # seconds
    NOTION_INTEGRATION_MAX_TIME = 5.0  # seconds


# Performance Goals (aspirational targets for optimization)
class PerformanceGoals:
    """Aspirational performance goals for future optimization."""

    # Email Processing Goals
    EMAIL_PROCESSING_TARGET_TIME = 3.0  # seconds (vs 5.0 threshold)
    EMAIL_THROUGHPUT_TARGET = 0.5  # emails/second (vs 0.1 threshold)

    # LLM Extraction Goals
    LLM_RESPONSE_TARGET_TIME = 3.0  # seconds (vs 5.0 threshold)
    LLM_THROUGHPUT_TARGET = 0.5  # extractions/second (vs 0.2 threshold)

    # Notion Integration Goals
    NOTION_API_TARGET_TIME = 2.0  # seconds (vs 3.0 threshold)
    NOTION_THROUGHPUT_TARGET = 0.5  # operations/second (vs 0.3 threshold)

    # Pipeline Goals
    PIPELINE_TARGET_TIME = 10.0  # seconds (vs 15.0 threshold)
    PIPELINE_THROUGHPUT_TARGET = 0.1  # emails/second (vs 0.05 threshold)

    # Error Rate Goals
    ERROR_RATE_TARGET = 0.01  # 1% (vs 5-10% thresholds)


# Threshold Validation
def validate_thresholds() -> bool:
    """Validate that all defined thresholds are valid.

    Returns:
        True if all thresholds are valid, False otherwise
    """
    all_thresholds = [
        EMAIL_PROCESSING_THRESHOLDS,
        EMAIL_PARSING_THRESHOLDS,
        EMAIL_TEXT_EXTRACTION_THRESHOLDS,
        LLM_EXTRACTION_THRESHOLDS,
        LLM_BATCH_EXTRACTION_THRESHOLDS,
        NOTION_INTEGRATION_THRESHOLDS,
        NOTION_READ_THRESHOLDS,
        NOTION_WRITE_THRESHOLDS,
        PIPELINE_THRESHOLDS,
    ]

    for thresholds in all_thresholds:
        errors = thresholds.validate()
        if errors:
            print(f"Threshold validation errors: {errors}")
            return False

    return True


# Threshold Summary for Documentation
THRESHOLD_SUMMARY = {
    "email_processing": {
        "max_response_time": 5.0,
        "max_processing_time": 10.0,
        "min_throughput": 0.1,
        "max_error_rate": 0.1,
    },
    "email_parsing": {
        "max_processing_time": 1.0,
        "min_throughput": 10.0,
        "max_error_rate": 0.05,
    },
    "email_text_extraction": {
        "max_processing_time": 0.5,
        "min_throughput": 20.0,
        "max_error_rate": 0.01,
    },
    "llm_extraction": {
        "max_response_time": 5.0,
        "max_processing_time": 5.0,
        "min_throughput": 0.2,
        "max_error_rate": 0.05,
    },
    "llm_batch_extraction": {
        "max_processing_time": 30.0,
        "min_throughput": 0.15,
        "max_error_rate": 0.1,
    },
    "notion_integration": {
        "max_response_time": 3.0,
        "max_processing_time": 5.0,
        "min_throughput": 0.3,
        "max_error_rate": 0.05,
    },
    "notion_read": {
        "max_response_time": 3.0,
        "max_error_rate": 0.1,
    },
    "notion_write": {
        "max_response_time": 5.0,
        "max_error_rate": 0.1,
    },
    "pipeline": {
        "max_processing_time": 15.0,
        "min_throughput": 0.05,
        "max_error_rate": 0.1,
    },
}


if __name__ == "__main__":
    # Validate all thresholds on module execution
    import json

    print("=" * 70)
    print("Performance Threshold Validation")
    print("=" * 70)

    is_valid = validate_thresholds()

    if is_valid:
        print("✅ All thresholds are valid")
        print()
        print("Threshold Summary:")
        print(json.dumps(THRESHOLD_SUMMARY, indent=2))
    else:
        print("❌ Threshold validation failed")
