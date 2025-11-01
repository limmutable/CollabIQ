"""Pytest configuration for CollabIQ tests.

This module configures pytest for the CollabIQ test suite, including:
- Python path setup for importing src modules
- Shared fixtures
- Test markers
"""

import sys
from pathlib import Path

# Add src directory to Python path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))
