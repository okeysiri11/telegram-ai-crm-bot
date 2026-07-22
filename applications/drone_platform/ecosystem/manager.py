"""Drone Ecosystem Manager — unified registry, search, knowledge, dashboard, events, sync (Sprint 11.10)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.exceptions import ValidationError
from applications.drone_platform.shared.store import DroneStore, drone_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


MODULE_CATALOG = (
    "engineering",
    "firmware",
    "mavlink",
    "mission_planning",
    "manufacturing",
    "warehouse",
    "lifecycle",
    "cloud",
    "mission_center",
    "ground_control",
    "digital_twin",
    "resilience",
    "fleet",
    "swarm",
)


class DroneEcosystemManager:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store
        self._seed_registry()

    def _seed_registry(self) -> None:
        if self.store.ecosystem_registry.list_all():
            return
        for name in MODULE_CATALOG:
            rid = f"eco_{name}"
            self.store.ecosystem_registry.save(
                rid,
                {
                    "registry_id": rid,
                    "module": name,
                    "status": "connected",
                    "version": "1.0",
                    "synced_at": _now(),
                },
            )

    def register_module(self, *, module: str, version: str = "1.0", metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        if not module:
            raise ValidationError("module required")
        rid = f"eco_{module}"
        item = {
            "registry_id": rid,
            "module": module,
            "status": "connected",
            "version": version,
            "metadata": dict(metadata or {}),
            "synced_at": _now(),
        }
        self.store.ecosystem_registry.save(rid, item)
        return item

    def unified_registry(self) -> dict[str, Any]:
        self._seed_registry()
        modules = self.store.ecosystem_registry.list_all()
        return {"modules": modules, "count": len(modules), "catalog": list(MODULE_CATALOG)}

    def unified_search(self, *, query: str, domains: list[str] | None = None) -> dict[str, Any]:
        q = (query or "").lower().strip()
        domains = domains or list(MODULE_CATALOG)
        hits: list[dict[str, Any]] = []
        for mod in self.store.ecosystem_registry.list_all():
            if mod.get("module") not in domains:
                continue
            if not q or q in str(mod.get("module", "")).lower() or q in str(mod.get("status", "")).lower():
                hits.append({"type": "module", "id": mod.get("registry_id"), "module": mod.get("module"), "status": mod.get("status")})
        for twin in self.store.unified_twins.list_all():
            blob = f"{twin.get('name', '')} {twin.get('twin_type', '')}".lower()
            if not q or q in blob:
                hits.append({"type": "twin", "id": twin.get("twin_id"), "name": twin.get("name"), "twin_type": twin.get("twin_type")})
        for life in self.store.aircraft_lifecycles_eco.list_all():
            blob = f"{life.get('aircraft_id', '')} {life.get('stage', '')}".lower()
            if not q or q in blob:
                hits.append({"type": "lifecycle", "id": life.get("lifecycle_id"), "aircraft_id": life.get("aircraft_id"), "stage": life.get("stage")})
        return {"query": query, "hits": hits, "count": len(hits)}

    def unified_knowledge(self) -> dict[str, Any]:
        return {
            "nodes": [
                {"id": "engineering", "links": ["firmware", "manufacturing", "digital_twin"]},
                {"id": "firmware", "links": ["mavlink", "mission_planning"]},
                {"id": "mission_center", "links": ["ground_control", "fleet", "cloud"]},
                {"id": "cloud", "links": ["digital_twin", "lifecycle"]},
                {"id": "ai", "links": ["engineering", "mission_center", "manufacturing", "cloud"]},
            ],
            "updated_at": _now(),
        }

    def unified_dashboard(self) -> dict[str, Any]:
        reg = self.unified_registry()
        return {
            "type": "unified_dashboard",
            "modules_connected": reg["count"],
            "events": len(self.store.ecosystem_events.list_all()),
            "twins": len(self.store.unified_twins.list_all()),
            "lifecycles": len(self.store.aircraft_lifecycles_eco.list_all()),
            "syncs": len(self.store.ecosystem_syncs.list_all()),
            "at": _now(),
        }

    def unified_analytics(self) -> dict[str, Any]:
        return {
            "module_health": {m["module"]: m.get("status") for m in self.store.ecosystem_registry.list_all()},
            "event_count": len(self.store.ecosystem_events.list_all()),
            "twin_count": len(self.store.unified_twins.list_all()),
            "lifecycle_active": len([x for x in self.store.aircraft_lifecycles_eco.list_all() if x.get("stage") not in {"retirement"}]),
            "at": _now(),
        }

    def publish_event(self, *, topic: str, payload: dict[str, Any] | None = None, source: str = "ecosystem") -> dict[str, Any]:
        if not topic:
            raise ValidationError("topic required")
        eid = f"eevt_{uuid.uuid4().hex[:12]}"
        event = {"event_id": eid, "topic": topic, "source": source, "payload": dict(payload or {}), "at": _now()}
        self.store.ecosystem_events.save(eid, event)
        return event

    def list_events(self, *, topic: str | None = None) -> list[dict[str, Any]]:
        events = self.store.ecosystem_events.list_all()
        if topic:
            events = [e for e in events if e.get("topic") == topic]
        return events

    def cross_module_sync(self, *, modules: list[str] | None = None) -> dict[str, Any]:
        self._seed_registry()
        mods = list(modules or MODULE_CATALOG)
        sid = f"esync_{uuid.uuid4().hex[:12]}"
        for name in mods:
            rid = f"eco_{name}"
            item = self.store.ecosystem_registry.get(rid)
            if item:
                item["synced_at"] = _now()
                item["status"] = "connected"
                self.store.ecosystem_registry.save(rid, item)
            else:
                self.register_module(module=name)
        record = {"sync_id": sid, "modules": mods, "status": "completed", "at": _now()}
        self.store.ecosystem_syncs.save(sid, record)
        self.publish_event(topic="ecosystem.sync", payload={"sync_id": sid, "modules": mods})
        return record

    def status(self) -> dict[str, Any]:
        self._seed_registry()
        return {
            "drone_ecosystem": "1.0",
            "modules": len(self.store.ecosystem_registry.list_all()),
            "events": len(self.store.ecosystem_events.list_all()),
            "ready": True,
        }


drone_ecosystem_manager = DroneEcosystemManager()
