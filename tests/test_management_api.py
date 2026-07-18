"""Tests — Platform Management API."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from platform_management.management_router import register_management_routes
from platform_management.permissions import ManagementRole, resolve_role
from platform_management.response_models import success_response


@pytest.fixture
def management_app():
    app = web.Application()
    register_management_routes(app)
    return app



@pytest.fixture(autouse=True)
def _grant_owner(monkeypatch):
    async def _owner(_tid):
        return ManagementRole.OWNER

    monkeypatch.setattr(
        "platform_management.permissions.resolve_role",
        _owner,
    )


@pytest.mark.asyncio
async def test_system_endpoint_envelope(management_app, actor_header):
    with patch(
        "platform_management.management_service.management_service.system_info",
        new_callable=AsyncMock,
        return_value={"platform_version": "2.0.0", "uptime_seconds": 10},
    ), patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        async with TestClient(TestServer(management_app)) as client:
            resp = await client.get("/management/system", headers=actor_header)
            assert resp.status == 200
            body = await resp.json()
            assert body["success"] is True
            assert body["request_id"]
            assert body["data"]["platform_version"] == "2.0.0"
            assert body["errors"] == []


@pytest.mark.asyncio
async def test_health_endpoint(management_app, actor_header):
    with patch(
        "platform_management.management_service.management_service.health",
        new_callable=AsyncMock,
        return_value={"overall_status": "healthy"},
    ), patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        async with TestClient(TestServer(management_app)) as client:
            resp = await client.get("/management/health", headers=actor_header)
            assert resp.status == 200
            assert (await resp.json())["data"]["overall_status"] == "healthy"


@pytest.mark.asyncio
async def test_permissions_denied_without_actor(management_app, monkeypatch):
    async def _deny(_tid):
        from platform_management.exceptions import ManagementPermissionError

        raise ManagementPermissionError("actor_telegram_id is required")

    monkeypatch.setattr("platform_management.permissions.resolve_role", _deny)
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
async def test_readonly_cannot_mutate_config(management_app, actor_header, monkeypatch):
    async def _readonly(_tid):
        return ManagementRole.READ_ONLY

    monkeypatch.setattr("platform_management.permissions.resolve_role", _readonly)
    with patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        async with TestClient(TestServer(management_app)) as client:
            resp = await client.put(
                "/management/configuration/sla.assignment_sec",
                headers=actor_header,
                json={"value": 100},
            )
            assert resp.status == 403


@pytest.mark.asyncio
async def test_configuration_get_delegates(management_app, actor_header):
    with patch(
        "platform_management.management_service.management_service.config_get",
        new_callable=AsyncMock,
        return_value=900,
    ), patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        async with TestClient(TestServer(management_app)) as client:
            resp = await client.get(
                "/management/configuration/sla.assignment_sec",
                headers=actor_header,
            )
            body = await resp.json()
            assert body["data"]["value"] == 900


@pytest.mark.asyncio
async def test_configuration_set_admin(management_app, actor_header):
    with patch(
        "platform_management.management_service.management_service.config_set",
        new_callable=AsyncMock,
        return_value={"key": "sla.assignment_sec", "value": 600},
    ), patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        async with TestClient(TestServer(management_app)) as client:
            resp = await client.put(
                "/management/configuration/sla.assignment_sec",
                headers=actor_header,
                json={"value": 600},
            )
            assert resp.status == 200
            assert (await resp.json())["data"]["value"] == 600


@pytest.mark.asyncio
async def test_configuration_export_import(management_app, actor_header):
    export_payload = {"entries": {"notifications.enabled": {"value": True}}}
    with patch(
        "platform_management.management_service.management_service.config_export",
        new_callable=AsyncMock,
        return_value=export_payload,
    ), patch(
        "platform_management.management_service.management_service.config_import",
        new_callable=AsyncMock,
        return_value={"imported": 1},
    ), patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        async with TestClient(TestServer(management_app)) as client:
            export_resp = await client.get("/management/configuration/export", headers=actor_header)
            assert export_resp.status == 200
            import_resp = await client.post(
                "/management/configuration/import",
                headers=actor_header,
                json={"payload": export_payload},
            )
            assert import_resp.status == 200
            assert (await import_resp.json())["data"]["imported"] == 1


@pytest.mark.asyncio
async def test_verticals_list(management_app, actor_header):
    with patch(
        "platform_management.management_service.management_service.list_verticals",
        new_callable=AsyncMock,
        return_value=[{"code": "auto", "enabled": True}],
    ), patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        async with TestClient(TestServer(management_app)) as client:
            resp = await client.get("/management/verticals", headers=actor_header)
            assert (await resp.json())["data"]["verticals"][0]["code"] == "auto"


@pytest.mark.asyncio
async def test_audit_search(management_app, actor_header):
    with patch(
        "platform_management.management_service.management_service.audit_search",
        new_callable=AsyncMock,
        return_value=[{"event_type": "REQUEST_CREATED"}],
    ), patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        async with TestClient(TestServer(management_app)) as client:
            resp = await client.get("/management/audit", headers=actor_header)
            assert (await resp.json())["data"]["count"] == 1


@pytest.mark.asyncio
async def test_statistics_requests(management_app, actor_header):
    with patch(
        "platform_management.management_service.management_service.requests_overview",
        new_callable=AsyncMock,
        return_value={"summary": {"overdue": 2}},
    ), patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        async with TestClient(TestServer(management_app)) as client:
            resp = await client.get("/management/requests", headers=actor_header)
            assert (await resp.json())["data"]["summary"]["overdue"] == 2


@pytest.mark.asyncio
async def test_openapi_spec(management_app, auth_headers):
    async with TestClient(TestServer(management_app)) as client:
        unauth = await client.get("/management/openapi.json")
        assert unauth.status == 401
        resp = await client.get("/management/openapi.json", headers=auth_headers)
        assert resp.status == 200
        spec = await resp.json()
        assert spec["openapi"] == "3.0.3"
        assert "/management/system" in spec["paths"]
        assert "ManagementResponse" in spec["components"]["schemas"]
        assert "BearerAuth" in spec["components"]["securitySchemes"]


@pytest.mark.asyncio
async def test_openapi_docs(management_app, auth_headers):
    async with TestClient(TestServer(management_app)) as client:
        unauth = await client.get("/management/docs")
        assert unauth.status == 401
        resp = await client.get("/management/docs", headers=auth_headers)
        assert resp.status == 200
        text = await resp.text()
        assert "swagger-ui" in text


@pytest.mark.asyncio
async def test_feature_flags_crud(management_app, actor_header):
    with patch(
        "platform_management.management_service.management_service.feature_flags_list",
        new_callable=AsyncMock,
        return_value={"feature_flags.verticals.auto": True},
    ), patch(
        "platform_management.management_service.management_service.feature_flag_disable",
        new_callable=AsyncMock,
        return_value={"key": "feature_flags.verticals.auto", "value": False},
    ), patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        async with TestClient(TestServer(management_app)) as client:
            list_resp = await client.get("/management/feature-flags", headers=actor_header)
            assert list_resp.status == 200
            disable_resp = await client.post(
                "/management/feature-flags/verticals.auto/disable",
                headers=actor_header,
            )
            assert disable_resp.status == 200


def test_standard_response_shape():
    resp = success_response({"ok": True}, request_id="req-1")
    import json

    body = json.loads(resp.text)
    assert body["success"] is True
    assert body["request_id"] == "req-1"
    assert body["data"] == {"ok": True}
    assert body["errors"] == []


@pytest.mark.asyncio
async def test_resolve_role_owner(monkeypatch):
    monkeypatch.setattr("config.OWNER_ID", 42)
    with patch(
        "services.pg_platform_permissions_engine.PlatformPermissionsEngineV1.user_has_permission",
        new_callable=AsyncMock,
        return_value=False,
    ):
        role = await resolve_role(42)
        assert role == ManagementRole.OWNER
