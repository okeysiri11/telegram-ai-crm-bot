"""Shared Memory connectors — link apps to Platform memory engines without rewriting them (Sprint 12.0)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.ecosystem.shared.store import UnifiedEcosystemStore, unified_ecosystem_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


MEMORY_ENGINES = (
    "semantic_memory",
    "long_term_memory",
    "knowledge_graph",
    "learning_engine",
    "decision_engine",
    "reasoning_engine",
    "planning_engine",
    "collaboration_engine",
)


class SharedMemoryHub:
    def __init__(self, store: UnifiedEcosystemStore | None = None) -> None:
        self.store = store or unified_ecosystem_store

    def connect_application(self, *, app_id: str, engines: list[str] | None = None) -> dict[str, Any]:
        linked = list(engines or MEMORY_ENGINES)
        mid = f"mem_{app_id}"
        item = {
            "link_id": mid,
            "app_id": app_id,
            "engines": linked,
            "connected": True,
            "at": _now(),
        }
        # Prefer top-level ecosystem global memory when present
        try:
            from ecosystem import ecosystem

            if hasattr(ecosystem.engine, "assistant"):
                item["ecosystem_memory"] = "linked"
        except Exception:
            item["ecosystem_memory"] = "local_fallback"
        self.store.memory_links.save(mid, item)
        return item

    def connect_all(self, app_ids: list[str]) -> dict[str, Any]:
        links = [self.connect_application(app_id=a) for a in app_ids]
        return {"links": links, "count": len(links), "engines": list(MEMORY_ENGINES)}

    def put(self, *, app_id: str, key: str, value: Any, engine: str = "semantic_memory") -> dict[str, Any]:
        eid = f"mkv_{uuid.uuid4().hex[:10]}"
        record = {"memory_id": eid, "app_id": app_id, "key": key, "value": value, "engine": engine, "at": _now()}
        self.store.memory_links.save(eid, record)
        return record

    def status(self) -> dict[str, Any]:
        return {"shared_memory": "1.0", "engines": list(MEMORY_ENGINES), "links": len(self.store.memory_links.list_all()), "ready": True}


shared_memory_hub = SharedMemoryHub()
