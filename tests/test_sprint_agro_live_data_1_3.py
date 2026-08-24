"""AGRO Live Data 1.3 — adapters, ingest, reviews, analysts, no fake values."""

from __future__ import annotations

import json
import uuid

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.agro_enterprise.api.register import register_agro_enterprise_routes
from services.agro_ops import get_agro_ops_service, reset_agro_ops_for_tests
from services.agro_ops.providers import SimpleFetchResult, fingerprint, interpret_fetch, normalize_observation

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
    if "429" in url:
        return SimpleFetchResult(status=429, text="rate", headers={"Retry-After": "60"}, rate_limited=True)
    if "timeout" in url:
        return SimpleFetchResult(error="timeout: deadline", unavailable=True, timed_out=True)
    if "fail" in url:
        return SimpleFetchResult(status=500, text="boom", unavailable=True)
    if "data.gov.ua" in url:
        return SimpleFetchResult(
            status=200,
            text=json.dumps({"success": True, "result": {"results": [{"id": "pkg-1", "title": "Митна статистика", "metadata_modified": "2026-08-01T00:00:00"}]}}),
        )
    if "meteo" in url or url.endswith("/"):
        return SimpleFetchResult(status=200, text="<!doctype html><html><body>official</body></html>")
    if "cornell" in url or "usda" in url:
        return SimpleFetchResult(status=200, text=json.dumps({"id": "wasde", "title": "WASDE", "date_created": "2026-08-12"}))
    if "faostat" in url:
        return SimpleFetchResult(status=200, text=json.dumps({"data": [{"domain_code": "PP", "domain_name": "Producer Prices"}]}))
    if "worldbank" in url:
        return SimpleFetchResult(status=200, text=json.dumps([{}, [{"id": "2", "name": "WDI"}]]))
    if "eurostat" in url:
        return SimpleFetchResult(status=200, text="TABLE toc catalogue")
    return SimpleFetchResult(unavailable=True, error="no mock")


async def test_health_sprint_1_3(client: TestClient):
    body = await (await client.get(f"{OPS}/health")).json()
    assert body["sprint"] == "agro-2.0"


async def test_unprobed_requires_configuration(client: TestClient):
    org = f"org-a13-{uuid.uuid4().hex[:8]}"
    items = {i["id"]: i for i in (await (await client.get(f"{OPS}/providers", headers=_hdr(org))).json())["items"]}
    assert items["usda_wasde"]["health_state"] == "REQUIRES_CONFIGURATION"
    assert items["manual_import"]["health_state"] == "CONNECTED"


async def test_fetch_429_timeout_failure_partial(client: TestClient):
    from services.agro_ops.providers import PROVIDER_SPECS

    spec = dict(PROVIDER_SPECS[0])
    spec["url"] = "https://example.test/429"
    out = interpret_fetch(spec, SimpleFetchResult(status=429, rate_limited=True, headers={"Retry-After": "30"}))
    assert out["probe_result"] == "FAILED"
    assert "429" in out["error"]

    timed = interpret_fetch(spec, SimpleFetchResult(timed_out=True, error="timeout", unavailable=True))
    assert timed["probe_result"] == "FAILED"
    assert "Таймаут" in timed["note_ru"]

    failed = interpret_fetch(spec, SimpleFetchResult(status=500, unavailable=True))
    assert failed["probe_result"] == "FAILED"

    blocked = interpret_fetch(spec, SimpleFetchResult(status=403, blocked=True))
    assert blocked["probe_result"] == "BLOCKED"

    html = interpret_fetch(
        next(p for p in PROVIDER_SPECS if p["id"] == "ua_hydromet"),
        SimpleFetchResult(status=200, text="<!doctype html><html>meteo</html>"),
    )
    assert html["probe_result"] == "PARTIAL"


async def test_normalize_dedupe_raw_and_review(client: TestClient):
    org = f"org-a13i-{uuid.uuid4().hex[:8]}"
    svc = get_agro_ops_service()
    svc.set_provider_fetch(_fake_fetch)
    first = await (await client.post(f"{OPS}/providers/refresh-all", json={}, headers=_hdr(org))).json()
    assert first["ok"]
    customs = next(i for i in first["items"] if i["provider_id"] == "ua_customs_open_data")
    assert customs["probe_result"] == "PARTIAL"
    second = await (await client.post(f"{OPS}/providers/ua_customs_open_data/probe", json={}, headers=_hdr(org))).json()
    obs = await (await client.get(f"{OPS}/providers/observations?provider_id=ua_customs_open_data", headers=_hdr(org))).json()
    trade = [i for i in obs["items"] if i.get("record_kind") == "trade_observation"]
    assert len(trade) == 1
    assert trade[0]["adapter_type"] == "open_data_api"
    assert trade[0]["source_url"]
    assert trade[0]["ingested_at"]
    snaps = [i for i in obs["items"] if i.get("record_kind") == "provider_snapshot"]
    assert snaps[0].get("raw_excerpt")
    assert fingerprint("a", "b") == fingerprint("a", "b")

    detail = await (await client.get(f"{OPS}/providers/ua_customs_open_data", headers=_hdr(org))).json()
    assert detail["item"]["health_state"] in {"PARTIAL", "METADATA_ONLY"}
    assert detail["observations"]

    agents = await (await client.post(f"{OPS}/agents/run", json={}, headers=_hdr(org))).json()
    assert agents["ok"]
    assert agents["item"]["record_type"] == "agents_run"
    assert agents["item"]["id"]
    stored = await (await client.get(f"{OPS}/agents", headers=_hdr(org))).json()
    assert stored["items"][0]["id"] == agents["item"]["id"]

    review = await (await client.post(f"{OPS}/reports/generate", json={"kind": "evening"}, headers=_hdr(org))).json()
    assert review["ok"]
    assert review["item"]["observation_count"] >= 1
    trade_sec = next(s for s in review["item"]["sections"] if s["id"] == "trade")
    assert trade_sec["status"] == "DATA"
    assert any(b.get("provider_id") == "ua_customs_open_data" for b in trade_sec["bullets"])
    assert "не выдумываются" in review["item"]["sources_note_ru"]

    other = await (await client.get(f"{OPS}/providers/observations", headers=_hdr(f"org-z-{uuid.uuid4().hex[:6]}"))).json()
    assert other["items"] == []
    assert second["ok"]

    sweep = await get_agro_ops_service().run_report_sweep(org, kind="morning")
    assert sweep["ok"]
    morning = await (await client.get(f"{OPS}/reports?kind=morning", headers=_hdr(org))).json()
    assert morning["items"]
    assert morning["items"][0]["id"]


async def test_normalize_helper_no_fake_numbers():
    spec = {"id": "ua_stat", "url": "https://data.gov.ua", "source_type": "open_data_api", "country": "UA", "region": "Украина"}
    row = normalize_observation({"title": "Набор", "raw_value": "Набор", "source_reference": "x"}, spec, "2026-08-16T00:00:00+00:00")
    assert row["normalized_value"] is None
    assert row["raw_value"] == "Набор"
    assert row["adapter_type"] == "open_data_api"
