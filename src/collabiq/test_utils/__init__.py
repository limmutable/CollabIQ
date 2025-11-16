"""
Test Utils Library - Standalone library for testing utilities.

This library provides utilities for test cleanup, performance monitoring, and fuzz testing,
with both programmatic API and CLI interface per constitution principle II.

Usage (Python API):
    from src.collabiq.test_utils import cleanup_notion, monitor_performance, generate_fuzz_input

    result = cleanup_notion(database_id="abc123", test_run_id="test-001")
    # Returns: {"cleaned": 15, "errors": 0, "duration": 3.2}

Usage (CLI):
    python -m src.collabiq.test_utils.cli cleanup --database-id=abc123
    # Output: {"cleaned": 15, "errors": 0, "duration": 3.2}
"""

__version__ = "0.1.0"

# Library exports
from .notion_cleanup import cleanup_notion, NotionTestCleanup

# Future exports (to be implemented)
# from .performance_monitor import monitor_performance, assert_performance
# from .fuzz_generator import generate_fuzz_input

__all__ = [
    "cleanup_notion",
    "NotionTestCleanup",
]
