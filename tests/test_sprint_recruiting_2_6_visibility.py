"""Sprint Recruiting 2.6 — Vanguard ingest write identity vs recruiter read identity."""

from __future__ import annotations

import json
import time
import uuid

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.recruiting_enterprise.api.register import register_recruiting_enterprise_routes
from services.recruiting_ops import reset_recruiting_ops_for_tests
from services.recruiting_ops.ingest_auth import DEV_FALLBACK_SECRET, sign_ingest_body
from services.recruiting_ops.projects import canonical_vanguard_org

OPS = "/api/recruiting-ops/v1"
INGEST = f"{OPS}/vanguard/leads"


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
def reset_ops(monkeypatch):
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("VANGUARD_INGEST_SECRET", DEV_FALLBACK_SECRET)
    monkeypatch.delenv("VANGUARD_ORGANIZATION_ID", raising=False)
    reset_recruiting_ops_for_tests()
    yield
    reset_recruiting_ops_for_tests()


def _hdr(org: str, role: str = "platform_owner", extra: dict[str, str] | None = None) -> dict[str, str]:
    headers = {"X-Organization-Id": org, "X-Role": role}
    if extra:
        headers.update(extra)
    return headers


def _website_payload(**overrides) -> dict:
    submission = overrides.pop("external_id", None) or f"sub-{uuid.uuid4().hex[:12]}"
    payload = {
        "name": "Ada Lovelace",
        "email": f"ada.{uuid.uuid4().hex[:8]}@example.com",
        "phone": "+44 7700 900123",
        "country": "United Kingdom",
        "preferred_language": "en",
        "program_of_interest": "logistics",
        "application_message": "I want to train.",
        "contact_consent": True,
        "source": "vanguard-global",
        "project_key": "vanguard",
        "external_id": submission,
        "idempotency_key": submission,
    }
    payload.update(overrides)
    return payload


def _signed(body: dict, *, secret: str = DEV_FALLBACK_SECRET) -> tuple[bytes, dict[str, str]]:
    raw = json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ts = str(time.time())
    nn = uuid.uuid4().hex
    sig = sign_ingest_body(body=raw, timestamp=ts, nonce=nn, secret=secret)
    return raw, {
        "Content-Type": "application/json",
        "X-Vanguard-Signature": sig,
        "X-Vanguard-Timestamp": ts,
        "X-Vanguard-Nonce": nn,
    }


async def _ingest(client: TestClient, body: dict | None = None) -> dict:
    payload = body or _website_payload()
    raw, headers = _signed(payload)
    res = await client.post(INGEST, data=raw, headers=headers)
    assert res.status == 201, await res.text()
    data = await res.json()
    assert data["ok"] is True
    return data["item"]


async def test_hmac_ingest_still_returns_201_without_jwt(client: TestClient):
    item = await _ingest(client)
    assert item["project_key"] == "vanguard"
    assert item["organization_id"] == canonical_vanguard_org()
    assert item["organization_id"] == "ados"


async def test_owner_demo_corp_sees_ados_vanguard_lead(client: TestClient):
    item = await _ingest(client)
    listed = await client.get(
        f"{OPS}/leads?project=vanguard",
        headers=_hdr("demo-corp", extra={"X-Tenant-Id": "demo-corp"}),
    )
    assert listed.status == 200
    body = await listed.json()
    ids = [row["id"] for row in body["items"]]
    assert item["id"] in ids
    assert body.get("project") == "vanguard"


async def test_recruiter_demo_corp_does_not_see_ados_lead(client: TestClient):
    item = await _ingest(client)
    listed = await client.get(
        f"{OPS}/leads?project=vanguard",
        headers=_hdr("demo-corp", role="recruiter", extra={"X-Tenant-Id": "demo-corp"}),
    )
    assert listed.status == 200
    ids = [row["id"] for row in (await listed.json())["items"]]
    assert item["id"] not in ids


async def test_owner_unrelated_tenant_does_not_see_ados_lead(client: TestClient):
    item = await _ingest(client)
    other = f"globefly-{uuid.uuid4().hex[:6]}"
    listed = await client.get(f"{OPS}/leads", headers=_hdr(other))
    assert listed.status == 200
    ids = [row["id"] for row in (await listed.json())["items"]]
    assert item["id"] not in ids


async def test_dashboard_and_vanguard_counters_agree(client: TestClient):
    item = await _ingest(client)
    dash = await (await client.get(f"{OPS}/dashboard", headers=_hdr("demo-corp"))).json()
    home = await (await client.get(f"{OPS}/leads", headers=_hdr("demo-corp"))).json()
    vg = await (await client.get(f"{OPS}/leads?project=vanguard", headers=_hdr("demo-corp"))).json()
    overview = await (await client.get(f"{OPS}/projects/vanguard", headers=_hdr("demo-corp"))).json()
    assert dash["ok"] is True
    assert overview["ok"] is True
    home_ids = [row["id"] for row in home["items"]]
    vg_ids = [row["id"] for row in vg["items"]]
    assert item["id"] in home_ids
    assert item["id"] in vg_ids
    assert dash["cards"]["leads"] == len(home["items"])
    assert overview["cards"]["leads"] == len(vg["items"])
    assert overview["cards"]["applications_today"] >= 1
    assert overview["cards"]["applications_7d"] >= 1
    assert overview["cards"]["last_application_at"]
    recent = [row["id"] for row in overview.get("recent_leads") or []]
    assert item["id"] in recent


async def test_recruiting_org_header_wins_over_jwt_tenant(client: TestClient):
    item = await _ingest(client)
    listed = await client.get(
        f"{OPS}/leads?project=vanguard",
        headers={
            "X-Role": "platform_owner",
            "X-Tenant-Id": "demo-corp",
            "X-Organization-Id": "demo-corp",
            "X-Recruiting-Organization-Id": "ados",
        },
    )
    assert listed.status == 200
    ids = [row["id"] for row in (await listed.json())["items"]]
    assert item["id"] in ids


async def test_hmac_headers_unchanged_in_2_6():
    raw, headers = _signed(_website_payload())
    assert set(headers) >= {
        "X-Vanguard-Signature",
        "X-Vanguard-Timestamp",
        "X-Vanguard-Nonce",
        "Content-Type",
    }
    blob = json.dumps(headers)
    assert DEV_FALLBACK_SECRET not in blob
    assert "IAM_JWT_SECRET" not in blob
