"""API request manager for iDRAC Redfish integration."""

import asyncio
import logging
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import (
    MAX_CONCURRENT_REQUESTS,
    MAX_RETRIES,
    MIN_TIME_BETWEEN_REQUESTS,
    PRIORITY_CRITICAL,
    RETRY_BACKOFF_FACTOR,
    RETRY_STATUSES,
)

_LOGGER = logging.getLogger(__name__)


class ApiRequestManager:
    """Manage API requests with rate limiting and retry logic."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the API request manager."""
        self.hass = hass
        self._last_request_time: datetime | None = None
        self._request_lock = asyncio.Lock()
        self._semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        self._request_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._queue_task: asyncio.Task | None = None

    async def request(
        self,
        func: Callable,
        *args: Any,
        priority: int = PRIORITY_CRITICAL,
        timeout: int = 20,
        **kwargs: Any,
    ) -> Any:
        """Execute an API request with rate limiting and retry logic.

        Args:
            func: The async function to call
            *args: Positional arguments for the function
            priority: Request priority (lower = higher priority)
            timeout: Request timeout in seconds
            **kwargs: Keyword arguments for the function
        """
        async with self._semaphore:
            # Rate limiting
            async with self._request_lock:
                if self._last_request_time:
                    elapsed = (datetime.now() - self._last_request_time).total_seconds()
                    if elapsed < MIN_TIME_BETWEEN_REQUESTS:
                        await asyncio.sleep(MIN_TIME_BETWEEN_REQUESTS - elapsed)
                self._last_request_time = datetime.now()

            # Retry logic with exponential backoff
            last_exception = None
            for attempt in range(MAX_RETRIES):
                try:
                    result = await asyncio.wait_for(
                        func(*args, **kwargs),
                        timeout=timeout
                    )
                    return result
                except asyncio.TimeoutError as ex:
                    last_exception = ex
                    if attempt < MAX_RETRIES - 1:
                        wait_time = RETRY_BACKOFF_FACTOR ** attempt
                        _LOGGER.warning(
                            "Request timeout (attempt %d/%d), retrying in %ds",
                            attempt + 1,
                            MAX_RETRIES,
                            wait_time,
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        _LOGGER.error("Request failed after %d attempts", MAX_RETRIES)
                except Exception as ex:
                    last_exception = ex
                    # Check if it's a retryable HTTP error
                    if hasattr(ex, "status") and ex.status in RETRY_STATUSES:
                        if attempt < MAX_RETRIES - 1:
                            wait_time = RETRY_BACKOFF_FACTOR ** attempt
                            _LOGGER.warning(
                                "API error %s (attempt %d/%d), retrying in %ds: %s",
                                ex.status if hasattr(ex, "status") else "unknown",
                                attempt + 1,
                                MAX_RETRIES,
                                wait_time,
                                ex,
                            )
                            await asyncio.sleep(wait_time)
                        else:
                            _LOGGER.error("Request failed after %d attempts", MAX_RETRIES)
                    else:
                        # Non-retryable error, raise immediately
                        raise

            # All retries failed
            raise HomeAssistantError(
                f"API request failed after {MAX_RETRIES} attempts"
            ) from last_exception

    async def batch_request(
        self,
        requests: list[tuple[Callable, tuple, dict]],
        timeout: int = 20,
    ) -> list[Any]:
        """Execute multiple API requests concurrently with rate limiting.

        Args:
            requests: List of (function, args, kwargs) tuples
            timeout: Timeout for each individual request
        """
        tasks = [
            self.request(func, *args, timeout=timeout, **kwargs)
            for func, args, kwargs in requests
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)
