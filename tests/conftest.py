"""Pytest configuration for CollabIQ tests.

This module configures pytest for the CollabIQ test suite, including:
- Python path setup for importing src modules
- Shared fixtures
- Test markers
"""

import sys
from pathlib import Path
import pytest

# Add src directory to Python path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))


@pytest.fixture(autouse=True)
def reset_circuit_breakers():
    """Reset all circuit breakers before each test to ensure test isolation."""
    from error_handling.circuit_breaker import (
        gmail_circuit_breaker,
        gemini_circuit_breaker,
        notion_circuit_breaker,
        infisical_circuit_breaker,
        CircuitState,
    )

    # Reset all global circuit breaker instances to CLOSED state
    for cb in [gmail_circuit_breaker, gemini_circuit_breaker, notion_circuit_breaker, infisical_circuit_breaker]:
        cb.state_obj.state = CircuitState.CLOSED
        cb.state_obj.failure_count = 0
        cb.state_obj.success_count = 0
        cb.state_obj.last_failure_time = None
        cb.state_obj.open_timestamp = None

    yield

    # Clean up after test - reset to CLOSED
    for cb in [gmail_circuit_breaker, gemini_circuit_breaker, notion_circuit_breaker, infisical_circuit_breaker]:
        cb.state_obj.state = CircuitState.CLOSED
        cb.state_obj.failure_count = 0
        cb.state_obj.success_count = 0
        cb.state_obj.last_failure_time = None
        cb.state_obj.open_timestamp = None
