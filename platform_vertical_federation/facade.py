"""Enterprise Vertical Federation library — Sprint 27.3."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from platform_vertical_federation.models import (
    API_PREFIX,
    ARCHITECTURE,
    CORE_VERTICALS,
    CROSS_VERTICAL_LINKS,
    HUB,
    KPI_TARGETS,
    KNOWLEDGE_SCOPES,
    MARKETPLACE_ASSET_TYPES,
    PRINCIPLES,
    SPRINT,
    VERSION,
    WEB_PATH,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def _slug(name: str) -> str:
    return name.lower().replace(" ", "_")


class VerticalFederationLibrary:
    """Unified control plane for industry verticals."""

    def __init__(self) -> None:
        self._verticals = self._seed_verticals()
        self._directors = self._seed_directors()
        self._links = self._seed_links()
        self._messages: list[dict[str, Any]] = []
        self._marketplace: list[dict[str, Any]] = self._seed_marketplace()
        self._knowledge: list[dict[str, Any]] = self._seed_knowledge()
        self._events: list[dict[str, Any]] = [
            {"type": "sync", "message": "Auto ↔ Finance KPI sync completed"},
            {"type": "publish", "message": "Beauty published CRM widget pack"},
        ]
        self._alerts: list[dict[str, Any]] = [
            {"level": "info", "message": "Port throughput within SLA"},
            {"level": "warn", "message": "Logistics AI utilization above 85%"},
        ]
        self._recommendations: list[str] = [
            "Connect Construction marketplace listings to CRM pipeline",
            "Promote Drone → AI Vision semantic knowledge pack to shared scope",
        ]
        self._custom: list[dict[str, Any]] = []

    def _seed_verticals(self) -> list[dict[str, Any]]:
        owners = {
            "Auto": "auto_ops",
            "Beauty": "beauty_ops",
            "Finance": "cfo_office",
            "Legal": "clo_office",
            "Crypto": "treasury",
            "Port": "port_ops",
            "Agriculture": "agro_ops",
            "Drone": "ai_vision_lab",
        }
        rows = []
        for i, name in enumerate(CORE_VERTICALS):
            code = _slug(name)
            status = "production" if name in ("Auto", "Beauty", "Finance", "Legal") else "ready"
            if name in ("Education", "Hospitality"):
                status = "pilot"
            rows.append(
                {
                    "id": f"vert_{code}",
                    "name": name,
                    "status": status,
                    "owner": owners.get(name, f"{code}_owner"),
                    "ai_director": f"{name} AI Director",
                    "workspace": f"/workspaces/{code}",
                    "kpi": {
                        "score": 88 - (i % 7),
                        "activity": 40 + (i * 3) % 50,
                        "ai_utilization": round(0.45 + (i % 5) * 0.08, 2),
                    },
                    "applications": [f"{code}_app", f"{code}_crm"] if name != "Drone" else [f"{code}_fleet"],
                    "agents": [f"agent_{code}_ops", f"agent_{code}_analyst"],
                    "api": f"/api/{code}/v1",
                    "knowledge_base": f"kb://verticals/{code}",
                    "agent_count": 2 + (i % 4),
                }
            )
        return rows

    def _seed_directors(self) -> list[dict[str, Any]]:
        return [
            {
                "vertical_id": v["id"],
                "vertical": v["name"],
                "director": v["ai_director"],
                "status": "active",
                "capabilities": [
                    "manage_agents",
                    "analyze_kpi",
                    "distribute_tasks",
                    "control_processes",
                    "talk_to_executive_ai",
                ],
                "linked_executive": "AI Director",
                "load": round(0.3 + (idx % 5) * 0.1, 2),
            }
            for idx, v in enumerate(self._verticals)
        ]

    def _seed_links(self) -> list[dict[str, Any]]:
        links = []
        for src, dst in CROSS_VERTICAL_LINKS:
            links.append(
                {
                    "id": _id("xlink"),
                    "source": src,
                    "target": dst,
                    "channel": "cross_vertical_bus",
                    "status": "active",
                }
            )
        return links

    def _seed_marketplace(self) -> list[dict[str, Any]]:
        samples = [
            ("Beauty", "applications", "Beauty Booking Suite"),
            ("Auto", "ai_agents", "Vehicle Lead Qualifier"),
            ("Finance", "dashboards", "Treasury Pulse"),
            ("Logistics", "automation", "Route Rebalancer"),
            ("Construction", "workflows", "Permit Approval Flow"),
            ("Marketplace", "templates", "Listing Launch Kit"),
            ("Drone", "widgets", "Flight Health Widget"),
        ]
        return [
            {
                "id": _id("vmp"),
                "vertical": vertical,
                "asset_type": asset_type,
                "name": name,
                "status": "published",
                "published_at": _now(),
            }
            for vertical, asset_type, name in samples
        ]

    def _seed_knowledge(self) -> list[dict[str, Any]]:
        rows = [
            ("shared", "Platform-wide CRM → Finance invoice handshake"),
            ("industry", "Auto: OEM compliance checklist"),
            ("local", "Port terminal A shift policy"),
            ("ai_memory", "Executive AI remembered Logistics overload last week"),
            ("semantic", "embedding://verticals/agro-drone-vision"),
        ]
        return [
            {
                "id": _id("vkg"),
                "scope": scope,
                "content": content,
                "created_at": _now(),
            }
            for scope, content in rows
        ]

    def bootstrap(self) -> dict[str, Any]:
        self.__init__()
        return {
            "bootstrap": True,
            "version": VERSION,
            "sprint": SPRINT,
            "hub": HUB,
            "api_prefix": API_PREFIX,
            "web_path": WEB_PATH,
            "vertical_registry_ready": True,
            "vertical_executive_ai_ready": True,
            "cross_vertical_communication_ready": True,
            "unified_dashboard_ready": True,
            "vertical_marketplace_ready": True,
            "knowledge_federation_ready": True,
            "architecture": list(ARCHITECTURE),
            "full": {
                "inventory": self.inventory(),
                "dashboard": self.dashboard(),
                "registry": self.registry(),
                "directors": self.directors(),
                "links": self.links(),
                "marketplace": self.marketplace_list(),
                "knowledge": self.knowledge_list(),
                "integrations": {
                    "ai_os": "/api/ai-os/v1",
                    "organization_brain": "/api/organization-brain/v1",
                    "executive_ai": "connected",
                },
            },
        }

    def inventory(self) -> dict[str, Any]:
        return {
            "hub": HUB,
            "version": VERSION,
            "sprint": SPRINT,
            "architecture": list(ARCHITECTURE),
            "core_verticals": list(CORE_VERTICALS),
            "cross_vertical_links": [f"{a}→{b}" for a, b in CROSS_VERTICAL_LINKS],
            "marketplace_asset_types": list(MARKETPLACE_ASSET_TYPES),
            "knowledge_scopes": list(KNOWLEDGE_SCOPES),
            "principles": list(PRINCIPLES),
            "kpi_targets": dict(KPI_TARGETS),
            "counts": {
                "verticals": len(self._verticals) + len(self._custom),
                "directors": len(self._directors),
                "links": len(self._links),
                "marketplace": len(self._marketplace),
                "knowledge": len(self._knowledge),
                "messages": len(self._messages),
            },
        }

    def registry(self) -> dict[str, Any]:
        items = list(self._verticals) + list(self._custom)
        return {
            "ready": True,
            "count": len(items),
            "supports_custom": True,
            "items": items,
        }

    def register_custom(self, name: str, owner: str | None = None) -> dict[str, Any]:
        code = _slug(name)
        row = {
            "id": f"vert_custom_{code}",
            "name": name,
            "status": "custom",
            "owner": owner or f"{code}_owner",
            "ai_director": f"{name} AI Director",
            "workspace": f"/workspaces/custom/{code}",
            "kpi": {"score": 70, "activity": 20, "ai_utilization": 0.3},
            "applications": [f"{code}_app"],
            "agents": [f"agent_{code}_ops"],
            "api": f"/api/custom/{code}/v1",
            "knowledge_base": f"kb://verticals/custom/{code}",
            "agent_count": 1,
            "custom": True,
        }
        self._custom.append(row)
        self._directors.append(
            {
                "vertical_id": row["id"],
                "vertical": name,
                "director": row["ai_director"],
                "status": "active",
                "capabilities": [
                    "manage_agents",
                    "analyze_kpi",
                    "distribute_tasks",
                    "control_processes",
                    "talk_to_executive_ai",
                ],
                "linked_executive": "AI Director",
                "load": 0.25,
            }
        )
        return {"ok": True, **row}

    def directors(self, vertical: str | None = None) -> dict[str, Any]:
        items = self._directors
        if vertical:
            items = [
                d
                for d in items
                if d["vertical"].lower() == vertical.lower() or d["vertical_id"] == vertical
            ]
        return {"ready": True, "count": len(items), "items": list(items), "executive_ai_connected": True}

    def director_act(self, vertical: str, action: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        director = next(
            (
                d
                for d in self._directors
                if d["vertical"].lower() == vertical.lower() or d["vertical_id"] == vertical
            ),
            None,
        )
        if not director:
            director = {
                "vertical": vertical,
                "director": f"{vertical} AI Director",
                "linked_executive": "AI Director",
            }
        allowed = {
            "manage_agents",
            "analyze_kpi",
            "distribute_tasks",
            "control_processes",
            "talk_to_executive_ai",
        }
        act = action if action in allowed else "analyze_kpi"
        result = {
            "ok": True,
            "action_id": _id("vdir"),
            "vertical": director.get("vertical", vertical),
            "director": director.get("director"),
            "action": act,
            "payload": payload or {},
            "executive_ai": "acknowledged" if act == "talk_to_executive_ai" else "notified",
            "created_at": _now(),
        }
        self._events.append({"type": "director_action", "message": f"{result['director']}::{act}"})
        return result

    def links(self) -> dict[str, Any]:
        return {"ready": True, "count": len(self._links), "items": list(self._links)}

    def communicate(self, source: str, target: str, message: str, *, kind: str = "event") -> dict[str, Any]:
        record = {
            "message_id": _id("xvmsg"),
            "ok": True,
            "source": source,
            "target": target,
            "kind": kind,
            "message": message,
            "routed": True,
            "created_at": _now(),
        }
        self._messages.append(record)
        self._events.append(
            {"type": "cross_vertical", "message": f"{source} → {target}: {message[:80]}"}
        )
        return record

    def messages(self) -> dict[str, Any]:
        return {"count": len(self._messages), "items": list(self._messages)}

    def marketplace_publish(
        self,
        vertical: str,
        asset_type: str,
        name: str,
    ) -> dict[str, Any]:
        atype = asset_type if asset_type in MARKETPLACE_ASSET_TYPES else "templates"
        item = {
            "id": _id("vmp"),
            "vertical": vertical,
            "asset_type": atype,
            "name": name,
            "status": "published",
            "published_at": _now(),
        }
        self._marketplace.append(item)
        return {"ok": True, **item}

    def marketplace_list(self, vertical: str | None = None) -> dict[str, Any]:
        items = self._marketplace
        if vertical:
            items = [m for m in items if m["vertical"].lower() == vertical.lower()]
        by_type = {t: 0 for t in MARKETPLACE_ASSET_TYPES}
        for row in self._marketplace:
            by_type[row["asset_type"]] = by_type.get(row["asset_type"], 0) + 1
        return {
            "ready": True,
            "asset_types": list(MARKETPLACE_ASSET_TYPES),
            "counts": by_type,
            "items": list(items),
        }

    def knowledge_write(self, scope: str, content: str) -> dict[str, Any]:
        scope_norm = scope if scope in KNOWLEDGE_SCOPES else "shared"
        item = {
            "id": _id("vkg"),
            "scope": scope_norm,
            "content": content,
            "created_at": _now(),
        }
        self._knowledge.append(item)
        return {"ok": True, **item}

    def knowledge_list(self, scope: str | None = None) -> dict[str, Any]:
        items = self._knowledge
        if scope:
            items = [k for k in items if k["scope"] == scope]
        by_scope = {s: 0 for s in KNOWLEDGE_SCOPES}
        for row in self._knowledge:
            by_scope[row["scope"]] = by_scope.get(row["scope"], 0) + 1
        return {
            "ready": True,
            "scopes": list(KNOWLEDGE_SCOPES),
            "counts": by_scope,
            "items": list(items),
        }

    def semantic_search(self, query: str) -> dict[str, Any]:
        q = query.lower()
        hits = [k for k in self._knowledge if q in k["content"].lower() or k["scope"] == "semantic"]
        if not hits:
            hits = [k for k in self._knowledge if k["scope"] in ("shared", "semantic")][:3]
        return {
            "ok": True,
            "query": query,
            "mode": "semantic",
            "count": len(hits),
            "hits": hits,
        }

    def dashboard(self) -> dict[str, Any]:
        all_verts = list(self._verticals) + list(self._custom)
        total_agents = sum(v.get("agent_count", 0) for v in all_verts)
        ai_avg = sum(v["kpi"]["ai_utilization"] for v in all_verts) / max(1, len(all_verts))
        return {
            "title": "Vertical Federation Dashboard",
            "version": VERSION,
            "sprint": SPRINT,
            "vertical_states": [
                {
                    "id": v["id"],
                    "name": v["name"],
                    "status": v["status"],
                    "kpi_score": v["kpi"]["score"],
                    "activity": v["kpi"]["activity"],
                    "agents": v["agent_count"],
                    "ai_utilization": v["kpi"]["ai_utilization"],
                }
                for v in all_verts
            ],
            "kpi": {
                "verticals_total": len(all_verts),
                "production": sum(1 for v in all_verts if v["status"] == "production"),
                "avg_kpi": round(
                    sum(v["kpi"]["score"] for v in all_verts) / max(1, len(all_verts)), 1
                ),
                "agents_total": total_agents,
                "ai_utilization_avg": round(ai_avg, 3),
            },
            "activity": {
                "messages": len(self._messages),
                "marketplace_assets": len(self._marketplace),
                "director_actions": sum(1 for e in self._events if e["type"] == "director_action"),
            },
            "events": list(self._events)[-10:],
            "alerts": list(self._alerts),
            "recommendations": list(self._recommendations),
            "executive_ai_connected": True,
            "links_active": sum(1 for l in self._links if l["status"] == "active"),
        }

    def status(self) -> dict[str, Any]:
        return {
            "version": VERSION,
            "sprint": SPRINT,
            "hub": HUB,
            "api_prefix": API_PREFIX,
            "verticals": len(self._verticals) + len(self._custom),
            "directors": len(self._directors),
            "links": len(self._links),
            "marketplace": len(self._marketplace),
            "knowledge": len(self._knowledge),
            "ready": True,
        }
