"""Permissions for AI Command Center."""

from __future__ import annotations

ALLOWED_ROLES = frozenset(
    {"owner", "admin", "platform_owner", "developer", "manager", "operator", "read_only"}
)

TOOL_PERMISSIONS: dict[str, frozenset[str]] = {
    "generate_image": frozenset({"owner", "admin", "platform_owner", "manager", "operator"}),
    "generate_video": frozenset({"owner", "admin", "platform_owner", "manager"}),
    "generate_voice": frozenset({"owner", "admin", "platform_owner", "manager", "operator"}),
    "crm_action": frozenset({"owner", "admin", "platform_owner", "manager", "operator"}),
    "erp_action": frozenset({"owner", "admin", "platform_owner", "manager"}),
    "publish": frozenset({"owner", "admin", "platform_owner", "manager"}),
    "workflow": frozenset({"owner", "admin", "platform_owner", "developer"}),
}


def can_use_tool(role: str, tool_id: str) -> bool:
    role_n = (role or "owner").lower()
    if role_n not in ALLOWED_ROLES:
        return False
    allowed = TOOL_PERMISSIONS.get(tool_id)
    if allowed is None:
        return True
    return role_n in allowed or role_n in ("owner", "admin", "platform_owner")


def filter_tools_for_role(role: str, tools: list[str]) -> list[str]:
    return [t for t in tools if can_use_tool(role, t)]
