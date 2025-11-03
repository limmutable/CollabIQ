# API Contract: GeminiAdapter Extension for Company Matching

**Interface**: `GeminiAdapter.extract_entities()`
**Version**: Phase 2b (extends Phase 1b)
**Date**: 2025-11-02

## Method Signature

```python
class GeminiAdapter(LLMProvider):
    def extract_entities(
        self,
        email_text: str,
        company_context: Optional[str] = None  # NEW parameter
    ) -> ExtractedEntities:
        """Extract 5 key entities from email with optional company matching.

        Args:
            email_text: Cleaned email body (Korean/English/mixed)
            company_context: Optional markdown-formatted company list from
                           NotionIntegrator.format_for_llm(). If provided,
                           enables company matching and populates matched_*
                           fields in return value. If None, behaves as Phase 1b
                           (extraction only, matched fields = None).

        Returns:
            ExtractedEntities: Pydantic model with 5 entities (Phase 1b) +
                             4 matching fields (Phase 2b):
                             - matched_company_id: Notion page ID or None
                             - matched_partner_id: Notion page ID or None
                             - startup_match_confidence: float 0.0-1.0 or None
                             - partner_match_confidence: float 0.0-1.0 or None

        Raises:
            LLMAPIError: Gemini API request failed
            LLMAuthenticationError: Invalid API key
            LLMRateLimitError: Rate limit exceeded (429)
            LLMTimeoutError: Request timeout
            LLMValidationError: Invalid response schema

        Examples:
            >>> # Phase 1b mode (backward compatible)
            >>> entities = adapter.extract_entities("본봄 파일럿 킥오프")
            >>> assert entities.matched_company_id is None

            >>> # Phase 2b mode (with matching)
            >>> company_ctx = "## Portfolio\\n- 본봄 (ID: abc123)"
            >>> entities = adapter.extract_entities("본봄 파일럿 킥오프", company_ctx)
            >>> assert entities.matched_company_id == "abc123"
            >>> assert entities.startup_match_confidence >= 0.90
        """
```

## Contract Tests (TDD Red Phase)

```python
# tests/contract/test_gemini_adapter_matching_contract.py
import pytest
from src.llm_adapters.gemini_adapter import GeminiAdapter
from src.llm_provider.types import ExtractedEntities

class TestGeminiAdapterMatchingContract:
    """Contract tests for Phase 2b company matching extension."""

    def test_backward_compatibility_without_company_context(self):
        """MUST: Phase 1b mode works when company_context=None."""
        adapter = GeminiAdapter(api_key="test_key")
        entities = adapter.extract_entities("브레이크앤컴퍼니와 협업")

        assert isinstance(entities, ExtractedEntities)
        assert entities.matched_company_id is None
        assert entities.matched_partner_id is None
        assert entities.startup_match_confidence is None
        assert entities.partner_match_confidence is None

    def test_matching_enabled_with_company_context(self):
        """MUST: Phase 2b matching populates matched_* fields when company_context provided."""
        adapter = GeminiAdapter(api_key=os.getenv("GEMINI_API_KEY"))
        company_ctx = "## Portfolio Companies\\n- 브레이크앤컴퍼니 (ID: abc123)"

        entities = adapter.extract_entities("브레이크앤컴퍼니와 협업", company_context=company_ctx)

        assert entities.matched_company_id is not None
        assert entities.startup_match_confidence is not None
        assert 0.0 <= entities.startup_match_confidence <= 1.0

    def test_confidence_threshold_enforcement(self):
        """MUST: Low confidence (<0.70) returns null matched_company_id."""
        adapter = GeminiAdapter(api_key=os.getenv("GEMINI_API_KEY"))
        company_ctx = "## Portfolio Companies\\n- Known Company (ID: xyz789)"

        # Email with unknown company
        entities = adapter.extract_entities("UnknownCorp와 협업", company_context=company_ctx)

        if entities.startup_match_confidence and entities.startup_match_confidence < 0.70:
            assert entities.matched_company_id is None

    def test_return_type_validation(self):
        """MUST: Return value is always valid ExtractedEntities."""
        adapter = GeminiAdapter(api_key=os.getenv("GEMINI_API_KEY"))

        entities = adapter.extract_entities("test email")
        assert isinstance(entities, ExtractedEntities)

        # Pydantic validation should pass
        entities.model_validate(entities.model_dump())
```

## Success Criteria Mapping

| Success Criterion | Contract Enforcement |
|-------------------|---------------------|
| SC-001: ≥85% accuracy | Validated in integration tests, not contract |
| SC-002: Confidence calibration | `assert 0.0 <= confidence <= 1.0` |
| SC-003: ≤3s performance | Measured in integration tests, not contract |
| SC-004: ≥90% no-match precision | Validated in integration tests |
| SC-005: ≥80% fuzzy matching | Validated in integration tests |

## Non-Functional Requirements

- **Idempotency**: Same inputs → same outputs (no side effects)
- **Thread Safety**: Single-threaded usage (no concurrency guarantees needed for MVP)
- **Error Handling**: All LLM exceptions propagate with context (no silent failures)
- **Logging**: Log all matching attempts with confidence scores for post-hoc analysis
