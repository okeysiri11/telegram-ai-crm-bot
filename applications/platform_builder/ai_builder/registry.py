"""AI Registry + Group AI Chat foundation for Platform Builder."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.platform_builder.shared.store import PlatformBuilderStore, platform_builder_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


class AIBuilderRegistry:
    """Registers AI specialists created by the AI Builder wizard."""

    def __init__(self, store: PlatformBuilderStore | None = None) -> None:
        self.store = store or platform_builder_store

    def register(self, agent: dict[str, Any]) -> dict[str, Any]:
        aid = agent.get("agent_id") or _id("ai_agent")
        record = {
            **agent,
            "agent_id": aid,
            "registry": "platform_builder_ai_registry",
            "lifecycle": "registered",
            "registered_at": _now(),
            "source": "ai_builder",
            "sprint": "28.2",
        }
        self.store.ai_registry.save(aid, record)
        # Try enterprise hub registry when available (best-effort).
        try:
            from applications.enterprise_hub.ai_agents.registry import AgentRegistry as HubRegistry

            hub = HubRegistry()
            hub.register_agent(
                name=record["name"],
                agent_type="general",
                capabilities=list(record.get("skills") or []),
                permissions=list(record.get("permissions") or []),
                profile={
                    "profession": record.get("profession"),
                    "specialization": record.get("specialization"),
                    "knowledge": record.get("knowledge"),
                    "personality": record.get("personality"),
                    "builder_agent_id": aid,
                },
            )
            record["hub_registry"] = "synced"
        except Exception:
            record["hub_registry"] = "local_only"
        return record

    def list_agents(self) -> dict[str, Any]:
        items = self.store.ai_registry.list_all()
        return {"count": len(items), "items": items, "registry": "platform_builder_ai_registry"}

    def get(self, agent_id: str) -> dict[str, Any] | None:
        return self.store.ai_registry.get(agent_id)

    def group_chat_foundation(self) -> dict[str, Any]:
        return {
            "ready": True,
            "status": "foundation",
            "description": (
                "Architecture reserved for inviting multiple AI specialists into one conversation."
            ),
            "model": {
                "conversation_id": "string",
                "title": "string",
                "participant_agent_ids": ["agent_id"],
                "human_participants": ["user_id"],
                "moderator": "orchestrator | human",
                "turn_policy": "round_robin | capability_routing | user_directed",
                "shared_memory_scope": "conversation",
            },
            "apis_planned": [
                "POST /group-chat/sessions",
                "POST /group-chat/sessions/{id}/invite",
                "POST /group-chat/sessions/{id}/message",
            ],
            "note": "No live multi-agent chat runtime in this sprint — architecture only.",
        }

    def prepare_group_chat(self, agent_ids: list[str], title: str | None = None) -> dict[str, Any]:
        sid = _id("gchat")
        record = {
            "session_id": sid,
            "title": title or "Group AI Chat (foundation)",
            "participant_agent_ids": list(agent_ids),
            "status": "architecture_only",
            "created_at": _now(),
        }
        self.store.group_chat_sessions.save(sid, record)
        return {"ok": True, "foundation": True, **record}
