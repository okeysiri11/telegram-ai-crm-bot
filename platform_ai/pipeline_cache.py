"""Sprint 43.1 — AI generation result cache (identical prompts reuse)."""

from __future__ import annotations

import hashlib
import time
from threading import Lock
from typing import Any


class AiResultCache:
    def __init__(self, *, max_entries: int = 512, ttl_sec: float = 3600.0) -> None:
        self._max = max_entries
        self._ttl = ttl_sec
        self._lock = Lock()
        self._store: dict[str, tuple[float, dict[str, Any]]] = {}
        self.hits = 0
        self.misses = 0

    def reset(self) -> None:
        with self._lock:
            self._store.clear()
            self.hits = 0
            self.misses = 0

    @staticmethod
    def key(owner_id: str, modality: str, prompt: str, provider: str | None = None) -> str:
        raw = f"{owner_id}|{modality}|{provider or '*'}|{prompt.strip().lower()}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, cache_key: str) -> dict[str, Any] | None:
        with self._lock:
            hit = self._store.get(cache_key)
            if not hit:
                self.misses += 1
                return None
            ts, payload = hit
            if time.time() - ts > self._ttl:
                self._store.pop(cache_key, None)
                self.misses += 1
                return None
            self.hits += 1
            return dict(payload)

    def set(self, cache_key: str, payload: dict[str, Any]) -> None:
        with self._lock:
            self._store[cache_key] = (time.time(), dict(payload))
            if len(self._store) > self._max:
                oldest = sorted(self._store.items(), key=lambda x: x[1][0])[: len(self._store) - self._max]
                for k, _ in oldest:
                    self._store.pop(k, None)

    def stats(self) -> dict[str, Any]:
        with self._lock:
            return {
                "entries": len(self._store),
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": round(self.hits / max(1, self.hits + self.misses), 3),
            }


ai_result_cache = AiResultCache()
