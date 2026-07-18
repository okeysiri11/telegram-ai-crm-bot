# Context builder — assemble AI context from platform sources.

from __future__ import annotations

from typing import Any

from platform_ai.models import AIMessage, AIRequest


class ContextBuilder:
    """Assemble context from Configuration, Workflow, Plugin SDK, requests, managers."""

    async def build(self, request: AIRequest) -> dict[str, Any]:
        ctx: dict[str, Any] = dict(request.context)

        ctx.setdefault("configuration", self._from_configuration())
        ctx.setdefault("plugin", self._from_plugin(request.plugin_id))

        if "request_id" in ctx:
            ctx.setdefault("request", await self._from_request(ctx["request_id"]))
        if "manager_id" in ctx:
            ctx.setdefault("manager", await self._from_manager(ctx["manager_id"]))
        if "workflow_id" in ctx:
            ctx.setdefault("workflow", self._from_workflow(ctx["workflow_id"]))

        if "conversation_id" in ctx:
            from platform_ai.conversation_manager import conversation_manager

            history = conversation_manager.get_messages(ctx["conversation_id"])
            ctx["conversation_history"] = [{"role": m.role, "content": m.content} for m in history]

        return ctx

    def build_messages(self, request: AIRequest, context: dict[str, Any]) -> list[AIMessage]:
        messages: list[AIMessage] = []

        system_parts = []
        if context.get("configuration"):
            system_parts.append(f"Platform config available: {len(context['configuration'])} keys")
        if context.get("plugin"):
            system_parts.append(f"Plugin: {context['plugin'].get('plugin_id', 'unknown')}")
        if context.get("request"):
            req = context["request"]
            system_parts.append(f"Request {req.get('request_number', '')}: {req.get('description', '')[:200]}")
        if system_parts:
            messages.append(AIMessage(role="system", content="\n".join(system_parts)))

        for item in context.get("conversation_history", []):
            messages.append(AIMessage(role=item["role"], content=item["content"]))

        if request.messages:
            messages.extend(request.messages)
        elif request.prompt:
            messages.append(AIMessage(role="user", content=request.prompt))

        return messages

    def _from_configuration(self) -> dict[str, Any]:
        try:
            from platform_configuration.config_provider import config_provider

            return {"feature_flags": config_provider.get_section("feature_flags")}
        except Exception:
            return {}

    def _from_plugin(self, plugin_id: str | None) -> dict[str, Any]:
        if not plugin_id:
            return {}
        return {"plugin_id": plugin_id}

    async def _from_request(self, request_id: str) -> dict[str, Any]:
        try:
            from platform_management.statistics import get_request_statistics

            stats = await get_request_statistics()
            return {"request_id": request_id, "stats_available": bool(stats)}
        except Exception:
            return {"request_id": request_id}

    async def _from_manager(self, manager_id: str) -> dict[str, Any]:
        return {"manager_id": manager_id}

    def _from_workflow(self, workflow_id: str) -> dict[str, Any]:
        try:
            from platform_sdk.workflow_loader import sdk_workflow_loader

            sdk_workflow_loader.ensure_loaded()
            return {"workflow_id": workflow_id, "loaded": True}
        except Exception:
            return {"workflow_id": workflow_id}


context_builder = ContextBuilder()
