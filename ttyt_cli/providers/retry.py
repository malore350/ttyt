"""Shared retry decorator with exponential backoff for LLM provider API calls.

Retries only on HTTP 429 (rate limit) and 5xx (server errors).
Does NOT retry on 4xx (client errors like 401/403).
"""

import time
import re
from functools import wraps


def retry_with_backoff(max_retries: int = 3, base_delay: float = 2.0):
    """Decorator: retry on 429 and 5xx errors with exponential backoff.

    Retry delays: base_delay, base_delay*2, base_delay*4 (2s, 4s, 8s by default)
    Only retries on: HTTP 429 (rate limit) and 5xx (server errors)
    Does NOT retry on: 4xx (client errors like 401/403)
    On final failure: raises the original exception
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    status_code = _extract_status_code(e)
                    if status_code is None or (status_code != 429 and status_code < 500):
                        raise  # Don't retry if we can't determine status, or it's 4xx
                    if attempt < max_retries:
                        delay = base_delay * (2**attempt)
                        time.sleep(delay)
            raise last_exception

        return wrapper

    return decorator


def _extract_status_code(exception: Exception) -> int | None:
    """Extract HTTP status code from various SDK exception types."""
    # Try common attributes across SDKs
    for attr in ("status_code", "status", "code", "http_status"):
        val = getattr(exception, attr, None)
        if val is not None:
            try:
                return int(val)
            except (ValueError, TypeError):
                pass

    # Try extracting from string representation
    match = re.search(
        r"status(?:[ _]code)?[=: ]*(\d{3})", str(exception), re.IGNORECASE
    )
    if match:
        return int(match.group(1))
    return None
