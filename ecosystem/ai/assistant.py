# Unified AI Assistant — cross-application intelligence.

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from events.publisher import publish

from ecosystem.events import AssistantInvokedEvent
from ecosystem.shared.store import EcosystemStore, ecosystem_store


def _id() -> str:
    return str(uuid.uuid4())


def _ts() -> float:
    return time.time()


@dataclass
class AssistantSession:
    session_id: str = field(default_factory=_id)
    user_id: str = ""
    application_id: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    turns: list[dict[str, str]] = field(default_factory=list)
    created_at: float = field(default_factory=_ts)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "application_id": self.application_id,
            "context": dict(self.context),
            "turns": list(self.turns),
            "created_at": self.created_at,
        }


class UnifiedAssistant:
    def __init__(self, store: EcosystemStore | None = None) -> None:
        self._store = store or ecosystem_store

    async def invoke(
        self,
        user_id: str,
        message: str,
        *,
        application_id: str = "",
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        session = AssistantSession(user_id=user_id, application_id=application_id, context=context or {})
        session.turns.append({"role": "user", "content": message})
        response = await self._route_and_respond(user_id, message, application_id=application_id, context=context)
        session.turns.append({"role": "assistant", "content": response.get("reply", "")})
        self._store.assistant_sessions.save(session.session_id, session)
        await publish(AssistantInvokedEvent(user_id=user_id, session_id=session.session_id, application_id=application_id, intent=response.get("intent", "")))
        return {"session_id": session.session_id, **response}

    async def delegate_task(
        self,
        user_id: str,
        task_type: str,
        payload: dict[str, Any],
        *,
        target_agent: str = "",
    ) -> dict[str, Any]:
        try:
            from ecosystem.integrations.platform_bridge import platform_bridge

            result = await platform_bridge.delegate_task(task_type, payload, agent_id=target_agent)
            return {"delegated": True, "task_type": task_type, "result": result}
        except Exception:
            return {"delegated": False, "task_type": task_type, "status": "fallback", "payload": payload}

    def share_context(self, session_id: str, context: dict[str, Any]) -> AssistantSession:
        session = self._store.assistant_sessions.get(session_id)
        if session is None:
            session = AssistantSession(session_id=session_id, context=context)
        else:
            session.context.update(context)
        self._store.assistant_sessions.save(session.session_id, session)
        return session

    async def _route_and_respond(
        self,
        user_id: str,
        message: str,
        *,
        application_id: str = "",
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        try:
            from ecosystem.integrations.platform_bridge import platform_bridge

            result = await platform_bridge.route_assistant(user_id, message, application_id=application_id, context=context or {})
            if result:
                return result
        except Exception:
            pass
        intent = "general"
        if application_id == "auto_marketplace":
            intent = "auto_marketplace"
        return {
            "reply": f"Ecosystem assistant ready. Received: {message}",
            "intent": intent,
            "application_id": application_id or "ecosystem",
            "routed": bool(application_id),
        }


unified_assistant = UnifiedAssistant()
