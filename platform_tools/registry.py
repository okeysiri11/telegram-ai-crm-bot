# ToolRegistry — register, discover, and validate platform tools.

from __future__ import annotations

import logging
from typing import Callable

from platform_tools.exceptions import ToolAlreadyRegisteredError, ToolNotFoundError
from platform_tools.models import Tool, ToolCategory, ToolHandler, ToolPermission
from platform_tools.validation import validate_tool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Central registry for all platform tools."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}
        self._discoverers: list[Callable[[], list[Tool]]] = []

    def reset(self) -> None:
        self._tools.clear()
        self._discoverers.clear()

    def register_tool(self, tool: Tool) -> Tool:
        validate_tool(tool)
        if tool.tool_id in self._tools:
            raise ToolAlreadyRegisteredError(tool.tool_id)
        self._tools[tool.tool_id] = tool
        logger.info("tool_registered id=%s category=%s", tool.tool_id, tool.category.value)
        return tool

    def register_handler(
        self,
        tool_id: str,
        name: str,
        description: str,
        category: ToolCategory,
        handler: ToolHandler,
        *,
        required_permissions: list[ToolPermission] | None = None,
        version: str = "1.0.0",
        author: str = "Platform",
    ) -> Tool:
        tool = Tool(
            tool_id=tool_id,
            name=name,
            description=description,
            category=category,
            handler=handler,
            required_permissions=required_permissions or [ToolPermission.EXECUTE],
            version=version,
            author=author,
        )
        return self.register_tool(tool)

    def remove_tool(self, tool_id: str) -> None:
        if tool_id not in self._tools:
            raise ToolNotFoundError(tool_id)
        del self._tools[tool_id]
        logger.info("tool_removed id=%s", tool_id)

    def get(self, tool_id: str) -> Tool:
        if tool_id not in self._tools:
            raise ToolNotFoundError(tool_id)
        return self._tools[tool_id]

    def list_tools(self, *, category: ToolCategory | None = None, enabled_only: bool = True) -> list[Tool]:
        tools = list(self._tools.values())
        if enabled_only:
            tools = [t for t in tools if t.enabled]
        if category is not None:
            tools = [t for t in tools if t.category == category]
        return tools

    def discover_tools(self) -> list[Tool]:
        discovered: list[Tool] = []
        for discoverer in self._discoverers:
            for tool in discoverer():
                if tool.tool_id not in self._tools:
                    validate_tool(tool)
                    self._tools[tool.tool_id] = tool
                    discovered.append(tool)
                    logger.info("tool_discovered id=%s", tool.tool_id)
        return discovered

    def add_discoverer(self, discoverer: Callable[[], list[Tool]]) -> None:
        self._discoverers.append(discoverer)

    def validate_tool(self, tool: Tool) -> None:
        validate_tool(tool)

    def categories(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for tool in self._tools.values():
            counts[tool.category.value] = counts.get(tool.category.value, 0) + 1
        return counts

    def summary(self) -> dict:
        return {
            "total": len(self._tools),
            "enabled": sum(1 for t in self._tools.values() if t.enabled),
            "categories": self.categories(),
        }


tool_registry = ToolRegistry()
