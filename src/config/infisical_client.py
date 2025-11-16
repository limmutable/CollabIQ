"""Infisical secret management client for centralized credential storage.

Provides integration with Infisical API for secure secret retrieval with
three-tier fallback: API → SDK cache → .env file.

Usage:
    from config.infisical_client import InfisicalClient

    client = InfisicalClient(settings)
    secret = client.get_secret("GEMINI_API_KEY")
"""

import logging
import os
import time
from typing import Any, Dict, Optional

try:
    from infisical_sdk import InfisicalSDKClient
    INFISICAL_AVAILABLE = True
except ImportError:
    InfisicalSDKClient = None  # type: ignore
    INFISICAL_AVAILABLE = False

logger = logging.getLogger(__name__)


class InfisicalAuthError(Exception):
    """Authentication failed with Infisical.

    Raised when Universal Auth credentials (client_id/client_secret) are
    invalid or expired.

    Example:
        try:
            client.authenticate()
        except InfisicalAuthError as e:
            logger.error(f"Auth failed: {e}")
            # Fall back to .env file
    """

    pass


class InfisicalConnectionError(Exception):
    """Cannot connect to Infisical host.

    Raised when network connection to Infisical API fails (timeout, DNS
    resolution, network unreachable).

    Example:
        try:
            client.get_secret("API_KEY")
        except InfisicalConnectionError as e:
            logger.warning(f"Connection failed: {e}")
            # Fall back to cache or .env
    """

    pass


class SecretNotFoundError(Exception):
    """Secret not found in Infisical.

    Raised when requested secret key does not exist in the specified
    project/environment.

    Example:
        try:
            client.get_secret("NONEXISTENT_KEY")
        except SecretNotFoundError as e:
            logger.error(f"Secret missing: {e}")
            # Fall back to .env or raise error
    """

    pass


class InfisicalCacheMissError(Exception):
    """Cache expired and API unreachable.

    Raised when SDK cache has expired and fresh API fetch fails. Indicates
    need to fall back to .env file or manual intervention.

    Example:
        try:
            client.get_secret("API_KEY")
        except InfisicalCacheMissError as e:
            logger.warning(f"Cache miss: {e}")
            # Fall back to .env file
    """

    pass


