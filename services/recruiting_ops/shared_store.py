"""Shared rate-limit and HMAC-nonce store for Vanguard.

Redis when REDIS_URL (or VANGUARD_SHARED_STORE_URL) is reachable.
Otherwise process-local — not shared across instances, labelled honestly.

Tests may inject a dict-backed store so two logical instances share state.
"""

from __future__ import annotations

import logging
import os
import time
from collections import defaultdict, deque
from typing import Any

logger = logging.getLogger(__name__)

RATE_PREFIX = "vanguard:rl:"
NONCE_PREFIX = "vanguard:nonce:"

_OVERRIDE: "SharedStore | None" = None
_STORE: "SharedStore | None" = None


class SharedStore:
    def __init__(
        self,
        *,
        backend: str,
        shared: bool,
        mapping: dict[str, Any] | None = None,
        redis_client: Any | None = None,
    ) -> None:
        self.backend = backend
        self.shared = shared
        self._map = mapping if mapping is not None else {}
        self._windows: dict[str, deque[float]] = defaultdict(deque)
        self._redis = redis_client

    @classmethod
    def connect(cls) -> "SharedStore":
        url = (os.getenv("VANGUARD_SHARED_STORE_URL") or os.getenv("REDIS_URL") or "").strip()
        if not url:
            return cls(backend="process_local", shared=False)
        try:
            import redis

            client = redis.Redis.from_url(url, decode_responses=True, socket_connect_timeout=0.4, socket_timeout=0.8)
            client.ping()
            return cls(backend="redis", shared=True, redis_client=client)
        except Exception as exc:
            logger.warning("vanguard shared store Redis unavailable, using process_local: %s", exc)
            return cls(backend="process_local", shared=False)

    def describe(self) -> dict[str, Any]:
        return {"backend": self.backend, "shared": self.shared}

    def hit_rate(self, key: str, limit: int, window: int) -> dict[str, Any]:
        if self._redis is not None:
            return self._hit_rate_redis(key, limit, window)
        if self.shared and self._map is not None and self.backend != "process_local":
            return self._hit_rate_map(key, limit, window)
        return self._hit_rate_local(key, limit, window)

    def claim_nonce(self, nonce: str, ttl_seconds: int) -> bool:
        token = str(nonce or "").strip()
        if not token:
            return False
        if self._redis is not None:
            ok = self._redis.set(f"{NONCE_PREFIX}{token}", "1", nx=True, ex=max(1, ttl_seconds))
            return bool(ok)
        bucket = self._map.setdefault("nonces", {})
        now = time.time()
        seen = float(bucket.get(token) or 0)
        if seen and now - seen < ttl_seconds:
            return False
        bucket[token] = now
        stale = [k for k, ts in list(bucket.items()) if now - float(ts) > ttl_seconds * 2]
        for k in stale:
            bucket.pop(k, None)
        return True

    def reset(self) -> None:
        self._windows.clear()
        self._map.clear()
        if self._redis is not None:
            try:
                for pattern in (f"{RATE_PREFIX}*", f"{NONCE_PREFIX}*"):
                    for key in self._redis.scan_iter(match=pattern, count=100):
                        self._redis.delete(key)
            except Exception:
                logger.warning("vanguard shared store redis reset skipped")

    def _hit_rate_local(self, key: str, limit: int, window: int) -> dict[str, Any]:
        now = time.monotonic()
        span = float(window)
        bucket = self._windows[key]
        while bucket and now - bucket[0] > span:
            bucket.popleft()
        if len(bucket) >= limit:
            retry = max(1, int(span - (now - bucket[0])))
            return _limited(retry, limit)
        bucket.append(now)
        return {"allowed": True, "limit": limit, "remaining": max(0, limit - len(bucket))}

    def _hit_rate_map(self, key: str, limit: int, window: int) -> dict[str, Any]:
        now = time.time()
        span = float(window)
        windows = self._map.setdefault("windows", {})
        stamps: list[float] = list(windows.get(key) or [])
        stamps = [t for t in stamps if now - t <= span]
        if len(stamps) >= limit:
            retry = max(1, int(span - (now - stamps[0])))
            windows[key] = stamps
            return _limited(retry, limit)
        stamps.append(now)
        windows[key] = stamps
        return {"allowed": True, "limit": limit, "remaining": max(0, limit - len(stamps))}

    def _hit_rate_redis(self, key: str, limit: int, window: int) -> dict[str, Any]:
        assert self._redis is not None
        now = time.time()
        redis_key = f"{RATE_PREFIX}{key}"
        pipe = self._redis.pipeline()
        pipe.zremrangebyscore(redis_key, 0, now - window)
        pipe.zcard(redis_key)
        _removed, count = pipe.execute()
        count = int(count or 0)
        if count >= limit:
            oldest = self._redis.zrange(redis_key, 0, 0, withscores=True)
            oldest_ts = float(oldest[0][1]) if oldest else now
            retry = max(1, int(window - (now - oldest_ts)))
            return _limited(retry, limit)
        member = f"{now}:{os.getpid()}:{count}"
        pipe = self._redis.pipeline()
        pipe.zadd(redis_key, {member: now})
        pipe.expire(redis_key, window + 5)
        pipe.execute()
        return {"allowed": True, "limit": limit, "remaining": max(0, limit - count - 1)}


def _limited(retry: int, limit: int) -> dict[str, Any]:
    return {
        "allowed": False,
        "error": "rate_limited",
        "retry_after_seconds": retry,
        "limit": limit,
        "message_ru": "Слишком много заявок. Подождите и повторите.",
    }


def get_store() -> SharedStore:
    global _STORE
    if _OVERRIDE is not None:
        return _OVERRIDE
    if _STORE is None:
        _STORE = SharedStore.connect()
    return _STORE


def set_store_for_tests(store: SharedStore | None) -> None:
    global _OVERRIDE, _STORE
    _OVERRIDE = store
    _STORE = None


def reset_shared_store_for_tests() -> None:
    global _STORE, _OVERRIDE
    if _OVERRIDE is not None:
        _OVERRIDE.reset()
    if _STORE is not None:
        _STORE.reset()
    _STORE = None
    _OVERRIDE = None
