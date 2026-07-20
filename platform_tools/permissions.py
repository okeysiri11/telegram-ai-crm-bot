# Tool permissions — per-agent and per-user access control.

from __future__ import annotations

import logging

from platform_tools.exceptions import ToolPermissionDeniedError
from platform_tools.models import Tool, ToolContext, ToolPermission

logger = logging.getLogger(__name__)


class ToolPermissionService:
    """Manage per-agent and per-user tool permissions."""

    def __init__(self) -> None:
        self._agent_permissions: dict[str, set[str]] = {}
        self._user_permissions: dict[str, set[str]] = {}
        self._agent_tools: dict[str, set[str]] = {}

    def reset(self) -> None:
        self._agent_permissions.clear()
        self._user_permissions.clear()
        self._agent_tools.clear()

    def grant_agent_permission(self, agent_id: str, permission: ToolPermission | str) -> None:
        perm = permission.value if isinstance(permission, ToolPermission) else permission
        self._agent_permissions.setdefault(agent_id, set()).add(perm)

    def grant_user_permission(self, user_id: str, permission: ToolPermission | str) -> None:
        perm = permission.value if isinstance(permission, ToolPermission) else permission
        self._user_permissions.setdefault(user_id, set()).add(perm)

    def set_agent_tools(self, agent_id: str, tool_ids: list[str]) -> None:
        self._agent_tools[agent_id] = set(tool_ids)

    def get_agent_tools(self, agent_id: str) -> set[str]:
        return set(self._agent_tools.get(agent_id, set()))

    def check(self, tool: Tool, context: ToolContext) -> None:
        for required in tool.required_permissions:
            if not context.has_permission(required):
                agent_perms = self._agent_permissions.get(context.agent_id or "", set())
                user_perms = self._user_permissions.get(context.user_id or "", set())
                if required.value not in agent_perms and required.value not in user_perms:
                    raise ToolPermissionDeniedError(tool.tool_id, required.value)

        if context.agent_id and self._agent_tools.get(context.agent_id):
            allowed = self._agent_tools[context.agent_id]
            if tool.tool_id not in allowed:
                raise ToolPermissionDeniedError(tool.tool_id, "agent_tool_access")

    def build_context(
        self,
        *,
        agent_id: str | None = None,
        user_id: str | None = None,
        session_id: str | None = None,
        extra_permissions: list[str] | None = None,
    ) -> ToolContext:
        perms: set[str] = set(extra_permissions or [])
        perms.update(self._agent_permissions.get(agent_id or "", set()))
        perms.update(self._user_permissions.get(user_id or "", set()))
        if not perms:
            perms.add(ToolPermission.EXECUTE.value)
        return ToolContext(
            agent_id=agent_id,
            user_id=user_id,
            session_id=session_id,
            permissions=sorted(perms),
        )


tool_permission_service = ToolPermissionService()
