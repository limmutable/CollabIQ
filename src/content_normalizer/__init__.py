"""
Content normalizer for cleaning email text.

This package contains the ContentNormalizer class and supporting utilities for
removing signatures, quoted threads, and disclaimers from email body text.
"""

from .normalizer import CleaningResult, ContentNormalizer

__all__ = [
    "ContentNormalizer",
    "CleaningResult",
]
