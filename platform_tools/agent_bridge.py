# Agent Registry integration — agents declare tools, orchestrator provides access.

from __future__ import annotations

import logging
from typing import Any

from platform_agents.registry import AgentRegistry, agent_registry
from platform_tools.executor import ToolExecutor, tool_executor
from platform_tools.models import ToolContext, ToolResult
from platform_tools.permissions import ToolPermissionService, tool_permission_service
from platform_tools.registry import ToolRegistry, tool_registry

logger = logging.getLogger(__name__)


class AgentToolBridge:
    """Bridge between Agent Registry and Tool Framework."""

    def __init__(
        self,
        *,
        agent_registry_instance: AgentRegistry | None = None,
        tool_registry_instance: ToolRegistry | None = None,
        executor: ToolExecutor | None = None,
        permissions: ToolPermissionService | None = None,
    ) -> None:
        self._agents = agent_registry_instance or agent_registry
        self._tools = tool_registry_instance or tool_registry
        self._executor = executor or tool_executor
        self._permissions = permissions or tool_permission_service
        self._agent_tool_map: dict[str, list[str]] = {}

    def reset(self) -> None:
        self._agent_tool_map.clear()

    def declare_agent_tools(self, agent_id: str, tool_ids: list[str]) -> None:
        """Agent declares supported tools."""
        for tool_id in tool_ids:
            self._tools.get(tool_id)
        self._agent_tool_map[agent_id] = list(tool_ids)
        self._permissions.set_agent_tools(agent_id, tool_ids)
        logger.info("agent_tools_declared agent=%s tools=%s", agent_id, tool_ids)

    def get_agent_tools(self, agent_id: str) -> list[str]:
        return list(self._agent_tool_map.get(agent_id, []))

    def auto_declare_from_registry(self) -> dict[str, list[str]]:
        """Discover tools for all registered agents based on capability naming convention."""
        mapping: dict[str, list[str]] = {}
        for meta in self._agents.list_agents():
            tool_ids = [
                t.tool_id
                for t in self._tools.list_tools()
                if meta.id.split("_")[0] in t.tool_id or t.category.value in meta.capabilities
            ]
            if tool_ids:
                self.declare_agent_tools(meta.id, tool_ids)
                mapping[meta.id] = tool_ids
        return mapping

    async def execute_for_agent(
        self,
        agent_id: str,
        tool_id: str,
        payload: dict[str, Any] | None = None,
        *,
        user_id: str | None = None,
    ) -> ToolResult:
        """Execute tool on behalf of an agent with proper context."""
        if agent_id in self._agent_tool_map and tool_id not in self._agent_tool_map[agent_id]:
            from platform_tools.exceptions import ToolPermissionDeniedError

            raise ToolPermissionDeniedError(tool_id, "agent_tool_access")

        context = self._permissions.build_context(agent_id=agent_id, user_id=user_id)
        return await self._executor.execute(tool_id, payload, context=context)

    def tool_access_for_orchestrator(self, agent_id: str) -> dict[str, Any]:
        """Provide tool access descriptor for orchestrator injection."""
        tools = self.get_agent_tools(agent_id)
        return {
            "agent_id": agent_id,
            "available_tools": tools,
            "tool_definitions": [self._tools.get(tid).to_dict() for tid in tools],
        }


agent_tool_bridge = AgentToolBridge()
