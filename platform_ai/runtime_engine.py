"""AI Runtime Engine — request lifecycle, context, sandbox, inference pipeline.

Wraps platform_ai.AIService (canonical entry) + ToolRuntime. Sprint 36.3.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from platform_ai.ai_service import ai_service
from platform_ai.models import AIMessage, AIRequest, TaskType
from platform_ai.prompt_service import prompt_service
from platform_ai.provider_manager import provider_manager
from platform_ai.provider_router import provider_router
from platform_ai.runtime_models import (
    AIRuntimeLog,
    AIRuntimeSession,
    RuntimeContext,
    SessionStatus,
    new_id,
)
from platform_ai.tool_runtime import tool_runtime

logger = logging.getLogger(__name__)


class RuntimeSandbox:
    def __init__(self) -> None:
        self._boxes: dict[str, dict[str, Any]] = {}

    def reset(self) -> None:
        self._boxes.clear()

    def create(self, session_id: str) -> str:
        sid = new_id("rsbx")
        self._boxes[sid] = {"session_id": session_id, "started_at": time.time(), "allowed": True}
        return sid

    def destroy(self, sandbox_id: str) -> None:
        self._boxes.pop(sandbox_id, None)

    def get(self, sandbox_id: str) -> dict[str, Any] | None:
        return self._boxes.get(sandbox_id)


class ContextManager:
    def __init__(self) -> None:
        self._contexts: dict[str, RuntimeContext] = {}

    def reset(self) -> None:
        self._contexts.clear()

    def get_or_create(self, session_id: str, **kwargs: Any) -> RuntimeContext:
        ctx = self._contexts.get(session_id)
        if ctx is None:
            ctx = RuntimeContext(session_id=session_id, **kwargs)
            self._contexts[session_id] = ctx
        return ctx

    def append_message(self, session_id: str, role: str, content: str) -> RuntimeContext:
        ctx = self.get_or_create(session_id)
        ctx.messages.append({"role": role, "content": content, "ts": time.time()})
        return ctx

    def set_memory(self, session_id: str, key: str, value: Any) -> RuntimeContext:
        ctx = self.get_or_create(session_id)
        ctx.memory[key] = value
        return ctx


class AIRuntimeEngine:
    """Unified execution engine for agents, LLM, prompts, tools, memory."""

    def __init__(self) -> None:
        self.sessions: dict[str, AIRuntimeSession] = {}
        self.logs: list[AIRuntimeLog] = []
        self.context_manager = ContextManager()
        self.sandbox = RuntimeSandbox()
        self._request_count = 0

    def reset(self) -> None:
        self.sessions.clear()
        self.logs.clear()
        self.context_manager.reset()
        self.sandbox.reset()
        self._request_count = 0
        tool_runtime.reset()

    def _log(
        self,
        level: str,
        message: str,
        *,
        session_id: str | None = None,
        provider_id: str | None = None,
        model_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> AIRuntimeLog:
        entry = AIRuntimeLog(
            log_id=new_id("ailog"),
            level=level,
            message=message,
            session_id=session_id,
            provider_id=provider_id,
            model_id=model_id,
            details=details or {},
        )
        self.logs.append(entry)
        self.logs = self.logs[-5000:]
        return entry

    def create_session(
        self,
        *,
        user_id: str | None = None,
        tenant_id: str | None = None,
        provider_id: str | None = None,
        model_id: str | None = None,
        tools: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AIRuntimeSession:
        session_id = new_id("airs")
        sandbox_id = self.sandbox.create(session_id)
        ctx = self.context_manager.get_or_create(
            session_id,
            user_id=user_id,
            tenant_id=tenant_id,
            tools_enabled=list(tools or []),
            metadata=dict(metadata or {}),
            sandbox_id=sandbox_id,
        )
        session = AIRuntimeSession(
            session_id=session_id,
            provider_id=provider_id,
            model_id=model_id,
            context=ctx,
        )
        self.sessions[session_id] = session
        self._log("info", "session_created", session_id=session_id, details={"sandbox_id": sandbox_id})
        return session

    def get_session(self, session_id: str) -> AIRuntimeSession:
        session = self.sessions.get(session_id)
        if session is None:
            raise KeyError(f"session not found: {session_id}")
        return session

    def list_sessions(self, *, status: str | None = None) -> list[AIRuntimeSession]:
        rows = list(self.sessions.values())
        if status:
            rows = [s for s in rows if (s.status.value if isinstance(s.status, SessionStatus) else s.status) == status]
        return sorted(rows, key=lambda s: s.created_at, reverse=True)

    def close_session(self, session_id: str, *, status: SessionStatus = SessionStatus.COMPLETED) -> AIRuntimeSession:
        session = self.get_session(session_id)
        if session.context and session.context.sandbox_id:
            self.sandbox.destroy(session.context.sandbox_id)
        session.status = status
        session.finished_at = time.time()
        session.updated_at = time.time()
        self._log("info", "session_closed", session_id=session_id, details={"status": status.value})
        return session

    def preview_route(self, body: dict[str, Any]) -> dict[str, Any]:
        ai_service.initialize()
        request = self._build_request(body)
        decision = provider_router.route(request)
        return {
            "provider_id": decision.provider_id,
            "model_id": decision.model_id,
            "reason": decision.reason,
            "fallback_chain": provider_manager.fallback_chain,
        }

    def _build_request(self, body: dict[str, Any], *, session: AIRuntimeSession | None = None) -> AIRequest:
        task = body.get("task_type", TaskType.CHAT.value)
        try:
            task_type = TaskType(task)
        except ValueError:
            task_type = TaskType.CHAT

        messages: list[AIMessage] = []
        for m in body.get("messages") or []:
            messages.append(AIMessage(role=str(m.get("role", "user")), content=str(m.get("content", ""))))
        if session and session.context:
            for m in session.context.messages[-20:]:
                if not any(x.content == m.get("content") and x.role == m.get("role") for x in messages):
                    messages.insert(0, AIMessage(role=str(m.get("role", "user")), content=str(m.get("content", ""))))

        return AIRequest(
            prompt=str(body.get("prompt") or body.get("input") or ""),
            messages=messages,
            task_type=task_type,
            model=body.get("model") or body.get("model_id") or (session.model_id if session else None),
            provider=body.get("provider") or body.get("provider_id") or (session.provider_id if session else None),
            template_id=body.get("template_id"),
            template_vars=dict(body.get("template_vars") or body.get("variables") or {}),
            context=dict(body.get("context") or {}),
            max_tokens=int(body.get("max_tokens") or 1024),
            temperature=float(body.get("temperature") or 0.7),
            use_cache=bool(body.get("use_cache", True)),
            plugin_id=body.get("plugin_id"),
        )

    async def execute(
        self,
        body: dict[str, Any],
        *,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Full inference pipeline: context → prompt → route → complete → tools → audit."""
        ai_service.initialize()
        self._request_count += 1
        started = time.monotonic()

        session: AIRuntimeSession | None = None
        if session_id:
            session = self.get_session(session_id)
        elif body.get("create_session"):
            session = self.create_session(
                user_id=body.get("user_id"),
                tenant_id=body.get("tenant_id"),
                provider_id=body.get("provider") or body.get("provider_id"),
                model_id=body.get("model") or body.get("model_id"),
                tools=body.get("tools"),
                metadata=body.get("metadata"),
            )
            session_id = session.session_id

        request = self._build_request(body, session=session)
        self._log(
            "info",
            "request_started",
            session_id=session_id,
            provider_id=request.provider,
            model_id=request.model,
        )

        if session and request.prompt:
            self.context_manager.append_message(session.session_id, "user", request.prompt)

        response = await ai_service.complete(request)

        tool_calls: list[dict[str, Any]] = []
        if body.get("tools") or body.get("function_calling") or (session and session.context and session.context.tools_enabled):
            tool_calls = await self._maybe_run_tools(body, session_id=session_id)

        if session:
            session.request_count += 1
            session.provider_id = response.provider_id
            session.model_id = response.model_id
            session.updated_at = time.time()
            self.context_manager.append_message(session.session_id, "assistant", response.content)

        result = {
            **response.to_dict(),
            "session_id": session_id,
            "tool_calls": tool_calls,
            "pipeline_ms": (time.monotonic() - started) * 1000,
            "routing": {
                "provider_id": response.provider_id,
                "model_id": response.model_id,
                "fallback_used": response.fallback_used,
            },
        }
        self._log(
            "info",
            "request_completed",
            session_id=session_id,
            provider_id=response.provider_id,
            model_id=response.model_id,
            details={"latency_ms": response.latency_ms, "cached": response.cached},
        )
        return result

    async def _maybe_run_tools(
        self,
        body: dict[str, Any],
        *,
        session_id: str | None,
    ) -> list[dict[str, Any]]:
        requested = list(body.get("tool_calls") or [])
        if not requested and body.get("auto_tools"):
            # Demo: invoke first enabled tool with empty args when auto_tools
            tools = tool_runtime.list_tools(enabled_only=True)
            if tools:
                requested = [{"tool_id": tools[0].tool_id, "arguments": {}}]
        results: list[dict[str, Any]] = []
        for call in requested:
            tool_id = str(call.get("tool_id") or call.get("name") or "")
            if not tool_id:
                continue
            rec = await tool_runtime.execute(
                tool_id,
                dict(call.get("arguments") or call.get("args") or {}),
                session_id=session_id,
            )
            results.append(rec.to_dict())
            self._log(
                "info" if rec.success else "error",
                "tool_executed",
                session_id=session_id,
                details={"tool_id": tool_id, "success": rec.success},
            )
        return results

    def monitoring(self) -> dict[str, Any]:
        ai_service.initialize()
        active = sum(1 for s in self.sessions.values() if s.status == SessionStatus.ACTIVE)
        return {
            "sessions_total": len(self.sessions),
            "sessions_active": active,
            "requests": self._request_count,
            "logs": len(self.logs),
            "tools": len(tool_runtime.list_tools()),
            "tool_executions": len(tool_runtime.executions()),
            "providers": len(provider_manager.fallback_chain),
            "prompts": len(prompt_service.list_templates()),
            "sandboxes": len(self.sandbox._boxes),
        }


ai_runtime_engine = AIRuntimeEngine()
