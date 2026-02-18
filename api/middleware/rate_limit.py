"""
Simple in-memory rate limiter using a sliding window per IP.

For production with multiple workers, swap _store for Redis.
This implementation avoids leaking user data — only IPs are stored,
and they expire automatically after the window closes.
"""

import time
import logging
from collections import defaultdict, deque
from typing import Callable, Deque, Dict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 60, window_seconds: int = 60):
        super().__init__(app)
        self._max = max_requests
        self._window = window_seconds
        # IP → deque of timestamps within the current window
        self._store: Dict[str, Deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Only rate-limit the API endpoints, not static assets
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        ip = self._get_ip(request)
        now = time.monotonic()
        window_start = now - self._window

        timestamps = self._store[ip]
        # Drop timestamps outside the current window
        while timestamps and timestamps[0] < window_start:
            timestamps.popleft()

        if len(timestamps) >= self._max:
            retry_after = int(self._window - (now - timestamps[0]))
            logger.warning("Rate limit hit for IP %s", ip)
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please slow down."},
                headers={"Retry-After": str(max(retry_after, 1))},
            )

        timestamps.append(now)
        return await call_next(request)

    @staticmethod
    def _get_ip(request: Request) -> str:
        # Respect X-Forwarded-For only if you trust your proxy layer.
        # By default we use the direct client IP to prevent spoofing.
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Take the leftmost (original client) IP
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"