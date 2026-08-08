"""Sprint 40.1 — Critical CRM API readiness fixes (LeadSource 400 + mutating auth)."""

from __future__ import annotations

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.register import register_auto_marketplace_routes


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_auto_marketplace_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    auto_marketplace.reset()
    yield
    auto_marketplace.reset()


AUTH = {"Authorization": "Bearer test-token-40-1"}


@pytest.mark.asyncio
async def test_invalid_lead_source_returns_400(client: TestClient):
    resp = await client.post(
        "/api/auto/v1/crm/leads",
        json={"name": "Bad", "source": "not-a-real-source"},
        headers=AUTH,
    )
    assert resp.status == 400
    body = await resp.json()
    assert "invalid lead source" in body.get("error", "").lower()


@pytest.mark.asyncio
async def test_valid_lead_source_returns_201(client: TestClient):
    resp = await client.post(
        "/api/auto/v1/crm/leads",
        json={"source": "web", "notes": "ok", "utm_source": "globefly"},
        headers=AUTH,
    )
    assert resp.status == 201
    body = await resp.json()
    assert body.get("source") == "web"


@pytest.mark.asyncio
async def test_missing_lead_returns_404(client: TestClient):
    # next-action uses leads.get → NotFoundError → 404
    resp = await client.get(
        "/api/auto/v1/crm/leads/does-not-exist-zzzz/next-action",
        headers=AUTH,
    )
    assert resp.status == 404
    body = await resp.json()
    assert "not found" in body.get("error", "").lower()


@pytest.mark.asyncio
async def test_qualify_without_auth_returns_401(client: TestClient):
    resp = await client.post(
        "/api/auto/v1/crm/leads/does-not-exist-zzzz/qualify",
        json={"agent_id": "a1"},
    )
    assert resp.status == 401



@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method,path,payload",
    [
        ("POST", "/api/auto/v1/crm/leads", {"source": "web"}),
        ("POST", "/api/auto/v1/crm/deals", {"title": "x", "stage": "prospect"}),
        ("POST", "/api/auto/v1/crm/customers", {"first_name": "A"}),
        ("POST", "/api/auto/v1/crm/tasks", {"title": "t"}),
        ("POST", "/api/auto/v1/crm/activities/calls", {"customer_id": "c1"}),
        ("POST", "/api/auto/v1/crm/activities/emails", {"customer_id": "c1"}),
        ("POST", "/api/auto/v1/crm/calendar/meetings", {"title": "m"}),
        ("POST", "/api/auto/v1/crm/requests", {"buyer_id": "b1"}),
        ("POST", "/api/auto/v1/crm/appointments", {"buyer_id": "b1"}),
        ("POST", "/api/auto/v1/crm/negotiations", {"buyer_id": "b1"}),
        ("POST", "/api/auto/v1/crm/reservations", {"vehicle_id": "v1"}),
    ],
)
async def test_mutating_crm_requires_auth(client: TestClient, method: str, path: str, payload: dict):
    resp = await client.request(method, path, json=payload)
    assert resp.status == 401, await resp.text()


@pytest.mark.asyncio
async def test_get_crm_remains_readable_without_auth(client: TestClient):
    # Current policy: GET stays available for read permissions with default role.
    resp = await client.get("/api/auto/v1/crm/pipeline")
    assert resp.status == 200


@pytest.mark.asyncio
async def test_invalid_deal_stage_filter_returns_400(client: TestClient):
    resp = await client.get("/api/auto/v1/crm/deals?stage=not-a-stage")
    assert resp.status == 400
