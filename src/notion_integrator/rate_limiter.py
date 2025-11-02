"""
Rate Limiter Implementation

Token bucket algorithm to enforce Notion API rate limit of 3 requests/second.
Provides async-safe rate limiting with request queuing.

Key Features:
- Token bucket algorithm for smooth rate limiting
- Async/await support with asyncio primitives
- Request queuing when rate limit reached
- Configurable rate and burst capacity
- Thread-safe operation

Usage:
    >>> limiter = RateLimiter(rate_per_second=3)
    >>> async with limiter:
    ...     # Make API call
    ...     response = await notion_client.databases.retrieve(db_id)
"""

import asyncio
import time
from typing import Optional


class RateLimiter:
    """
    Token bucket rate limiter for async operations.

    Enforces a maximum rate of requests per second using the token bucket
    algorithm. Supports burst capacity and smooth request distribution.

    Attributes:
        rate_per_second: Maximum requests per second
        capacity: Maximum tokens (burst capacity)
        tokens: Current available tokens
        last_update: Last time tokens were added
        _lock: Async lock for thread safety
    """

    def __init__(
        self,
        rate_per_second: float = 3.0,
        capacity: Optional[int] = None,
    ):
        """
        Initialize rate limiter.

        Args:
            rate_per_second: Maximum requests per second (default: 3.0 for Notion API)
            capacity: Maximum burst capacity (default: same as rate_per_second)
        """
        self.rate_per_second = rate_per_second
        self.capacity = capacity if capacity is not None else int(rate_per_second)
        self.tokens = float(self.capacity)
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()
        self._waiting_count = 0

    async def acquire(self, tokens: int = 1) -> None:
        """
        Acquire tokens from the bucket.

        Blocks until sufficient tokens are available. Tokens are refilled
        continuously at the configured rate.

        Args:
            tokens: Number of tokens to acquire (default: 1)

        Raises:
            ValueError: If tokens requested exceeds capacity
        """
        if tokens > self.capacity:
            raise ValueError(
                f"Cannot acquire {tokens} tokens (capacity: {self.capacity})"
            )

        async with self._lock:
            self._waiting_count += 1
            try:
                while True:
                    # Refill tokens based on elapsed time
                    now = time.monotonic()
                    elapsed = now - self.last_update
                    self.tokens = min(
                        self.capacity,
                        self.tokens + elapsed * self.rate_per_second,
                    )
                    self.last_update = now

                    # Check if enough tokens available
                    if self.tokens >= tokens:
                        self.tokens -= tokens
                        return

                    # Calculate wait time for next token
                    tokens_needed = tokens - self.tokens
                    wait_time = tokens_needed / self.rate_per_second

                    # Release lock while waiting to allow other operations
                    self._lock.release()
                    try:
                        await asyncio.sleep(wait_time)
                    finally:
                        await self._lock.acquire()
            finally:
                self._waiting_count -= 1

    async def __aenter__(self):
        """Context manager entry - acquire one token."""
        await self.acquire(1)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - no-op (tokens already consumed)."""
        return False

    def get_stats(self) -> dict:
        """
        Get current rate limiter statistics.

        Returns:
            Dictionary with current state:
            - available_tokens: Current token count
            - capacity: Maximum tokens
            - rate_per_second: Configured rate
            - waiting_requests: Number of requests waiting for tokens
        """
        return {
            "available_tokens": self.tokens,
            "capacity": self.capacity,
            "rate_per_second": self.rate_per_second,
            "waiting_requests": self._waiting_count,
        }

    async def reset(self) -> None:
        """
        Reset rate limiter to initial state.

        Refills token bucket to capacity. Useful for testing or manual reset.
        """
        async with self._lock:
            self.tokens = float(self.capacity)
            self.last_update = time.monotonic()


class AdaptiveRateLimiter(RateLimiter):
    """
    Rate limiter with adaptive rate adjustment.

    Automatically reduces rate when rate limit errors are detected,
    and gradually increases rate when operations are successful.

    Useful for APIs with unpredictable rate limits or retry-after headers.
    """

    def __init__(
        self,
        initial_rate: float = 3.0,
        min_rate: float = 1.0,
        max_rate: float = 3.0,
        backoff_factor: float = 0.5,
        recovery_factor: float = 1.1,
    ):
        """
        Initialize adaptive rate limiter.

        Args:
            initial_rate: Starting rate per second
            min_rate: Minimum allowed rate (safety floor)
            max_rate: Maximum allowed rate (ceiling)
            backoff_factor: Multiplier when rate limit hit (0.5 = halve rate)
            recovery_factor: Multiplier for gradual recovery (1.1 = 10% increase)
        """
        super().__init__(rate_per_second=initial_rate)
        self.min_rate = min_rate
        self.max_rate = max_rate
        self.backoff_factor = backoff_factor
        self.recovery_factor = recovery_factor
        self._consecutive_successes = 0

    async def handle_rate_limit_error(
        self, retry_after: Optional[float] = None
    ) -> None:
        """
        Handle rate limit error by reducing rate.

        Args:
            retry_after: Suggested wait time from API (seconds)
        """
        async with self._lock:
            if retry_after:
                # Use suggested wait time to calculate new rate
                new_rate = 1.0 / retry_after
                self.rate_per_second = max(
                    self.min_rate, min(new_rate, self.rate_per_second)
                )
            else:
                # Reduce rate by backoff factor
                self.rate_per_second = max(
                    self.min_rate, self.rate_per_second * self.backoff_factor
                )

            # Reset tokens to prevent burst after rate reduction
            self.tokens = float(self.capacity)
            self.last_update = time.monotonic()
            self._consecutive_successes = 0

    async def handle_success(self) -> None:
        """
        Handle successful operation - gradually increase rate.

        Rate increases after multiple consecutive successes to avoid
        oscillation between rate limit errors and recovery.
        """
        async with self._lock:
            self._consecutive_successes += 1

            # Only increase rate after sustained success (e.g., 10 requests)
            if self._consecutive_successes >= 10:
                self.rate_per_second = min(
                    self.max_rate, self.rate_per_second * self.recovery_factor
                )
                self._consecutive_successes = 0
