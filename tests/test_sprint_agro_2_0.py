"""AGRO 2.0 — weather desk, business UI, settings IA, history/source actions."""

from __future__ import annotations

import json
import uuid

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.agro_enterprise.api.register import register_agro_enterprise_routes
from services.agro_ops import get_agro_ops_service, reset_agro_ops_for_tests
from services.agro_ops.presentation import (
    business_brief,
    cron_to_human,
    is_technical_text,
    present_schedule,
    strip_tech_from_provider,
)
from services.agro_ops.providers import SimpleFetchResult
from services.agro_ops.weather import crop_cell, history_compare, map_point, oblast_by_id
from tests.test_sprint_agro_1_7 import _fake_fetch as _fake_17

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


def _meteo(tmax: list[float], rain: list[float]) -> str:
    days = ["2026-08-18", "2026-08-19", "2026-08-20", "2026-08-21"]
    return json.dumps(
        {
            "daily": {
                "time": days[: len(tmax)],
                "temperature_2m_max": tmax,
                "precipitation_sum": rain,
            }
        }
    )


async def _fake_weather(url: str, spec=None, **kwargs) -> SimpleFetchResult:
    if "open-meteo.com" in url and "forecast" in url:
        from urllib.parse import parse_qs, urlparse

        lat = float((parse_qs(urlparse(url).query).get("latitude") or ["50"])[0])
        if lat < 47.5:
            return SimpleFetchResult(status=200, text=_meteo([34.0, 35.0, 36.0, 33.0], [0.0, 1.0, 0.5, 0.0]), content_type="application/json")
        if 49.5 <= lat <= 50.1:
            return SimpleFetchResult(status=200, text=_meteo([18.0, 19.0, 17.5, 18.5], [12.0, 15.0, 10.0, 8.0]), content_type="application/json")
        return SimpleFetchResult(status=200, text=_meteo([24.0, 25.0, 23.0, 24.5], [4.0, 5.0, 3.0, 4.0]), content_type="application/json")
    return await _fake_17(url)


async def test_health_sprint_2_0(client: TestClient):
    body = await (await client.get(f"{OPS}/health")).json()
    assert body["sprint"] == "agro-2.0"
    assert body["status"] == "ok"
    assert body["pipeline_version"] == "AGRO_1_9"
    assert body["ux_version"] == "AGRO_2_0"


def test_weather_region_mapping_and_crop_impact():
    odesa = oblast_by_id("odesa")
    lviv = oblast_by_id("lviv")
    assert odesa and lviv
    assert odesa["macro"] == "south"
    assert lviv["macro"] == "west"
    po = map_point(odesa["lat"], odesa["lon"])
    pl = map_point(lviv["lat"], lviv["lon"])
    assert po != pl
    hot = crop_cell("corn", 34.0, 2.0)
    wet = crop_cell("wheat", 18.0, 45.0)
    assert hot["level"] == "High"
    assert wet["level"] == "High"
    missing = crop_cell("soy", None, None)
    assert missing["missing"] is True


def test_never_invent_climate_normal():
    miss = history_compare(10.0, None, "mm")
    assert miss["ok"] is False
    assert "климатической нормой" in miss["text_ru"]
    ok = history_compare(8.0, 10.0, "mm")
    assert ok["ok"] is True
    assert ok["pct"] == -20.0


def test_schedule_human_and_tech_strip():
    human = cron_to_human("45 5 * * *")
    assert human["time_kyiv"] == "05:45"
    jobs = present_schedule([{"id": "ops_refresh", "cron_kyiv": "45 5 * * *", "label_ru": "Обновление данных"}])
    assert jobs[0]["time_kyiv"] == "05:45"
    assert is_technical_text("HTTP 403 from provider") is True
    assert is_technical_text("Получены свежие данные по погоде.") is False
    stripped = strip_tech_from_provider({"health_state": "BLOCKED", "note_ru": "HTTP 521 timeout", "error": "HTTP 521"})
    assert stripped["error_hidden"] is True
    assert "HTTP" not in stripped["business_note_ru"]


def test_business_brief_language():
    brief = business_brief(
        [{"id": "weather_provider", "health_state": "CONNECTED"}],
        [{"series_kind": "weather", "normalized_value": 20, "data_class": "numeric"}],
    )
    assert "свежие данные" in brief["text_ru"]
    assert "observations" not in brief["text_ru"]
    assert "metadata" not in brief["text_ru"]


