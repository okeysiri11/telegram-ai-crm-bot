"""Tests — Platform API v1.0 freeze (versioning, contracts, OpenAPI, deprecation)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer
from pydantic import ValidationError

from api.server import create_app
from platform_api.contracts import API_CONTRACT_VERSION, PLATFORM_API_VERSION
from platform_api.responses import ApiEnvelope
from platform_management.management_router import register_management_routes
from platform_management.permissions import ManagementRole
from platform_plugin_sdk.plugin_api import ManagementApi


@pytest.fixture
def management_app():
    app = web.Application()
    register_management_routes(app)
    return app


@pytest.fixture(autouse=True)
def _grant_owner(monkeypatch):
    async def _owner(_tid):
        return ManagementRole.OWNER

    monkeypatch.setattr("platform_management.permissions.resolve_role", _owner)


@pytest.mark.asyncio
async def test_management_v1_route_exists(management_app, actor_header):
    with patch(
        "platform_management.management_service.management_service.system_info",
        new_callable=AsyncMock,
        return_value={"platform_version": "2.0.0"},
    ), patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        async with TestClient(TestServer(management_app)) as client:
            resp = await client.get("/management/v1/system", headers=actor_header)
            assert resp.status == 200
            body = await resp.json()
            envelope = ApiEnvelope.model_validate(body)
            assert envelope.success is True
            assert envelope.api_version == PLATFORM_API_VERSION
            assert envelope.contract_version == API_CONTRACT_VERSION
            assert envelope.request_id


@pytest.mark.asyncio
async def test_legacy_management_route_returns_deprecation_headers(management_app, actor_header):
    with patch(
        "platform_management.management_service.management_service.system_info",
        new_callable=AsyncMock,
        return_value={"platform_version": "2.0.0"},
    ), patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        async with TestClient(TestServer(management_app)) as client:
            resp = await client.get("/management/system", headers=actor_header)
            assert resp.status == 200
            assert "Deprecation" in resp.headers
            assert resp.headers.get("X-API-Successor") == "/management/v1/system"


@pytest.mark.asyncio
async def test_management_v1_openapi_protected_and_versioned(management_app, auth_headers):
    with patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        async with TestClient(TestServer(management_app)) as client:
            unauth = await client.get("/management/v1/openapi.json")
            assert unauth.status == 401

            resp = await client.get("/management/v1/openapi.json", headers=auth_headers)
            assert resp.status == 200
            spec = await resp.json()
            assert spec["info"]["version"] == API_CONTRACT_VERSION
            assert "/management/v1/system" in spec["paths"]
            assert "/management/system" not in spec["paths"]
            assert "ApiEnvelope" in spec["components"]["schemas"]


@pytest.mark.asyncio
async def test_management_v1_docs_protected(management_app, auth_headers):
    with patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        async with TestClient(TestServer(management_app)) as client:
            assert (await client.get("/management/v1/docs")).status == 401
            resp = await client.get("/management/v1/docs", headers=auth_headers)
            assert resp.status == 200
            text = await resp.text()
            assert "/management/v1/openapi.json" in text


@pytest.mark.asyncio
async def test_public_api_v1_health_envelope():
    app = create_app()
    async with TestClient(TestServer(app)) as client:
        resp = await client.get("/api/v1")
        assert resp.status == 200
        body = await resp.json()
        envelope = ApiEnvelope.model_validate(body)
        assert envelope.success is True
        assert envelope.data["api_version"] == "v1"


@pytest.mark.asyncio
async def test_legacy_public_route_deprecation():
    app = create_app()
    async with TestClient(TestServer(app)) as client:
        resp = await client.get("/v1")
        assert resp.status in {200, 401, 403}
        assert "Deprecation" in resp.headers
        assert resp.headers.get("X-API-Successor") == "/api/v1"


@pytest.mark.asyncio
async def test_public_openapi_lists_v1_paths_only():
    app = create_app()
    async with TestClient(TestServer(app)) as client:
        resp = await client.get("/api/v1/openapi.json")
        assert resp.status == 200
        spec = await resp.json()
        assert spec["info"]["version"] == API_CONTRACT_VERSION
        assert any(path.startswith("/api/v1/") for path in spec["paths"])
        assert "/v1/deals" not in spec["paths"]


def test_api_envelope_rejects_anonymous_shape():
    with pytest.raises(ValidationError):
        ApiEnvelope.model_validate({"ok": True, "data": {}})


def test_plugin_sdk_references_frozen_management_api():
    assert ManagementApi.PREFIX == "/management/v1"
    assert ManagementApi.VERSION == "v1"
    assert ManagementApi.path("plugins/install") == "/management/v1/plugins/install"


def test_plugin_sdk_has_no_internal_imports():
    import ast
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "platform_plugin_sdk"
    forbidden = ("repositories", "database", "platform_ai.providers", "services.pg_")
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for prefix in forbidden:
                    assert not node.module.startswith(prefix), f"{path.name} imports {node.module}"
