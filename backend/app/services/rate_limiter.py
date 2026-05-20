"""Token-bucket rate limiter, keyed by SMTP account id.

In-memory, single-process. Two buckets per account (per-minute, per-hour).
Buckets reset on app restart — documented as a known limit.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass


@dataclass
class _Bucket:
    capacity: int
    refill_per_sec: float
    tokens: float
    updated: float

    def take(self, now: float) -> float:
        """Try to consume one token. Return seconds to wait (0 = took it)."""
        elapsed = now - self.updated
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_per_sec)
        self.updated = now
        if self.tokens >= 1:
            self.tokens -= 1
            return 0.0
        return max(0.001, (1 - self.tokens) / self.refill_per_sec)


class RateLimiter:
    def __init__(self) -> None:
        self._buckets: dict[tuple[str, str], _Bucket] = {}
        self._lock = asyncio.Lock()

    def _bucket(self, key: tuple[str, str], capacity: int, window_sec: float) -> _Bucket:
        b = self._buckets.get(key)
        if b is None:
            b = _Bucket(
                capacity=capacity,
                refill_per_sec=capacity / window_sec,
                tokens=float(capacity),
                updated=time.monotonic(),
            )
            self._buckets[key] = b
        else:
            b.capacity = capacity
            b.refill_per_sec = capacity / window_sec
        return b

    async def acquire(
        self,
        account_id: str,
        *,
        per_minute: int,
        per_hour: int,
        per_day: int,
    ) -> None:
        while True:
            wait = 0.0
            async with self._lock:
                now = time.monotonic()
                m_b = self._bucket((account_id, "min"), per_minute, 60.0)
                h_b = self._bucket((account_id, "hr"), per_hour, 3600.0)
                d_b = self._bucket((account_id, "day"), per_day, 86400.0)
                w_m = m_b.take(now)
                if w_m > 0:
                    wait = w_m
                else:
                    w_h = h_b.take(now)
                    if w_h > 0:
                        m_b.tokens = min(m_b.capacity, m_b.tokens + 1)
                        wait = w_h
                    else:
                        w_d = d_b.take(now)
                        if w_d > 0:
                            m_b.tokens = min(m_b.capacity, m_b.tokens + 1)
                            h_b.tokens = min(h_b.capacity, h_b.tokens + 1)
                            wait = w_d
            if wait <= 0:
                return
            await asyncio.sleep(wait)


_default = RateLimiter()


def default_limiter() -> RateLimiter:
    return _default
