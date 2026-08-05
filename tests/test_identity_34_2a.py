"""Sprint 34.2A — Unified Identity Core registries and auth wiring."""

from __future__ import annotations

import pytest

from platform_identity.authentication import authentication_service
from platform_identity.identity_service import identity_service
from platform_identity.jwt_service import jwt_service
from platform_identity.models import PlatformRole
from platform_identity.registries.permission_registry import (
    defaults_for_roles,
    expand_permissions,
    normalize_permission,
)
from platform_identity.registries.role_registry import normalize_role, normalize_roles
from platform_identity.registries.workspace_registry import (
    WORKSPACE_REGISTRY,
    normalize_workspace_codes,
)


@pytest.fixture(autouse=True)
def _reset_iam():
    identity_service.reset()
    yield
    identity_service.reset()


def test_role_registry_aliases():
    assert normalize_role("OWNER") == "owner"
    assert normalize_role("SUPER_ADMIN") == "owner"
    assert normalize_role("AUTO_MANAGER") == "manager"
    assert normalize_role("CUSTOMER") == "client"
    assert normalize_roles(["OWNER", "owner", "MANAGER"]) == ["owner", "manager"]


def test_permission_registry_aliases():
    assert normalize_permission("leads.view") == "crm.read"
    assert normalize_permission("ai.use") == "ai.use"
    assert "crm.read" in expand_permissions(["leads.view", "crm.read"])
    assert "owner.full" in defaults_for_roles(["owner"])


def test_workspace_registry():
    assert "crypto_otc" in WORKSPACE_REGISTRY
    assert normalize_workspace_codes(["crypto", "auto", "beauty"]) == [
        "crypto_otc",
        "auto",
        "cafe_beauty",
    ]


def test_identity_service_exposes_canonical_registries():
    roles = identity_service.list_canonical_roles()
    perms = identity_service.list_canonical_permissions()
    ws = identity_service.list_workspaces()
    assert "owner" in roles["roles"]
    assert "crm.read" in perms["permissions"]
    assert any(w["code"] == "agro" for w in ws["workspaces"])
    status = identity_service.status()
    assert status["sprint"] == "34.2A"
    assert status["identity_core"] is True


@pytest.mark.asyncio
async def test_authenticate_telegram_owner_without_db(monkeypatch):
    monkeypatch.setattr("config.OWNER_ID", 42)

    async def _fail(*_a, **_k):
        raise RuntimeError("db unavailable")

    monkeypatch.setattr(
        "platform_identity.user_resolver.user_resolver.ensure_telegram_user",
        _fail,
    )
    principal = await authentication_service.authenticate_telegram(42)
    assert PlatformRole.OWNER.value in principal.roles or "owner" in principal.roles
    assert principal.telegram_id == 42
    assert "owner.full" in principal.permissions or principal.is_owner


@pytest.mark.asyncio
async def test_jwt_includes_user_id_claim():
    jwt_service.reset()
    tokens = jwt_service.issue_tokens(
        subject="user:abc",
        roles=["owner"],
        permissions=["crm.read"],
        telegram_id=42,
        user_id="11111111-1111-1111-1111-111111111111",
    )
    claims = jwt_service.verify_access_token(tokens.access_token)
    assert claims["user_id"] == "11111111-1111-1111-1111-111111111111"
    assert claims["telegram_id"] == 42
