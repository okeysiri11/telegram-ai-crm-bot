"""Global Knowledge Graph merge + Analytics (Sprint 12.0)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from applications.ecosystem.shared.store import UnifiedEcosystemStore, unified_ecosystem_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


ROOT = Path(__file__).resolve().parents[2]


class GlobalKnowledge:
    """Merge knowledge registries from apps + knowledge/ without rewriting them."""

    def __init__(self, store: UnifiedEcosystemStore | None = None) -> None:
        self.store = store or unified_ecosystem_store

    def discover_sources(self) -> list[dict[str, Any]]:
        sources = []
        knowledge_root = ROOT / "knowledge"
        if knowledge_root.exists():
            sources.append({"id": "knowledge_system", "path": str(knowledge_root), "type": "obsidian"})
        app_docs = ROOT / "knowledge" / "applications"
        if app_docs.exists():
            for p in sorted(app_docs.glob("*.md")):
                sources.append({"id": f"app_doc:{p.stem}", "path": str(p), "type": "application_doc"})
        drone_kb = ROOT / "knowledge" / "drone"
        if drone_kb.exists():
            sources.append({"id": "drone_knowledge", "path": str(drone_kb), "type": "domain_pack", "files": len(list(drone_kb.glob("*.md")))})
        return sources

    def build_graph(self) -> dict[str, Any]:
        sources = self.discover_sources()
        nodes = [
            {"id": "platform_core", "label": "Platform Core"},
            {"id": "ecosystem", "label": "AI Ecosystem v1.5"},
            {"id": "ai_ecosystem", "label": "Unified AI Ecosystem 3.0"},
            {"id": "crm", "label": "CRM"},
            {"id": "auto_marketplace", "label": "Auto Marketplace"},
            {"id": "agro_marketplace", "label": "Agro Marketplace"},
            {"id": "port_erp", "label": "Port ERP"},
            {"id": "drone_platform", "label": "Drone Platform"},
            {"id": "knowledge_system", "label": "Knowledge System"},
        ]
        edges = [
            ("ai_ecosystem", "platform_core"),
            ("ai_ecosystem", "ecosystem"),
            ("ai_ecosystem", "crm"),
            ("ai_ecosystem", "auto_marketplace"),
            ("ai_ecosystem", "agro_marketplace"),
            ("ai_ecosystem", "port_erp"),
            ("ai_ecosystem", "drone_platform"),
            ("ai_ecosystem", "knowledge_system"),
            ("ecosystem", "platform_core"),
            ("auto_marketplace", "ecosystem"),
            ("agro_marketplace", "ecosystem"),
            ("port_erp", "ecosystem"),
            ("drone_platform", "ecosystem"),
        ]
        graph = {
            "graph_id": f"gkg_{uuid.uuid4().hex[:10]}",
            "nodes": nodes,
            "edges": [{"from": a, "to": b} for a, b in edges],
            "sources": sources,
            "source_count": len(sources),
            "at": _now(),
        }
        self.store.knowledge_nodes.save("global_graph", graph)
        return graph

    def status(self) -> dict[str, Any]:
        return {
            "global_knowledge": "1.0",
            "sources": len(self.discover_sources()),
            "ready": True,
            "global_knowledge_graph_ready": True,
        }


class EcosystemAnalytics:
    def __init__(self, store: UnifiedEcosystemStore | None = None) -> None:
        self.store = store or unified_ecosystem_store

    def kpis(self) -> dict[str, Any]:
        return {
            "applications": len(self.store.applications.list_all()),
            "agents_active": len([a for a in self.store.agents.list_all() if a.get("status") == "active"]),
            "exchanges": len(self.store.exchanges.list_all()),
            "events": len(self.store.events.list_all()),
            "sessions": len(self.store.sessions.list_all()),
            "at": _now(),
        }

    def report(self, *, report_type: str = "executive") -> dict[str, Any]:
        rid = f"erpt_{uuid.uuid4().hex[:10]}"
        sections = {
            "executive": ["kpis", "apps", "risks"],
            "financial": ["revenue_proxy", "costs_proxy"],
            "performance": ["latency", "uptime"],
            "ai": ["agents", "collaborations", "decisions"],
        }.get(report_type, ["summary"])
        report = {"report_id": rid, "report_type": report_type, "sections": sections, "kpis": self.kpis(), "status": "generated", "at": _now()}
        self.store.reports.save(rid, report)
        return report

    def status(self) -> dict[str, Any]:
        return {"analytics": "1.0", "reports": len(self.store.reports.list_all()), "ready": True}


global_knowledge = GlobalKnowledge()
ecosystem_analytics = EcosystemAnalytics()
