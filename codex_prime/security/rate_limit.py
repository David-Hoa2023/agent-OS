"""Rate limiting for API protection."""

from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict
import threading
import time


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""

    def __init__(self, identifier: str, limit: int, window: int, retry_after: float):
        self.identifier = identifier
        self.limit = limit
        self.window = window
        self.retry_after = retry_after
        super().__init__(
            f"Rate limit exceeded for '{identifier}': {limit} requests per {window}s. "
            f"Retry after {retry_after:.1f}s"
        )


@dataclass
class RateLimitInfo:
    """Information about rate limit status."""

    identifier: str
    limit: int
    window: int
    remaining: int
    reset_at: datetime

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            "identifier": self.identifier,
            "limit": self.limit,
            "window": self.window,
            "remaining": self.remaining,
            "reset_at": self.reset_at.isoformat()
        }


class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, default_limit: int = 60, default_window: int = 60):
        """
        Initialize rate limiter.

        Args:
            default_limit: Default number of requests allowed
            default_window: Default time window in seconds
        """
        self.default_limit = default_limit
        self.default_window = default_window

        # Storage: identifier -> (tokens, last_update)
        self._buckets: Dict[str, Tuple[float, float]] = defaultdict(lambda: (default_limit, time.time()))

        # Custom limits: identifier -> (limit, window)
        self._custom_limits: Dict[str, Tuple[int, int]] = {}

        # Lock for thread safety
        self._lock = threading.Lock()

    def set_limit(self, identifier: str, limit: int, window: int):
        """
        Set custom rate limit for an identifier.

        Args:
            identifier: Unique identifier (user_id, api_key, IP, etc.)
            limit: Number of requests allowed
            window: Time window in seconds
        """
        with self._lock:
            self._custom_limits[identifier] = (limit, window)

    def remove_limit(self, identifier: str):
        """Remove custom limit for an identifier."""
        with self._lock:
            if identifier in self._custom_limits:
                del self._custom_limits[identifier]
            if identifier in self._buckets:
                del self._buckets[identifier]

    def check_limit(self, identifier: str, cost: float = 1.0) -> RateLimitInfo:
        """
        Check rate limit without consuming tokens.

        Args:
            identifier: Unique identifier
            cost: Cost of the request (default: 1.0)

        Returns:
            Rate limit information
        """
        with self._lock:
            limit, window = self._custom_limits.get(identifier, (self.default_limit, self.default_window))
            tokens, last_update = self._buckets[identifier]

            # Refill tokens based on time passed
            now = time.time()
            time_passed = now - last_update
            refill_rate = limit / window
            new_tokens = min(limit, tokens + (time_passed * refill_rate))

            remaining = int(new_tokens)
            reset_at = datetime.now() + timedelta(seconds=(limit - new_tokens) / refill_rate)

            return RateLimitInfo(
                identifier=identifier,
                limit=limit,
                window=window,
                remaining=remaining,
                reset_at=reset_at
            )

    def consume(self, identifier: str, cost: float = 1.0) -> RateLimitInfo:
        """
        Consume tokens from rate limit bucket.

        Args:
            identifier: Unique identifier
            cost: Cost of the request (default: 1.0)

        Returns:
            Rate limit information

        Raises:
            RateLimitExceeded: If rate limit is exceeded
        """
        with self._lock:
            limit, window = self._custom_limits.get(identifier, (self.default_limit, self.default_window))
            tokens, last_update = self._buckets[identifier]

            # Refill tokens
            now = time.time()
            time_passed = now - last_update
            refill_rate = limit / window
            new_tokens = min(limit, tokens + (time_passed * refill_rate))

            # Check if enough tokens
            if new_tokens < cost:
                # Calculate retry after
                tokens_needed = cost - new_tokens
                retry_after = tokens_needed / refill_rate

                reset_at = datetime.now() + timedelta(seconds=(limit - new_tokens) / refill_rate)

                raise RateLimitExceeded(
                    identifier=identifier,
                    limit=limit,
                    window=window,
                    retry_after=retry_after
                )

            # Consume tokens
            new_tokens -= cost
            self._buckets[identifier] = (new_tokens, now)

            remaining = int(new_tokens)
            reset_at = datetime.now() + timedelta(seconds=(limit - new_tokens) / refill_rate)

            return RateLimitInfo(
                identifier=identifier,
                limit=limit,
                window=window,
                remaining=remaining,
                reset_at=reset_at
            )

    def reset(self, identifier: str):
        """Reset rate limit for an identifier."""
        with self._lock:
            if identifier in self._buckets:
                limit, _ = self._custom_limits.get(identifier, (self.default_limit, self.default_window))
                self._buckets[identifier] = (limit, time.time())

    def get_stats(self) -> Dict[str, Dict]:
        """Get statistics for all identifiers."""
        with self._lock:
            stats = {}
            for identifier in self._buckets.keys():
                info = self.check_limit(identifier)
                stats[identifier] = info.to_dict()
            return stats

    def cleanup_idle(self, idle_seconds: int = 3600):
        """
        Remove buckets that haven't been used recently.

        Args:
            idle_seconds: Remove buckets idle for this many seconds
        """
        with self._lock:
            now = time.time()
            idle_identifiers = [
                identifier for identifier, (_, last_update) in self._buckets.items()
                if now - last_update > idle_seconds
            ]

            for identifier in idle_identifiers:
                del self._buckets[identifier]


