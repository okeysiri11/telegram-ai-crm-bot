# AuthorizationManager — RBAC with policy evaluation.

from __future__ import annotations

from platform_security.exceptions import AuthorizationDeniedError
from platform_security.models import AccessPolicy, SecurityPrincipal
from platform_security.permissions import permission_manager
from platform_security.roles import RoleManager, role_manager


class AuthorizationManager:
    def __init__(self) -> None:
        self._policies: list[AccessPolicy] = []

    def reset(self) -> None:
        self._policies.clear()

    def register_policy(self, policy: AccessPolicy) -> None:
        self._policies.append(policy)
        self._policies.sort(key=lambda p: -p.priority)

    def authorize(
        self,
        principal: SecurityPrincipal,
        permission: str,
        *,
        resource: str | None = None,
    ) -> bool:
        for policy in self._policies:
            for role in principal.roles:
                if policy.effect == "deny" and policy.matches(role=role, permission=permission, resource=resource):
                    return False

        if permission_manager.check(principal, permission, resource=resource):
            return True

        return False

    def require(
        self,
        principal: SecurityPrincipal,
        permission: str,
        *,
        resource: str | None = None,
    ) -> None:
        if not self.authorize(principal, permission, resource=resource):
            raise AuthorizationDeniedError(
                f"Principal {principal.principal_id} denied {permission}",
                permission=permission,
            )

    def authorize_agent(self, principal: SecurityPrincipal, agent_id: str, action: str = "execute") -> bool:
        return self.authorize(principal, f"agent.{action}", resource=agent_id)

    def authorize_tool(self, principal: SecurityPrincipal, tool_id: str, action: str = "execute") -> bool:
        return self.authorize(principal, f"tool.{action}", resource=tool_id)

    def authorize_workflow(self, principal: SecurityPrincipal, workflow_id: str, action: str = "execute") -> bool:
        return self.authorize(principal, f"workflow.{action}", resource=workflow_id)

    def enrich_principal(self, principal: SecurityPrincipal, *, roles: RoleManager | None = None) -> SecurityPrincipal:
        rm = roles or role_manager
        perms = rm.effective_permissions(principal.roles)
        principal.permissions = sorted(set(principal.permissions) | perms)
        return principal


authorization_manager = AuthorizationManager()
