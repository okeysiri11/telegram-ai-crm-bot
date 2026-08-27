"""Sprint Recruiting 1.2 — projects catalog + Vanguard control center."""

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
def reset_ops(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("VANGUARD_INGEST_SECRET", DEV_FALLBACK_SECRET)
    monkeypatch.delenv("VANGUARD_WEBSITE_URL", raising=False)
    reset_recruiting_ops_for_tests()
    yield
    reset_recruiting_ops_for_tests()


def _hdr(org: str, role: str = "platform_owner") -> dict[str, str]:
    return {"X-Organization-Id": org, "X-Role": role}


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


async def test_projects_catalog_includes_vanguard(client: TestClient):
    org = f"proj-{uuid.uuid4().hex[:8]}"
    res = await client.get(f"{OPS}/projects", headers=_hdr(org))
    assert res.status == 200
    body = await res.json()
    keys = {item["project_key"] for item in body["items"]}
    assert "vanguard" in keys
    card = next(item for item in body["items"] if item["project_key"] == "vanguard")
    assert card["type"] == "recruiting_website"
    assert card["leads"] == 0
    assert card["public_url"] is None


async def test_vanguard_filter_and_lookup(client: TestClient):
    org = "ados"
    raw, headers = _signed(
        {
            "first_name": "Vanguard Lead",
            "email": "vg@example.com",
            "source": "vanguard",
            "external_id": "VG-TEST-1",
            "vacancy_id": "vac-1",
        }
    )
    ingested = await client.post(f"{OPS}/vanguard/leads", data=raw, headers=headers)
    assert ingested.status == 201
    item = (await ingested.json())["item"]
    assert item["project_key"] == "vanguard"
    assert item["source"] == "vanguard"

    await client.post(
        f"{OPS}/leads",
        json={"name": "Manual", "source": "manual", "email": "m@example.com"},
        headers=_hdr(org),
    )

    filtered = await (await client.get(f"{OPS}/leads?project=vanguard", headers=_hdr(org))).json()
    names = [row["name"] for row in filtered["items"]]
    assert "Vanguard Lead" in names
    assert "Manual" not in names

    overview = await (await client.get(f"{OPS}/projects/vanguard", headers=_hdr(org))).json()
    assert overview["ok"] is True
    assert overview["cards"]["new_leads"] >= 1
    assert overview["relationship"][0]["id"] == "website"

    integ = await (await client.get(f"{OPS}/projects/vanguard/integration", headers=_hdr(org))).json()
    assert integ["ok"] is True
    stage_ids = [row["id"] for row in integ["stages"]]
    assert stage_ids == ["website", "vanguard_endpoint", "recruiting_api", "database"]
    assert integ["website"]["public_url"] is None

    found = await (await client.get(f"{OPS}/lookup?q=VG-TEST-1", headers=_hdr(org))).json()
    assert found["found"] is True

    missing = await (await client.get(f"{OPS}/lookup?q=VG-ZT9TH2", headers=_hdr(org))).json()
    assert missing["found"] is False


async def test_legacy_source_vanguard_is_project_filterable(client: TestClient):
    org = f"legacy-{uuid.uuid4().hex[:8]}"
    created = await client.post(
        f"{OPS}/leads",
        json={"name": "Old Vanguard", "source": "vanguard", "email": "old@example.com"},
        headers=_hdr(org),
    )
    assert created.status == 201
    item = (await created.json())["item"]
    assert item["project_key"] == "vanguard"
    filtered = await (await client.get(f"{OPS}/leads?project=vanguard", headers=_hdr(org))).json()
    assert any(row["name"] == "Old Vanguard" for row in filtered["items"])
