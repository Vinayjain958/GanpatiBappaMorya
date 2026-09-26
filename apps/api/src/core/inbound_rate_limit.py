"""Minimal per-user inbound rate limiter for public-write endpoints.

`core/rate_limit.py::IntervalRateLimiter` paces this process's own
*outbound* calls to a single external service (Nominatim/OSRM/etc.) — a
different shape of problem to limiting how often one authenticated user
may call one of our own endpoints. This is a small in-memory sliding
window, single-process, matching the "adequate for a single-process
prototype" scope the rest of this codebase's rate limiting already
accepts (no Redis/external rate-limit service — spec §47).
"""

from __future__ import annotations

import time
from collections import defaultdict, deque


class SlidingWindowLimiter:
    def __init__(self, max_calls: int, window_seconds: float = 3600.0) -> None:
        self._max_calls = max_calls
        self._window_seconds = window_seconds
        self._calls: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        calls = self._calls[key]
        cutoff = now - self._window_seconds
        while calls and calls[0] < cutoff:
            calls.popleft()
        if len(calls) >= self._max_calls:
            return False
        calls.append(now)
        return True
