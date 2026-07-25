"""AI Team Center — dashboard for organization AI Specialists."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.platform_builder.shared.group_ai import (
    GROUP_AI_CHAT_FOUNDATION,
    TEAM_OWNER_ACTIONS,
)
from applications.platform_builder.shared.exceptions import NotFoundError, ValidationError
from applications.platform_builder.shared.store import PlatformBuilderStore, platform_builder_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


SEED_TEAM = [
    {
        "name": "Ava",
        "avatar": "🧑‍⚕️",
        "profession": "Medical",
        "specialization": "Dentistry · Implantology",
        "status": "active",
        "current_task": "Prepare visit summary",
        "memory_usage": 0.42,
        "last_activity": "2m ago",
        "capabilities": ["Answer Questions", "Analyze Documents"],
    },
    {
        "name": "Noah",
        "avatar": "💼",
        "profession": "Finance",
        "specialization": "Treasury · Cash Flow",
        "status": "busy",
        "current_task": "Weekly cash report",
        "memory_usage": 0.61,
        "last_activity": "5m ago",
        "capabilities": ["Create Reports", "Analytics"],
    },
    {
        "name": "Mia",
        "avatar": "📣",
        "profession": "Marketing",
        "specialization": "Campaigns",
        "status": "idle",
        "current_task": None,
        "memory_usage": 0.28,
        "last_activity": "1h ago",
        "capabilities": ["Recommendations", "Create Reports"],
    },
    {
        "name": "Leo",
        "avatar": "⚖️",
        "profession": "Law",
        "specialization": "Contracts",
        "status": "active",
        "current_task": "Review service agreement",
        "memory_usage": 0.55,
        "last_activity": "12m ago",
        "capabilities": ["Create Contracts", "Analyze Documents"],
    },
]


class AITeamCenter:
    """AI Team dashboard and owner actions for specialists."""

    def __init__(self, store: PlatformBuilderStore | None = None) -> None:
        self.store = store or platform_builder_store

    def register_center(self, *, organization_id: str, concierge_id: str | None = None) -> dict[str, Any]:
        org = (organization_id or "").strip()
        if not org:
            raise ValidationError("organization_id is required")
        existing = self.get_center(org)
        if existing:
            if concierge_id and existing.get("concierge_id") != concierge_id:
                existing["concierge_id"] = concierge_id
                self.store.ai_team_centers.save(org, existing)
            return existing
        tid = _id("aitc")
        members = []
        # Prefer specialists created via AI Builder for this org's platform registry.
        for agent in self.store.ai_registry.list_all():
            members.append(self._card_from_agent(agent))
        if not members:
            for seed in SEED_TEAM:
                members.append(self._card_from_seed(seed, org))
        record = {
            "team_center_id": tid,
            "organization_id": org,
            "concierge_id": concierge_id,
            "title": "AI Team Center",
            "members": members,
            "owner_actions": list(TEAM_OWNER_ACTIONS),
            "unlimited_specialists": True,
            "group_ai_chat": GROUP_AI_CHAT_FOUNDATION,
            "registered_at": _now(),
            "sprint": "28.3",
        }
        self.store.ai_team_centers.save(org, record)
        return record

    def _card_from_seed(self, seed: dict[str, Any], org: str) -> dict[str, Any]:
        return {
            "agent_id": _id("team_agent"),
            "organization_id": org,
            **seed,
            "paused": False,
        }

    def _card_from_agent(self, agent: dict[str, Any]) -> dict[str, Any]:
        return {
            "agent_id": agent.get("agent_id"),
            "name": agent.get("name"),
            "avatar": "🤖",
            "profession": agent.get("profession") or "Specialist",
            "specialization": ", ".join(agent.get("specialization") or []) or "General",
            "status": "active",
            "current_task": None,
            "memory_usage": 0.35,
            "last_activity": "just now",
            "capabilities": list(agent.get("skills") or [])[:4],
            "paused": False,
        }

    def get_center(self, organization_id: str) -> dict[str, Any] | None:
        return self.store.ai_team_centers.get(organization_id)

    def require_center(self, organization_id: str) -> dict[str, Any]:
        center = self.get_center(organization_id)
        if not center:
            raise NotFoundError(f"AI Team Center not found for organization: {organization_id}")
        return center

    def dashboard(self, organization_id: str = "org_demo") -> dict[str, Any]:
        center = self.get_center(organization_id) or self.register_center(organization_id=organization_id)
        members = center.get("members") or []
        return {
            "title": "AI Team",
            "organization_id": organization_id,
            "team_center_id": center["team_center_id"],
            "concierge_id": center.get("concierge_id"),
            "count": len(members),
            "active": sum(1 for m in members if m.get("status") in ("active", "busy") and not m.get("paused")),
            "paused": sum(1 for m in members if m.get("paused")),
            "members": members,
            "owner_actions": list(TEAM_OWNER_ACTIONS),
            "group_ai_chat": GROUP_AI_CHAT_FOUNDATION,
            "ready": True,
        }

    def action(self, organization_id: str, agent_id: str, action: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if action not in TEAM_OWNER_ACTIONS:
            raise ValidationError(f"Unsupported owner action: {action}")
        center = self.require_center(organization_id)
        member = next((m for m in center["members"] if m.get("agent_id") == agent_id), None)
        if not member:
            raise NotFoundError(f"Specialist not found: {agent_id}")
        payload = payload or {}
        if action == "pause_agent":
            member["paused"] = True
            member["status"] = "paused"
        elif action == "resume_agent":
            member["paused"] = False
            member["status"] = "active"
        elif action == "assign_task":
            member["current_task"] = payload.get("task") or "Assigned task"
            member["status"] = "busy"
        elif action == "remove_agent":
            center["members"] = [m for m in center["members"] if m.get("agent_id") != agent_id]
        elif action == "replace_agent":
            member["name"] = payload.get("name") or member["name"]
            member["profession"] = payload.get("profession") or member["profession"]
        elif action == "edit_agent":
            for key in ("name", "profession", "specialization", "capabilities"):
                if key in payload:
                    member[key] = payload[key]
        record = {
            "action_id": _id("team_act"),
            "organization_id": organization_id,
            "agent_id": agent_id,
            "action": action,
            "payload": payload,
            "ok": True,
            "created_at": _now(),
        }
        self.store.ai_team_actions.save(record["action_id"], record)
        self.store.ai_team_centers.save(organization_id, center)
        return {**record, "member": member if action != "remove_agent" else None, "dashboard": self.dashboard(organization_id)}

    def group_chat_foundation(self) -> dict[str, Any]:
        return dict(GROUP_AI_CHAT_FOUNDATION)

    def status(self) -> dict[str, Any]:
        return {
            "ready": True,
            "operational": True,
            "centers": len(self.store.ai_team_centers.list_all()),
            "owner_actions": list(TEAM_OWNER_ACTIONS),
            "group_ai_chat_foundation": True,
        }
