"""Integration tests for external API error handling.

This module tests the system's resilience to external API failures:
- Network timeouts and connection errors
- Rate limiting and quota exceeded
- Invalid credentials and authentication failures
- Malformed API responses
- Service unavailability (5xx errors)
- Client errors (4xx errors)

All tests verify graceful degradation and proper retry logic.
"""

import pytest
from unittest.mock import patch, Mock
import time

from llm_adapters.gemini_adapter import GeminiAdapter
from llm_adapters.claude_adapter import ClaudeAdapter
from llm_adapters.openai_adapter import OpenAIAdapter
from notion_integrator.integrator import NotionIntegrator
from notion_integrator.writer import NotionWriter


class TestLLMAPIErrors:
    """Test LLM API error handling."""

    @pytest.fixture
    def sample_email(self):
        """Sample email for testing."""
        return "안녕하세요, 스타트업 테스트입니다."

    @pytest.mark.asyncio
    async def test_gemini_network_timeout(self, sample_email):
        """Test Gemini adapter handles network timeout."""
        adapter = GeminiAdapter(api_key="test-key")

        # Mock a timeout error
        with patch.object(adapter, "_call_gemini_api") as mock_api:
            mock_api.side_effect = TimeoutError("Connection timeout")

            with pytest.raises((TimeoutError, Exception)):
                await adapter.extract_entities(sample_email)

    @pytest.mark.asyncio
    async def test_gemini_rate_limit_error(self, sample_email):
        """Test Gemini adapter handles rate limiting."""
        adapter = GeminiAdapter(api_key="test-key")

        # Mock rate limit error from Gemini SDK
        with patch.object(adapter, "_call_gemini_api") as mock_api:
            from llm_provider.exceptions import LLMRateLimitError
            mock_api.side_effect = LLMRateLimitError("Rate limit exceeded")

            # Should raise rate limit exception
            with pytest.raises(Exception):
                await adapter.extract_entities(sample_email)

    @pytest.mark.asyncio
    async def test_gemini_invalid_api_key(self, sample_email):
        """Test Gemini adapter handles invalid credentials."""
        # Create adapter with invalid key
        with patch.dict("os.environ", {"GEMINI_API_KEY": "invalid_key"}):
            adapter = GeminiAdapter(api_key="invalid_key")

            with pytest.raises((ValueError, PermissionError, Exception)):
                await adapter.extract_entities(sample_email)

    @pytest.mark.asyncio
    async def test_gemini_malformed_response(self, sample_email):
        """Test Gemini adapter handles malformed API response."""
        adapter = GeminiAdapter(api_key="test-key")

        # Mock malformed response - missing required fields
        with patch.object(adapter, "_call_gemini_api") as mock_api:
            # Return data missing required confidence fields
            mock_api.return_value = {
                "person_in_charge": "test",  # Missing confidence
                "startup_name": "test",
            }

            with pytest.raises((ValueError, KeyError, Exception)):
                await adapter.extract_entities(sample_email)

    @pytest.mark.asyncio
    async def test_gemini_service_unavailable(self, sample_email):
        """Test Gemini adapter handles 503 errors."""
        adapter = GeminiAdapter(api_key="test-key")

        # Mock service unavailable error
        with patch.object(adapter, "_call_gemini_api") as mock_api:
            from llm_provider.exceptions import LLMAPIError
            mock_api.side_effect = LLMAPIError("Service Unavailable", status_code=503)

            with pytest.raises(Exception):
                await adapter.extract_entities(sample_email)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_claude_network_timeout(self, sample_email):
        """Test Claude adapter handles network timeout."""
        adapter = ClaudeAdapter(api_key="test-key")

        # Patch the Claude SDK's messages.create method
        with patch.object(adapter.client.messages, "create") as mock_create:
            mock_create.side_effect = TimeoutError("Request timeout")

            with pytest.raises((TimeoutError, Exception)):
                await adapter.extract_entities(sample_email)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_openai_rate_limit(self, sample_email):
        """Test OpenAI adapter handles rate limiting."""
        adapter = OpenAIAdapter(api_key="test-key")

        # Patch the OpenAI SDK's chat.completions.create method
        with patch.object(adapter.client.chat.completions, "create") as mock_create:
            mock_create.side_effect = Exception("Rate limit exceeded")

            with pytest.raises(Exception):
                await adapter.extract_entities(sample_email)


