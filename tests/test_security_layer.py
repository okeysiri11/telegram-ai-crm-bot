"""Tests — Platform Security Layer (Sprint 5.1)."""

from __future__ import annotations

import pytest

from platform_identity.api_keys import api_key_service
from platform_identity.jwt_service import jwt_service
from platform_security.audit import AuditManager
from platform_security.authentication import AuthenticationProvider
from platform_security.authorization import AuthorizationManager
from platform_security.config import SecurityConfig
from platform_security.exceptions import AuthenticationFailedError, AuthorizationDeniedError, SecretNotFoundError
from platform_security.models import AccessPolicy, AuditEventType, SecurityPrincipal, SecurityRole
from platform_security.permissions import PermissionManager
from platform_security.roles import RoleManager
from platform_security.secrets import SecretManager
from platform_security.security_manager import SecurityManager


@pytest.fixture
def manager() -> SecurityManager:
    mgr = SecurityManager(
        auth=AuthenticationProvider(config=SecurityConfig(allow_anonymous=True)),
        authz=AuthorizationManager(),
        permissions=PermissionManager(),
        roles=RoleManager(),
        secrets=SecretManager(config=SecurityConfig(secret_master_key="test-key")),
        audit=AuditManager(),
    )
    yield mgr
    mgr.reset()
    api_key_service.reset()
    jwt_service._revoked_jti.clear()


def _principal(roles: list[str] | None = None, perms: list[str] | None = None) -> SecurityPrincipal:
    return SecurityPrincipal(
        principal_id="test-user",
        roles=roles or ["developer"],
        permissions=perms or [],
    )


@pytest.mark.asyncio
async def test_authenticate_anonymous(manager: SecurityManager):
    principal = await manager.authenticate(anonymous=True)
    assert principal.principal_id == "anonymous"
    assert "viewer" in principal.roles or "workflow.read" in principal.permissions or principal.roles


@pytest.mark.asyncio
async def test_authenticate_anonymous_disabled():
    mgr = SecurityManager(auth=AuthenticationProvider(config=SecurityConfig(allow_anonymous=False)))
    with pytest.raises(AuthenticationFailedError):
        await mgr.authenticate(anonymous=True)


@pytest.mark.asyncio
async def test_authenticate_jwt(manager: SecurityManager):
    tokens = jwt_service.issue_tokens(
        subject="user-1",
        roles=["administrator"],
        permissions=["system.read"],
    )
    principal = await manager.authenticate(jwt_token=tokens.access_token)
    assert principal.principal_id == "user-1"
    assert "administrator" in principal.roles


@pytest.mark.asyncio
async def test_authenticate_api_key(manager: SecurityManager):
    raw, record = api_key_service.create_key(name="test", scopes=["workflow.read"])
    principal = await manager.authenticate(api_key=raw)
    assert principal.auth_method.value == "api_key"


@pytest.mark.asyncio
async def test_authenticate_service_account(manager: SecurityManager):
    principal = await manager.authenticate(
        service_account_id="svc-1",
        service_credential="secret-cred",
    )
    assert principal.service_account_id == "svc-1"


@pytest.mark.asyncio
async def test_rbac_owner_has_all(manager: SecurityManager):
    principal = _principal(roles=[SecurityRole.OWNER.value])
    manager._authz.enrich_principal(principal)
    assert await manager.authorize(principal, "workflow.write")
    assert await manager.authorize(principal, "tool.execute")


@pytest.mark.asyncio
async def test_rbac_viewer_read_only(manager: SecurityManager):
    principal = _principal(roles=[SecurityRole.VIEWER.value])
    manager._authz.enrich_principal(principal)
    assert await manager.authorize(principal, "workflow.read")
    assert not await manager.authorize(principal, "workflow.write")


@pytest.mark.asyncio
async def test_rbac_developer_can_write(manager: SecurityManager):
    principal = _principal(roles=[SecurityRole.DEVELOPER.value])
    manager._authz.enrich_principal(principal)
    assert await manager.authorize(principal, "workflow.write")
    assert await manager.authorize(principal, "tool.execute")


@pytest.mark.asyncio
async def test_authorization_denied_raises(manager: SecurityManager):
    principal = _principal(roles=[SecurityRole.VIEWER.value])
    manager._authz.enrich_principal(principal)
    with pytest.raises(AuthorizationDeniedError):
        await manager.require(principal, "config.write")


@pytest.mark.asyncio
async def test_agent_permission(manager: SecurityManager):
    principal = _principal(roles=[SecurityRole.AI_AGENT.value])
    manager._authz.enrich_principal(principal)
    assert await manager.authorize_agent(principal, "auto_agent")


