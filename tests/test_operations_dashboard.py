"""Tests — Platform Operations Dashboard backend."""

from __future__ import annotations

import asyncio
import time
from unittest.mock import AsyncMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from platform_management.management_router import register_management_routes
from platform_management.permissions import ManagementRole
from platform_operations.dashboard_service import OperationsDashboardService, widget_cache
from platform_operations.models import SharedDashboardContext, WidgetMeta, WidgetPayload, utc_now_iso
from platform_operations.operations_service import operations_service
from platform_operations.widgets import ALL_WIDGET_IDS, get_widget_spec


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


@pytest.fixture(autouse=True)
def _clear_widget_cache():
    widget_cache._memory.clear()
    yield
    widget_cache._memory.clear()


def _sample_dashboard() -> dict:
    widgets = {}
    for wid in ALL_WIDGET_IDS:
        spec = get_widget_spec(wid)
        widgets[wid] = {
            "meta": {
                "widget_id": wid,
                "updated_at": utc_now_iso(),
                "refresh_interval": spec.refresh_interval,
                "status": "ok",
                "cache_hit": False,
                "duration_ms": 1.0,
            },
            "data": {"sample": True},
        }
    return {
        "generated_at": utc_now_iso(),
        "duration_ms": 5.0,
        "cache_hit": False,
        "widgets": widgets,
    }


@pytest.mark.asyncio
async def test_dashboard_endpoint_returns_all_widgets(management_app, actor_header):
    sample = _sample_dashboard()
    with patch(
        "platform_operations.operations_service.operations_service.get_dashboard",
        new_callable=AsyncMock,
        return_value=sample,
    ), patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        async with TestClient(TestServer(management_app)) as client:
            resp = await client.get("/management/dashboard", headers=actor_header)
            assert resp.status == 200
            body = await resp.json()
            assert body["success"] is True
            assert len(body["data"]["widgets"]) == len(ALL_WIDGET_IDS)


@pytest.mark.asyncio
async def test_dashboard_widget_endpoint(management_app, actor_header):
    widget_payload = {
        "meta": {"widget_id": "system_status", "updated_at": utc_now_iso(), "refresh_interval": 30, "status": "ok"},
        "data": {"health": "healthy"},
    }
    with patch(
        "platform_operations.operations_service.operations_service.get_widget",
        new_callable=AsyncMock,
        return_value=widget_payload,
    ), patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        async with TestClient(TestServer(management_app)) as client:
            resp = await client.get(
                "/management/dashboard/widgets/system_status",
                headers=actor_header,
            )
            body = await resp.json()
            assert body["data"]["data"]["health"] == "healthy"


@pytest.mark.asyncio
async def test_dashboard_permissions_denied(management_app, auth_headers, monkeypatch):
    async def _deny(_tid):
        from platform_management.exceptions import ManagementPermissionError

        raise ManagementPermissionError("denied")

    monkeypatch.setattr("platform_management.permissions.resolve_role", _deny)
    with patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        async with TestClient(TestServer(management_app)) as client:
            resp = await client.get("/management/dashboard", headers=auth_headers)
            assert resp.status == 403


@pytest.mark.asyncio
async def test_widget_cache_hit():
    cached = {"meta": {"updated_at": utc_now_iso(), "refresh_interval": 30}, "data": {"cached": True}}
    await widget_cache.set("system_status", cached, ttl_seconds=60)
    payload = await OperationsDashboardService.fetch_widget("system_status", use_cache=True)
    assert payload.meta.cache_hit is True
    assert payload.data == {"cached": True}


@pytest.mark.asyncio
async def test_aggregate_dashboard_parallel():
    async def _fast_builder(_ctx: SharedDashboardContext):
        await asyncio.sleep(0.01)
        return {"ok": True}

    with patch.dict(
        "platform_operations.dashboard_service.WIDGET_BUILDERS",
        {wid: _fast_builder for wid in ALL_WIDGET_IDS},
        clear=False,
    ):
        started = time.perf_counter()
        dashboard = await OperationsDashboardService.aggregate_dashboard(use_cache=False)
        elapsed_ms = (time.perf_counter() - started) * 1000

    assert len(dashboard.widgets) == len(ALL_WIDGET_IDS)
    assert elapsed_ms < 2000
    assert dashboard.cache_hit is False


