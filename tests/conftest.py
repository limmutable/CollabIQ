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
    from error_handling.circuit_breaker import CircuitBreaker

    # Reset all circuit breaker instances
    CircuitBreaker._instances = {}

    yield

    # Clean up after test
    CircuitBreaker._instances = {}
