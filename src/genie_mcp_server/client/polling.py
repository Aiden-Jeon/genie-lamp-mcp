"""Async polling utilities for long-running operations."""

import asyncio
import time
from typing import Any, Callable


async def poll_until_complete(
    check_fn: Callable[[], tuple[bool, Any]],
    timeout_seconds: int = 300,
    poll_interval_seconds: int = 2,
) -> Any:
    """Poll a function until it completes or times out.

    Args:
        check_fn: Synchronous function that returns (is_complete, result)
        timeout_seconds: Maximum time to wait before timing out
        poll_interval_seconds: Time to wait between polls

    Returns:
        The result from check_fn when is_complete is True

    Raises:
        TimeoutError: If the operation times out
    """
    start_time = time.time()

    while True:
        is_complete, result = check_fn()

        if is_complete:
            return result

        elapsed = time.time() - start_time
        if elapsed >= timeout_seconds:
            raise asyncio.TimeoutError(
                f"Operation timed out after {timeout_seconds} seconds. "
                f"Consider increasing timeout_seconds parameter."
            )

        await asyncio.sleep(poll_interval_seconds)
