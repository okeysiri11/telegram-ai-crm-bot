# Integration bridges — Workflow, Tools, Memory, Agents, Orchestrator.

from __future__ import annotations

import logging

from platform_security.models import SecurityPrincipal

logger = logging.getLogger(__name__)


class SecurityIntegrations:
    @staticmethod
    def check_workflow_access(principal: SecurityPrincipal, workflow_id: str, action: str = "execute") -> bool:
        from platform_security.authorization import authorization_manager

        return authorization_manager.authorize_workflow(principal, workflow_id, action)

    @staticmethod
    def check_tool_access(principal: SecurityPrincipal, tool_id: str, action: str = "execute") -> bool:
        from platform_security.authorization import authorization_manager

        return authorization_manager.authorize_tool(principal, tool_id, action)

    @staticmethod
    def check_agent_access(principal: SecurityPrincipal, agent_id: str, action: str = "execute") -> bool:
        from platform_security.authorization import authorization_manager

        return authorization_manager.authorize_agent(principal, agent_id, action)

    @staticmethod
    async def authorize_orchestrator_route(principal: SecurityPrincipal, capability: str) -> bool:
        from platform_security.permissions import permission_manager

        return permission_manager.check_capability(principal, capability, "execute")

    @staticmethod
    async def protect_memory_access(principal: SecurityPrincipal, user_id: str) -> bool:
        return permission_manager.check(principal, "repository.read", resource=f"memory:{user_id}")

    @staticmethod
    def agent_permissions_from_registry(agent_id: str) -> list[str]:
        try:
            from platform_agents.registry import agent_registry

            agent = agent_registry.get(agent_id)
            meta = agent.metadata()
            return [f"capability.execute:{c}" for c in meta.capabilities]
        except Exception:
            logger.debug("agent_registry unavailable for security")
            return []

    @staticmethod
    async def bridge_identity_authorize(principal: SecurityPrincipal, permission: str) -> bool:
        try:
            from platform_identity.models import AuthMethod, Principal
            from platform_identity.policy_engine import policy_engine

            identity = Principal(
                principal_id=principal.principal_id,
                auth_method=AuthMethod.JWT,
                roles=principal.roles,
                permissions=principal.permissions,
            )
            return await policy_engine.authorize(identity, permission)
        except Exception:
            return False


security_integrations = SecurityIntegrations()

# Late import to avoid circular reference in protect_memory_access
from platform_security.permissions import permission_manager  # noqa: E402