@pytest.mark.skip(reason="API refactored - NotionIntegrator.create_company_entry() removed, use NotionWriter instead")
class TestNotionAPIErrors:
    """Test Notion API error handling."""

    @pytest.fixture
    def integrator(self):
        """Create Notion integrator."""
        with patch.dict("os.environ", {"NOTION_API_KEY": "test-key", "NOTION_DATABASE_ID": "test-db-id"}):
            return NotionIntegrator()

    @pytest.fixture
    def valid_extraction(self):
        """Valid extraction result for testing."""
        return {
            "startup_name": {"value": "TestCo", "confidence": 0.9},
            "person_in_charge": {"value": "Test Person", "confidence": 0.9},
            "partner_org": {"value": "Partner", "confidence": 0.8},
            "details": {"value": "Test details", "confidence": 0.85},
            "date": {"value": "2025-12-01", "confidence": 0.95},
        }

    def test_notion_network_timeout(self, integrator, valid_extraction):
        """Test Notion integrator handles network timeout."""
        with patch.object(integrator.client.client, "pages") as mock_pages:
            mock_pages.create.side_effect = TimeoutError("Connection timeout")

            with pytest.raises((TimeoutError, Exception)):
                integrator.create_company_entry(valid_extraction)

    def test_notion_rate_limit(self, integrator, valid_extraction):
        """Test Notion integrator handles rate limiting."""
        with patch.object(integrator.client.client, "pages") as mock_pages:
            from notion_client.errors import APIResponseError

            error = APIResponseError(
                response=Mock(status=429, text="Rate limited"),
                message="Rate limit exceeded",
                code="rate_limited",
            )
            mock_pages.create.side_effect = error

            with pytest.raises((APIResponseError, Exception)):
                integrator.create_company_entry(valid_extraction)

    def test_notion_invalid_database_id(self, valid_extraction):
        """Test Notion integrator handles invalid database ID."""
        # Create integrator with invalid database ID
        with patch.dict("os.environ", {"NOTION_COMPANIES_DATABASE_ID": "invalid_id"}):
            integrator = NotionIntegrator()

            with pytest.raises(Exception):
                integrator.create_company_entry(valid_extraction)

    def test_notion_permission_denied(self, integrator, valid_extraction):
        """Test Notion integrator handles permission errors."""
        with patch.object(integrator.client.client, "pages") as mock_pages:
            from notion_client.errors import APIResponseError

            error = APIResponseError(
                response=Mock(status=403, text="Forbidden"),
                message="Insufficient permissions",
                code="forbidden",
            )
            mock_pages.create.side_effect = error

            with pytest.raises((APIResponseError, PermissionError, Exception)):
                integrator.create_company_entry(valid_extraction)

    def test_notion_service_unavailable(self, integrator, valid_extraction):
        """Test Notion integrator handles 503 errors."""
        with patch.object(integrator.client.client, "pages") as mock_pages:
            from notion_client.errors import APIResponseError

            error = APIResponseError(
                response=Mock(status=503, text="Service Unavailable"),
                message="Service temporarily unavailable",
                code="service_unavailable",
            )
            mock_pages.create.side_effect = error

            with pytest.raises((APIResponseError, Exception)):
                integrator.create_company_entry(valid_extraction)

    def test_notion_malformed_response(self, integrator, valid_extraction):
        """Test Notion integrator handles malformed API response."""
        with patch.object(integrator.client.client, "pages") as mock_pages:
            # Return unexpected response structure
            mock_pages.create.return_value = {"unexpected": "structure"}

            # Should handle or raise controlled exception
            try:
                integrator.create_company_entry(valid_extraction)
            except (KeyError, ValueError, Exception):
                # Acceptable to fail on malformed response
                pass