@pytest.mark.asyncio
async def test_warm_cache_dashboard_under_200ms():
    async def _instant(_ctx):
        return {"v": 1}

    with patch.dict(
        "platform_operations.dashboard_service.WIDGET_BUILDERS",
        {wid: _instant for wid in ALL_WIDGET_IDS},
        clear=False,
    ):
        await OperationsDashboardService.aggregate_dashboard(use_cache=False)
        started = time.perf_counter()
        cached = await OperationsDashboardService.aggregate_dashboard(use_cache=True)
        elapsed_ms = (time.perf_counter() - started) * 1000

    assert cached.cache_hit is True
    assert elapsed_ms < 200


@pytest.mark.asyncio
async def test_system_status_widget_delegates():
    with patch(
        "platform_management.system_info.get_system_info",
        new_callable=AsyncMock,
        return_value={"platform_version": "2.0.0", "uptime_seconds": 100},
    ), patch(
        "platform_management.health.get_health_snapshot",
        new_callable=AsyncMock,
        return_value={"overall_status": "healthy", "event_bus": {}},
    ), patch(
        "platform_management.system_info.get_component_statuses",
        new_callable=AsyncMock,
        return_value={"database": {"status": "healthy"}},
    ):
        payload = await OperationsDashboardService.fetch_widget(
            "system_status",
            use_cache=False,
        )
    assert payload.data["version"] == "2.0.0"
    assert payload.meta.status == "ok"
    assert payload.meta.refresh_interval == 30


@pytest.mark.asyncio
async def test_metrics_endpoint(management_app, actor_header):
    with patch(
        "platform_operations.operations_service.build_metrics",
        new_callable=AsyncMock,
        return_value={"period": "month", "totals": {"requests_created": 10}},
    ), patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        async with TestClient(TestServer(management_app)) as client:
            resp = await client.get("/management/dashboard/metrics?period=month", headers=actor_header)
            body = await resp.json()
            assert body["data"]["totals"]["requests_created"] == 10


@pytest.mark.asyncio
async def test_timeline_endpoints(management_app, actor_header):
    with patch(
        "platform_operations.operations_service.event_timeline",
        new_callable=AsyncMock,
        return_value={"count": 2, "entries": []},
    ), patch(
        "platform_operations.operations_service.audit_timeline",
        new_callable=AsyncMock,
        return_value={"count": 3, "entries": []},
    ), patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        async with TestClient(TestServer(management_app)) as client:
            ev = await client.get("/management/dashboard/timeline/events", headers=actor_header)
            au = await client.get(
                "/management/dashboard/timeline/audit?category=configuration",
                headers=actor_header,
            )
            assert (await ev.json())["data"]["count"] == 2
            assert (await au.json())["data"]["count"] == 3


@pytest.mark.asyncio
async def test_refresh_dashboard(management_app, actor_header):
    with patch(
        "platform_operations.operations_service.operations_service.refresh_dashboard",
        new_callable=AsyncMock,
        return_value=_sample_dashboard(),
    ), patch(
        "platform_management.management_service.management_service.log_request",
        new_callable=AsyncMock,
    ):
        async with TestClient(TestServer(management_app)) as client:
            resp = await client.get("/management/dashboard?refresh=true", headers=actor_header)
            assert resp.status == 200


def test_widget_registry_complete():
    assert len(ALL_WIDGET_IDS) == 26
    for wid in ALL_WIDGET_IDS:
        spec = get_widget_spec(wid)
        assert spec.refresh_interval > 0
        assert spec.ttl_seconds > 0


def test_widget_payload_envelope():
    meta = WidgetMeta(widget_id="test", updated_at=utc_now_iso(), refresh_interval=30)
    payload = WidgetPayload(meta=meta, data={"x": 1})
    body = payload.to_dict()
    assert body["meta"]["widget_id"] == "test"
    assert body["data"]["x"] == 1
