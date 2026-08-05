"""Sprint 30.0 — Security & governance hardening tests."""

from __future__ import annotations

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from platform_security.consent import ConsentRequiredError, consent_registry, require_likeness_consent
from platform_security.jwt_secrets import is_insecure_secret, normalize_jwt_secrets, validate_signing_secret
from platform_security.permission_engine import PermissionContext, permission_resolver
from repositories.tenant_scope import TenantIsolationError, apply_tenant_filter, require_tenant_id


def test_normalize_jwt_secrets_prefers_iam():
    jwt_s, iam_s = normalize_jwt_secrets(
        jwt_secret="change-me-in-production",
        iam_secret="secure-iam-secret-value-32chars!!",
    )
    assert iam_s == "secure-iam-secret-value-32chars!!"
    assert jwt_s == iam_s


def test_normalize_jwt_secrets_mirrors_jwt_when_iam_insecure():
    jwt_s, iam_s = normalize_jwt_secrets(
        jwt_secret="secure-jwt-secret-value-32chars!!!",
        iam_secret="change-me-in-production",
    )
    assert jwt_s == "secure-jwt-secret-value-32chars!!!"
    assert iam_s == jwt_s


def test_is_insecure_secret():
    assert is_insecure_secret("change-me-in-production")
    assert is_insecure_secret("")
    assert not is_insecure_secret("a-real-secret-key-here")


def test_validate_signing_secret_rejects_default(monkeypatch):
    monkeypatch.setenv("IAM_JWT_SECRET", "change-me-in-production")
    monkeypatch.setenv("JWT_SECRET", "change-me-in-production")
    from platform_configuration.configuration_center import configuration_center
    from platform_configuration.env_source import load_environment

    load_environment.cache_clear()
    configuration_center._settings = None
    configuration_center.load(overrides={"environment": "development"})
    with pytest.raises(RuntimeError, match="IAM_JWT_SECRET"):
        validate_signing_secret()


def test_tenant_require_raises():
    with pytest.raises(TenantIsolationError):
        require_tenant_id(None)


def test_apply_tenant_filter_required(monkeypatch):
    class Model:
        tenant_id = object()

    class FakeSelect:
        def where(self, *_a, **_k):
            return self

    with pytest.raises(TenantIsolationError):
        apply_tenant_filter(FakeSelect(), Model, None, required=True)


def test_permission_engine_allows_star():
    ctx = PermissionContext(principal_id="p1", roles=["owner"], permissions=["*"])
    assert permission_resolver.allow(ctx, "workflow.execute") is True
    permission_resolver.cache.clear()


def test_consent_gate_blocks_without_record():
    consent_registry.clear()
    with pytest.raises(ConsentRequiredError):
        require_likeness_consent(subject_id="user-1", purpose="avatar")
    consent_registry.grant(subject_id="user-1", purpose="avatar", granted_by="admin")
    record = require_likeness_consent(subject_id="user-1", purpose="avatar")
    assert record.subject_id == "user-1"


@pytest.mark.asyncio
async def test_security_middleware_adds_request_id_and_headers():
    from middleware.security_middleware import (
        request_id_middleware,
        secure_headers_middleware,
    )

    async def ok(_request):
        return web.json_response({"ok": True})

    app = web.Application(middlewares=[request_id_middleware, secure_headers_middleware])
    app.router.add_get("/ping", ok)
    async with TestClient(TestServer(app)) as client:
        resp = await client.get("/ping")
        assert resp.status == 200
        assert resp.headers.get("X-Request-Id")
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"


@pytest.mark.asyncio
async def test_platform_builder_header_auth_still_works_in_dev(monkeypatch):
    monkeypatch.setenv("ALLOW_HEADER_AUTH", "true")
    monkeypatch.setenv("ENVIRONMENT", "development")
    from platform_configuration.configuration_center import configuration_center
    from platform_configuration.env_source import load_environment

    load_environment.cache_clear()
    configuration_center._settings = None
    configuration_center.load(overrides={"environment": "development"})

    from applications.platform_builder.api.middleware import auth_middleware

    async def ok(request):
        return web.json_response(
            {
                "principal": request.get("principal"),
                "role": request.get("platform_role"),
                "auth_source": request.get("auth_source"),
            }
        )

    app = web.Application(middlewares=[auth_middleware])
    app.router.add_get("/x", ok)
    async with TestClient(TestServer(app)) as client:
        resp = await client.get("/x", headers={"X-Platform-Role": "platform_owner"})
        assert resp.status == 200
        body = await resp.json()
        assert body["role"] == "platform_owner"
        assert body["auth_source"] == "header_compat"
