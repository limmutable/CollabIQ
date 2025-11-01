"""Unit tests for InfisicalClient secret management integration.

Tests cover initialization, authentication, secret retrieval, caching,
and fallback scenarios per TDD approach - these tests MUST FAIL before
implementation begins.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from config.infisical_client import (
    InfisicalAuthError,
    InfisicalCacheMissError,
    InfisicalClient,
    InfisicalConnectionError,
    SecretNotFoundError,
)
from config.settings import Settings


@pytest.fixture
def mock_settings():
    """Create mock Settings with Infisical enabled."""
    settings = Mock(spec=Settings)
    settings.infisical_enabled = True
    settings.infisical_host = "https://app.infisical.com"
    settings.infisical_project_id = "test-project-123"
    settings.infisical_environment = "dev"
    settings.infisical_client_id = "test-client-id"
    settings.infisical_client_secret = "test-client-secret"
    settings.infisical_cache_ttl = 60
    return settings


@pytest.fixture
def mock_settings_disabled():
    """Create mock Settings with Infisical disabled."""
    settings = Mock(spec=Settings)
    settings.infisical_enabled = False
    return settings


class TestInfisicalClientInitialization:
    """Test InfisicalClient initialization and configuration."""

    def test_init_with_enabled_settings(self, mock_settings):
        """Test client initializes correctly when Infisical is enabled."""
        client = InfisicalClient(mock_settings)

        assert client.settings == mock_settings
        assert client.enabled is True
        assert client._sdk_client is None  # Not initialized until authenticate()
        assert client._cache == {}
        assert client._cache_timestamps == {}

    def test_init_with_disabled_settings(self, mock_settings_disabled):
        """Test client initializes but stays disabled when Infisical is off."""
        client = InfisicalClient(mock_settings_disabled)

        assert client.enabled is False
        assert client._sdk_client is None

    def test_init_validates_required_fields(self):
        """Test initialization fails when required config fields are missing."""
        settings = Mock(spec=Settings)
        settings.infisical_enabled = True
        settings.infisical_project_id = None  # Missing required field

        with pytest.raises(ValueError, match="project_id is required"):
            InfisicalClient(settings)

    def test_init_validates_environment_slug(self):
        """Test initialization validates environment is one of: dev, staging, prod."""
        settings = Mock(spec=Settings)
        settings.infisical_enabled = True
        settings.infisical_project_id = "test-project"
        settings.infisical_environment = "invalid-env"

        with pytest.raises(
            ValueError, match="environment must be one of: dev, staging, prod"
        ):
            InfisicalClient(settings)


class TestInfisicalClientAuthentication:
    """Test InfisicalClient authentication with Universal Auth."""

    @patch("src.config.infisical_client.InfisicalClient")
    def test_authenticate_success(self, mock_sdk, mock_settings):
        """Test successful authentication with valid credentials."""
        # Mock SDK authentication
        mock_sdk_instance = MagicMock()
        mock_sdk.return_value = mock_sdk_instance

        client = InfisicalClient(mock_settings)
        client.authenticate()

        assert client._sdk_client is not None
        assert client.is_connected() is True

    @patch("src.config.infisical_client.InfisicalClient")
    def test_authenticate_invalid_credentials(self, mock_sdk, mock_settings):
        """Test authentication fails with invalid client_id/client_secret."""
        mock_sdk.side_effect = Exception("Invalid client credentials")

        client = InfisicalClient(mock_settings)

        with pytest.raises(InfisicalAuthError, match="Invalid client credentials"):
            client.authenticate()

    @patch("src.config.infisical_client.InfisicalClient")
    def test_authenticate_connection_timeout(self, mock_sdk, mock_settings):
        """Test authentication fails when network connection times out."""
        mock_sdk.side_effect = TimeoutError("Connection timeout")

        client = InfisicalClient(mock_settings)

        with pytest.raises(
            InfisicalConnectionError, match="Connection timeout"
        ):
            client.authenticate()

    def test_authenticate_when_disabled(self, mock_settings_disabled):
        """Test authenticate() does nothing when Infisical is disabled."""
        client = InfisicalClient(mock_settings_disabled)
        client.authenticate()  # Should not raise

        assert client._sdk_client is None
        assert client.is_connected() is False


class TestInfisicalClientSecretRetrieval:
    """Test secret retrieval with three-tier fallback logic."""

    @patch("src.config.infisical_client.InfisicalClient")
    def test_get_secret_from_api_success(self, mock_sdk, mock_settings):
        """Test successful secret retrieval from Infisical API."""
        mock_sdk_instance = MagicMock()
        mock_sdk_instance.get_secret.return_value = {"value": "api-secret-value"}
        mock_sdk.return_value = mock_sdk_instance

        client = InfisicalClient(mock_settings)
        client.authenticate()

        secret = client.get_secret("GEMINI_API_KEY")

        assert secret == "api-secret-value"
        assert "GEMINI_API_KEY" in client._cache
        assert client._cache["GEMINI_API_KEY"] == "api-secret-value"

    @patch("src.config.infisical_client.InfisicalClient")
    def test_get_secret_from_cache(self, mock_sdk, mock_settings):
        """Test secret retrieval from cache when TTL not expired."""
        client = InfisicalClient(mock_settings)
        client._cache["CACHED_KEY"] = "cached-value"
        client._cache_timestamps["CACHED_KEY"] = 1234567890  # Recent timestamp

        secret = client.get_secret("CACHED_KEY")

        assert secret == "cached-value"
        # SDK should not be called since cache hit
        mock_sdk.assert_not_called()

    @patch("src.config.infisical_client.InfisicalClient")
    @patch.dict("os.environ", {"GEMINI_API_KEY": "env-fallback-value"})
    def test_get_secret_fallback_to_env(self, mock_sdk, mock_settings):
        """Test fallback to .env file when API fails and cache expired."""
        mock_sdk.side_effect = InfisicalConnectionError("API unreachable")

        client = InfisicalClient(mock_settings)

        secret = client.get_secret("GEMINI_API_KEY")

        assert secret == "env-fallback-value"

    @patch("src.config.infisical_client.InfisicalClient")
    def test_get_secret_not_found(self, mock_sdk, mock_settings):
        """Test SecretNotFoundError when secret doesn't exist anywhere."""
        mock_sdk_instance = MagicMock()
        mock_sdk_instance.get_secret.side_effect = Exception("Secret not found")
        mock_sdk.return_value = mock_sdk_instance

        client = InfisicalClient(mock_settings)
        client.authenticate()

        with pytest.raises(SecretNotFoundError, match="NONEXISTENT_KEY"):
            client.get_secret("NONEXISTENT_KEY")

    def test_get_secret_when_disabled_uses_env(self, mock_settings_disabled):
        """Test get_secret() falls back to .env when Infisical disabled."""
        with patch.dict("os.environ", {"API_KEY": "env-only-value"}):
            client = InfisicalClient(mock_settings_disabled)
            secret = client.get_secret("API_KEY")

            assert secret == "env-only-value"


