"""AGRO 1.4 — raw store, analysts, reviews, history, fail-soft, no fake values."""

from __future__ import annotations

import json
import uuid

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.agro_enterprise.api.register import register_agro_enterprise_routes
from services.agro_ops import get_agro_ops_service, reset_agro_ops_for_tests
from services.agro_ops.analysts import calculate_chief_confidence
from services.agro_ops.http_safety import url_is_safe
from services.agro_ops.providers import SimpleFetchResult
from services.pg_scheduler_engine import DEFAULT_JOBS

OPS = "/api/agro-ops/v1"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_agro_enterprise_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_ops():
    reset_agro_ops_for_tests()
    yield
    reset_agro_ops_for_tests()


def _hdr(org: str, role: str = "agro_director") -> dict[str, str]:
    return {"X-Organization-Id": org, "X-Role": role}


async def _fake_fetch(url: str, headers=None) -> SimpleFetchResult:
    if "fail-eu" in url or "agricultural_markets" in url:
        return SimpleFetchResult(status=500, text="boom", unavailable=True)
    if "data.gov.ua" in url:
        return SimpleFetchResult(
            status=200,
            text=json.dumps(
                {
                    "success": True,
                    "result": {
                        "results": [
                            {"id": "pkg-1", "title": "Митна статистика", "metadata_modified": "2026-08-01T00:00:00"}
                        ]
                    },
                }
            ),
            content_type="application/json",
        )
    if "worldbank" in url:
        return SimpleFetchResult(status=200, text=json.dumps([{}, [{"id": "2", "name": "WDI"}]]), content_type="application/json")
    if "eurostat" in url:
        return SimpleFetchResult(status=200, text="TABLE toc catalogue", content_type="text/plain")
    if "meteo" in url:
        return SimpleFetchResult(
            status=200,
            text="<!doctype html><html><head><title>Укргидрометцентр</title></head><body><h1>Агрометеорологія</h1></body></html>",
            content_type="text/html",
        )
    if url.endswith("/") or "usda" in url or "fao" in url or "amis" in url or "minagro" in url or "uspa" in url:
        return SimpleFetchResult(status=200, text="<!doctype html><html><title>Official</title><h1>Portal</h1></html>", content_type="text/html")
    return SimpleFetchResult(unavailable=True, error="no mock")


async def test_health_sprint_1_4(client: TestClient):
    body = await (await client.get(f"{OPS}/health")).json()
    assert body["sprint"] == "agro-2.0"


def test_ssrf_and_confidence_formula():
    ok, _ = url_is_safe("https://data.gov.ua/api/3/action/package_search")
    assert ok is True
    blocked, reason = url_is_safe("http://127.0.0.1/secret")
    assert blocked is False
    assert reason in {"host", "private_ip"}
    assert calculate_chief_confidence(coverage=1, freshness=1, quality=1, agreement=1, missing_ratio=0) == 100
    assert calculate_chief_confidence(coverage=0, freshness=0, quality=0, agreement=0, missing_ratio=1) == 0
    assert calculate_chief_confidence(coverage=0.5, freshness=0.5, quality=0.5, agreement=0.5, missing_ratio=0.5) != 10


async def test_raw_normalize_analysts_report_history(client: TestClient):
    org = f"org-a14-{uuid.uuid4().hex[:8]}"
    svc = get_agro_ops_service()
    svc.set_provider_fetch(_fake_fetch)
    refresh = await (await client.post(f"{OPS}/providers/refresh-all", json={}, headers=_hdr(org))).json()
    assert refresh["ok"]
    customs = next(i for i in refresh["items"] if i["provider_id"] == "ua_customs_open_data")
    assert customs["probe_result"] == "PARTIAL"
    eu = next(i for i in refresh["items"] if i["provider_id"] == "ec_agri")
    assert eu["probe_result"] in {"FAILED", "PARTIAL", "CONNECTED"}

    detail = await (await client.get(f"{OPS}/providers/ua_customs_open_data", headers=_hdr(org))).json()
    assert detail["observations"]
    assert detail["raw"]
    assert detail["raw"][0]["content_hash"]
    raw2 = await (await client.post(f"{OPS}/providers/ua_customs_open_data/probe", json={}, headers=_hdr(org))).json()
    assert raw2["ok"]
    detail2 = await (await client.get(f"{OPS}/providers/ua_customs_open_data", headers=_hdr(org))).json()
    assert len(detail2["raw"]) == 1

    hydro = await (await client.get(f"{OPS}/providers/ua_hydromet", headers=_hdr(org))).json()
    titles = " ".join(str(o.get("title") or "") for o in hydro["observations"])
    assert "html" not in titles.lower()
    assert hydro["observations"]

    agents = await (await client.post(f"{OPS}/agents/run", json={}, headers=_hdr(org))).json()
    assert agents["ok"]
    assert agents["item"]["id"]
    assert "ukraine" in agents["item"]["specialists_executed"]
    assert "chief" in agents["item"]["specialists_executed"]
    trade_agent = next(a for a in agents["item"]["agents"] if a["agent"] == "trade")
    assert trade_agent["input_provider_ids"]
    assert trade_agent["input_record_ids"]
    assert agents["item"]["chief"]["confidence"] != 10
    assert isinstance(agents["item"]["chief"]["confidence"], int)

    other = f"org-z-{uuid.uuid4().hex[:6]}"
    isolated = await (await client.get(f"{OPS}/providers/observations", headers=_hdr(other))).json()
    assert isolated["items"] == []

    morning = await (await client.post(f"{OPS}/reports/generate", json={"kind": "morning_on_demand", "force": True}, headers=_hdr(org))).json()
    assert morning["ok"]
    rid = morning["item"]["id"]
    assert morning["item"]["report_type"] == "MORNING_ON_DEMAND"
    assert morning["item"]["observation_count"] >= 1
    trade_sec = next(s for s in morning["item"]["sections"] if s["id"] == "trade")
    assert trade_sec["status"] == "DATA"
    fetched = await (await client.get(f"{OPS}/reports/{rid}", headers=_hdr(org))).json()
    assert fetched["item"]["id"] == rid
    hist = await (await client.get(f"{OPS}/reports", headers=_hdr(org))).json()
    assert any(i["id"] == rid for i in hist["items"])

    weekly = await (await client.post(f"{OPS}/reports/generate", json={"kind": "weekly", "force": True}, headers=_hdr(org))).json()
    assert weekly["item"]["insufficient"] is True
    assert "Недостаточно" in weekly["item"]["themes"][0]["detail_ru"]

    opened = await (await client.post(f"{OPS}/reports/generate", json={"kind": "morning_on_demand", "open_latest": True}, headers=_hdr(org))).json()
    assert opened["item"]["id"] == rid


def test_scheduler_jobs_registered():
    keys = {j["job_key"] for j in DEFAULT_JOBS}
    assert "agro.providers.morning" in keys
    assert "agro.review.morning" in keys
    assert "agro.providers.evening" in keys
    assert "agro.review.evening" in keys
    assert len([j for j in DEFAULT_JOBS if j["job_key"] == "agro.review.morning"]) == 1
