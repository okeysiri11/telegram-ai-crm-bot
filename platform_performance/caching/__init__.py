"""Cache layer — Sprint 21.7."""

from __future__ import annotations

from typing import Any
import time

from platform_performance.models import CACHE_BACKENDS


class CacheLayer:
    def __init__(self) -> None:
        self._local: dict[str, tuple[Any, float]] = {}
        self._stats = {"hits": 0, "misses": 0, "invalidations": 0}

    def backends(self) -> list[str]:
        return list(CACHE_BACKENDS)

    def put(self, key: str, value: Any, *, ttl: float = 60.0, backend: str = "local") -> dict[str, Any]:
        if backend not in CACHE_BACKENDS:
            raise ValueError(f"unsupported cache backend: {backend}")
        self._local[key] = (value, time.time() + ttl)
        return {"key": key, "backend": backend, "ttl": ttl, "warmed": True}

    def get(self, key: str) -> dict[str, Any]:
        item = self._local.get(key)
        if not item or item[1] < time.time():
            self._stats["misses"] += 1
            if key in self._local:
                del self._local[key]
            return {"hit": False, "value": None}
        self._stats["hits"] += 1
        return {"hit": True, "value": item[0]}

    def invalidate(self, key: str) -> dict[str, Any]:
        self._local.pop(key, None)
        self._stats["invalidations"] += 1
        return {"key": key, "invalidated": True}

    def warm(self, entries: dict[str, Any], *, ttl: float = 120.0) -> dict[str, Any]:
        for k, v in entries.items():
            self.put(k, v, ttl=ttl, backend="redis")
        return {"warmed": len(entries), "backends": self.backends()}

    def status(self) -> dict[str, Any]:
        return {**self._stats, "keys": len(self._local), "backends": self.backends()}