@pytest.mark.asyncio
async def test_tool_permission(manager: SecurityManager):
    principal = _principal(roles=[SecurityRole.OPERATOR.value])
    manager._authz.enrich_principal(principal)
    assert await manager.authorize_tool(principal, "crm_lookup")


@pytest.mark.asyncio
async def test_workflow_permission(manager: SecurityManager):
    principal = _principal(roles=[SecurityRole.OPERATOR.value])
    manager._authz.enrich_principal(principal)
    assert await manager.authorize_workflow(principal, "wf-123")


@pytest.mark.asyncio
async def test_capability_permission():
    pm = PermissionManager()
    principal = _principal(roles=[SecurityRole.AI_AGENT.value])
    RoleManager().permissions_for_role(SecurityRole.AI_AGENT.value)
    principal.permissions = list(RoleManager().permissions_for_role(SecurityRole.AI_AGENT.value))
    assert pm.check_capability(principal, "buy_car", "execute")


@pytest.mark.asyncio
async def test_repository_permission():
    pm = PermissionManager()
    principal = _principal(roles=[SecurityRole.DEVELOPER.value])
    principal.permissions = list(RoleManager().permissions_for_role(SecurityRole.DEVELOPER.value))
    assert pm.check_repository(principal, "requests", "read")


def test_secret_store_and_retrieve(manager: SecurityManager):
    record = manager.store_secret("db_password", "super-secret")
    value = manager._secrets.retrieve(record.secret_id)
    assert value == "super-secret"


def test_secret_rotation(manager: SecurityManager):
    record = manager.store_secret("api_token", "token-v1")
    rotated = manager.rotate_secret(record.secret_id, "token-v2")
    assert rotated.version == 2
    assert manager._secrets.retrieve(record.secret_id) == "token-v2"


def test_secret_not_found(manager: SecurityManager):
    with pytest.raises(SecretNotFoundError):
        manager._secrets.retrieve("missing")


@pytest.mark.asyncio
async def test_secret_retrieve_with_auth(manager: SecurityManager):
    manager.store_secret("key", "value")
    owner = _principal(roles=[SecurityRole.OWNER.value])
    manager._authz.enrich_principal(owner)
    val = await manager.retrieve_secret("key", principal=owner)
    assert val == "value"


@pytest.mark.asyncio
async def test_audit_authentication(manager: SecurityManager):
    await manager.authenticate(anonymous=True)
    logs = manager.audit_log(event_type=AuditEventType.AUTHENTICATION)
    assert len(logs) >= 1


@pytest.mark.asyncio
async def test_audit_authorization(manager: SecurityManager):
    principal = _principal(roles=[SecurityRole.VIEWER.value])
    manager._authz.enrich_principal(principal)
    await manager.authorize(principal, "workflow.write")
    logs = manager.audit_log(event_type=AuditEventType.AUTHORIZATION)
    assert any(not r.success for r in logs)


@pytest.mark.asyncio
async def test_audit_tool_access(manager: SecurityManager):
    principal = _principal(roles=[SecurityRole.OPERATOR.value])
    manager._authz.enrich_principal(principal)
    await manager.authorize_tool(principal, "crm_lookup")
    logs = manager.audit_log(event_type=AuditEventType.TOOL_ACCESS)
    assert len(logs) >= 1


@pytest.mark.asyncio
async def test_custom_role(manager: SecurityManager):
    manager.register_custom_role("custom_analyst", ["workflow.read", "audit.read"])
    principal = _principal(roles=["custom_analyst"])
    manager._authz.enrich_principal(principal)
    assert await manager.authorize(principal, "audit.read")


def test_access_policy_deny():
    authz = AuthorizationManager()
    authz.register_policy(AccessPolicy(
        policy_id="deny-config",
        name="Deny Config",
        roles=["viewer"],
        permissions=["config.*"],
        effect="deny",
        priority=100,
    ))
    principal = _principal(roles=["viewer"])
    principal.permissions = list(RoleManager().permissions_for_role("viewer"))
    assert authz.authorize(principal, "config.write") is False


def test_permission_matrix(manager: SecurityManager):
    matrix = manager.permission_matrix([SecurityRole.DEVELOPER.value])
    assert matrix["workflow.write"] is True
    assert matrix["config.write"] is False


def test_metrics_summary(manager: SecurityManager):
    manager.store_secret("k", "v")
    summary = manager.metrics_summary()
    assert summary["secrets_stored"] == 1
    assert summary["roles_available"] >= 9


@pytest.mark.asyncio
async def test_integrations_tool_check():
    from platform_security.integrations import security_integrations

    principal = _principal(roles=[SecurityRole.OPERATOR.value])
    RoleManager()
    principal.permissions = list(RoleManager().permissions_for_role(SecurityRole.OPERATOR.value))
    assert security_integrations.check_tool_access(principal, "crm_lookup")
