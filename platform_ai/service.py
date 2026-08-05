"""AI Runtime Service façade — Sprint 36.3."""

from __future__ import annotations

from typing import Any

from platform_ai.ai_service import ai_service
from platform_ai.model_registry import model_registry
from platform_ai.prompt_runtime import prompt_runtime
from platform_ai.provider_manager import provider_manager
from platform_ai.runtime_engine import ai_runtime_engine
from platform_ai.runtime_models import ToolDefinition, ToolPermission
from platform_ai.tool_runtime import tool_runtime


class AIRuntimeService:
    def __init__(self) -> None:
        self.engine = ai_runtime_engine
        self.prompts = prompt_runtime
        self.tools = tool_runtime

    def reset(self) -> None:
        self.engine.reset()
        self.prompts.reset()
        self.tools.reset()
        ai_service.reset()

    def ensure_ready(self) -> None:
        ai_service.initialize()
        self.prompts.ensure_defaults()
        self.tools.ensure_seed()

    def status(self) -> dict[str, Any]:
        self.ensure_ready()
        return {
            "service": "ai_runtime",
            "canonical": "platform_ai",
            "sprint": "36.3",
            "monitoring": self.engine.monitoring(),
            "fallback_chain": provider_manager.fallback_chain,
            "default_provider": provider_manager.default_provider,
            "prompt_cache": self.prompts.cache_stats(),
            "mcp_compatible": True,
            "function_calling": True,
        }

    async def providers(self) -> list[dict[str, Any]]:
        self.ensure_ready()
        return [p.to_dict() for p in await provider_manager.health_all()]

    def models(self, *, provider_id: str | None = None) -> list[dict[str, Any]]:
        self.ensure_ready()
        rows = model_registry.list_by_provider(provider_id) if provider_id else model_registry.list_all()
        return [m.to_dict() for m in rows]

    def preview_route(self, body: dict[str, Any]) -> dict[str, Any]:
        self.ensure_ready()
        return self.engine.preview_route(body)

    async def complete(self, body: dict[str, Any]) -> dict[str, Any]:
        self.ensure_ready()
        if body.get("use_context_engine"):
            try:
                from platform_memory.service import context_engine_service

                ctx = await context_engine_service.for_ai_runtime(
                    {
                        "query": body.get("prompt") or body.get("input") or "",
                        "user_id": body.get("user_id"),
                        "session_id": body.get("context_session_id"),
                        "principal": body.get("user_id") or "system",
                    }
                )
                prefix = ctx.get("prompt_context") or ""
                if prefix:
                    body = {
                        **body,
                        "prompt": f"{prefix}\n\n{body.get('prompt') or body.get('input') or ''}".strip(),
                        "context": {**(body.get("context") or {}), "enterprise_context": ctx},
                    }
            except Exception:
                pass
        if body.get("use_project_memory"):
            try:
                from platform_memory.project_memory_service import project_memory_service

                mem = await project_memory_service.for_ai_runtime(
                    {
                        "query": body.get("prompt") or body.get("input") or "",
                        "project_id": body.get("project_id"),
                        "agent_id": body.get("agent_id") or body.get("user_id"),
                        "write": body.get("memory_write"),
                    }
                )
                prefix = mem.get("prompt_context") or ""
                if prefix:
                    body = {
                        **body,
                        "prompt": f"{prefix}\n\n{body.get('prompt') or body.get('input') or ''}".strip(),
                        "context": {**(body.get("context") or {}), "project_memory": mem},
                    }
            except Exception:
                pass
        return await self.engine.execute(body, session_id=body.get("session_id"))

    def create_session(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        self.ensure_ready()
        body = body or {}
        session = self.engine.create_session(
            user_id=body.get("user_id"),
            tenant_id=body.get("tenant_id"),
            provider_id=body.get("provider_id") or body.get("provider"),
            model_id=body.get("model_id") or body.get("model"),
            tools=body.get("tools"),
            metadata=body.get("metadata"),
        )
        return session.to_dict()

    def list_sessions(self, *, status: str | None = None) -> list[dict[str, Any]]:
        return [s.to_dict() for s in self.engine.list_sessions(status=status)]

    def get_session(self, session_id: str) -> dict[str, Any]:
        return self.engine.get_session(session_id).to_dict()

    def close_session(self, session_id: str) -> dict[str, Any]:
        return self.engine.close_session(session_id).to_dict()

    def list_prompts(self) -> list[dict[str, Any]]:
        return self.prompts.list_templates()

    def get_prompt(self, template_id: str, version: int | None = None) -> dict[str, Any]:
        return self.prompts.get_template(template_id, version)

    def create_prompt(self, body: dict[str, Any]) -> dict[str, Any]:
        return self.prompts.create_template(
            template_id=body.get("template_id"),
            name=str(body.get("name") or "Untitled"),
            body=str(body.get("body") or body.get("user_prompt") or ""),
            system_prompt=str(body.get("system_prompt") or ""),
            description=str(body.get("description") or ""),
            parent_id=body.get("parent_id"),
        )

    def version_prompt(self, template_id: str, body: dict[str, Any]) -> dict[str, Any]:
        return self.prompts.create_version(
            template_id,
            str(body.get("body") or body.get("user_prompt") or ""),
            system_prompt=str(body.get("system_prompt") or ""),
            changelog=str(body.get("changelog") or ""),
        )

    def prompt_versions(self, template_id: str) -> list[dict[str, Any]]:
        return self.prompts.versions(template_id)

    def validate_prompt(self, template_id: str, body: dict[str, Any]) -> dict[str, Any]:
        return self.prompts.validate(template_id, dict(body.get("variables") or {}), version=body.get("version"))

    def render_prompt(self, template_id: str, body: dict[str, Any]) -> dict[str, Any]:
        return self.prompts.render(
            template_id,
            dict(body.get("variables") or {}),
            version=body.get("version"),
            use_cache=bool(body.get("use_cache", True)),
            system_prompt_key=body.get("system_prompt_key"),
        )

    def system_prompts(self) -> dict[str, str]:
        return self.prompts.list_system_prompts()

    def list_tools(self) -> list[dict[str, Any]]:
        self.tools.ensure_seed()
        return [t.to_dict() for t in self.tools.list_tools()]

    def register_tool(self, body: dict[str, Any]) -> dict[str, Any]:
        tool = ToolDefinition(
            tool_id=str(body.get("tool_id") or body.get("name") or "tool_custom"),
            name=str(body.get("name") or "custom"),
            description=str(body.get("description") or ""),
            parameters=dict(body.get("parameters") or {}),
            permission=ToolPermission(body.get("permission") or "allow"),
            mcp_compatible=bool(body.get("mcp_compatible", True)),
            timeout_sec=float(body.get("timeout_sec") or 30),
            sandbox=bool(body.get("sandbox", True)),
            enabled=bool(body.get("enabled", True)),
            metadata=dict(body.get("metadata") or {}),
        )
        handler = body.get("_handler")
        self.tools.register(tool, handler=handler if callable(handler) else (lambda args: {"ok": True, "args": args}))
        return tool.to_dict()

    def function_schemas(self) -> list[dict[str, Any]]:
        return self.tools.function_schemas()

    async def execute_tool(self, tool_id: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        body = body or {}
        rec = await self.tools.execute(
            tool_id,
            dict(body.get("arguments") or body.get("args") or {}),
            session_id=body.get("session_id"),
        )
        return rec.to_dict()

    def tool_executions(self, *, limit: int = 100) -> list[dict[str, Any]]:
        return [e.to_dict() for e in self.tools.executions(limit=limit)]

    def logs(self, *, limit: int = 100) -> list[dict[str, Any]]:
        return [e.to_dict() for e in self.engine.logs[-limit:]]

    def monitoring(self) -> dict[str, Any]:
        self.ensure_ready()
        return self.engine.monitoring()


ai_runtime_service = AIRuntimeService()
