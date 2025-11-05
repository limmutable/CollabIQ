"""
End-to-End Test Harness for MVP Pipeline Validation

This package provides utilities for testing the complete CollabIQ MVP pipeline:
- Email reception → Entity extraction → Company matching → Classification → Notion write

Components:
- models: Pydantic data models for test runs, errors, and performance metrics
- runner: E2E test orchestrator
- error_collector: Error tracking and categorization
- performance_tracker: Timing and resource metrics
- report_generator: Test summary and error reports
- validators: Data integrity checks
"""

__version__ = "0.1.0"
