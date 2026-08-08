"""Sprint 40.2 — Public /api/v1 CRM foundation (leads, clients, CRM deals, reports)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from api.v1 import register_api_v1_routes
from applications.auto_marketplace import auto_marketplace
from services.pg_api_gateway_engine import ApiAuthContext, ApiAuthenticationError


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_api_v1_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_crm_store():
    auto_marketplace.reset()
    yield
    auto_marketplace.reset()


@pytest.fixture
def auth_ctx() -> ApiAuthContext:
    return ApiAuthContext(
        client_id=uuid4(),
        client_code="sprint-40-2",
        permissions={
            "lead.read",
            "lead.write",
            "client.read",
            "client.write",
            "deal.read",
            "deal.write",
            "report.read",
        },
        actor_user_id=1,
        auth_method="test",
    )


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {"Authorization": "Bearer test-token-40-2"}


@pytest.fixture(autouse=True)
def mock_gateway(auth_ctx: ApiAuthContext):
    with patch(
        "api.middleware.ApiGatewayEngineV1.authenticate_request",
        new_callable=AsyncMock,
        return_value=auth_ctx,
    ), patch(
        "api.middleware.ApiGatewayEngineV1.check_rate_limit",
        new_callable=AsyncMock,
    ), patch(
        "api.middleware.ApiGatewayEngineV1.log_request",
        new_callable=AsyncMock,
    ):
        yield


@pytest.mark.asyncio
async def test_leads_crud_and_validation(client: TestClient, auth_headers):
    bad = await client.post(
        "/api/v1/leads",
        json={"source": "not-a-real-source"},
        headers=auth_headers,
    )
    assert bad.status == 400

    created = await client.post(
        "/api/v1/leads",
        json={"source": "web", "notes": "GlobeFly", "utm_source": "site"},
        headers=auth_headers,
    )
    assert created.status == 201
    body = await created.json()
    assert body["success"] is True
    lead_id = body["data"]["lead_id"]
    assert body["data"]["metadata"]["utm_source"] == "site"

    listed = await client.get(
        "/api/v1/leads?page=1&page_size=10&sort=created_at&order=desc",
        headers=auth_headers,
    )
    assert listed.status == 200
    listed_body = await listed.json()
    assert listed_body["data"]["pagination"]["total"] >= 1

    got = await client.get(f"/api/v1/leads/{lead_id}", headers=auth_headers)
    assert got.status == 200

    patched = await client.patch(
        f"/api/v1/leads/{lead_id}",
        json={"notes": "updated", "status": "contacted"},
        headers=auth_headers,
    )
    assert patched.status == 200
    assert (await patched.json())["data"]["notes"] == "updated"

    missing = await client.get("/api/v1/leads/does-not-exist", headers=auth_headers)
    assert missing.status == 404

    deleted = await client.delete(f"/api/v1/leads/{lead_id}", headers=auth_headers)
    assert deleted.status == 200
    assert (await deleted.json())["data"]["deleted"] is True


@pytest.mark.asyncio
async def test_clients_crud(client: TestClient, auth_headers):
    created = await client.post(
        "/api/v1/clients",
        json={"first_name": "Ada", "last_name": "Lovelace", "email": "ada@example.com"},
        headers=auth_headers,
    )
    assert created.status == 201
    client_id = (await created.json())["data"]["client_id"]

    listed = await client.get("/api/v1/clients?email=ada@example.com", headers=auth_headers)
    assert listed.status == 200
    assert (await listed.json())["data"]["pagination"]["total"] == 1

    patched = await client.patch(
        f"/api/v1/clients/{client_id}",
        json={"phone": "+100"},
        headers=auth_headers,
    )
    assert patched.status == 200
    assert (await patched.json())["data"]["phone"] == "+100"

    deleted = await client.delete(f"/api/v1/clients/{client_id}", headers=auth_headers)
    assert deleted.status == 200


@pytest.mark.asyncio
async def test_crm_deals_crud(client: TestClient, auth_headers):
    created = await client.post(
        "/api/v1/crm/deals",
        json={"customer_id": "c1", "amount": 12000, "stage": "prospect"},
        headers=auth_headers,
    )
    assert created.status == 201
    deal_id = (await created.json())["data"]["deal_id"]

    listed = await client.get("/api/v1/crm/deals?stage=prospect", headers=auth_headers)
    assert listed.status == 200

    patched = await client.patch(
        f"/api/v1/crm/deals/{deal_id}",
        json={"stage": "negotiation"},
        headers=auth_headers,
    )
    assert patched.status == 200
    assert (await patched.json())["data"]["stage"] == "negotiation"

    bad_stage = await client.patch(
        f"/api/v1/crm/deals/{deal_id}",
        json={"stage": "not-a-stage"},
        headers=auth_headers,
    )
    assert bad_stage.status == 400

    deleted = await client.delete(f"/api/v1/crm/deals/{deal_id}", headers=auth_headers)
    assert deleted.status == 200


@pytest.mark.asyncio
async def test_reports_endpoints(client: TestClient, auth_headers):
    catalog = await client.get("/api/v1/reports", headers=auth_headers)
    assert catalog.status == 200
    items = (await catalog.json())["data"]["items"]
    assert {i["id"] for i in items} >= {"pipeline", "forecast", "conversion", "crm-metrics"}

    for report_id in ("pipeline", "forecast", "conversion", "crm-metrics"):
        resp = await client.get(f"/api/v1/reports/{report_id}", headers=auth_headers)
        assert resp.status == 200, await resp.text()
        body = await resp.json()
        assert body["success"] is True
        assert body["data"]["report_id"] == report_id

    missing = await client.get("/api/v1/reports/unknown-report", headers=auth_headers)
    assert missing.status == 404


@pytest.mark.asyncio
async def test_leads_require_auth(client: TestClient):
    with patch(
        "api.middleware.ApiGatewayEngineV1.authenticate_request",
        new_callable=AsyncMock,
        side_effect=ApiAuthenticationError("Missing authentication credentials"),
    ):
        resp = await client.get("/api/v1/leads")
        assert resp.status == 401


@pytest.mark.asyncio
async def test_openapi_includes_crm_paths(client: TestClient):
    resp = await client.get("/api/v1/openapi.json")
    assert resp.status == 200
    spec = await resp.json()
    paths = spec["paths"]
    assert "/api/v1/leads" in paths
    assert "/api/v1/clients" in paths
    assert "/api/v1/reports" in paths
    assert "/api/v1/crm/deals" in paths
    assert "/api/v1/deals/{deal_id}" in paths


@pytest.mark.asyncio
async def test_docs_and_no_501_on_leads(client: TestClient, auth_headers):
    docs = await client.get("/api/v1/docs")
    assert docs.status == 200
    assert "swagger" in (await docs.text()).lower()

    resp = await client.get("/api/v1/leads", headers=auth_headers)
    assert resp.status == 200
    assert resp.status != 501


@pytest.mark.asyncio
async def test_rbac_denies_missing_permission(client: TestClient, auth_headers):
    restricted = ApiAuthContext(
        client_id=uuid4(),
        client_code="no-leads",
        permissions={"deal.read"},
        actor_user_id=1,
        auth_method="test",
    )
    with patch(
        "api.middleware.ApiGatewayEngineV1.authenticate_request",
        new_callable=AsyncMock,
        return_value=restricted,
    ):
        resp = await client.get("/api/v1/leads", headers=auth_headers)
        assert resp.status == 403
