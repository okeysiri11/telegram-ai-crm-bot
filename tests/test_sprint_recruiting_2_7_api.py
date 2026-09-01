"""Sprint Recruiting 2.7 — production same-origin routing, CORS, e77ed37 mapping."""

from __future__ import annotations

import json
import time
import uuid

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from api.cors_middleware import cors_middleware, origin_matches_request_host
from applications.recruiting_enterprise.api.register import register_recruiting_enterprise_routes
from services.recruiting_ops import reset_recruiting_ops_for_tests
from services.recruiting_ops.ingest_auth import DEV_FALLBACK_SECRET, sign_ingest_body
from services.recruiting_ops.projects import canonical_vanguard_org

OPS = "/api/recruiting-ops/v1"
INGEST = f"{OPS}/vanguard/leads"


@pytest.fixture
def app() -> web.Application:
    application = web.Application(middlewares=[cors_middleware])
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


def _hdr(org: str, role: str = "platform_owner") -> dict[str, str]:
    return {"X-Organization-Id": org, "X-Role": role, "X-Recruiting-Organization-Id": org}


def _website_payload() -> dict:
    submission = f"sub-{uuid.uuid4().hex[:12]}"
    return {
        "name": "Ada Lovelace",
        "email": f"ada.{uuid.uuid4().hex[:8]}@example.com",
        "phone": "+44 7700 900123",
        "program_of_interest": "logistics",
        "contact_consent": True,
        "source": "vanguard-global",
        "project_key": "vanguard",
        "external_id": submission,
        "idempotency_key": submission,
    }


def _signed(body: dict) -> tuple[bytes, dict[str, str]]:
    raw = json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ts = str(time.time())
    nn = uuid.uuid4().hex
    sig = sign_ingest_body(body=raw, timestamp=ts, nonce=nn, secret=DEV_FALLBACK_SECRET)
    return raw, {
        "Content-Type": "application/json",
        "X-Vanguard-Signature": sig,
        "X-Vanguard-Timestamp": ts,
        "X-Vanguard-Nonce": nn,
    }


def test_same_origin_host_matches_render():
    class _Req:
        headers = {"Host": "ados-web.onrender.com"}
        host = "ados-web.onrender.com"

    assert origin_matches_request_host("https://ados-web.onrender.com", _Req())
    assert not origin_matches_request_host("https://evil.example", _Req())


async def test_health_leads_vacancies_candidates_routes_exist(client: TestClient):
    health = await client.get(f"{OPS}/health")
    assert health.status == 200
    for path in ("/leads", "/vacancies", "/candidates"):
        res = await client.get(f"{OPS}{path}", headers=_hdr("ados"))
        assert res.status == 200, path


async def test_production_origin_cors_allows_recruiting_headers(client: TestClient, monkeypatch):
    monkeypatch.setenv("ADOS_CORS_ORIGINS", "https://ados-web.onrender.com")
    origin = "https://ados-web.onrender.com"
    preflight = await client.options(
        f"{OPS}/leads",
        headers={
            "Origin": origin,
            "Host": "ados-web.onrender.com",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization,x-role,x-organization-id,x-recruiting-organization-id",
        },
    )
    assert preflight.status == 204
    assert preflight.headers.get("Access-Control-Allow-Origin") == origin
    allowed = (preflight.headers.get("Access-Control-Allow-Headers") or "").lower()
    assert "x-recruiting-organization-id" in allowed
    assert "authorization" in allowed


async def test_owner_demo_corp_still_sees_ados_vanguard_lead(client: TestClient):
    raw, headers = _signed(_website_payload())
    ingested = await client.post(INGEST, data=raw, headers=headers)
    assert ingested.status == 201
    item = (await ingested.json())["item"]
    assert item["organization_id"] == canonical_vanguard_org()
    assert item["project_key"] == "vanguard"
    listed = await client.get(f"{OPS}/leads?project=vanguard", headers=_hdr("demo-corp"))
    assert listed.status == 200
    ids = [row["id"] for row in (await listed.json())["items"]]
    assert item["id"] in ids


async def test_recruiter_isolation_and_unrelated_owner_tenant(client: TestClient):
    raw, headers = _signed(_website_payload())
    ingested = await client.post(INGEST, data=raw, headers=headers)
    item = (await ingested.json())["item"]
    rec = await client.get(f"{OPS}/leads?project=vanguard", headers=_hdr("demo-corp", role="recruiter"))
    assert item["id"] not in [row["id"] for row in (await rec.json())["items"]]
    other = f"globefly-{uuid.uuid4().hex[:6]}"
    owner_other = await client.get(f"{OPS}/leads", headers=_hdr(other))
    assert item["id"] not in [row["id"] for row in (await owner_other.json())["items"]]
