"""Shared rate-limit and HMAC-nonce store for Vanguard.

Redis when REDIS_URL (or VANGUARD_SHARED_STORE_URL) is reachable.
shared=True only for a live Redis client — never for process memory.

Production: no silent process_local fallback. Unavailable Redis is fail-closed.
Development: process_local is allowed and labelled shared=False.
"""

from __future__ import annotations

import logging
import os
import time
from collections import defaultdict, deque
from typing import Any

from services.recruiting_ops.runtime import is_production_runtime

logger = logging.getLogger(__name__)

RATE_PREFIX = "vanguard:rl:"
NONCE_PREFIX = "vanguard:nonce:"

RATE_LUA = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
local member = ARGV[4]
redis.call('ZREMRANGEBYSCORE', key, '-inf', now - window)
local count = redis.call('ZCARD', key)
if count >= limit then
  local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
  local oldest_ts = now
  if oldest[2] then oldest_ts = tonumber(oldest[2]) end
  local retry = math.floor(window - (now - oldest_ts))
  if retry < 1 then retry = 1 end
  return {0, count, retry}
end
redis.call('ZADD', key, now, member)
redis.call('EXPIRE', key, math.floor(window) + 5)
return {1, count + 1, 0}
"""

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
        fail_closed: bool = False,
        reason: str | None = None,
    ) -> None:
        self.backend = backend
        if backend in {"process_local", "unavailable"}:
            self.shared = False
        else:
            self.shared = bool(shared)
        if backend == "redis" and redis_client is None:
            self.shared = False
        self.fail_closed = fail_closed
        self.reason = reason
        self._map = mapping if mapping is not None else {}
        self._windows: dict[str, deque[float]] = defaultdict(deque)
        self._redis = redis_client

    @classmethod
    def connect(cls) -> "SharedStore":
        url = (os.getenv("VANGUARD_SHARED_STORE_URL") or os.getenv("REDIS_URL") or "").strip()
        production = is_production_runtime()
        if not url:
            if production:
                logger.error("vanguard shared store REDIS_URL missing in production — fail closed")
                return cls(
                    backend="unavailable",
                    shared=False,
                    fail_closed=True,
                    reason="REDIS_URL_not_configured",
                )
            return cls(backend="process_local", shared=False, reason="REDIS_URL_not_configured")
        try:
            import redis

            client = redis.Redis.from_url(
                url,
                decode_responses=True,
                socket_connect_timeout=0.4,
                socket_timeout=0.8,
            )
            client.ping()
            return cls(backend="redis", shared=True, redis_client=client)
        except Exception as exc:
            if production:
                logger.error("vanguard shared store Redis unavailable in production — fail closed: %s", exc)
                return cls(
                    backend="unavailable",
                    shared=False,
                    fail_closed=True,
                    reason="redis_unavailable",
                )
            logger.warning("vanguard shared store Redis unavailable, using process_local: %s", exc)
            return cls(backend="process_local", shared=False, reason="redis_unavailable")

    def describe(self) -> dict[str, Any]:
        return {
            "backend": self.backend,
            "shared": self.shared,
            "fail_closed": self.fail_closed,
            "reason": self.reason,
        }

    def hit_rate(self, key: str, limit: int, window: int) -> dict[str, Any]:
        if self.fail_closed:
            return {
                "allowed": False,
                "error": "store_unavailable",
                "retry_after_seconds": 30,
                "limit": limit,
                "store": self.backend,
                "shared": False,
                "fail_closed": True,
                "message_ru": "Хранилище лимитов недоступно. Повторите позже.",
            }
        if self._redis is not None:
            result = self._hit_rate_redis(key, limit, window)
            result["store"] = "redis"
            result["shared"] = True
            return result
        if self.backend == "memory_shared" and self._map is not None:
            result = self._hit_rate_map(key, limit, window)
            result["store"] = "memory_shared"
            result["shared"] = True
            return result
        result = self._hit_rate_local(key, limit, window)
        result["store"] = "process_local"
        result["shared"] = False
        return result

    def claim_nonce(self, nonce: str, ttl_seconds: int) -> bool:
        token = str(nonce or "").strip()
        if not token:
            return False
        if self.fail_closed:
            return False
        if self._redis is not None:
            ok = self._redis.set(f"{NONCE_PREFIX}{token}", "1", nx=True, ex=max(1, int(ttl_seconds)))
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

    def has_nonce(self, nonce: str) -> bool:
        token = str(nonce or "").strip()
        if not token:
            return False
        if self._redis is not None:
            try:
                return bool(self._redis.exists(f"{NONCE_PREFIX}{token}"))
            except Exception:
                return False
        bucket = self._map.get("nonces") or {}
        seen = float(bucket.get(token) or 0)
        return bool(seen)

    def nonce_ttl(self, nonce: str) -> int | None:
        token = str(nonce or "").strip()
        if self._redis is not None:
            ttl = int(self._redis.ttl(f"{NONCE_PREFIX}{token}"))
            return ttl if ttl >= 0 else None
        bucket = self._map.get("nonces") or {}
        seen = float(bucket.get(token) or 0)
        if not seen:
            return None
        return max(0, int(seen + 300 - time.time()))

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
        member = f"{now}:{os.getpid()}:{time.time_ns()}"
        allowed, count, retry = self._redis.eval(RATE_LUA, 1, redis_key, now, window, limit, member)
        if int(allowed) == 1:
            return {"allowed": True, "limit": limit, "remaining": max(0, limit - int(count))}
        return _limited(max(1, int(retry)), limit)


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


def redis_reachable() -> bool:
    url = (os.getenv("VANGUARD_SHARED_STORE_URL") or os.getenv("REDIS_URL") or "").strip()
    if not url:
        return False
    try:
        import redis

        client = redis.Redis.from_url(url, decode_responses=True, socket_connect_timeout=0.4, socket_timeout=0.8)
        return bool(client.ping())
    except Exception:
        return False
