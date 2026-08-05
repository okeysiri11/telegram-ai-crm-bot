"""Tool Execution Runtime — registry, sandbox, function calling, MCP-compatible schemas."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Callable, Awaitable

from platform_ai.runtime_models import (
    ToolDefinition,
    ToolExecutionRecord,
    ToolPermission,
    new_id,
)

logger = logging.getLogger(__name__)

ToolHandler = Callable[[dict[str, Any]], Awaitable[Any] | Any]


class ToolSandbox:
    def __init__(self) -> None:
        self._active: dict[str, dict[str, Any]] = {}

    def reset(self) -> None:
        self._active.clear()

    def enter(self, tool_id: str) -> str:
        sid = new_id("tsbx")
        self._active[sid] = {"tool_id": tool_id, "started_at": time.time()}
        return sid

    def exit(self, sandbox_id: str) -> None:
        self._active.pop(sandbox_id, None)


class ToolRuntime:
    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}
        self._handlers: dict[str, ToolHandler] = {}
        self._executions: list[ToolExecutionRecord] = []
        self.sandbox = ToolSandbox()
        self._seeded = False

    def reset(self) -> None:
        self._tools.clear()
        self._handlers.clear()
        self._executions.clear()
        self.sandbox.reset()
        self._seeded = False

    def ensure_seed(self) -> None:
        if self._seeded:
            return
        self.register(
            ToolDefinition(
                tool_id="tool_echo",
                name="echo",
                description="Echo arguments back (demo)",
                parameters={"type": "object", "properties": {"text": {"type": "string"}}},
            ),
            handler=lambda args: {"echo": args.get("text", "")},
        )
        self.register(
            ToolDefinition(
                tool_id="tool_add",
                name="add",
                description="Add two numbers",
                parameters={
                    "type": "object",
                    "properties": {"a": {"type": "number"}, "b": {"type": "number"}},
                    "required": ["a", "b"],
                },
            ),
            handler=lambda args: {"sum": float(args.get("a", 0)) + float(args.get("b", 0))},
        )
        self.register(
            ToolDefinition(
                tool_id="tool_search",
                name="knowledge_search",
                description="MCP-compatible knowledge search stub",
                parameters={"type": "object", "properties": {"query": {"type": "string"}}},
                mcp_compatible=True,
            ),
            handler=lambda args: {"hits": [], "query": args.get("query")},
        )
        self._seeded = True

    def register(self, tool: ToolDefinition, *, handler: ToolHandler | None = None) -> ToolDefinition:
        self._tools[tool.tool_id] = tool
        self._tools[tool.name] = tool
        if handler is not None:
            self._handlers[tool.tool_id] = handler
            self._handlers[tool.name] = handler
        return tool

    def list_tools(self, *, enabled_only: bool = False) -> list[ToolDefinition]:
        self.ensure_seed()
        seen: set[str] = set()
        rows: list[ToolDefinition] = []
        for tool in self._tools.values():
            if tool.tool_id in seen:
                continue
            seen.add(tool.tool_id)
            if enabled_only and not tool.enabled:
                continue
            rows.append(tool)
        return sorted(rows, key=lambda t: t.name)

    def get(self, tool_id: str) -> ToolDefinition:
        self.ensure_seed()
        tool = self._tools.get(tool_id)
        if tool is None:
            raise KeyError(f"tool not found: {tool_id}")
        return tool

    def function_schemas(self) -> list[dict[str, Any]]:
        return [t.to_dict()["function_schema"] for t in self.list_tools(enabled_only=True)]

    def check_permission(self, tool_id: str) -> bool:
        tool = self.get(tool_id)
        if not tool.enabled:
            return False
        return tool.permission != ToolPermission.DENY

    async def execute(
        self,
        tool_id: str,
        arguments: dict[str, Any] | None = None,
        *,
        session_id: str | None = None,
    ) -> ToolExecutionRecord:
        self.ensure_seed()
        tool = self.get(tool_id)
        arguments = arguments or {}
        started = time.monotonic()
        sandbox_id = self.sandbox.enter(tool.tool_id) if tool.sandbox else None
        try:
            if not self.check_permission(tool.tool_id):
                raise PermissionError(f"tool denied: {tool.tool_id}")
            handler = self._handlers.get(tool.tool_id) or self._handlers.get(tool.name)
            if handler is None:
                raise KeyError(f"no handler for tool: {tool.tool_id}")

            async def _run() -> Any:
                result = handler(arguments)
                if asyncio.iscoroutine(result) or asyncio.isfuture(result):
                    return await result  # type: ignore[misc]
                return result

            result = await asyncio.wait_for(_run(), timeout=tool.timeout_sec)
            rec = ToolExecutionRecord(
                execution_id=new_id("tex"),
                tool_id=tool.tool_id,
                session_id=session_id,
                arguments=arguments,
                result=result,
                success=True,
                duration_ms=(time.monotonic() - started) * 1000,
            )
        except Exception as exc:
            rec = ToolExecutionRecord(
                execution_id=new_id("tex"),
                tool_id=tool.tool_id,
                session_id=session_id,
                arguments=arguments,
                success=False,
                error=str(exc),
                duration_ms=(time.monotonic() - started) * 1000,
            )
            logger.warning("tool_execution_failed tool=%s err=%s", tool.tool_id, exc)
        finally:
            if sandbox_id:
                self.sandbox.exit(sandbox_id)
        self._executions.append(rec)
        self._executions = self._executions[-5000:]
        return rec

    def executions(self, *, limit: int = 100) -> list[ToolExecutionRecord]:
        return self._executions[-limit:]


tool_runtime = ToolRuntime()
