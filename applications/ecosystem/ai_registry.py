"""Unified AI agent registry — registers existing AIs without rewriting apps (Sprint 12.0)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.ecosystem.shared.store import UnifiedEcosystemStore, unified_ecosystem_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


AGENT_CATALOG = (
    {"agent_id": "chief", "name": "Chief AI", "status": "active", "application": "ai_ecosystem"},
    {"agent_id": "crm", "name": "CRM AI", "status": "active", "application": "crm"},
    {"agent_id": "auto", "name": "Auto AI", "status": "active", "application": "auto_marketplace"},
    {"agent_id": "agro", "name": "Agro AI", "status": "active", "application": "agro_marketplace"},
    {"agent_id": "port", "name": "Port AI", "status": "active", "application": "port_erp"},
    {"agent_id": "drone", "name": "Drone AI", "status": "active", "application": "drone_platform"},
    {"agent_id": "legal", "name": "Legal AI", "status": "future", "application": "legal_platform"},
    {"agent_id": "construction", "name": "Construction AI", "status": "future", "application": "construction"},
    {"agent_id": "medical", "name": "Medical AI", "status": "future", "application": "medical"},
    {"agent_id": "manufacturing", "name": "Manufacturing AI", "status": "future", "application": "manufacturing"},
    {"agent_id": "accounting", "name": "Accounting AI", "status": "future", "application": "accounting"},
)


class UnifiedAIRegistry:
    def __init__(self, store: UnifiedEcosystemStore | None = None) -> None:
        self.store = store or unified_ecosystem_store
        self._seed()

    def _seed(self) -> None:
        if self.store.agents.list_all():
            return
        for agent in AGENT_CATALOG:
            self.store.agents.save(agent["agent_id"], {**agent, "registered_at": _now()})

    def list_agents(self, *, active_only: bool = False) -> list[dict[str, Any]]:
        self._seed()
        agents = self.store.agents.list_all()
        if active_only:
            agents = [a for a in agents if a.get("status") == "active"]
        return agents

    def register_agent(self, *, agent_id: str, name: str, application: str = "", status: str = "active") -> dict[str, Any]:
        item = {"agent_id": agent_id, "name": name, "application": application, "status": status, "registered_at": _now()}
        self.store.agents.save(agent_id, item)
        return item

    def collaborate(self, *, query: str, agents: list[str] | None = None, context: dict[str, Any] | None = None) -> dict[str, Any]:
        self._seed()
        selected = list(agents or ["chief", "crm", "auto", "agro", "port", "drone"])
        contributions = []
        for aid in selected:
            agent = self.store.agents.get(aid)
            if not agent or agent.get("status") == "future":
                continue
            contributions.append(
                {
                    "agent_id": aid,
                    "name": agent.get("name"),
                    "advice": f"{agent.get('name')} reviewed: prioritize safe, auditable action for '{query[:80]}'",
                }
            )
        # Prefer top-level ecosystem assistant when available
        ecosystem_reply = None
        try:
            from ecosystem import ecosystem

            if hasattr(ecosystem, "engine") and hasattr(ecosystem.engine, "assistant"):
                ecosystem_reply = {"source": "ecosystem.assistant", "note": "multi-agent engine available"}
        except Exception:
            ecosystem_reply = {"source": "local", "note": "ecosystem assistant bridge fallback"}

        # Prefer drone chief AI when available for synthesis
        drone_synth = None
        try:
            from applications.drone_platform import drone_platform

            if hasattr(drone_platform, "ai") and hasattr(drone_platform.ai, "assist"):
                drone_synth = drone_platform.ai.assist(
                    agent="multi_agent_collaborate",
                    query=query,
                    context={"agents": ["engineering", "mission", "fleet"], **(context or {})},
                )
        except Exception:
            drone_synth = None

        return {
            "collaboration_id": f"collab_{uuid.uuid4().hex[:10]}",
            "engine": "platform_multi_agent",
            "query": query,
            "agents": selected,
            "contributions": contributions,
            "ecosystem": ecosystem_reply,
            "drone_synthesis": drone_synth,
            "synthesis": "Chief AI merges specialist advice; escalate risks; keep Platform Core unmodified.",
            "policy": "engineering_assistance_only",
            "at": _now(),
        }

    def chief(self, *, query: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.collaborate(query=query, agents=["chief", "crm", "auto", "agro", "port", "drone"], context=context)

    def status(self) -> dict[str, Any]:
        agents = self.list_agents()
        return {
            "unified_ai": "1.0",
            "agents": len(agents),
            "active": sum(1 for a in agents if a.get("status") == "active"),
            "future": sum(1 for a in agents if a.get("status") == "future"),
            "chief_ai_ready": True,
            "ready": True,
        }


unified_ai_registry = UnifiedAIRegistry()
