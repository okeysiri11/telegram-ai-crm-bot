"""Tests — Platform Identity & Access Management."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from platform_identity.api_keys import api_key_service
from platform_identity.authentication import authentication_service
from platform_identity.exceptions import ApiKeyError, AuthenticationError, AuthorizationError, TokenError
from platform_identity.identity_router import register_identity_routes
from platform_identity.identity_service import identity_service
from platform_identity.jwt_service import jwt_service
from platform_identity.models import AuthMethod, PlatformRole, Principal, ResourceRef
from platform_identity.policy_engine import policy_engine
from platform_identity.session_manager import session_manager
from platform_management.management_router import register_management_routes
from platform_management.permissions import ManagementRole
from platform_realtime.channel_manager import ChannelManager


@pytest.fixture(autouse=True)
def _reset_iam():
    identity_service.reset()
    yield
    identity_service.reset()


@pytest.fixture
def owner_principal():
    return Principal(
        principal_id="telegram:42",
        auth_method=AuthMethod.TELEGRAM_OWNER,
        roles=[PlatformRole.OWNER.value],
        permissions=[],
        telegram_id=42,
    )


@pytest.fixture
def readonly_principal():
    return Principal(
        principal_id="telegram:99",
        auth_method=AuthMethod.TELEGRAM_USER,
        roles=[PlatformRole.READ_ONLY.value],
        permissions=[],
        telegram_id=99,
    )



@pytest.fixture(autouse=True)
def _grant_owner(monkeypatch):
    async def _owner(_tid):
        return ManagementRole.OWNER

    monkeypatch.setattr("platform_management.permissions.resolve_role", _owner)


@pytest.mark.asyncio
async def test_authenticate_telegram_owner(monkeypatch):
    monkeypatch.setattr("config.OWNER_ID", 42)
    principal = await authentication_service.authenticate_telegram(42)
    assert principal.auth_method == AuthMethod.TELEGRAM_OWNER
    assert PlatformRole.OWNER.value in principal.roles


@pytest.mark.asyncio
async def test_authenticate_request_via_bearer_jwt(monkeypatch):
    monkeypatch.setattr("config.OWNER_ID", 42)
    jwt_service.reset()
    tokens = jwt_service.issue_tokens(
        subject="telegram:42",
        roles=[PlatformRole.OWNER.value],
        permissions=["management.read"],
        telegram_id=42,
    )
    request = MagicMock()
    request.headers.get = lambda key, default="": {
        "Authorization": f"Bearer {tokens.access_token}",
        "X-API-Key": "",
        "User-Agent": "test",
        "X-Forwarded-For": "",
    }.get(key, default)
    request.query.get = lambda key, default=None: default
    request.transport = None
    with patch(
        "platform_identity.audit_hooks.iam_audit.log_authentication",
        new_callable=AsyncMock,
    ):
        principal = await authentication_service.authenticate_request(request)
    assert principal.telegram_id == 42
    assert principal.auth_method == AuthMethod.JWT


@pytest.mark.asyncio
async def test_authenticate_request_missing_credentials():
    request = MagicMock()
    request.headers.get = MagicMock(return_value="")
    request.query.get = lambda key, default=None: default
    request.transport = None
    with patch(
        "platform_identity.audit_hooks.iam_audit.log_authentication",
        new_callable=AsyncMock,
    ):
        with pytest.raises(AuthenticationError):
            await authentication_service.authenticate_request(request)


@pytest.mark.asyncio
async def test_owner_has_all_permissions(owner_principal):
    assert await identity_service.authorize(owner_principal, "configuration.write")
    assert await identity_service.authorize(owner_principal, "management.admin")


@pytest.mark.asyncio
async def test_readonly_denied_configuration_write(readonly_principal):
    assert await identity_service.authorize(readonly_principal, "dashboard.read")
    assert not await identity_service.authorize(readonly_principal, "configuration.write")


@pytest.mark.asyncio
async def test_assert_authorized_raises(readonly_principal):
    with pytest.raises(AuthorizationError):
        await identity_service.assert_authorized(readonly_principal, "plugins.write")


@pytest.mark.asyncio
async def test_role_inheritance():
    from platform_identity.role_service import role_service

    perms = role_service.permissions_for_role(PlatformRole.ADMINISTRATOR.value)
    assert "dashboard.read" in perms
    assert "configuration.write" in perms


@pytest.mark.asyncio
async def test_custom_deny_policy():
    policy_engine.create_policy(
        name="deny-config",
        effect="deny",
        permissions=["configuration.*"],
        roles=[PlatformRole.ADMINISTRATOR.value],
    )
    admin = Principal(
        principal_id="telegram:100",
        auth_method=AuthMethod.TELEGRAM_USER,
        roles=[PlatformRole.ADMINISTRATOR.value],
        permissions=[],
        telegram_id=100,
    )
    assert not await identity_service.authorize(admin, "configuration.read")


@pytest.mark.asyncio
async def test_resource_level_tenant_isolation():
    principal = Principal(
        principal_id="telegram:200",
        auth_method=AuthMethod.TELEGRAM_USER,
        roles=[PlatformRole.OPERATOR.value],
        permissions=["requests.read"],
        telegram_id=200,
        tenant_id="tenant-a",
    )
    allowed = await identity_service.authorize(
        principal,
        "requests.read",
        resource=ResourceRef(type="request", id="r1", tenant_id="tenant-a"),
    )
    denied = await identity_service.authorize(
        principal,
        "requests.read",
        resource=ResourceRef(type="request", id="r2", tenant_id="tenant-b"),
    )
    assert allowed is True
    assert denied is False


@pytest.mark.asyncio
async def test_jwt_issue_verify_rotate():
    tokens = jwt_service.issue_tokens(
        subject="telegram:42",
        roles=[PlatformRole.OWNER.value],
        permissions=["management.read"],
        telegram_id=42,
    )
    claims = jwt_service.verify_access_token(tokens.access_token)
    assert claims["sub"] == "telegram:42"
    assert claims["token_type"] == "access"

    rotated = jwt_service.rotate_refresh_token(tokens.refresh_token)
    assert rotated.access_token != tokens.access_token

    with pytest.raises(TokenError):
        jwt_service.rotate_refresh_token(tokens.refresh_token)


@pytest.mark.asyncio
async def test_jwt_revocation():
    tokens = jwt_service.issue_tokens(
        subject="telegram:42",
        roles=["owner"],
        permissions=[],
        telegram_id=42,
    )
    jwt_service.revoke_token(tokens.access_token)
    with pytest.raises(TokenError):
        jwt_service.verify_access_token(tokens.access_token)


@pytest.mark.asyncio
async def test_login_creates_session():
    with patch("config.OWNER_ID", 42), patch(
        "platform_identity.audit_hooks.iam_audit.log_session_created",
        new_callable=AsyncMock,
    ):
        result = await identity_service.login(42, ip="127.0.0.1", device="test")
    assert result["access_token"]
    assert result["session_id"]
    assert len(session_manager.list_sessions()) == 1


@pytest.mark.asyncio
async def test_api_key_lifecycle():
    raw, record = api_key_service.create_key(
        name="test-key",
        scopes=["management.read", "sdk.read"],
        telegram_id=42,
    )
    assert raw.startswith("iam_live_")

    with patch(
        "platform_identity.audit_hooks.iam_audit.log_api_key_usage",
        new_callable=AsyncMock,
    ):
        principal = await api_key_service.authenticate(raw)
    assert principal.auth_method == AuthMethod.API_KEY
    assert "management.read" in principal.permissions

    api_key_service.disable_key(record.key_id)
    with pytest.raises(ApiKeyError):
        await api_key_service.authenticate(raw)


@pytest.mark.asyncio
async def test_api_key_rotation():
    raw, record = api_key_service.create_key(name="rotate-me", scopes=["management.read"])
    new_raw, new_record = api_key_service.rotate_key(record.key_id)
    assert new_raw != raw
    assert new_record.key_id != record.key_id
    with pytest.raises(ApiKeyError):
        await api_key_service.authenticate(raw)


@pytest.mark.asyncio
async def test_session_revocation():
    with patch("config.OWNER_ID", 42), patch(
        "platform_identity.audit_hooks.iam_audit.log_session_created",
        new_callable=AsyncMock,
    ):
        result = await identity_service.login(42, ip="127.0.0.1", device="test")
    session_id = result["session_id"]
    session_manager.revoke(session_id)
    with pytest.raises(Exception):
        session_manager.validate(session_id)


@pytest.mark.asyncio
async def test_realtime_channel_via_iam(owner_principal, readonly_principal):
    assert await ChannelManager.can_subscribe(owner_principal, "configuration")
    assert await ChannelManager.can_subscribe(readonly_principal, "dashboard")
    assert not await ChannelManager.can_subscribe(readonly_principal, "configuration")


@pytest.mark.asyncio
async def test_identity_status_endpoint(actor_header):
    app = web.Application()
    register_management_routes(app)

    with patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        async with TestClient(TestServer(app)) as client:
            resp = await client.get("/management/identity", headers=actor_header)
            assert resp.status == 200
            body = await resp.json()
            assert body["success"] is True
            assert "permissions" in body["data"]
            assert "roles" in body["data"]


@pytest.mark.asyncio
async def test_identity_api_key_create_endpoint(actor_header):
    app = web.Application()
    register_identity_routes(app)

    async def _admin(_tid):
        return ManagementRole.ADMINISTRATOR

    with patch("platform_management.permissions.resolve_role", _admin), patch(
        "platform_identity.identity_router.iam_audit.log_api_key_created",
        new_callable=AsyncMock,
    ), patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        async with TestClient(TestServer(app)) as client:
            resp = await client.post(
                "/management/identity/api-keys",
                headers=actor_header,
                json={"name": "ci-key", "scopes": ["management.read"]},
            )
            assert resp.status == 201
            body = await resp.json()
            assert body["data"]["api_key"].startswith("iam_live_")


@pytest.mark.asyncio
async def test_resolve_management_role_via_iam(monkeypatch):
    monkeypatch.setattr("config.OWNER_ID", 42)
    role = await identity_service.resolve_management_role(42)
    assert role == ManagementRole.OWNER


@pytest.mark.asyncio
async def test_has_legacy_permission(monkeypatch):
    monkeypatch.setattr("config.OWNER_ID", 42)
    assert await identity_service.has_legacy_permission(42, "admin.access")
