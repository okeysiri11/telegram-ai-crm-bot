"""Tests — former unauthenticated admin routes must not be exposed."""

from __future__ import annotations

import re
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from platform_management.management_router import register_management_routes
from platform_management.permissions import ManagementRole

ROOT = Path(__file__).resolve().parents[1]
ADMIN_ROUTE_PATTERN = re.compile(
    r"register_(?:sla|managers_pool|assignment|workflow|platform_sdk|configuration)_admin_routes\(app\)"
)

FORMER_ADMIN_PATHS = [
    ("GET", "/api/v1/sla/overdue"),
    ("GET", "/api/v1/sla/risk"),
    ("GET", "/api/v1/sla/statistics"),
    ("GET", "/api/v1/sla/owner-escalated"),
    ("GET", "/api/v1/managers/pool"),
    ("GET", "/api/v1/assignment/statistics"),
    ("GET", "/api/v1/workflows"),
    ("GET", "/api/v1/verticals"),
    ("GET", "/api/v1/configuration"),
]

MANAGEMENT_SLA_PATHS = [
    "/management/v1/sla/overdue",
    "/management/v1/sla/risk",
    "/management/v1/sla/statistics",
    "/management/v1/sla/owner-escalated",
]


@pytest.fixture
def management_app(monkeypatch):
    async def _owner(_tid):
        return ManagementRole.OWNER

    monkeypatch.setattr("platform_management.permissions.resolve_role", _owner)
    app = web.Application()
    register_management_routes(app)
    return app


def test_server_does_not_register_unauthenticated_admin_routes():
    server_text = (ROOT / "api" / "server.py").read_text(encoding="utf-8")
    registrations = ADMIN_ROUTE_PATTERN.findall(server_text)
    assert registrations == []


@pytest.mark.parametrize("method,path", FORMER_ADMIN_PATHS)
def test_former_admin_paths_not_registered_on_management_app(management_app, method, path):
    routes = {(r.method, r.resource.canonical) for r in management_app.router.routes()}
    assert (method, path) not in routes


@pytest.mark.asyncio
@pytest.mark.parametrize("path", MANAGEMENT_SLA_PATHS)
async def test_management_sla_requires_authentication(management_app, path):
    with patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        async with TestClient(TestServer(management_app)) as client:
            resp = await client.get(path)
            assert resp.status == 401
            body = await resp.json()
            assert body["success"] is False


@pytest.mark.asyncio
async def test_management_sla_accessible_with_jwt(management_app, auth_headers):
    stats = {"active": 0, "overdue": 0, "risk": 0, "completed_today": 0, "avg_response_minutes": None}
    with patch(
        "platform_management.management_service.management_service.sla_statistics",
        new=AsyncMock(return_value=stats),
    ), patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        async with TestClient(TestServer(management_app)) as client:
            resp = await client.get("/management/v1/sla/statistics", headers=auth_headers)
            assert resp.status == 200
            body = await resp.json()
            assert body["success"] is True
            assert body["data"] == stats
