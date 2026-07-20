# PermissionManager — capability, agent, tool, workflow, repository permissions.

from __future__ import annotations

import fnmatch

from platform_security.models import PermissionScope, SecurityPrincipal
from platform_security.roles import role_manager


class PermissionManager:
    SCOPE_PREFIXES = {
        PermissionScope.CAPABILITY: "capability",
        PermissionScope.AGENT: "agent",
        PermissionScope.TOOL: "tool",
        PermissionScope.WORKFLOW: "workflow",
        PermissionScope.REPOSITORY: "repository",
        PermissionScope.SYSTEM: "system",
    }

    def permission_key(self, scope: PermissionScope, action: str) -> str:
        prefix = self.SCOPE_PREFIXES[scope]
        return f"{prefix}.{action}"

    def grant(self, principal: SecurityPrincipal, permission: str) -> None:
        if permission not in principal.permissions:
            principal.permissions.append(permission)

    def revoke(self, principal: SecurityPrincipal, permission: str) -> None:
        if permission in principal.permissions:
            principal.permissions.remove(permission)

    def check(
        self,
        principal: SecurityPrincipal,
        permission: str,
        *,
        resource: str | None = None,
    ) -> bool:
        effective = set(principal.permissions)
        if not effective:
            effective.update(role_manager.effective_permissions(principal.roles))

        if "*" in effective:
            return True

        if permission in effective:
            return True

        for perm in effective:
            if perm.endswith(".*") and permission.startswith(perm[:-1]):
                return True
            if fnmatch.fnmatch(permission, perm):
                return True

        if resource:
            scoped = f"{permission}:{resource}"
            if scoped in effective:
                return True

        return False

    def check_capability(self, principal: SecurityPrincipal, capability: str, action: str = "execute") -> bool:
        return self.check(principal, self.permission_key(PermissionScope.CAPABILITY, action), resource=capability)

    def check_agent(self, principal: SecurityPrincipal, agent_id: str, action: str = "execute") -> bool:
        return self.check(principal, self.permission_key(PermissionScope.AGENT, action), resource=agent_id)

    def check_tool(self, principal: SecurityPrincipal, tool_id: str, action: str = "execute") -> bool:
        return self.check(principal, self.permission_key(PermissionScope.TOOL, action), resource=tool_id)

    def check_workflow(self, principal: SecurityPrincipal, workflow_id: str, action: str = "execute") -> bool:
        return self.check(principal, self.permission_key(PermissionScope.WORKFLOW, action), resource=workflow_id)

    def check_repository(self, principal: SecurityPrincipal, repo: str, action: str = "read") -> bool:
        return self.check(principal, self.permission_key(PermissionScope.REPOSITORY, action), resource=repo)

    def matrix(self, roles: list[str]) -> dict[str, bool]:
        perms = role_manager.effective_permissions(roles)
        all_perms = [
            "workflow.read", "workflow.write", "workflow.execute",
            "tool.read", "tool.execute",
            "agent.read", "agent.execute",
            "repository.read", "repository.write",
            "capability.read", "capability.execute",
            "audit.read", "config.read", "config.write",
        ]
        return {p: self._perm_in_set(p, perms) for p in all_perms}

    def _perm_in_set(self, permission: str, perms: set[str]) -> bool:
        if "*" in perms:
            return True
        if permission in perms:
            return True
        for perm in perms:
            if perm.endswith(".*") and permission.startswith(perm[:-1]):
                return True
            if fnmatch.fnmatch(permission, perm):
                return True
        return False


permission_manager = PermissionManager()
