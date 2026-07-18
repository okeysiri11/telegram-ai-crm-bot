# Rate limiter — per provider, endpoint, and API key.

from __future__ import annotations

import time
from dataclasses import dataclass, field

from platform_integrations.exceptions import RateLimitExceededError


@dataclass
class RateLimitBucket:
    limit: int
    window_seconds: float
    timestamps: list[float] = field(default_factory=list)

    def allow(self) -> bool:
        now = time.monotonic()
        cutoff = now - self.window_seconds
        self.timestamps = [ts for ts in self.timestamps if ts > cutoff]
        if len(self.timestamps) >= self.limit:
            return False
        self.timestamps.append(now)
        return True


class RateLimiter:
    DEFAULT_LIMIT = 100
    DEFAULT_WINDOW = 60.0

    def __init__(self) -> None:
        self._buckets: dict[str, RateLimitBucket] = {}
        self._limits: dict[str, tuple[int, float]] = {}

    def reset(self) -> None:
        self._buckets.clear()
        self._limits.clear()

    def configure(self, key: str, *, limit: int, window_seconds: float) -> None:
        self._limits[key] = (limit, window_seconds)

    def _bucket(self, key: str) -> RateLimitBucket:
        if key not in self._buckets:
            limit, window = self._limits.get(key, (self.DEFAULT_LIMIT, self.DEFAULT_WINDOW))
            self._buckets[key] = RateLimitBucket(limit=limit, window_seconds=window)
        return self._buckets[key]

    def check(
        self,
        *,
        provider: str,
        endpoint: str = "default",
        api_key: str | None = None,
    ) -> None:
        keys = [
            f"provider:{provider}",
            f"endpoint:{provider}:{endpoint}",
        ]
        if api_key:
            keys.append(f"apikey:{api_key}")

        for key in keys:
            if not self._bucket(key).allow():
                raise RateLimitExceededError(f"Rate limit exceeded for {key}")

    def stats(self) -> dict[str, dict]:
        return {
            key: {"limit": b.limit, "window_seconds": b.window_seconds, "used": len(b.timestamps)}
            for key, b in self._buckets.items()
        }


rate_limiter = RateLimiter()
