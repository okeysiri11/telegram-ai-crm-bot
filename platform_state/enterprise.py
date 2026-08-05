"""Enterprise runtime facade — Sprint 34.2D assembly."""

from __future__ import annotations

from typing import Any

from platform_state.audit_timeline import audit_timeline
from platform_state.cache import background_reconciler, batch_sync, incremental_delta, platform_cache
from platform_state.conflict_engine import MergeStrategy, conflict_engine
from platform_state.entity import CanonicalEntity, ENTITY_TYPES
from platform_state.event_store import event_store
from platform_state.replay import replay_engine
from platform_state.self_healing import self_healing
from platform_state.telemetry import enterprise_telemetry
from platform_state.transaction import PlatformTransaction, begin_transaction
from platform_state.version_engine import OptimisticLockError, version_engine


class EnterpriseRuntime:
    """Deterministic enterprise OS foundation over PlatformState."""

    def __init__(self) -> None:
        self.versions = version_engine
        self.events = event_store
        self.replay = replay_engine
        self.conflicts = conflict_engine
        self.timeline = audit_timeline
        self.telemetry = enterprise_telemetry
        self.healing = self_healing
        self.cache = platform_cache
        self.reconciler = background_reconciler

    def status(self) -> dict[str, Any]:
        return {
            "sprint": "34.2D",
            "deterministic": True,
            "foundation_locked": True,
            "foundation_sprint": "35.1",
            "entity_types": list(ENTITY_TYPES),
            "version_heads": len(version_engine._heads),
            "version_engine": version_engine.status(),
            "event_store_count": event_store.count(),
            "event_store_max_seq": event_store.max_seq(),
            "pending_conflicts": len(conflict_engine.pending_reviews()),
            "conflict_count": conflict_engine.conflict_count,
            "telemetry": enterprise_telemetry.snapshot(),
            "cache": {
                "entities": len(platform_cache.entities),
                "events": len(platform_cache.events),
            },
            "healing": self_healing.history(10),
            "version_mixin": "database.models.mixins.VersionMixin",
            "event_bus": "events.event_bus.PlatformEventBus",
        }

    def begin_tx(self, **kwargs: Any) -> PlatformTransaction:
        return begin_transaction(**kwargs)

    async def batch(self, changes: list[dict[str, Any]]) -> dict[str, Any]:
        return await batch_sync(changes)

    def delta(self, since: str | None = None, **kwargs: Any) -> dict[str, Any]:
        return incremental_delta(since, **kwargs)

    def reset(self) -> None:
        version_engine.reset()
        event_store.reset()
        conflict_engine.reset()
        audit_timeline.reset()
        enterprise_telemetry.reset()
        self_healing.reset()
        platform_cache.reset()


enterprise_runtime = EnterpriseRuntime()

__all__ = [
    "EnterpriseRuntime",
    "enterprise_runtime",
    "CanonicalEntity",
    "MergeStrategy",
    "OptimisticLockError",
    "begin_transaction",
]