async def test_weather_dashboard_odesa_lviv_differ(client: TestClient, monkeypatch):
    org = f"org-a20-{uuid.uuid4().hex[:8]}"
    svc = get_agro_ops_service()
    monkeypatch.setattr(svc, "_fetch_url", _fake_weather)
    dash = await (await client.get(f"{OPS}/weather/dashboard", headers=_hdr(org))).json()
    assert dash["ok"] is True
    assert dash["map"]["regions"]
    assert any(r["id"] == "odesa" for r in dash["map"]["regions"])
    odesa = await (await client.get(f"{OPS}/weather/regions/odesa", headers=_hdr(org))).json()
    lviv = await (await client.get(f"{OPS}/weather/regions/lviv", headers=_hdr(org))).json()
    assert odesa["ok"] is True and lviv["ok"] is True
    assert odesa["item"]["temperature"] != lviv["item"]["temperature"]
    assert odesa["item"]["rain"] != lviv["item"]["rain"]
    assert odesa["crop_impact"]
    assert "климатической нормой" in (odesa.get("monthly_outlook_ru") or dash["history"]["note_ru"])
    south = next(m for m in dash["macros"] if m["macro_id"] == "south")
    assert south["title_ru"]
    matrix = dash["matrix"]
    assert {c["id"] for c in matrix["columns"]} >= {"wheat", "corn", "sunflower", "barley", "soy"}
    assert len(matrix["rows"]) == 5


async def test_analytics_open_and_business_cards(client: TestClient, monkeypatch):
    org = f"org-a20b-{uuid.uuid4().hex[:8]}"
    svc = get_agro_ops_service()
    monkeypatch.setattr(svc, "_fetch_url", _fake_weather)
    dash = await (await client.get(f"{OPS}/analytics/dashboard", headers=_hdr(org))).json()
    assert dash["ok"] is True
    assert dash["business_brief"]["text_ru"]
    assert "HTTP 403" not in json.dumps(dash["business_brief"])
    assert "risk_cards" in dash
    assert "opportunity_cards" in dash
    assert "what_changed" in dash
    run = await (
        await client.post(f"{OPS}/analytics/run", json={"analysis_type": "operational"}, headers=_hdr(org))
    ).json()
    assert run["ok"] is True
    item_id = run["item"]["id"]
    opened = await (await client.get(f"{OPS}/analytics/{item_id}", headers=_hdr(org))).json()
    assert opened["ok"] is True
    assert opened["item"]["id"] == item_id
    listed = await (await client.get(f"{OPS}/analytics", headers=_hdr(org))).json()
    assert any(i["id"] == item_id for i in listed["items"])


async def test_provider_actions_and_settings_desk(client: TestClient, monkeypatch):
    org = f"org-a20c-{uuid.uuid4().hex[:8]}"
    svc = get_agro_ops_service()
    monkeypatch.setattr(svc, "_fetch_url", _fake_weather)
    status = await (await client.get(f"{OPS}/providers", headers=_hdr(org))).json()
    items = status.get("items") or []
    live = [p for p in items if p.get("url") and p.get("id") != "manual_import"][:5]
    assert len(live) >= 5
    for p in live:
        detail = await (await client.get(f"{OPS}/providers/{p['id']}", headers=_hdr(org))).json()
        assert detail["ok"] is True
        assert "item" in detail
        probe = await (await client.post(f"{OPS}/providers/{p['id']}/probe", json={}, headers=_hdr(org))).json()
        assert probe.get("ok") is not False or probe.get("item") or probe.get("message_ru")
    desk = await (await client.get(f"{OPS}/settings/desk", headers=_hdr(org))).json()
    assert desk["ok"] is True
    tabs = [t["id"] for t in desk["tabs"]]
    assert tabs == ["general", "sources", "intel", "analytics", "weather", "schedule", "notifications", "diagnostics"]
    assert desk["diagnostics"] is not None
    assert desk["item"]["analytics_detail"] == "standard"
    saved = await (
        await client.put(
            f"{OPS}/settings/desk",
            json={**desk["item"], "report_length": "short"},
            headers=_hdr(org),
        )
    ).json()
    assert saved["ok"] is True
    assert saved["item"]["report_length"] == "short"
    sched = await (await client.get(f"{OPS}/scheduler", headers=_hdr(org))).json()
    assert sched["jobs_human"]
    assert any(j.get("time_kyiv") == "05:45" for j in sched["jobs_human"])
    assert any("45 5" in str(j.get("cron_kyiv")) for j in sched["jobs"])


async def test_report_business_sections(client: TestClient, monkeypatch):
    org = f"org-a20d-{uuid.uuid4().hex[:8]}"
    svc = get_agro_ops_service()
    monkeypatch.setattr(svc, "_fetch_url", _fake_weather)
    gen = await (
        await client.post(f"{OPS}/reports/generate", json={"kind": "morning", "generate": True}, headers=_hdr(org))
    ).json()
    item = gen.get("item") or {}
    assert item.get("business_sections")
    labels = [s["label_ru"] for s in item["business_sections"]]
    assert "Главное за 1 минуту" in labels
    assert "Что контролировать сегодня" in labels
    assert item.get("sections")
    opened = await (await client.get(f"{OPS}/reports/{item['id']}", headers=_hdr(org))).json()
    assert opened["ok"] is True
    assert opened["item"]["id"] == item["id"]
