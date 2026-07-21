# Application bridge — connect apps, share AI context, collaborate agents.

from __future__ import annotations

import logging
from typing import Any

from events.publisher import publish

from ecosystem.communication.events import AgentDelegatedEvent, ContextSharedEvent
from ecosystem.communication.models import SharedContext
from ecosystem.communication.service_registry.registry import ServiceRegistry, service_registry
from ecosystem.shared.store import EcosystemStore, ecosystem_store

logger = logging.getLogger(__name__)


class ApplicationBridge:
    """Bridge for application connectivity, context sharing, and AI collaboration."""

    def __init__(
        self,
        store: EcosystemStore | None = None,
        registry: ServiceRegistry | None = None,
    ) -> None:
        self._store = store or ecosystem_store
        self._registry = registry or service_registry

    async def connect_application(
        self,
        application_id: str,
        *,
        version: str = "1.0.0",
        capabilities: list[str] | None = None,
        endpoints: dict[str, str] | None = None,
        dependencies: list[str] | None = None,
    ) -> dict[str, Any]:
        reg = await self._registry.register(
            application_id,
            version=version,
            capabilities=capabilities or [],
            endpoints=endpoints or {},
            dependencies=dependencies or [],
        )
        connected = await self._registry.connect(application_id)
        return {"registration": reg.to_dict(), "connected": connected.is_connected}

    async def share_context(
        self,
        user_id: str,
        application_id: str,
        data: dict[str, Any],
        *,
        shared_with: list[str] | None = None,
    ) -> SharedContext:
        targets = shared_with or [
            r.application_id
            for r in self._registry.list_applications()
            if r.is_connected and r.application_id != application_id
        ]
        context = SharedContext(
            user_id=user_id,
            application_id=application_id,
            data=data,
            shared_with=targets,
        )
        self._store.shared_contexts.save(context.context_id, context)
        try:
            from ecosystem.integrations.platform_bridge import platform_bridge

            await platform_bridge.store_memory(
                user_id,
                str(data),
                application_id=application_id,
            )
        except Exception:
            logger.debug("context memory bridge unavailable")
        await publish(
            ContextSharedEvent(
                context_id=context.context_id,
                user_id=user_id,
                source_application=application_id,
                shared_with=targets,
            )
        )
        return context

    def get_shared_context(self, context_id: str) -> SharedContext | None:
        return self._store.shared_contexts.get(context_id)

    def list_contexts(self, user_id: str) -> list[SharedContext]:
        return [c for c in self._store.shared_contexts.list_all() if c.user_id == user_id]

    async def route_ai_event(
        self,
        event_name: str,
        payload: dict[str, Any],
        *,
        source_application: str,
    ) -> dict[str, Any]:
        from ecosystem.communication.event_bus.bus import event_bus

        event = await event_bus.publish_ai(event_name, payload, source=source_application)
        return event.to_dict()

    async def collaborate_agents(
        self,
        source_application: str,
        task_type: str,
        payload: dict[str, Any],
        *,
        target_agent: str = "",
        partner_application: str = "",
    ) -> dict[str, Any]:
        result = await self.delegate_task(
            source_application,
            task_type,
            payload,
            target_agent=target_agent,
        )
        if partner_application:
            from ecosystem.communication.message_router.router import message_router

            await message_router.direct(
                source_application,
                partner_application,
                {"task_type": task_type, "collaboration": True, "result": result},
            )
        return result

    async def delegate_task(
        self,
        source_application: str,
        task_type: str,
        payload: dict[str, Any],
        *,
        target_agent: str = "",
    ) -> dict[str, Any]:
        try:
            from ecosystem.integrations.platform_bridge import platform_bridge

            result = await platform_bridge.delegate_task(task_type, payload, agent_id=target_agent)
        except Exception:
            result = {"status": "fallback", "task_type": task_type, "payload": payload}
        await publish(
            AgentDelegatedEvent(
                task_type=task_type,
                source_application=source_application,
                target_agent=target_agent,
                payload=payload,
            )
        )
        return {"delegated": True, "source_application": source_application, "result": result}

    async def exchange_knowledge(
        self,
        source_application: str,
        target_application: str,
        knowledge: dict[str, Any],
    ) -> dict[str, Any]:
        from ecosystem.communication.message_router.router import message_router

        envelope = await message_router.direct(
            source_application,
            target_application,
            {"type": "knowledge_exchange", "knowledge": knowledge},
        )
        return {"exchanged": True, "message_id": envelope.message_id, "knowledge": knowledge}


application_bridge = ApplicationBridge()
