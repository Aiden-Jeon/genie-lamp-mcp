"""Rate limiting utilities for Genie API calls."""

import asyncio
import time
from collections import deque


class RateLimiter:
    """Token bucket rate limiter for Genie API calls.

    Genie API limits: 5 queries per minute in Public Preview.
    """

    def __init__(self, max_requests: int = 5, window_seconds: int = 60):
        """Initialize rate limiter.

        Args:
            max_requests: Maximum requests allowed in the time window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: deque[float] = deque()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Acquire permission to make a request, blocking if rate limit reached.

        This method will wait if necessary until a request slot is available.
        """
        async with self._lock:
            now = time.time()

            # Remove requests outside the current window
            while self.requests and self.requests[0] <= now - self.window_seconds:
                self.requests.popleft()

            # If at limit, wait until the oldest request expires
            if len(self.requests) >= self.max_requests:
                oldest_request = self.requests[0]
                wait_time = self.window_seconds - (now - oldest_request)
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    # Clean up again after waiting
                    now = time.time()
                    while self.requests and self.requests[0] <= now - self.window_seconds:
                        self.requests.popleft()

            # Record this request
            self.requests.append(time.time())

    def reset(self) -> None:
        """Reset the rate limiter, clearing all tracked requests."""
        self.requests.clear()


# Global rate limiter instance for Genie API calls
genie_rate_limiter = RateLimiter(max_requests=5, window_seconds=60)
