# RoleManager — platform roles with inheritance and custom role support.

from __future__ import annotations

from platform_security.models import SecurityRole


ROLE_INHERITANCE: dict[str, list[str]] = {
    SecurityRole.OWNER.value: [SecurityRole.ADMINISTRATOR.value],
    SecurityRole.ADMINISTRATOR.value: [SecurityRole.DEVELOPER.value, SecurityRole.OPERATOR.value],
    SecurityRole.DEVELOPER.value: [SecurityRole.VIEWER.value],
    SecurityRole.MANAGER.value: [SecurityRole.VIEWER.value],
    SecurityRole.OPERATOR.value: [SecurityRole.VIEWER.value],
    SecurityRole.AI_AGENT.value: [],
    SecurityRole.SERVICE.value: [],
}

DEFAULT_ROLE_PERMISSIONS: dict[str, list[str]] = {
    SecurityRole.OWNER.value: ["*"],
    SecurityRole.ADMINISTRATOR.value: [
        "system.*", "workflow.*", "tool.*", "agent.*", "repository.*", "capability.*", "audit.*", "config.*",
    ],
    SecurityRole.DEVELOPER.value: [
        "workflow.read", "workflow.write", "tool.read", "tool.execute", "agent.read", "agent.execute",
        "repository.read", "capability.read", "capability.execute",
    ],
    SecurityRole.OPERATOR.value: [
        "workflow.read", "workflow.execute", "tool.read", "tool.execute", "agent.read", "agent.execute",
    ],
    SecurityRole.MANAGER.value: [
        "workflow.read", "workflow.execute", "agent.read", "audit.read", "capability.read",
    ],
    SecurityRole.VIEWER.value: [
        "workflow.read", "tool.read", "agent.read", "repository.read", "capability.read",
    ],
    SecurityRole.AI_AGENT.value: [
        "agent.execute", "tool.execute", "capability.execute", "workflow.execute",
    ],
    SecurityRole.SERVICE.value: [
        "workflow.execute", "tool.execute", "repository.read",
    ],
}


class RoleManager:
    def __init__(self) -> None:
        self._custom_roles: dict[str, list[str]] = {}

    def reset(self) -> None:
        self._custom_roles.clear()

    def register_custom_role(self, role_name: str, permissions: list[str], *, inherits: list[str] | None = None) -> None:
        self._custom_roles[role_name] = list(permissions)
        if inherits:
            ROLE_INHERITANCE[role_name] = list(inherits)

    def permissions_for_role(self, role: str) -> set[str]:
        perms: set[str] = set()
        perms.update(DEFAULT_ROLE_PERMISSIONS.get(role, []))
        perms.update(self._custom_roles.get(role, []))
        for parent in ROLE_INHERITANCE.get(role, []):
            perms.update(self.permissions_for_role(parent))
        return perms

    def effective_permissions(self, roles: list[str]) -> set[str]:
        result: set[str] = set()
        for role in roles:
            result.update(self.permissions_for_role(role))
        return result

    def list_roles(self) -> list[str]:
        roles = {r.value for r in SecurityRole}
        roles.update(self._custom_roles.keys())
        return sorted(roles)

    def map_identity_role(self, identity_role: str) -> str:
        mapping = {
            "readonly": SecurityRole.VIEWER.value,
            "ai": SecurityRole.AI_AGENT.value,
            "plugin": SecurityRole.DEVELOPER.value,
        }
        return mapping.get(identity_role, identity_role)


role_manager = RoleManager()