class InfisicalClient:
    """Client for Infisical secret management with three-tier fallback.

    Implements secret retrieval with automatic fallback:
    1. Infisical API (fresh secret)
    2. SDK cache (TTL-based)
    3. .env file (last resort)

    Attributes:
        settings: Application settings with Infisical configuration
        enabled: Whether Infisical integration is active
        _sdk_client: Infisical SDK client instance
        _cache: In-memory secret cache (key -> value)
        _cache_timestamps: Cache entry timestamps for TTL expiration

    Example:
        >>> settings = get_settings()
        >>> client = InfisicalClient(settings)
        >>> client.authenticate()
        >>> api_key = client.get_secret("GEMINI_API_KEY")
    """

    def __init__(self, settings: Any) -> None:
        """Initialize InfisicalClient with settings validation.

        Args:
            settings: Application settings with Infisical config

        Raises:
            ValueError: If Infisical enabled but required fields missing
        """
        self.settings = settings
        self.enabled = settings.infisical_enabled
        self._sdk_client: Optional[InfisicalSDKClient] = None
        self._cache: Dict[str, str] = {}
        self._cache_timestamps: Dict[str, float] = {}

        # Validate required fields if enabled
        if self.enabled:
            if not settings.infisical_project_id:
                raise ValueError(
                    "infisical_project_id is required when Infisical is enabled"
                )
            if not settings.infisical_environment:
                raise ValueError(
                    "infisical_environment is required when Infisical is enabled"
                )
            if not settings.infisical_client_id:
                raise ValueError(
                    "infisical_client_id is required when Infisical is enabled"
                )
            if not settings.infisical_client_secret:
                raise ValueError(
                    "infisical_client_secret is required when Infisical is enabled"
                )

            # Validate environment slug (FR-005: environment-specific secret management)
            valid_envs = {"development", "production"}
            if settings.infisical_environment not in valid_envs:
                raise ValueError(
                    f"Invalid environment slug '{settings.infisical_environment}'. "
                    f"Must be one of: {', '.join(sorted(valid_envs))}. "
                    f"Please set INFISICAL_ENVIRONMENT to 'development' or 'production'."
                )

    def authenticate(self) -> None:
        """Authenticate with Infisical using Universal Auth credentials.

        Raises:
            InfisicalAuthError: If authentication fails (invalid credentials)
            InfisicalConnectionError: If connection to Infisical host fails
        """
        if not self.enabled:
            logger.info("Infisical is disabled - secrets will be read from .env file")
            return

        if not INFISICAL_AVAILABLE:
            logger.warning("Infisical SDK not available - falling back to .env file")
            self.enabled = False
            return

        try:
            logger.info(
                f"Connecting to Infisical: {self.settings.infisical_host} "
                f"(project: {self.settings.infisical_project_id}, "
                f"env: {self.settings.infisical_environment})"
            )

            # Initialize SDK client with host and cache TTL
            self._sdk_client = InfisicalSDKClient(
                host=self.settings.infisical_host,
                cache_ttl=self.settings.infisical_cache_ttl,
            )

            # Authenticate with Universal Auth (machine identity)
            self._sdk_client.auth.universal_auth.login(
                client_id=self.settings.infisical_client_id,
                client_secret=self.settings.infisical_client_secret,
            )

            logger.info(
                f"✓ Successfully authenticated with Infisical "
                f"(cache TTL: {self.settings.infisical_cache_ttl}s)"
            )

        except TimeoutError as e:
            logger.error(f"Infisical connection timeout - will fall back to .env: {e}")
            raise InfisicalConnectionError(
                f"Connection timeout while connecting to {self.settings.infisical_host}. "
                f"Please check your network connection and verify the Infisical host is reachable."
            ) from e
        except Exception as e:
            # Check if it's an auth error vs connection error
            error_msg = str(e).lower()
            if (
                "credential" in error_msg
                or "auth" in error_msg
                or "invalid" in error_msg
                or "401" in error_msg
                or "403" in error_msg
            ):
                logger.error(
                    f"Infisical authentication failed - will fall back to .env: {e}"
                )
                raise InfisicalAuthError(
                    f"Authentication failed with Infisical. Invalid machine identity credentials.\n"
                    f"Please verify:\n"
                    f"  1. INFISICAL_CLIENT_ID is correct (starts with 'machine-identity-')\n"
                    f"  2. INFISICAL_CLIENT_SECRET is correct (not expired)\n"
                    f"  3. Machine identity has read access to '{self.settings.infisical_environment}' environment\n"
                    f"  4. Project ID '{self.settings.infisical_project_id}' exists\n\n"
                    f"To regenerate credentials:\n"
                    f"  1. Go to Infisical dashboard → Project Settings → Machine Identities\n"
                    f"  2. Select your machine identity\n"
                    f"  3. Navigate to Authentication → Universal Auth → Generate Credentials\n\n"
                    f"Original error: {e}"
                ) from e
            else:
                logger.error(
                    f"Infisical connection failed - will fall back to .env: {e}"
                )
                raise InfisicalConnectionError(
                    f"Failed to connect to Infisical at {self.settings.infisical_host}.\n"
                    f"Please check:\n"
                    f"  1. Network connectivity (try: ping app.infisical.com)\n"
                    f"  2. Firewall/proxy settings\n"
                    f"  3. INFISICAL_HOST is correct (default: https://app.infisical.com)\n\n"
                    f"Temporary workaround: Set INFISICAL_ENABLED=false in .env to use local secrets\n\n"
                    f"Original error: {e}"
                ) from e

    def get_secret(self, key: str, secret_path: str = "/") -> str:
        """Retrieve secret with three-tier fallback logic.

        1. Try Infisical API (if enabled and authenticated)
        2. Fall back to cache (SDK built-in cache)
        3. Fall back to .env file

        Args:
            key: Secret key to retrieve (e.g., "GEMINI_API_KEY")
            secret_path: Infisical secret path (default: "/")

        Returns:
            Secret value as string

        Raises:
            SecretNotFoundError: If secret not found in any source
            InfisicalCacheMissError: If cache expired and API unreachable
        """
        # If Infisical disabled, go straight to .env
        if not self.enabled:
            logger.debug(f"Retrieving '{key}' from .env (Infisical disabled)")
            return self._get_from_env(key)

        # Check our local cache first (if not expired)
        if key in self._cache and not self._is_cache_expired(key):
            logger.debug(
                f"✓ Retrieved '{key}' from cache (age: {int(time.time() - self._cache_timestamps[key])}s)"
            )
            return self._cache[key]

        # Cache expired or miss - fetch from Infisical API
        is_refresh = key in self._cache
        if is_refresh:
            logger.info(
                f"Cache expired for '{key}' (TTL: {self.settings.infisical_cache_ttl}s) - refreshing from Infisical"
            )

        # Try fetching from Infisical API (SDK handles its own caching)
        if self._sdk_client:
            try:
                secret_response = self._sdk_client.secrets.get_secret_by_name(
                    secret_name=key,
                    environment_slug=self.settings.infisical_environment,
                    project_id=self.settings.infisical_project_id,
                    secret_path=secret_path,
                )

                # Cache the secret in our local cache
                value = secret_response.secretValue
                self._cache[key] = value
                self._cache_timestamps[key] = time.time()

                if is_refresh:
                    logger.info(f"✓ Cache refreshed for '{key}' from Infisical API")
                else:
                    logger.info(f"✓ Retrieved '{key}' from Infisical API (first fetch)")

                return value

            except InfisicalConnectionError as e:
                # API unreachable, fall back to .env
                logger.warning(
                    f"Infisical API unreachable for '{key}', falling back to .env: {e}"
                )
                return self._get_from_env(key)
            except Exception as e:
                # Secret not found in Infisical or other API error
                if "not found" in str(e).lower() or "404" in str(e):
                    # Try .env as last resort
                    logger.warning(
                        f"Secret '{key}' not found in Infisical, falling back to .env"
                    )
                    return self._get_from_env(key)
                else:
                    # Connection error, fall back to .env
                    logger.warning(
                        f"Infisical error for '{key}', falling back to .env: {e}"
                    )
                    return self._get_from_env(key)

        # No SDK client, fall back to .env
        logger.warning(f"No Infisical client available, retrieving '{key}' from .env")
        return self._get_from_env(key)

    def get_all_secrets(self, secret_path: str = "/") -> Dict[str, str]:
        """Retrieve all secrets for current project/environment.

        Args:
            secret_path: Infisical secret path (default: "/")

        Returns:
            Dictionary of all secrets (key -> value)

        Raises:
            InfisicalConnectionError: If API call fails
        """
        if not self.enabled or not self._sdk_client:
            return {}

        try:
            logger.info(
                f"Fetching all secrets from Infisical (environment: {self.settings.infisical_environment})"
            )

            secrets_response = self._sdk_client.secrets.list_secrets(
                environment_slug=self.settings.infisical_environment,
                project_id=self.settings.infisical_project_id,
                secret_path=secret_path,
            )

            # Cache all secrets
            secrets_dict = {}
            current_time = time.time()
            for secret in secrets_response.secrets:
                key = secret.secretKey
                value = secret.secretValue
                secrets_dict[key] = value
                self._cache[key] = value
                self._cache_timestamps[key] = current_time

            logger.info(
                f"✓ Cache refreshed with {len(secrets_dict)} secrets from Infisical (TTL: {self.settings.infisical_cache_ttl}s)"
            )

            return secrets_dict

        except Exception as e:
            raise InfisicalConnectionError(f"Failed to fetch all secrets: {e}") from e

    def refresh_cache(self) -> None:
        """Manually refresh cache by fetching all secrets from API.

        Useful for proactively warming cache or after config changes.
        """
        if self.enabled and self._sdk_client:
            self.get_all_secrets()

    def is_connected(self) -> bool:
        """Check if client is authenticated and connected to Infisical.

        Returns:
            True if SDK client is initialized and ready, False otherwise
        """
        return self.enabled and self._sdk_client is not None

    def _is_cache_expired(self, key: str) -> bool:
        """Check if cached secret has exceeded TTL.

        Args:
            key: Secret key to check

        Returns:
            True if cache expired, False if still valid
        """
        if key not in self._cache_timestamps:
            return True

        elapsed = time.time() - self._cache_timestamps[key]
        return elapsed > self.settings.infisical_cache_ttl

    def _get_from_env(self, key: str) -> str:
        """Fall back to .env file for secret retrieval.

        Args:
            key: Environment variable name

        Returns:
            Value from environment variable

        Raises:
            SecretNotFoundError: If key not found in environment
        """
        value = os.getenv(key)
        if value is None:
            raise SecretNotFoundError(
                f"Secret '{key}' not found in Infisical or .env file"
            )
        return value