class TestInfisicalClientBulkRetrieval:
    """Test get_all_secrets() bulk retrieval with caching."""

    @patch("src.config.infisical_client.InfisicalClient")
    def test_get_all_secrets_success(self, mock_sdk, mock_settings):
        """Test bulk retrieval of all secrets from Infisical."""
        mock_sdk_instance = MagicMock()
        mock_sdk_instance.get_all_secrets.return_value = {
            "GEMINI_API_KEY": "secret-1",
            "NOTION_API_KEY": "secret-2",
            "GMAIL_TOKEN": "secret-3",
        }
        mock_sdk.return_value = mock_sdk_instance

        client = InfisicalClient(mock_settings)
        client.authenticate()

        secrets = client.get_all_secrets()

        assert len(secrets) == 3
        assert secrets["GEMINI_API_KEY"] == "secret-1"
        assert secrets["NOTION_API_KEY"] == "secret-2"
        # All secrets should be cached
        assert len(client._cache) == 3

    @patch("src.config.infisical_client.InfisicalClient")
    def test_get_all_secrets_caches_with_timestamp(self, mock_sdk, mock_settings):
        """Test get_all_secrets() updates cache with timestamps."""
        mock_sdk_instance = MagicMock()
        mock_sdk_instance.get_all_secrets.return_value = {
            "KEY1": "value1",
            "KEY2": "value2",
        }
        mock_sdk.return_value = mock_sdk_instance

        client = InfisicalClient(mock_settings)
        client.authenticate()

        with patch("time.time", return_value=1234567890):
            client.get_all_secrets()

        assert client._cache_timestamps["KEY1"] == 1234567890
        assert client._cache_timestamps["KEY2"] == 1234567890


class TestInfisicalClientCacheManagement:
    """Test cache refresh and invalidation logic."""

    def test_refresh_cache_success(self, mock_settings):
        """Test manual cache refresh via refresh_cache()."""
        with patch.object(
            InfisicalClient, "get_all_secrets", return_value={"KEY": "new-value"}
        ):
            client = InfisicalClient(mock_settings)
            client._cache["KEY"] = "old-value"

            client.refresh_cache()

            assert client._cache["KEY"] == "new-value"

    def test_cache_ttl_expiration(self, mock_settings):
        """Test cache expires after TTL seconds (60 default)."""
        client = InfisicalClient(mock_settings)
        client._cache["EXPIRED_KEY"] = "old-value"
        client._cache_timestamps["EXPIRED_KEY"] = 1000000000  # Very old timestamp

        # Mock current time to be 120 seconds later (> 60 TTL)
        with patch("time.time", return_value=1000000120):
            is_expired = client._is_cache_expired("EXPIRED_KEY")

        assert is_expired is True

    def test_cache_ttl_not_expired(self, mock_settings):
        """Test cache is valid within TTL window."""
        client = InfisicalClient(mock_settings)
        client._cache["FRESH_KEY"] = "fresh-value"
        client._cache_timestamps["FRESH_KEY"] = 1000000000

        # Mock current time to be 30 seconds later (< 60 TTL)
        with patch("time.time", return_value=1000000030):
            is_expired = client._is_cache_expired("FRESH_KEY")

        assert is_expired is False


class TestInfisicalClientConnectionStatus:
    """Test is_connected() health check."""

    @patch("src.config.infisical_client.InfisicalClient")
    def test_is_connected_true_when_authenticated(self, mock_sdk, mock_settings):
        """Test is_connected() returns True after successful auth."""
        mock_sdk_instance = MagicMock()
        mock_sdk.return_value = mock_sdk_instance

        client = InfisicalClient(mock_settings)
        client.authenticate()

        assert client.is_connected() is True

    def test_is_connected_false_when_not_authenticated(self, mock_settings):
        """Test is_connected() returns False before authentication."""
        client = InfisicalClient(mock_settings)

        assert client.is_connected() is False

    def test_is_connected_false_when_disabled(self, mock_settings_disabled):
        """Test is_connected() returns False when Infisical disabled."""
        client = InfisicalClient(mock_settings_disabled)

        assert client.is_connected() is False
