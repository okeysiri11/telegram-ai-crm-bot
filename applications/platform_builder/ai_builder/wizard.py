"""Enterprise AI Builder wizard — Sprint 28.2."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.platform_builder.ai_builder.catalogs import (
    NAME_SUGGESTIONS,
    PROFESSIONS,
    WIZARD_STEPS,
    full_catalog,
    specialization_for,
)
from applications.platform_builder.ai_builder.registry import AIBuilderRegistry
from applications.platform_builder.shared.exceptions import NotFoundError, ValidationError
from applications.platform_builder.shared.store import PlatformBuilderStore, platform_builder_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


class AIBuilderWizard:
    """Complete visual wizard for creating AI specialists."""

    def __init__(self, store: PlatformBuilderStore | None = None) -> None:
        self.store = store or platform_builder_store
        self.registry = AIBuilderRegistry(self.store)

    def catalog(self) -> dict[str, Any]:
        return {
            "ready": True,
            "builder_id": "ai",
            "version": "1.1.0",
            "sprint": "28.2",
            "operational": True,
            **full_catalog(),
        }

    def start_session(self, *, agent_count: int | str = 1, custom_count: int | None = None) -> dict[str, Any]:
        count = self._resolve_count(agent_count, custom_count)
        sid = _id("aiwiz")
        agents = [
            {
                "slot": i + 1,
                "name": "",
                "name_gender": "neutral",
                "profession": None,
                "profession_custom": "",
                "specialization": [],
                "knowledge": [],
                "skills": [],
                "permissions": [],
                "personality": {
                    "gender": "neutral",
                    "communication_style": "business_professional",
                    "professional_tone": "balanced",
                    "conversation_style": "ask_clarify",
                },
            }
            for i in range(count)
        ]
        record = {
            "session_id": sid,
            "status": "in_progress",
            "step": 1,
            "agent_count": count,
            "agents": agents,
            "multi_agent": count > 1,
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.store.ai_sessions.save(sid, record)
        return record

    def _resolve_count(self, agent_count: int | str, custom_count: int | None) -> int:
        if agent_count == "custom":
            if not custom_count or custom_count < 1 or custom_count > 50:
                raise ValidationError("custom_count must be between 1 and 50")
            return int(custom_count)
        try:
            value = int(agent_count)
        except (TypeError, ValueError) as exc:
            raise ValidationError("agent_count must be a number or custom") from exc
        if value not in {1, 2, 3, 5, 10, 20}:
            raise ValidationError("agent_count must be 1, 2, 3, 5, 10, 20, or custom")
        return value

    def get_session(self, session_id: str) -> dict[str, Any]:
        session = self.store.ai_sessions.get(session_id)
        if not session:
            raise NotFoundError(f"AI Builder session not found: {session_id}")
        return session

    def update_session(self, session_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        session = self.get_session(session_id)
        if "step" in patch:
            step = int(patch["step"])
            if step < 1 or step > 10:
                raise ValidationError("step must be between 1 and 10")
            session["step"] = step
        if "agents" in patch:
            agents = patch["agents"]
            if not isinstance(agents, list) or len(agents) != session["agent_count"]:
                raise ValidationError("agents must match the session agent_count")
            session["agents"] = agents
        if "active_slot" in patch:
            session["active_slot"] = int(patch["active_slot"])
        session["updated_at"] = _now()
        self.store.ai_sessions.save(session_id, session)
        return session

    def suggest_names(self, gender: str = "neutral") -> dict[str, Any]:
        key = gender if gender in NAME_SUGGESTIONS else "neutral"
        return {"gender": key, "suggestions": list(NAME_SUGGESTIONS[key])}

    def specializations(self, profession_id: str) -> dict[str, Any]:
        profession = next((p for p in PROFESSIONS if p["id"] == profession_id), None)
        return {
            "profession_id": profession_id,
            "profession_name": profession["name"] if profession else profession_id,
            "tree": specialization_for(profession_id),
            "multi_select": True,
        }

    def personality_preview(self, personality: dict[str, Any], name: str = "Alex") -> dict[str, Any]:
        style = (personality or {}).get("communication_style") or "business_professional"
        samples = {
            "business_professional": f"{name}: Good day. I can prepare a clear summary for your team.",
            "expert": f"{name}: Based on the available records, here is the precise recommendation.",
            "friendly": f"{name}: Happy to help! Here’s a simple way to look at it.",
            "best_friend": f"{name}: I’ve got you — let’s figure this out together.",
            "best_girlfriend": f"{name}: I’m right here with you. Tell me what you need.",
            "mentor": f"{name}: Let’s take this one step at a time so it stays clear.",
            "energetic": f"{name}: Great timing! Let’s move this forward.",
            "direct": f"{name}: Next action: confirm the record, then send the update.",
            "without_formalities": f"{name}: Sure — here’s the short version.",
            "very_informal": f"{name}: Yep, easy — try this.",
            "technical": f"{name}: Map the CRM field to workflow step 3, then relaunch.",
            "short": f"{name}: Done. Next?",
            "detailed": f"{name}: Here’s a full walkthrough with each step explained.",
        }
        return {
            "name": name,
            "style": style,
            "preview": [
                {"role": "user", "text": "Can you help me with today’s priorities?"},
                {"role": "assistant", "text": samples.get(style, samples["friendly"])},
            ],
        }

    def summary(self, session_id: str) -> dict[str, Any]:
        session = self.get_session(session_id)
        cards = []
        for agent in session["agents"]:
            cards.append(
                {
                    "slot": agent.get("slot"),
                    "name": agent.get("name") or f"Specialist {agent.get('slot')}",
                    "profession": agent.get("profession"),
                    "profession_custom": agent.get("profession_custom"),
                    "specialization": agent.get("specialization") or [],
                    "knowledge": agent.get("knowledge") or [],
                    "skills": agent.get("skills") or [],
                    "permissions": agent.get("permissions") or [],
                    "personality": agent.get("personality") or {},
                }
            )
        return {
            "session_id": session_id,
            "agent_count": session["agent_count"],
            "multi_agent": session["multi_agent"],
            "cards": cards,
            "title": "AI Team Summary" if session["multi_agent"] else "AI Card",
        }

    def create(self, session_id: str) -> dict[str, Any]:
        session = self.get_session(session_id)
        created = []
        for agent in session["agents"]:
            name = (agent.get("name") or "").strip()
            if not name:
                raise ValidationError(f"Name is required for agent slot {agent.get('slot')}")
            profession = agent.get("profession") or agent.get("profession_custom")
            if not profession:
                raise ValidationError(f"Profession is required for {name}")
            record = self.registry.register(
                {
                    "name": name,
                    "name_gender": agent.get("name_gender") or "neutral",
                    "profession": profession,
                    "specialization": agent.get("specialization") or [],
                    "knowledge": agent.get("knowledge") or [],
                    "skills": agent.get("skills") or [],
                    "permissions": agent.get("permissions") or [],
                    "personality": agent.get("personality") or {},
                    "session_id": session_id,
                    "slot": agent.get("slot"),
                    "configuration_saved": True,
                }
            )
            created.append(record)
        session["status"] = "created"
        session["created_agents"] = [c["agent_id"] for c in created]
        session["updated_at"] = _now()
        self.store.ai_sessions.save(session_id, session)
        group = None
        if len(created) > 1:
            group = self.registry.prepare_group_chat(
                [c["agent_id"] for c in created],
                title=f"Team from session {session_id}",
            )
        return {
            "ok": True,
            "session_id": session_id,
            "created_count": len(created),
            "agents": created,
            "registry": self.registry.list_agents(),
            "group_ai_chat": group,
            "message": "AI agents created, configurations saved, and registered in the AI Registry.",
        }

    def status(self) -> dict[str, Any]:
        return {
            "ready": True,
            "operational": True,
            "wizard_steps": len(WIZARD_STEPS),
            "sessions": len(self.store.ai_sessions.list_all()),
            "registered_agents": len(self.store.ai_registry.list_all()),
            "group_ai_chat": self.registry.group_chat_foundation(),
        }
