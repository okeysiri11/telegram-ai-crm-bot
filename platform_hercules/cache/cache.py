"""Multi-domain cache — LLM / prompt / media / workflow / embeddings."""

from __future__ import annotations

import hashlib
import threading
import time
from typing import Any


class HerculesCache:
    DOMAINS = (
        "llm",
        "prompt",
        "image",
        "video",
        "audio",
        "workflow",
        "document",
        "embedding",
    )

    def __init__(self, *, max_entries: int = 2000) -> None:
        self._lock = threading.RLock()
        self._data: dict[str, tuple[Any, float]] = {}
        self.max_entries = max_entries
        self.hits = 0
        self.misses = 0

    def _key(self, domain: str, raw: str) -> str:
        h = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
        return f"{domain}:{h}"

    def get(self, domain: str, raw_key: str) -> Any | None:
        key = self._key(domain, raw_key)
        with self._lock:
            item = self._data.get(key)
            if not item:
                self.misses += 1
                return None
            value, expires = item
            if expires and time.time() > expires:
                self._data.pop(key, None)
                self.misses += 1
                return None
            self.hits += 1
            return value

    def set(self, domain: str, raw_key: str, value: Any, *, ttl_sec: float = 3600) -> None:
        key = self._key(domain, raw_key)
        with self._lock:
            if len(self._data) >= self.max_entries:
                # drop oldest approx — first key
                self._data.pop(next(iter(self._data)), None)
            self._data[key] = (value, time.time() + ttl_sec)

    def stats(self) -> dict[str, Any]:
        with self._lock:
            return {
                "entries": len(self._data),
                "hits": self.hits,
                "misses": self.misses,
                "domains": list(self.DOMAINS),
            }


hercules_cache = HerculesCache()
