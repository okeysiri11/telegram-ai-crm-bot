"""Rate limiting & protection — Sprint 21.4."""

from __future__ import annotations

from typing import Any

from platform_security.models import PROTECTION_CONTROLS


class RateLimitProtection:
    def __init__(self) -> None:
        self._counters: dict[str, int] = {}

    def controls(self) -> list[str]:
        return list(PROTECTION_CONTROLS)

    def check(self, *, key: str, limit: int = 100, burst: int = 20) -> dict[str, Any]:
        count = self._counters.get(key, 0) + 1
        self._counters[key] = count
        allowed = count <= limit + burst
        return {
            "allowed": allowed,
            "key": key,
            "count": count,
            "limit": limit,
            "burst": burst,
            "controls": self.controls(),
        }
