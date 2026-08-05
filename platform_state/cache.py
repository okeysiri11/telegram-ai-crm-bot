"""Performance caches + batch/incremental sync helpers (Sprint 34.2D)."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from typing import Any, Callable, Hashable

from platform_state.telemetry import enterprise_telemetry


class LRUCache:
    def __init__(self, maxsize: int = 1024) -> None:
        self._maxsize = maxsize
        self._data: OrderedDict[Hashable, Any] = OrderedDict()
        self._lock = threading.RLock()

    def get(self, key: Hashable) -> Any | None:
        with self._lock:
            if key not in self._data:
                enterprise_telemetry.incr("cache_misses")
                return None
            self._data.move_to_end(key)
            enterprise_telemetry.incr("cache_hits")
            return self._data[key]

    def set(self, key: Hashable, value: Any) -> None:
        with self._lock:
            self._data[key] = value
            self._data.move_to_end(key)
            while len(self._data) > self._maxsize:
                self._data.popitem(last=False)

    def invalidate(self, key: Hashable | None = None) -> None:
        with self._lock:
            if key is None:
                self._data.clear()
            else:
                self._data.pop(key, None)

    def __len__(self) -> int:
        return len(self._data)


class TTLCache:
    def __init__(self, maxsize: int = 512, ttl_s: float = 30.0) -> None:
        self._lru = LRUCache(maxsize=maxsize)
        self._ttl = ttl_s
        self._expires: dict[Hashable, float] = {}
        self._lock = threading.RLock()

    def get(self, key: Hashable) -> Any | None:
        with self._lock:
            exp = self._expires.get(key)
            if exp is not None and time.monotonic() > exp:
                self._lru.invalidate(key)
                self._expires.pop(key, None)
                enterprise_telemetry.incr("cache_misses")
                return None
            return self._lru.get(key)

    def set(self, key: Hashable, value: Any) -> None:
        with self._lock:
            self._lru.set(key, value)
            self._expires[key] = time.monotonic() + self._ttl

    def invalidate(self, key: Hashable | None = None) -> None:
        with self._lock:
            if key is None:
                self._lru.invalidate()
                self._expires.clear()
            else:
                self._lru.invalidate(key)
                self._expires.pop(key, None)


class PlatformCache:
    def __init__(self) -> None:
        self.entities = LRUCache(maxsize=4096)
        self.events = LRUCache(maxsize=8192)
        self.queries = TTLCache(maxsize=1024, ttl_s=15.0)

    def get_entity(self, entity_type: str, entity_id: str) -> Any | None:
        return self.entities.get(f"{entity_type}:{entity_id}")

    def put_entity(self, entity_type: str, entity_id: str, value: Any) -> None:
        self.entities.set(f"{entity_type}:{entity_id}", value)

    def get_or_load(self, key: str, loader: Callable[[], Any]) -> Any:
        cached = self.queries.get(key)
        if cached is not None:
            return cached
        value = loader()
        self.queries.set(key, value)
        return value

    def reset(self) -> None:
        self.entities.invalidate()
        self.events.invalidate()
        self.queries.invalidate()


platform_cache = PlatformCache()


async def batch_sync(changes: list[dict[str, Any]]) -> dict[str, Any]:
    """Apply multiple mutations in one sync cycle."""
    from platform_state.service import platform_state

    results = []
    with enterprise_telemetry.time_block("batch_sync"):
        for change in changes:
            op = change.get("op")
            # Reuse mutate path logic via adapters
            if op == "task.create":
                results.append(
                    await platform_state.tasks.create(
                        title=str(change["title"]),
                        creator_telegram_id=int(change.get("telegram_id") or 0),
                        source_client=str(change.get("source_client") or "api"),
                        skip_db=bool(change.get("skip_db", True)),
                    )
                )
            elif op == "crm.lead.upsert":
                results.append(
                    await platform_state.crm.update_lead(
                        dict(change.get("lead") or change),
                        source_client=str(change.get("source_client") or "api"),
                    )
                )
            elif op == "notification.create":
                results.append(
                    await platform_state.notifications.create(
                        title=str(change.get("title") or "Notification"),
                        body=str(change.get("body") or ""),
                        user_id=change.get("user_id"),
                        source_client=str(change.get("source_client") or "api"),
                    )
                )
            else:
                results.append({"error": f"unsupported op {op}"})
    return {"count": len(results), "results": results, "revision": platform_state.sync.revision}


def incremental_delta(since: str | None, *, slices: list[str] | None = None) -> dict[str, Any]:
    from platform_state.service import platform_state

    with enterprise_telemetry.time_block("incremental_sync"):
        return platform_state.delta(since, slices=slices)


class BackgroundReconciler:
    def __init__(self) -> None:
        self._last_run: str | None = None
        self._runs = 0

    def reconcile(self) -> dict[str, Any]:
        from platform_state.event_store import event_store as es
        from platform_state.models import utcnow
        from platform_state.replay import replay_engine

        after = max(0, es.max_seq() - 50)
        result = replay_engine.replay_all(after_seq=after)
        self._runs += 1
        self._last_run = utcnow().isoformat()
        platform_cache.queries.invalidate()
        return {
            "runs": self._runs,
            "last_run": self._last_run,
            "replay": result.to_dict(),
        }


background_reconciler = BackgroundReconciler()
