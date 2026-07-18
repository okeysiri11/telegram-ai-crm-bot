"""Tests — Management API production security (JWT / API key)."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import AsyncMock, patch

import jwt
import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from platform_identity.api_keys import api_key_service
from platform_identity.exceptions import AuthenticationError
from platform_identity.jwt_service import get_jwt_secret, jwt_service
from platform_identity.models import PlatformRole
from platform_management.management_router import register_management_routes
from platform_management.permissions import ManagementRole


@pytest.fixture
def management_app():
    app = web.Application()
    register_management_routes(app)
    return app


@pytest.mark.asyncio
async def test_jwt_success(management_app, auth_headers):
    with patch(
        "platform_management.management_service.management_service.system_info",
        new_callable=AsyncMock,
        return_value={"platform_version": "2.0.0"},
    ), patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        async with TestClient(TestServer(management_app)) as client:
            resp = await client.get("/management/system", headers=auth_headers)
            assert resp.status == 200
            body = await resp.json()
            assert body["success"] is True


@pytest.mark.asyncio
async def test_jwt_fail_missing_token(management_app):
    with patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        async with TestClient(TestServer(management_app)) as client:
            resp = await client.get("/management/system")
            assert resp.status == 401
            body = await resp.json()
            assert body["success"] is False


@pytest.mark.asyncio
async def test_jwt_fail_telegram_header_not_accepted(management_app):
    with patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        async with TestClient(TestServer(management_app)) as client:
            resp = await client.get(
                "/management/system",
                headers={"X-Actor-Telegram-Id": "42"},
            )
            assert resp.status == 401


@pytest.mark.asyncio
async def test_api_key_success(management_app, api_key_headers, monkeypatch):
    async def _readonly(_tid):
        return ManagementRole.READ_ONLY

    monkeypatch.setattr("platform_management.permissions.resolve_role", _readonly)
    with patch(
        "platform_management.management_service.management_service.system_info",
        new_callable=AsyncMock,
        return_value={"platform_version": "2.0.0"},
    ), patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        async with TestClient(TestServer(management_app)) as client:
            resp = await client.get("/management/system", headers=api_key_headers)
            assert resp.status == 200


@pytest.mark.asyncio
async def test_docs_unauthorized(management_app):
    with patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        async with TestClient(TestServer(management_app)) as client:
            docs = await client.get("/management/v1/docs")
            assert docs.status == 401
            openapi = await client.get("/management/v1/openapi.json")
            assert openapi.status == 401


@pytest.mark.asyncio
async def test_docs_authorized(management_app, auth_headers):
    with patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        async with TestClient(TestServer(management_app)) as client:
            resp = await client.get("/management/v1/openapi.json", headers=auth_headers)
            assert resp.status == 200
            spec = await resp.json()
            assert spec["components"]["securitySchemes"]["BearerAuth"]


@pytest.mark.asyncio
async def test_expired_token(management_app, monkeypatch):
    from datetime import datetime, timezone

    monkeypatch.setattr("config.OWNER_ID", 42)
    jwt_service.reset()
    secret = get_jwt_secret()
    expired_payload = {
        "sub": "telegram:42",
        "roles": [PlatformRole.OWNER.value],
        "permissions": ["management.read"],
        "token_type": "access",
        "jti": "expired-test",
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        "iat": datetime.now(timezone.utc) - timedelta(hours=2),
        "telegram_id": 42,
    }
    token = jwt.encode(expired_payload, secret, algorithm="HS256")
    headers = {"Authorization": f"Bearer {token}"}

    with patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        async with TestClient(TestServer(management_app)) as client:
            resp = await client.get("/management/system", headers=headers)
            assert resp.status == 401


@pytest.mark.asyncio
async def test_login_requires_proof(management_app, login_proof):
    async with TestClient(TestServer(management_app)) as client:
        resp = await client.post(
            "/management/identity/login",
            json={"telegram_id": 42},
        )
        assert resp.status == 401

        ok = await client.post(
            "/management/identity/login",
            json={"telegram_id": 42, "login_proof": login_proof},
        )
        assert ok.status == 200
        body = await ok.json()
        assert body["success"] is True
        assert body["data"]["access_token"]


@pytest.mark.asyncio
async def test_login_rejects_arbitrary_id_without_proof(management_app):
    async with TestClient(TestServer(management_app)) as client:
        resp = await client.post(
            "/management/identity/login",
            json={"telegram_id": 999999},
        )
        assert resp.status == 401


@pytest.mark.asyncio
async def test_jwt_secret_validation_fails_on_default():
    from platform_configuration.configuration_center import configuration_center
    from platform_configuration.env_source import load_environment
    from platform_identity.jwt_service import validate_iam_jwt_secret

    import os

    old = os.environ.get("IAM_JWT_SECRET")
    try:
        os.environ["IAM_JWT_SECRET"] = "change-me-in-production"
        load_environment.cache_clear()
        configuration_center.reload()
        with pytest.raises(RuntimeError):
            validate_iam_jwt_secret()
    finally:
        if old is None:
            os.environ.pop("IAM_JWT_SECRET", None)
        else:
            os.environ["IAM_JWT_SECRET"] = old
        load_environment.cache_clear()
        configuration_center.reload()


@pytest.mark.asyncio
async def test_authenticate_request_rejects_telegram_header():
    from unittest.mock import MagicMock

    from platform_identity.authentication import authentication_service

    request = MagicMock()
    request.headers.get = lambda key, default="": {
        "Authorization": "",
        "X-API-Key": "",
        "X-Actor-Telegram-Id": "42",
        "User-Agent": "test",
        "X-Forwarded-For": "",
    }.get(key, default)
    request.query.get = lambda key, default=None: default
    request.transport = None

    with pytest.raises(AuthenticationError):
        await authentication_service.authenticate_request(request)


@pytest.mark.asyncio
async def test_config_diagnostics_endpoint(management_app, auth_headers):
    with patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        async with TestClient(TestServer(management_app)) as client:
            resp = await client.get("/management/v1/config", headers=auth_headers)
            assert resp.status == 200
            body = await resp.json()
            assert body["success"] is True
            assert "settings" in body["data"]
            assert "diagnostics" in body["data"]
            assert "feature_flags" in body["data"]["settings"]
            assert body["data"]["settings"]["redis"]["url"] == "***"
