"""Sprint Recruiting 2.9 — recruiter directory and attention items on dashboard."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.recruiting_enterprise.api.register import register_recruiting_enterprise_routes
from services.recruiting_ops import reset_recruiting_ops_for_tests

OPS = "/api/recruiting-ops/v1"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_recruiting_enterprise_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_ops():
    reset_recruiting_ops_for_tests()
    yield
    reset_recruiting_ops_for_tests()


def _hdr(org: str, role: str = "recruiter") -> dict[str, str]:
    return {
        "X-Organization-Id": org,
        "X-Role": role,
        "X-Recruiting-Organization-Id": org,
    }


async def test_dashboard_lists_recruiters_and_linkable_attention(client: TestClient):
    org = f"ux-{uuid.uuid4().hex[:8]}"
    h = _hdr(org, "platform_owner")
    stale = (datetime.now(timezone.utc) - timedelta(hours=30)).isoformat()
    created = await client.post(
        f"{OPS}/leads",
        json={"name": "Старый", "email": "old@example.com", "phone": "+380501000020", "submitted_at": stale},
        headers=h,
    )
    assert created.status == 201
    assigned = await client.post(
        f"{OPS}/leads",
        json={"name": "Ира", "email": "ira@example.com", "phone": "+380501000021", "assignee": "Timofii"},
        headers=h,
    )
    assert assigned.status == 201
    dash = await client.get(f"{OPS}/dashboard", headers=h)
    assert dash.status == 200
    body = await dash.json()
    assert "new_leads" in body["cards"]
    labels = {item["id"] for item in body.get("recruiters") or []}
    assert "Timofii" in labels
    kinds = {item["kind"] for item in body.get("attention_items") or []}
    assert "unassigned" in kinds
    assert any(item.get("entity_type") == "lead" and item.get("entity_id") for item in body.get("attention_items") or [])


async def test_unassign_recruiter_persists(client: TestClient):
    org = f"ux-un-{uuid.uuid4().hex[:8]}"
    h = _hdr(org)
    lead = await client.post(
        f"{OPS}/leads",
        json={"name": "Снять", "email": "off@example.com", "phone": "+380501000022", "assignee": "Timofii"},
        headers=h,
    )
    lead_id = (await lead.json())["item"]["id"]
    cleared = await client.post(f"{OPS}/leads/{lead_id}/assign", json={"assignee": ""}, headers=h)
    assert cleared.status == 200
    assert not (await cleared.json())["item"].get("assignee")
