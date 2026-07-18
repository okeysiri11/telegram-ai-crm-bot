"""Tests — SLA Dashboard API."""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from repositories.sla_repository import SLARepository
from routers.admin.sla_router import register_sla_admin_routes
from services.sla_dashboard_service import SlaDashboardService, sla_dashboard_service


@pytest.fixture
async def sla_api_client():
    app = web.Application()
    register_sla_admin_routes(app)
    async with TestClient(TestServer(app)) as client:
        yield client


def _overdue_item(**kwargs) -> dict:
    return {
        "request_id": kwargs.get("request_id", str(uuid.uuid4())),
        "request_number": kwargs.get("request_number", "REALTY-00123"),
        "manager": kwargs.get("manager", "Lucifer"),
        "vertical": kwargs.get("vertical", "REALTY"),
        "deadline": kwargs.get("deadline", datetime.now(timezone.utc).isoformat()),
        "escalation_level": kwargs.get("escalation_level", 1),
        "minutes_overdue": kwargs.get("minutes_overdue", 41),
    }


def _risk_item(**kwargs) -> dict:
    return {
        "request_id": kwargs.get("request_id", str(uuid.uuid4())),
        "request_number": kwargs.get("request_number", "AUTO-00045"),
        "manager": kwargs.get("manager", "Boroda"),
        "vertical": kwargs.get("vertical", "AUTO"),
        "deadline": kwargs.get("deadline", (datetime.now(timezone.utc) + timedelta(minutes=20)).isoformat()),
        "escalation_level": 0,
        "minutes_remaining": kwargs.get("minutes_remaining", 20),
    }


@pytest.mark.asyncio
async def test_api_overdue(sla_api_client):
    items = [_overdue_item()]
    with patch.object(SlaDashboardService, "get_overdue", new=AsyncMock(return_value=items)):
        resp = await sla_api_client.get("/api/v1/sla/overdue")
        assert resp.status == 200
        data = await resp.json()
        assert len(data) == 1
        assert data[0]["request_number"] == "REALTY-00123"
        assert data[0]["manager"] == "Lucifer"
        assert data[0]["minutes_overdue"] == 41


@pytest.mark.asyncio
async def test_api_risk(sla_api_client):
    items = [_risk_item()]
    with patch.object(SlaDashboardService, "get_at_risk", new=AsyncMock(return_value=items)):
        resp = await sla_api_client.get("/api/v1/sla/risk")
        assert resp.status == 200
        data = await resp.json()
        assert data[0]["vertical"] == "AUTO"
        assert data[0]["minutes_remaining"] == 20


@pytest.mark.asyncio
async def test_api_statistics(sla_api_client):
    stats = {
        "active": 183,
        "overdue": 7,
        "risk": 12,
        "completed_today": 44,
        "avg_response_minutes": 18.0,
    }
    with patch.object(SlaDashboardService, "get_statistics", new=AsyncMock(return_value=stats)):
        resp = await sla_api_client.get("/api/v1/sla/statistics")
        assert resp.status == 200
        data = await resp.json()
        assert data["active"] == 183
        assert data["overdue"] == 7
        assert data["risk"] == 12
        assert data["completed_today"] == 44
        assert data["avg_response_minutes"] == 18.0


@pytest.mark.asyncio
async def test_api_empty_database(sla_api_client):
    empty_stats = {
        "active": 0,
        "overdue": 0,
        "risk": 0,
        "completed_today": 0,
        "avg_response_minutes": None,
    }
    with patch.object(SlaDashboardService, "get_overdue", new=AsyncMock(return_value=[])), patch.object(
        SlaDashboardService, "get_at_risk", new=AsyncMock(return_value=[])
    ), patch.object(SlaDashboardService, "get_statistics", new=AsyncMock(return_value=empty_stats)):
        overdue = await (await sla_api_client.get("/api/v1/sla/overdue")).json()
        risk = await (await sla_api_client.get("/api/v1/sla/risk")).json()
        stats = await (await sla_api_client.get("/api/v1/sla/statistics")).json()

    assert overdue == []
    assert risk == []
    assert stats["active"] == 0
    assert stats["avg_response_minutes"] is None