class SlidingWindowRateLimiter:
    """Sliding window rate limiter for more precise control."""

    def __init__(self, default_limit: int = 60, default_window: int = 60):
        """
        Initialize sliding window rate limiter.

        Args:
            default_limit: Default number of requests allowed
            default_window: Default time window in seconds
        """
        self.default_limit = default_limit
        self.default_window = default_window

        # Storage: identifier -> list of timestamps
        self._requests: Dict[str, list] = defaultdict(list)

        # Custom limits
        self._custom_limits: Dict[str, Tuple[int, int]] = {}

        # Lock for thread safety
        self._lock = threading.Lock()

    def set_limit(self, identifier: str, limit: int, window: int):
        """Set custom rate limit."""
        with self._lock:
            self._custom_limits[identifier] = (limit, window)

    def consume(self, identifier: str) -> RateLimitInfo:
        """
        Record a request and check rate limit.

        Args:
            identifier: Unique identifier

        Returns:
            Rate limit information

        Raises:
            RateLimitExceeded: If rate limit is exceeded
        """
        with self._lock:
            limit, window = self._custom_limits.get(identifier, (self.default_limit, self.default_window))

            now = time.time()
            window_start = now - window

            # Get requests list
            requests = self._requests[identifier]

            # Remove old requests outside the window
            requests[:] = [ts for ts in requests if ts > window_start]

            # Check limit
            if len(requests) >= limit:
                # Calculate retry after (time until oldest request expires)
                oldest_request = requests[0]
                retry_after = (oldest_request + window) - now
                reset_at = datetime.fromtimestamp(oldest_request + window)

                raise RateLimitExceeded(
                    identifier=identifier,
                    limit=limit,
                    window=window,
                    retry_after=retry_after
                )

            # Add current request
            requests.append(now)

            remaining = limit - len(requests)
            reset_at = datetime.fromtimestamp(requests[0] + window) if requests else datetime.now()

            return RateLimitInfo(
                identifier=identifier,
                limit=limit,
                window=window,
                remaining=remaining,
                reset_at=reset_at
            )

    def check_limit(self, identifier: str) -> RateLimitInfo:
        """Check current rate limit status."""
        with self._lock:
            limit, window = self._custom_limits.get(identifier, (self.default_limit, self.default_window))

            now = time.time()
            window_start = now - window

            requests = self._requests.get(identifier, [])
            recent_requests = [ts for ts in requests if ts > window_start]

            remaining = limit - len(recent_requests)
            reset_at = datetime.fromtimestamp(recent_requests[0] + window) if recent_requests else datetime.now()

            return RateLimitInfo(
                identifier=identifier,
                limit=limit,
                window=window,
                remaining=remaining,
                reset_at=reset_at
            )

    def reset(self, identifier: str):
        """Reset rate limit for an identifier."""
        with self._lock:
            if identifier in self._requests:
                self._requests[identifier].clear()

    def cleanup_idle(self, idle_seconds: int = 3600):
        """Remove idle identifiers."""
        with self._lock:
            now = time.time()
            idle_identifiers = [
                identifier for identifier, requests in self._requests.items()
                if not requests or (now - requests[-1]) > idle_seconds
            ]

            for identifier in idle_identifiers:
                del self._requests[identifier]
