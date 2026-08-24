"""AGRO 1.5 — analytics runs, freshness, gaps, versioning, no fabricated conclusions."""

from __future__ import annotations

import json
import uuid

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.agro_enterprise.api.register import register_agro_enterprise_routes
from services.agro_ops import get_agro_ops_service, reset_agro_ops_for_tests
from services.agro_ops.providers import SimpleFetchResult

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
    if "agricultural_markets" in url:
        return SimpleFetchResult(status=500, text="boom", unavailable=True)
    if "data.gov.ua" in url:
        return SimpleFetchResult(
            status=200,
            text=json.dumps(
                {
                    "success": True,
                    "result": {"results": [{"id": "pkg-1", "title": "Митна статистика", "metadata_modified": "2026-08-01T00:00:00"}]},
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


async def test_health_sprint_1_5(client: TestClient):
    body = await (await client.get(f"{OPS}/health")).json()
    assert body["sprint"] == "agro-2.0"


async def test_analysis_run_history_versioning_and_honesty(client: TestClient):
    org = f"org-a15-{uuid.uuid4().hex[:8]}"
    svc = get_agro_ops_service()
    svc.set_provider_fetch(_fake_fetch)
    h = _hdr(org)
    refresh = await (await client.post(f"{OPS}/providers/refresh-all", json={}, headers=h)).json()
    assert refresh["ok"]
    connected = [
        i
        for i in refresh["items"]
        if i.get("probe_result") in {"CONNECTED", "PARTIAL"} and int(i.get("observation_count") or 0) >= 0
    ]
    assert any(i.get("probe_result") in {"CONNECTED", "PARTIAL"} for i in refresh["items"])

    empty = await (await client.post(f"{OPS}/reports/generate", json={"kind": "morning", "force": True}, headers=h)).json()
    assert "Внешние источники не подключены" not in str(empty["item"].get("sources_note_ru") or empty["item"].get("summary") or "")
    assert int(empty["item"].get("observation_count") or 0) >= 1
    v1_id = empty["item"]["id"]

    v2 = await (await client.post(f"{OPS}/reports/generate", json={"kind": "morning", "recalculate": True}, headers=h)).json()
    assert v2["item"]["id"] != v1_id
    assert int(v2["item"].get("version") or 0) >= 2
    hist = await (await client.get(f"{OPS}/reports?kind=morning", headers=h)).json()
    morning = [i for i in hist["items"] if i.get("report_kind") == "morning"]
    assert len(morning) >= 2
    latest = next(i for i in morning if i.get("is_latest"))
    assert latest["id"] == v2["item"]["id"]
    assert latest.get("latest_badge_ru") == "АКТУАЛЬНЫЙ"

    dash = await (await client.get(f"{OPS}/analytics/dashboard", headers=h)).json()
    assert dash["ok"]
    assert dash["freshness"]
    assert any("котировки" in g.lower() or "погод" in g.lower() or "тариф" in g.lower() for g in dash["gaps"])

    run = await (await client.post(f"{OPS}/analytics/run", json={"analysis_type": "operational"}, headers=h)).json()
    assert run["ok"]
    item = run["item"]
    assert item["record_type"] == "analysis_run"
    assert item["id"]
    assert "chief" in item["specialists_executed"]
    assert len(item.get("specialists_with_data") or item.get("specialists_executed") or []) >= 3
    assert item["chief"]["confidence"] != 10
    prices = item["sections"]["prices"]
    assert prices["status"] in {"DATA", "INSUFFICIENT"}
    if prices["status"] == "INSUFFICIENT":
        assert "Недостаточно" in str(prices.get("note_ru") or "")
    if item["chief"].get("metadata_only"):
        assert "метаданн" in str(item["chief"].get("note_ru") or "").lower()

    fetched = await (await client.get(f"{OPS}/analytics/{item['id']}", headers=h)).json()
    assert fetched["item"]["id"] == item["id"]
    listed = await (await client.get(f"{OPS}/analytics", headers=h)).json()
    assert any(i["id"] == item["id"] for i in listed["items"])

    custom = await (
        await client.post(
            f"{OPS}/analytics/run",
            json={"analysis_type": "custom", "question": "Что сейчас происходит с пшеницей?"},
            headers=h,
        )
    ).json()
    assert custom["ok"]
    assert custom["item"]["question"]

    note = await (await client.post(f"{OPS}/analytics/{item['id']}/notify", json={"title": "Уведомить если риск станет HIGH"}, headers=h)).json()
    assert note["ok"]
    task = await (
        await client.post(
            f"{OPS}/analytics/{item['id']}/task",
            json={"title": "Связаться с контрагентами по кукурузе", "priority": "high", "commodity": "Кукуруза"},
            headers=h,
        )
    ).json()
    assert task["ok"]
    assert task["item"]["analysis_id"] == item["id"]
    cal = await (await client.post(f"{OPS}/analytics/{item['id']}/calendar", json={"title": "USDA report follow-up"}, headers=h)).json()
    assert cal["ok"]

    other = f"org-z15-{uuid.uuid4().hex[:6]}"
    isolated = await (await client.get(f"{OPS}/analytics", headers=_hdr(other))).json()
    assert isolated["items"] == []


async def test_failed_provider_does_not_block_analysis(client: TestClient):
    org = f"org-a15f-{uuid.uuid4().hex[:8]}"
    get_agro_ops_service().set_provider_fetch(_fake_fetch)
    h = _hdr(org)
    refresh = await (await client.post(f"{OPS}/providers/refresh-all", json={}, headers=h)).json()
    eu = next(i for i in refresh["items"] if i["provider_id"] == "ec_agri")
    assert eu["probe_result"] == "FAILED"
    run = await (await client.post(f"{OPS}/analytics/run", json={"analysis_type": "morning"}, headers=h)).json()
    assert run["ok"]
    assert run["item"]["chief"]
