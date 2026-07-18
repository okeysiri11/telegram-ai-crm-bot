# Configuration cache — Redis with in-memory fallback.

from __future__ import annotations

import json
import logging
import time
from typing import Any

from platform_configuration.configuration_center import configuration_center

logger = logging.getLogger(__name__)

_DEFAULT_TTL = 300
_KEY_PREFIX = "platform:config:"


class ConfigCache:
    def __init__(self, *, ttl_seconds: int | None = None) -> None:
        self.ttl_seconds = ttl_seconds if ttl_seconds is not None else _DEFAULT_TTL
        self._memory: dict[str, tuple[float, Any]] = {}
        self._redis = None
        self._redis_checked = False

    async def _get_redis(self):
        if self._redis_checked:
            return self._redis
        self._redis_checked = True
        redis_url = configuration_center.settings.redis.url.strip()
        if not redis_url:
            return None
        try:
            from redis.asyncio import Redis

            client = Redis.from_url(redis_url, decode_responses=True)
            await client.ping()
            self._redis = client
            logger.info("config_cache_redis_connected")
        except Exception as exc:
            logger.debug("config_cache_redis_unavailable: %s", exc)
            self._redis = None
        return self._redis

    def _cache_key(self, key: str) -> str:
        return f"{_KEY_PREFIX}{key}"

    async def get(self, key: str) -> Any | None:
        redis = await self._get_redis()
        ck = self._cache_key(key)
        if redis is not None:
            try:
                raw = await redis.get(ck)
                if raw is not None:
                    return json.loads(raw)
            except Exception:
                logger.debug("config_cache_redis_get_failed key=%s", key, exc_info=True)

        entry = self._memory.get(ck)
        if entry is None:
            return None
        expires_at, value = entry
        if time.monotonic() > expires_at:
            self._memory.pop(ck, None)
            return None
        return value

    async def set(self, key: str, value: Any) -> None:
        ck = self._cache_key(key)
        expires_at = time.monotonic() + self.ttl_seconds
        self._memory[ck] = (expires_at, value)

        redis = await self._get_redis()
        if redis is not None:
            try:
                await redis.setex(ck, self.ttl_seconds, json.dumps(value, default=str))
            except Exception:
                logger.debug("config_cache_redis_set_failed key=%s", key, exc_info=True)

    async def delete(self, key: str) -> None:
        ck = self._cache_key(key)
        self._memory.pop(ck, None)
        redis = await self._get_redis()
        if redis is not None:
            try:
                await redis.delete(ck)
            except Exception:
                logger.debug("config_cache_redis_delete_failed key=%s", key, exc_info=True)

    async def invalidate_section(self, section: str) -> None:
        prefix = f"{_KEY_PREFIX}{section}."
        to_delete = [k for k in self._memory if k.startswith(prefix)]
        for k in to_delete:
            self._memory.pop(k, None)

        redis = await self._get_redis()
        if redis is not None:
            try:
                async for key in redis.scan_iter(match=f"{prefix}*"):
                    await redis.delete(key)
            except Exception:
                logger.debug("config_cache_section_invalidate_failed section=%s", section, exc_info=True)

    async def clear(self) -> None:
        self._memory.clear()
        redis = await self._get_redis()
        if redis is not None:
            try:
                async for key in redis.scan_iter(match=f"{_KEY_PREFIX}*"):
                    await redis.delete(key)
            except Exception:
                logger.debug("config_cache_clear_failed", exc_info=True)


config_cache = ConfigCache()
