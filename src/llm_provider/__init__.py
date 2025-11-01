"""LLM Provider abstraction layer for entity extraction.

This module provides an abstract interface for LLM-based entity extraction,
enabling swappability between different LLM providers (Gemini, GPT-4, Claude).
"""

from .exceptions import (
    LLMAPIError,
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMValidationError,
)
from .types import (
    BatchSummary,
    ConfidenceScores,
    ExtractedEntities,
    ExtractionBatch,
)

__all__ = [
    "LLMAPIError",
    "LLMAuthenticationError",
    "LLMRateLimitError",
    "LLMTimeoutError",
    "LLMValidationError",
    "BatchSummary",
    "ConfidenceScores",
    "ExtractedEntities",
    "ExtractionBatch",
]