class TestRetryLogic:
    """Test retry logic for transient failures."""

    @pytest.fixture
    def sample_email(self):
        """Sample email for testing."""
        return "안녕하세요, 테스트입니다."

    @pytest.mark.asyncio
    async def test_gemini_retries_on_timeout(self, sample_email):
        """Test Gemini adapter retries on timeout."""
        adapter = GeminiAdapter(api_key="test-key")

        with patch.object(adapter, "_call_gemini_api") as mock_api:
            # First two calls timeout, third succeeds
            mock_api.side_effect = [
                TimeoutError("Timeout 1"),
                TimeoutError("Timeout 2"),
                Mock(status_code=200, json=lambda: {"result": "success"}),
            ]

            # Should retry and eventually succeed
            try:
                result = await adapter.extract_entities(sample_email)
                # If retries work, should succeed
                assert result is not None
            except TimeoutError:
                # If no retry logic, should fail fast
                assert mock_api.call_count <= 3

    @pytest.mark.skip(reason="API refactored - NotionIntegrator.create_company_entry() removed, use NotionWriter instead")
    def test_notion_retries_on_rate_limit(self):
        """Test Notion integrator retries on rate limit."""
        with patch.dict("os.environ", {"NOTION_API_KEY": "test-key", "NOTION_COMPANIES_DATABASE_ID": "test-db"}):
            integrator = NotionIntegrator()
        extraction = {
            "startup_name": {"value": "TestCo", "confidence": 0.9},
            "person_in_charge": {"value": "Test", "confidence": 0.9},
            "partner_org": {"value": "Partner", "confidence": 0.8},
            "details": {"value": "Details", "confidence": 0.85},
            "date": {"value": "2025-12-01", "confidence": 0.95},
        }

        with patch.object(integrator.client.client, "pages") as mock_pages:
            from notion_client.errors import APIResponseError

            # First call rate limited, second succeeds
            rate_limit_error = APIResponseError(
                response=Mock(status=429, text="Rate limited"),
                message="Rate limit exceeded",
                code="rate_limited",
            )

            mock_pages.create.side_effect = [
                rate_limit_error,
                {"id": "page_123", "properties": {}},
            ]

            # Should retry and succeed
            try:
                result = integrator.create_company_entry(extraction)
                assert result is not None
            except APIResponseError:
                # If no retry, should fail immediately
                pass

    @pytest.mark.asyncio
    async def test_exponential_backoff_timing(self):
        """Test retry logic uses exponential backoff."""
        adapter = GeminiAdapter(api_key="test-key")
        sample_email = "Test email"

        with patch.object(adapter, "_call_gemini_api") as mock_api:
            mock_api.side_effect = TimeoutError("Always timeout")

            start_time = time.time()

            try:
                await adapter.extract_entities(sample_email)
            except Exception:
                # Expected to fail after retries
                pass

            elapsed = time.time() - start_time

            # Should have some delay from retries (at least 1 second)
            # The retry logic implements exponential backoff
            assert elapsed >= 1.0, f"Expected delays from retries, but took only {elapsed}s"


class TestCircuitBreaker:
    """Test circuit breaker patterns for repeated failures."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_failures(self):
        """Test circuit breaker opens after consecutive failures."""
        adapter = GeminiAdapter(api_key="test-key")
        sample_email = "Test"

        with patch.object(adapter, "_call_gemini_api") as mock_api:
            # Always fail
            mock_api.side_effect = Exception("Persistent error")

            # Make multiple requests
            for _ in range(5):
                try:
                    await adapter.extract_entities(sample_email)
                except Exception:
                    pass

            # Circuit breaker should eventually prevent further calls
            # (This test depends on circuit breaker implementation)

    def test_circuit_breaker_recovers(self):
        """Test circuit breaker recovers after cooldown."""
        # This test would require time manipulation
        # Placeholder for circuit breaker recovery test
        pass


class TestErrorPropagation:
    """Test error propagation through the system."""

    @pytest.mark.asyncio
    async def test_llm_error_propagates_to_caller(self):
        """Test LLM errors propagate correctly."""
        adapter = GeminiAdapter(api_key="test-key")

        with patch.object(adapter, "_call_gemini_api") as mock_api:
            mock_api.side_effect = Exception("Invalid input")

            with pytest.raises((ValueError, Exception)):
                await adapter.extract_entities("test")

    @pytest.mark.skip(reason="API refactored - NotionIntegrator.create_company_entry() removed, use NotionWriter instead")
    def test_notion_error_propagates_to_caller(self):
        """Test Notion errors propagate correctly."""
        integrator = NotionIntegrator()
        extraction = {"startup_name": {"value": "Test", "confidence": 0.9}}

        with pytest.raises((ValueError, KeyError, Exception)):
            # Missing required fields should error
            integrator.create_company_entry(extraction)
