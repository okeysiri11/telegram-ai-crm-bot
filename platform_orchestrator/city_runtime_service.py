"""Enterprise City Runtime service façade — Sprint 37.0."""

from __future__ import annotations

from typing import Any

from platform_orchestrator.city_runtime_engine import (
    EnterpriseCityRuntimeEngine,
    enterprise_city_runtime_engine,
)
from platform_orchestrator.city_runtime_models import WorkspaceModule


class EnterpriseCityRuntimeService:
    def __init__(self, engine: EnterpriseCityRuntimeEngine | None = None) -> None:
        self.engine = engine or enterprise_city_runtime_engine

    def reset(self) -> None:
        self.engine.reset()

    def ensure_ready(self) -> None:
        self.engine.ensure_seed()

    def status(self) -> dict[str, Any]:
        self.ensure_ready()
        return {
            "service": "enterprise_city_runtime",
            "canonical": "platform_orchestrator",
            "sprint": "37.0",
            "workspace_modules": [m.value for m in WorkspaceModule],
            "statistics": self.engine.statistics(),
            "integrations": [
                "ai_runtime",
                "multi_agent_runtime",
                "project_memory",
                "context_engine",
                "workflow_runtime",
                "creative_factory",
                "voice_runtime",
                "skills_sdk",
                "event_bus",
                "service_builder",
                "crm",
                "erp",
                "analytics",
                "knowledge_base",
            ],
            "ui": "/platform",
            "spatial_adapter": "/enterprise-city",
        }

    def list_services(self, **kwargs: Any) -> list[dict[str, Any]]:
        return [s.to_dict() for s in self.engine.list_services(**kwargs)]

    def get_service(self, service_id: str) -> dict[str, Any]:
        return self.engine.get_service(service_id).to_dict()

    def register_service(self, body: dict[str, Any]) -> dict[str, Any]:
        return self.engine.register_service(body).to_dict()

    def navigation(self) -> list[dict[str, Any]]:
        return self.engine.navigation()

    def workspace(self) -> list[dict[str, Any]]:
        return self.engine.workspace_modules()

    def command_palette(self, query: str = "") -> list[dict[str, Any]]:
        return self.engine.command_palette(query)

    def route_to(self, target: str, *, session_id: str | None = None) -> dict[str, Any]:
        return self.engine.route_to(target, session_id=session_id)

    def create_session(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.engine.create_session(body).to_dict()

    def list_sessions(self) -> list[dict[str, Any]]:
        return [s.to_dict() for s in self.engine.list_sessions()]

    def get_session(self, session_id: str) -> dict[str, Any]:
        return self.engine.get_session(session_id).to_dict()

    def update_shared(self, session_id: str, body: dict[str, Any]) -> dict[str, Any]:
        return self.engine.update_shared(session_id, body).to_dict()

    def publish_event(self, event: dict[str, Any]) -> dict[str, Any]:
        return self.engine.publish_event(event)

    def list_events(self, *, limit: int = 100) -> list[dict[str, Any]]:
        return self.engine.list_events(limit=limit)

    def notify(self, body: dict[str, Any]) -> dict[str, Any]:
        return self.engine.notify(
            str(body.get("title") or "Notification"),
            str(body.get("body") or ""),
            level=str(body.get("level") or "info"),
            module=str(body.get("module") or "platform"),
        ).to_dict()

    def list_notifications(self, *, unread_only: bool = False) -> list[dict[str, Any]]:
        return [n.to_dict() for n in self.engine.list_notifications(unread_only=unread_only)]

    def mark_read(self, notification_id: str) -> dict[str, Any]:
        return self.engine.mark_read(notification_id).to_dict()

    def search(self, query: str, *, kind: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        return [h.to_dict() for h in self.engine.search(query, kind=kind, limit=limit)]

    def dashboard(self) -> dict[str, Any]:
        return self.engine.dashboard()

    def list_health(self) -> list[dict[str, Any]]:
        return [h.to_dict() for h in self.engine.list_health()]

    def set_health(self, component_id: str, body: dict[str, Any]) -> dict[str, Any]:
        return self.engine.set_health(
            component_id,
            str(body.get("level") or "healthy"),
            message=str(body.get("message") or ""),
        ).to_dict()

    def list_metrics(self) -> list[dict[str, Any]]:
        return [m.to_dict() for m in self.engine.list_metrics()]

    def upsert_metric(self, body: dict[str, Any]) -> dict[str, Any]:
        return self.engine.upsert_metric(body).to_dict()

    def list_config(self) -> list[dict[str, Any]]:
        return [c.to_dict() for c in self.engine.list_config()]

    def set_config(self, body: dict[str, Any]) -> dict[str, Any]:
        return self.engine.set_config(
            str(body.get("key") or ""),
            body.get("value"),
            category=str(body.get("category") or "general"),
            description=str(body.get("description") or ""),
        ).to_dict()

    def list_usage(self, *, limit: int = 100) -> list[dict[str, Any]]:
        return [u.to_dict() for u in self.engine.list_usage(limit=limit)]

    def list_activity(self, *, limit: int = 100) -> list[dict[str, Any]]:
        return [a.to_dict() for a in self.engine.list_activity(limit=limit)]

    async def execute_command(self, body: dict[str, Any]) -> dict[str, Any]:
        return (await self.engine.execute_command(body)).to_dict()

    def list_commands(self, *, limit: int = 50) -> list[dict[str, Any]]:
        return [c.to_dict() for c in self.engine.list_commands(limit=limit)]

    def production_readiness(self) -> dict[str, Any]:
        return self.engine.production_readiness()

    def statistics(self) -> dict[str, Any]:
        return self.engine.statistics()

    async def probe_integrations(self) -> dict[str, Any]:
        return await self.engine.probe_integrations()

    # Integration façades — soft-call each module
    async def for_ai_runtime(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        body = body or {}
        self.route_to("ai_runtime")
        return {"consumer": "ai_runtime", "routed": True, "query": body.get("query")}

    async def for_multi_agent(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        body = body or {}
        try:
            from platform_orchestrator.multi_agent_service import multi_agent_runtime_service

            st = multi_agent_runtime_service.status()
        except Exception as exc:  # noqa: BLE001
            st = {"error": str(exc)}
        return {"consumer": "multi_agent_runtime", "status": st}

    async def for_project_memory(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        body = body or {}
        try:
            from platform_memory.project_memory_service import project_memory_service

            await project_memory_service.remember(
                {
                    "kind": "agent",
                    "layer": "working",
                    "title": "City Runtime note",
                    "content": str(body.get("content") or "Enterprise City session"),
                    "agent_id": "enterprise_city_runtime",
                    "project_id": body.get("project_id") or "proj_ados",
                }
            )
            ok = True
        except Exception:
            ok = False
        return {"consumer": "project_memory", "ok": ok}

    async def for_context_engine(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        body = body or {}
        ctx = None
        try:
            from platform_memory.service import context_engine_service

            ctx = await context_engine_service.for_ai_runtime(
                {"query": body.get("query") or "platform status", "use_project_memory": False}
            )
        except Exception as exc:  # noqa: BLE001
            ctx = {"error": str(exc)}
        return {"consumer": "context_engine", "context": ctx}

    async def for_creative(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        body = body or {}
        try:
            from platform_ai.creative_service import creative_factory_service

            st = creative_factory_service.status()
        except Exception as exc:  # noqa: BLE001
            st = {"error": str(exc)}
        return {"consumer": "creative_factory", "status": st}

    async def for_voice(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        body = body or {}
        parsed = None
        try:
            from platform_ai.voice_service import voice_runtime_service

            parsed = voice_runtime_service.parse(
                str(body.get("transcript") or "open platform dashboard")
            )
        except Exception as exc:  # noqa: BLE001
            parsed = {"error": str(exc)}
        cmd = await self.execute_command(
            {"text": str(body.get("transcript") or "open platform dashboard"), "kind": "voice"}
        )
        return {"consumer": "voice_runtime", "voice": parsed, "command": cmd}

    async def for_skills(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        body = body or {}
        try:
            from platform_ai.skills_sdk_service import skills_sdk_service

            st = skills_sdk_service.status()
        except Exception as exc:  # noqa: BLE001
            st = {"error": str(exc)}
        return {"consumer": "skills_sdk", "status": st}

    async def for_workflow(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        body = body or {}
        cmd = await self.execute_command(
            {"text": str(body.get("text") or "run workflow campaign launch"), "kind": "workflow_execution"}
        )
        return {"consumer": "workflow_runtime", "command": cmd}

    async def for_event_bus(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        body = body or {}
        event = self.publish_event({"type": body.get("type") or "platform.city.ping", **body})
        return {"consumer": "event_bus", "event": event}


enterprise_city_runtime_service = EnterpriseCityRuntimeService()
