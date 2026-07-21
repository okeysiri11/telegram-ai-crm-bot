# Ecosystem bridge — consumes AI Ecosystem v1.5 without modifying ecosystem packages.

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class EcosystemBridge:
    """Reuse Identity, Assistant, Communication, Governance, Workforce, Knowledge Graph."""

    @staticmethod
    def validate_identity(access_token: str) -> Any | None:
        try:
            from ecosystem import ecosystem

            return ecosystem.engine.identity.validate_session(access_token)
        except Exception:
            logger.debug("ecosystem identity unavailable")
            return None

    @staticmethod
    async def ask_assistant(message: str, *, user_id: str = "", context: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            from ecosystem import ecosystem

            result = await ecosystem.engine.assistant.invoke(
                user_id or "agro-anonymous",
                message,
                application_id="agro_marketplace",
                context=context or {"application": "agro_marketplace"},
            )
            return result if isinstance(result, dict) else {"reply": str(result)}
        except Exception:
            logger.debug("unified assistant unavailable")
            return {"reply": "Assistant unavailable", "fallback": True}

    @staticmethod
    async def publish_ecosystem_event(event_type: str, payload: dict[str, Any]) -> None:
        try:
            from ecosystem import ecosystem

            bus = ecosystem.engine.communication.bus
            await bus.publish_application(event_type, payload, source="agro_marketplace")
        except Exception:
            logger.debug("ecosystem event bus unavailable")

    @staticmethod
    def check_governance(action: str, context: dict[str, Any] | None = None) -> bool:
        try:
            from ecosystem import ecosystem

            governance = getattr(ecosystem.engine, "governance", None)
            if governance is None:
                return True
            policies = getattr(governance, "policies", None)
            if policies is not None and hasattr(policies, "evaluate"):
                result = policies.evaluate(action, context or {})
                return bool(result) if not isinstance(result, dict) else result.get("allowed", True)
            return True
        except Exception:
            return True

    @staticmethod
    def knowledge_lookup(query: str) -> list[dict[str, Any]]:
        try:
            from ecosystem.assistant.knowledge_graph import knowledge_graph

            if hasattr(knowledge_graph, "search"):
                nodes = knowledge_graph.search(query)
            elif hasattr(knowledge_graph, "query"):
                nodes = knowledge_graph.query(query)
            else:
                nodes = []
            return [n.to_dict() if hasattr(n, "to_dict") else dict(n) for n in (nodes or [])]
        except Exception:
            return []

    @staticmethod
    async def invoke_workforce(task: str, *, context: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            from ecosystem import ecosystem

            workforce = getattr(ecosystem.engine, "workforce", None)
            if workforce is None:
                return {"status": "unavailable"}
            if hasattr(workforce, "execute"):
                result = await workforce.execute(task, context=context or {})
                return result if isinstance(result, dict) else {"result": str(result)}
            if hasattr(workforce, "dispatch"):
                result = await workforce.dispatch(task, context=context or {})
                return result if isinstance(result, dict) else {"result": str(result)}
            return {"status": "ok", "task": task, "layer": "workforce"}
        except Exception:
            logger.debug("AI workforce unavailable")
            return {"status": "fallback", "task": task}

    @staticmethod
    async def executive_brief(topic: str, *, metrics: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            from ecosystem import ecosystem

            workforce = getattr(ecosystem.engine, "workforce", None)
            executive = getattr(workforce, "executive", None) if workforce else None
            if executive is None:
                from ecosystem.workforce.executive import executive_service

                executive = executive_service
            if hasattr(executive, "brief"):
                result = await executive.brief(topic, metrics=metrics or {})
                return result if isinstance(result, dict) else {"brief": str(result)}
            if hasattr(executive, "report"):
                result = await executive.report(topic, metrics=metrics or {})
                return result if isinstance(result, dict) else {"brief": str(result)}
            return {"topic": topic, "metrics": metrics or {}, "status": "ok"}
        except Exception:
            logger.debug("executive AI unavailable")
            return {"topic": topic, "metrics": metrics or {}, "fallback": True}

    @staticmethod
    def ecosystem_health() -> dict[str, Any]:
        try:
            from ecosystem import ecosystem

            return {
                "ecosystem_dependency": "AI Ecosystem v1.5",
                "health": ecosystem.health(),
            }
        except Exception:
            return {"ecosystem_dependency": "AI Ecosystem v1.5", "available": False}


ecosystem_bridge = EcosystemBridge()