@pytest.mark.asyncio
async def test_service_delegates_to_repository():
    mock_repo = AsyncMock()
    mock_repo.get_overdue_requests.return_value = [_overdue_item()]
    mock_repo.get_risk_requests.return_value = [_risk_item(vertical="AGRO", request_number="AGRO-00001")]
    mock_repo.get_sla_statistics.return_value = {
        "active": 2,
        "overdue": 1,
        "risk": 1,
        "completed_today": 0,
        "avg_response_minutes": 12.5,
    }

    mock_cm = AsyncMock()
    mock_cm.__aenter__.return_value = AsyncMock()
    mock_cm.__aexit__.return_value = None

    with patch("services.sla_dashboard_service.get_session", return_value=mock_cm), patch(
        "services.sla_dashboard_service.SLARepository",
        return_value=mock_repo,
    ):
        overdue = await sla_dashboard_service.get_overdue()
        risk = await sla_dashboard_service.get_at_risk()
        stats = await sla_dashboard_service.get_statistics()

    assert overdue[0]["vertical"] == "REALTY"
    assert risk[0]["vertical"] == "AGRO"
    assert stats["active"] == 2
    mock_repo.get_overdue_requests.assert_awaited_once()
    mock_repo.get_risk_requests.assert_awaited_once()
    mock_repo.get_sla_statistics.assert_awaited_once()


@pytest.mark.asyncio
async def test_multiple_verticals_in_overdue():
    items = [
        _overdue_item(vertical="REALTY", request_number="REALTY-00001"),
        _overdue_item(vertical="AUTO", request_number="AUTO-00002", manager="Boroda"),
        _overdue_item(vertical="AGRO", request_number="AGRO-00003", manager="Chris"),
    ]
    with patch.object(SlaDashboardService, "get_overdue", new=AsyncMock(return_value=items)):
        app = web.Application()
        register_sla_admin_routes(app)
        async with TestClient(TestServer(app)) as client:
            data = await (await client.get("/api/v1/sla/overdue")).json()

    verticals = {item["vertical"] for item in data}
    assert verticals == {"REALTY", "AUTO", "AGRO"}


@pytest.mark.asyncio
async def test_repository_serialize_overdue_and_risk():
    now = datetime.now(timezone.utc)
    sla_row = MagicMock()
    sla_row.request_id = uuid.uuid4()
    sla_row.manager_id = 123456
    sla_row.first_response_deadline = now - timedelta(minutes=41)
    sla_row.escalation_level = 1

    repo = SLARepository(AsyncMock())
    repo._load_request_context = AsyncMock(
        return_value={
            "request_number": "REALTY-00123",
            "vertical": "REALTY",
            "manager": "Lucifer",
        }
    )

    overdue = await repo._serialize_sla_row(sla_row, now=now, include_overdue=True)
    risk_row = MagicMock()
    risk_row.request_id = uuid.uuid4()
    risk_row.manager_id = 123456
    risk_row.first_response_deadline = now + timedelta(minutes=25)
    risk_row.escalation_level = 0
    risk = await repo._serialize_sla_row(risk_row, now=now, include_risk=True)

    assert overdue["minutes_overdue"] == 41
    assert risk["minutes_remaining"] == 25


@pytest.mark.asyncio
@pytest.mark.skipif(
    os.getenv("RUN_SLA_PG_INTEGRATION") != "1",
    reason="PostgreSQL integration — set RUN_SLA_PG_INTEGRATION=1 and migrate request_sla",
)
async def test_postgres_statistics_empty_or_real():
    stats = await sla_dashboard_service.get_statistics()
    assert "active" in stats
    assert "overdue" in stats
    assert "risk" in stats
    assert "completed_today" in stats
    assert "avg_response_minutes" in stats
    assert stats["active"] >= 0
