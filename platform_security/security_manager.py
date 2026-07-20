# SecurityManager — unified security layer entry point.

from __future__ import annotations

import logging

from platform_security.audit import AuditManager, audit_manager
from platform_security.authentication import AuthenticationProvider, authentication_provider
from platform_security.authorization import AuthorizationManager, authorization_manager
from platform_security.config import DEFAULT_SECURITY_CONFIG, SecurityConfig
from platform_security.exceptions import AuthenticationFailedError, AuthorizationDeniedError
from platform_security.integrations import SecurityIntegrations, security_integrations
from platform_security.models import AccessPolicy, AuditEventType, SecurityPrincipal
from platform_security.permissions import PermissionManager, permission_manager
from platform_security.roles import RoleManager, role_manager
from platform_security.secrets import SecretManager, secret_manager
from platform_security.sessions import SessionManager, session_manager

logger = logging.getLogger(__name__)


class SecurityManager:
    """Enterprise-grade security facade for the platform."""

    def __init__(
        self,
        *,
        auth: AuthenticationProvider | None = None,
        authz: AuthorizationManager | None = None,
        permissions: PermissionManager | None = None,
        roles: RoleManager | None = None,
        secrets: SecretManager | None = None,
        sessions: SessionManager | None = None,
        audit: AuditManager | None = None,
        integrations: SecurityIntegrations | None = None,
        config: SecurityConfig | None = None,
    ) -> None:
        self._auth = auth or authentication_provider
        self._authz = authz or authorization_manager
        self._permissions = permissions or permission_manager
        self._roles = roles or role_manager
        self._secrets = secrets or secret_manager
        self._sessions = sessions or session_manager
        self._audit = audit or audit_manager
        self._integrations = integrations or security_integrations
        self._config = config or DEFAULT_SECURITY_CONFIG

    def reset(self) -> None:
        self._roles.reset()
        self._authz.reset()
        self._secrets.reset()
        self._audit.reset()

    async def authenticate(self, **kwargs) -> SecurityPrincipal:
        principal = await self._auth.authenticate(**kwargs)
        enriched = self._authz.enrich_principal(principal, roles=self._roles)
        await self._audit.log_authentication(
            enriched,
            method=enriched.auth_method.value,
            success=True,
        )
        return enriched

    async def authorize(
        self,
        principal: SecurityPrincipal,
        permission: str,
        *,
        resource: str | None = None,
    ) -> bool:
        self._authz.enrich_principal(principal, roles=self._roles)
        granted = self._authz.authorize(principal, permission, resource=resource)
        await self._audit.log_authorization(principal, permission=permission, resource=resource, granted=granted)
        if not granted:
            bridge = await self._integrations.bridge_identity_authorize(principal, permission)
            if bridge:
                await self._audit.log_authorization(principal, permission=permission, resource=resource, granted=True)
            return bridge
        return granted

    async def require(self, principal: SecurityPrincipal, permission: str, *, resource: str | None = None) -> None:
        if not await self.authorize(principal, permission, resource=resource):
            raise AuthorizationDeniedError(f"Denied: {permission}", permission=permission)

    async def authorize_tool(self, principal: SecurityPrincipal, tool_id: str) -> bool:
        ok = self._authz.authorize_tool(principal, tool_id)
        await self._audit.log_tool_access(principal, tool_id, success=ok)
        return ok

    async def authorize_workflow(self, principal: SecurityPrincipal, workflow_id: str) -> bool:
        ok = self._authz.authorize_workflow(principal, workflow_id)
        await self._audit.log_workflow_access(principal, workflow_id, success=ok)
        return ok

    async def authorize_agent(self, principal: SecurityPrincipal, agent_id: str) -> bool:
        return self._authz.authorize_agent(principal, agent_id)

    def register_policy(self, policy: AccessPolicy) -> None:
        self._authz.register_policy(policy)

    def register_custom_role(self, role_name: str, permissions: list[str], **kwargs) -> None:
        self._roles.register_custom_role(role_name, permissions, **kwargs)

    def store_secret(self, name: str, value: str, **kwargs):
        return self._secrets.store(name, value, **kwargs)

    async def retrieve_secret(self, name: str, *, principal: SecurityPrincipal | None = None) -> str:
        if principal:
            allowed = self._authz.authorize(principal, "config.read")
            await self._audit.log_secret_access(principal.principal_id, name, success=allowed)
            if not allowed:
                raise AuthorizationDeniedError("Secret access denied", permission="config.read")
        return self._secrets.retrieve_by_name(name)

    def rotate_secret(self, secret_id: str, new_value: str | None = None):
        return self._secrets.rotate(secret_id, new_value)

    async def create_session(self, principal: SecurityPrincipal, **kwargs) -> str:
        return await self._sessions.create_session(principal, **kwargs)

    def permission_matrix(self, roles: list[str]) -> dict[str, bool]:
        return self._permissions.matrix(roles)

    def audit_log(self, *, event_type: AuditEventType | None = None, limit: int = 100):
        return self._audit.query(event_type=event_type, limit=limit)

    def metrics_summary(self) -> dict:
        records = self._audit.records
        auth_count = sum(1 for r in records if r.event_type == AuditEventType.AUTHENTICATION)
        authz_count = sum(1 for r in records if r.event_type == AuditEventType.AUTHORIZATION)
        denied = sum(1 for r in records if r.event_type == AuditEventType.AUTHORIZATION and not r.success)
        return {
            "authentication_events": auth_count,
            "authorization_events": authz_count,
            "authorization_denied": denied,
            "audit_records": len(records),
            "secrets_stored": len(self._secrets.list_secrets()),
            "roles_available": len(self._roles.list_roles()),
        }


security_manager = SecurityManager()
