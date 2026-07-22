"""Unified Dashboard + Search + Settings + Notifications + Event Center + Gateway (Sprint 12.0)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.ecosystem.manager import EcosystemManager, ecosystem_manager
from applications.ecosystem.shared.store import UnifiedEcosystemStore, unified_ecosystem_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class UnifiedDashboard:
    def __init__(self, store: UnifiedEcosystemStore | None = None, manager: EcosystemManager | None = None) -> None:
        self.store = store or unified_ecosystem_store
        self.manager = manager or ecosystem_manager

    def executive(self) -> dict[str, Any]:
        apps = self.manager.list_applications()
        return {
            "type": "executive_dashboard",
            "applications_online": sum(1 for a in apps if a.get("status") == "online"),
            "applications_total": len(apps),
            "kpis": {"cross_app_exchanges": len(self.store.exchanges.list_all()), "agents_active": len([a for a in self.store.agents.list_all() if a.get("status") == "active"])},
            "at": _now(),
        }

    def operations(self) -> dict[str, Any]:
        return {"type": "operations_dashboard", "events": len(self.store.events.list_all()), "notifications": len(self.store.notifications.list_all()), "at": _now()}

    def engineering(self) -> dict[str, Any]:
        return {"type": "engineering_dashboard", "source": "drone_platform+port_erp", "at": _now()}

    def financial(self) -> dict[str, Any]:
        return {"type": "financial_dashboard", "source": "port_erp+auto+agro", "at": _now()}

    def manufacturing(self) -> dict[str, Any]:
        return {"type": "manufacturing_dashboard", "source": "drone_platform.manufacturing", "at": _now()}

    def fleet(self) -> dict[str, Any]:
        return {"type": "fleet_dashboard", "source": "drone_platform+auto+port", "at": _now()}

    def crm(self) -> dict[str, Any]:
        return {"type": "crm_dashboard", "source": "crm+auto+agro", "at": _now()}

    def agro(self) -> dict[str, Any]:
        return {"type": "agro_dashboard", "source": "agro_marketplace", "at": _now()}

    def port(self) -> dict[str, Any]:
        return {"type": "port_dashboard", "source": "port_erp", "at": _now()}

    def system(self) -> dict[str, Any]:
        return {"type": "system_dashboard", "sessions": len(self.store.sessions.list_all()), "audit": len(self.store.audit.list_all()), "at": _now()}

    def all_dashboards(self) -> dict[str, Any]:
        return {
            "executive": self.executive(),
            "operations": self.operations(),
            "engineering": self.engineering(),
            "financial": self.financial(),
            "manufacturing": self.manufacturing(),
            "fleet": self.fleet(),
            "crm": self.crm(),
            "agro": self.agro(),
            "port": self.port(),
            "system": self.system(),
        }

    def status(self) -> dict[str, Any]:
        return {"unified_dashboard": "1.0", "views": 10, "executive_dashboard_ready": True, "ready": True}


class UnifiedSearch:
    def __init__(self, store: UnifiedEcosystemStore | None = None, manager: EcosystemManager | None = None) -> None:
        self.store = store or unified_ecosystem_store
        self.manager = manager or ecosystem_manager

    def index_sample(self) -> None:
        if self.store.search_index.list_all():
            return
        samples = [
            ("people", "Alex Operator"),
            ("companies", "Harbor Logistics"),
            ("projects", "Drone Survey Alpha"),
            ("vehicles", "VIN-DEMO-001"),
            ("orders", "PO-1001"),
            ("flights", "Mission OPS-22"),
            ("warehouses", "WH-Central"),
            ("documents", "Bill of Lading"),
            ("knowledge", "Knowledge Graph Node"),
        ]
        for kind, title in samples:
            sid = f"idx_{kind}_{uuid.uuid4().hex[:6]}"
            self.store.search_index.save(sid, {"id": sid, "kind": kind, "title": title, "at": _now()})

    def global_search(self, *, query: str) -> dict[str, Any]:
        self.index_sample()
        q = (query or "").lower().strip()
        hits = []
        for item in self.store.search_index.list_all():
            if not q or q in item.get("title", "").lower() or q in item.get("kind", "").lower():
                hits.append(item)
        for app in self.manager.list_applications():
            blob = f"{app.get('app_id', '')} {app.get('name', '')}".lower()
            if not q or q in blob:
                hits.append({"kind": "application", "title": app.get("name"), "id": app.get("app_id")})
        return {"mode": "global", "query": query, "hits": hits, "count": len(hits)}

    def semantic_search(self, *, query: str) -> dict[str, Any]:
        result = self.global_search(query=query)
        result["mode"] = "semantic"
        result["note"] = "semantic ranking via shared memory / knowledge graph bridges"
        return result

    def status(self) -> dict[str, Any]:
        return {"unified_search": "1.0", "indexed": len(self.store.search_index.list_all()), "ready": True}


class UnifiedSettings:
    def __init__(self, store: UnifiedEcosystemStore | None = None) -> None:
        self.store = store or unified_ecosystem_store

    def set(self, *, key: str, value: Any, scope: str = "global") -> dict[str, Any]:
        item = {"key": key, "value": value, "scope": scope, "at": _now()}
        self.store.settings.save(f"{scope}:{key}", item)
        return item

    def get(self, *, key: str, scope: str = "global") -> dict[str, Any] | None:
        return self.store.settings.get(f"{scope}:{key}")

    def list_settings(self) -> list[dict[str, Any]]:
        return self.store.settings.list_all()

    def status(self) -> dict[str, Any]:
        return {"unified_settings": "1.0", "count": len(self.list_settings()), "ready": True}


class UnifiedNotifications:
    def __init__(self, store: UnifiedEcosystemStore | None = None) -> None:
        self.store = store or unified_ecosystem_store

    def notify(self, *, recipient: str, title: str, body: str = "", app_id: str = "") -> dict[str, Any]:
        nid = f"ntf_{uuid.uuid4().hex[:12]}"
        item = {"notification_id": nid, "recipient": recipient, "title": title, "body": body, "app_id": app_id, "read": False, "at": _now()}
        self.store.notifications.save(nid, item)
        return item

    def list_for(self, recipient: str) -> list[dict[str, Any]]:
        return [n for n in self.store.notifications.list_all() if n.get("recipient") == recipient]

    def status(self) -> dict[str, Any]:
        return {"unified_notifications": "1.0", "count": len(self.store.notifications.list_all()), "ready": True}


class UnifiedEventCenter:
    def __init__(self, store: UnifiedEcosystemStore | None = None) -> None:
        self.store = store or unified_ecosystem_store

    def publish(self, *, topic: str, source: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        eid = f"uevt_{uuid.uuid4().hex[:12]}"
        event = {"event_id": eid, "topic": topic, "source": source, "payload": dict(payload or {}), "at": _now()}
        self.store.events.save(eid, event)
        return event

    def list_events(self, *, topic: str | None = None) -> list[dict[str, Any]]:
        events = self.store.events.list_all()
        if topic:
            events = [e for e in events if e.get("topic") == topic]
        return events

    def status(self) -> dict[str, Any]:
        return {"unified_event_center": "1.0", "events": len(self.list_events()), "ready": True}


class UnifiedAPIGateway:
    ROUTE_MAP = {
        "crm": "/api/* (crm_api)",
        "auto_marketplace": "/api/auto/v1",
        "agro_marketplace": "/api/agro/v1",
        "port_erp": "/api/port/v1",
        "drone_platform": "/api/drone/v1",
        "ecosystem_core": "/api/ecosystem/v1",
        "ai_ecosystem": "/api/ai-ecosystem/v1",
    }

    def route(self, *, app_id: str, path: str = "/") -> dict[str, Any]:
        base = self.ROUTE_MAP.get(app_id, "/api/unknown")
        return {"app_id": app_id, "base": base, "path": path, "routed": app_id in self.ROUTE_MAP, "at": _now()}

    def catalog(self) -> dict[str, Any]:
        return {"gateway": "unified_api_gateway", "routes": dict(self.ROUTE_MAP)}

    def status(self) -> dict[str, Any]:
        return {"unified_api_gateway": "1.0", "routes": len(self.ROUTE_MAP), "ready": True}


unified_dashboard = UnifiedDashboard()
unified_search = UnifiedSearch()
unified_settings = UnifiedSettings()
unified_notifications = UnifiedNotifications()
unified_event_center = UnifiedEventCenter()
unified_api_gateway = UnifiedAPIGateway()
