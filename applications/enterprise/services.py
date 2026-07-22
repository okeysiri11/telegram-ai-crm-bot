"""Enterprise Services — gateway, registries, bus, search, backup (Sprint 12.5)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise.shared.store import EnterpriseStore, enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class EnterpriseServices:
    def __init__(self, store: EnterpriseStore | None = None) -> None:
        self.store = store or enterprise_store

    def register_route(self, *, path: str, target: str, method: str = "GET") -> dict[str, Any]:
        if not path or not target:
            raise ValidationError("path and target required")
        rid = _id("route")
        route = {
            "route_id": rid,
            "path": path,
            "target": target,
            "method": method.upper(),
            "status": "active",
            "registered_at": _now(),
        }
        return self.store.gateway_routes.save(rid, route)

    def register_organization(self, *, organization_id: str, name: str) -> dict[str, Any]:
        return self.store.organizations.get(organization_id) or {
            "organization_id": organization_id,
            "name": name,
            "registry": "organization",
            "registered_at": _now(),
        }

    def register_workspace(self, *, workspace_id: str, name: str) -> dict[str, Any]:
        return self.store.workspaces.get(workspace_id) or {
            "workspace_id": workspace_id,
            "name": name,
            "registry": "workspace",
            "registered_at": _now(),
        }

    def schedule(self, *, name: str, cron: str = "@hourly", payload: dict[str, Any] | None = None) -> dict[str, Any]:
        sid = _id("gsched")
        job = {
            "schedule_id": sid,
            "name": name,
            "cron": cron,
            "payload": payload or {},
            "status": "queued",
            "created_at": _now(),
        }
        return self.store.schedules.save(sid, job)

    def publish_event(self, *, topic: str, payload: dict[str, Any] | None = None, source: str = "enterprise") -> dict[str, Any]:
        if not topic:
            raise ValidationError("topic required")
        eid = _id("eevt")
        event = {
            "event_id": eid,
            "topic": topic,
            "payload": payload or {},
            "source": source,
            "published_at": _now(),
        }
        return self.store.events.save(eid, event)

    def search_index(self, *, key: str, document: dict[str, Any]) -> dict[str, Any]:
        if not key:
            raise ValidationError("search key required")
        entry = {"key": key, "document": document, "indexed_at": _now()}
        return self.store.search_index.save(key, entry)

    def search(self, query: str) -> list[dict[str, Any]]:
        q = (query or "").lower()
        results = []
        for item in self.store.search_index.list_all():
            blob = str(item.get("document", {})).lower() + " " + str(item.get("key", "")).lower()
            if q in blob:
                results.append(item)
        return results

    def store_knowledge(self, *, title: str, body: str, tags: list[str] | None = None) -> dict[str, Any]:
        kid = _id("eknow")
        doc = {
            "knowledge_id": kid,
            "title": title,
            "body": body,
            "tags": tags or [],
            "created_at": _now(),
        }
        return self.store.knowledge_docs.save(kid, doc)

    def backup(self, *, label: str = "enterprise") -> dict[str, Any]:
        bid = _id("bak")
        snapshot = {
            "backup_id": bid,
            "label": label,
            "counts": {
                "organizations": len(self.store.organizations.list_all()),
                "tenants": len(self.store.tenants.list_all()),
                "workspaces": len(self.store.workspaces.list_all()),
                "projects": len(self.store.projects.list_all()),
            },
            "status": "completed",
            "created_at": _now(),
        }
        return self.store.backups.save(bid, snapshot)

    def get_backup(self, backup_id: str) -> dict[str, Any]:
        item = self.store.backups.get(backup_id)
        if item is None:
            raise NotFoundError("backup", backup_id)
        return item

    def status(self) -> dict[str, Any]:
        return {
            "gateway_routes": len(self.store.gateway_routes.list_all()),
            "schedules": len(self.store.schedules.list_all()),
            "events": len(self.store.events.list_all()),
            "search_index": len(self.store.search_index.list_all()),
            "knowledge_docs": len(self.store.knowledge_docs.list_all()),
            "backups": len(self.store.backups.list_all()),
        }


enterprise_services = EnterpriseServices()
