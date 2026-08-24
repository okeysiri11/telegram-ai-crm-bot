"""AGRO Weather Intelligence — normalization, mapping, risk, confidence, recs, fallbacks."""

from __future__ import annotations

import json
import uuid

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.agro_enterprise.api.register import register_agro_enterprise_routes
from services.agro_ops import get_agro_ops_service, reset_agro_ops_for_tests
from services.agro_ops.providers import SimpleFetchResult
from services.agro_ops.series_parsers import parse_open_meteo
from services.agro_ops.weather import MACRO_REGIONS, UA_OBLASTS, oblast_by_id
from services.agro_ops.weather_intel import (
    agro_risk_from_metrics,
    confidence_from_context,
    outlook_30d_from_series,
    recommendations_from_forecast,
    resolve_crop_id,
)
from tests.test_sprint_agro_1_7 import _fake_fetch as _fake_17
from tests.test_sprint_agro_2_0 import _fake_weather, _hdr

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


def test_oblast_and_region_mapping():
    assert oblast_by_id("odesa")["macro"] == "south"
    assert oblast_by_id("lviv")["macro"] == "west"
    assert oblast_by_id("kyiv")["macro"] == "center"
    assert oblast_by_id("kharkiv")["macro"] == "east"
    assert oblast_by_id("chernihiv")["macro"] == "north"
    ids = {o["id"] for o in UA_OBLASTS}
    assert {m["id"] for m in MACRO_REGIONS} == {"south", "center", "west", "north", "east"}
    assert "crimea" in ids
    for spec in UA_OBLASTS:
        assert spec["macro"] in {m["id"] for m in MACRO_REGIONS}


def test_open_meteo_normalization_keeps_tmax_and_adds_current():
    body = json.dumps(
        {
            "daily": {
                "time": ["2026-08-18", "2026-08-19"],
                "temperature_2m_max": [34.0, 35.0],
                "temperature_2m_min": [18.0, 19.0],
                "precipitation_sum": [0.0, 1.2],
                "precipitation_probability_max": [10, 40],
                "wind_speed_10m_max": [4.0, 7.5],
                "weather_code": [0, 2],
            },
            "current": {
                "time": "2026-08-18T12:00",
                "temperature_2m": 26.0,
                "relative_humidity_2m": 38,
                "wind_speed_10m": 7.0,
                "surface_pressure": 1012.0,
                "weather_code": 0,
            },
        }
    )
    rows = parse_open_meteo(
        body,
        "weather_provider",
        "https://api.open-meteo.com/v1/forecast",
        oblast_id="odesa",
        region="Одесская область",
        macro_region="south",
    )
    metrics = {r["metric"] for r in rows}
    assert "tmax" in metrics and "precip" in metrics
    assert "tmin" in metrics and "humidity" in metrics and "current_temp" in metrics
    assert any(r.get("weather_risk") == "HIGH" for r in rows)
    legacy = parse_open_meteo(
        json.dumps({"daily": {"time": ["2026-08-16"], "temperature_2m_max": [36.0], "precipitation_sum": [22.0]}}),
        "weather_provider",
        "https://api.open-meteo.com",
    )
    assert any(r.get("metric") == "tmax" and r["normalized_value"] == 36.0 for r in legacy)


def test_risk_confidence_recommendations_partial():
    hot = agro_risk_from_metrics(tmax=34.0, precip_7=2.0, humidity=32.0, wind=12.0)
    assert hot["level"] == "High"
    assert hot["drought"] is True
    miss = agro_risk_from_metrics(tmax=None, precip_7=None)
    assert miss["missing"] is True
    conf = confidence_from_context(
        sources_count=1,
        freshness_hours=2.0,
        health_state="CONNECTED",
        present_metrics=["temperature", "precipitation", "humidity", "wind_speed"],
    )
    assert conf["sources_count"] == 1
    assert "1 источника" in conf["text_ru"]
    assert 40 <= conf["score"] <= 82
    recs = recommendations_from_forecast(
        [{"date": "2026-08-19", "precip": 0.0, "precip_probability": 10, "wind": 3.0, "tmax": 33}],
        tmax_avg=33.0,
        precip_7=2.0,
        humidity=32.0,
        wind=12.0,
        crop_id=None,
    )
    by_id = {r["id"]: r for r in recs}
    assert by_id["spraying"]["status"] == "not_recommended"
    assert by_id["irrigation"]["status"] == "recommended"
    assert by_id["harvest"]["general"] is True
    wheat = resolve_crop_id("Пшеница")
    assert wheat == "wheat"
    outlook = outlook_30d_from_series(forecast_days=[], precip_30=None, tmax_avg=None, precip_7=None)
    assert outlook["available"] is False
    assert "Недостаточно данных" in outlook["text_ru"]


async def test_weather_overview_regions_forecast_recs(client: TestClient, monkeypatch):
    org = f"org-awx-{uuid.uuid4().hex[:8]}"
    svc = get_agro_ops_service()
    monkeypatch.setattr(svc, "_fetch_url", _fake_weather)
    over = await (await client.get(f"{OPS}/weather/overview", headers=_hdr(org))).json()
    assert over["ok"] is True
    assert over["region_cards"]
    assert over["confidence"]["sources_count"] >= 1
    assert over["recommendations"]
    regions = await (await client.get(f"{OPS}/weather/regions", headers=_hdr(org))).json()
    assert len(regions["items"]) == 5
    odesa = await (await client.get(f"{OPS}/weather/oblasts/odesa", headers=_hdr(org))).json()
    assert odesa["ok"] is True
    assert odesa["item"]["temperature"] is not None
    fc = await (await client.get(f"{OPS}/weather/forecast?region=odesa&days=7", headers=_hdr(org))).json()
    assert fc["forecast"]
    out = await (await client.get(f"{OPS}/weather/outlook?region=south&days=30", headers=_hdr(org))).json()
    assert "климатической нормой" in (out.get("monthly_outlook_ru") or "") or out["outlook_30d"]
    risk = await (await client.get(f"{OPS}/weather/agro-risk?region=odesa&crop=кукуруза", headers=_hdr(org))).json()
    assert risk["agro_risk"]["level"] in {"High", "Medium", "Low"}
    recs = await (await client.get(f"{OPS}/weather/recommendations?region=odesa&crop=wheat", headers=_hdr(org))).json()
    assert recs["general"] is False
    refresh = await (await client.post(f"{OPS}/weather/refresh", json={}, headers=_hdr(org))).json()
    assert refresh["ok"] is True


async def test_provider_failure_keeps_cached_fallback(client: TestClient, monkeypatch):
    org = f"org-awx-fail-{uuid.uuid4().hex[:8]}"
    svc = get_agro_ops_service()
    monkeypatch.setattr(svc, "_fetch_url", _fake_weather)
    first = await (await client.get(f"{OPS}/weather/dashboard", headers=_hdr(org))).json()
    assert first["ok"] is True
    assert any(not o.get("missing") for o in first["oblasts"])

    async def down(url: str, spec=None, **kwargs):
        if "open-meteo.com" in url:
            return SimpleFetchResult(status=503, text="", error="unavailable", unavailable=True)
        return await _fake_17(url)

    monkeypatch.setattr(svc, "_fetch_url", down)
    again = await (await client.get(f"{OPS}/weather/overview", headers=_hdr(org))).json()
    assert again["ok"] is True
    assert any(o.get("temperature") is not None for o in again["oblasts"])
    odesa = await (await client.get(f"{OPS}/weather/regions/odesa", headers=_hdr(org))).json()
    assert odesa["item"]["temperature"] is not None


async def test_partial_open_meteo_does_not_invent_humidity(client: TestClient, monkeypatch):
    org = f"org-awx-part-{uuid.uuid4().hex[:8]}"
    svc = get_agro_ops_service()

    async def partial(url: str, spec=None, **kwargs):
        if "open-meteo.com" in url and "forecast" in url:
            return SimpleFetchResult(
                status=200,
                text=json.dumps({"daily": {"time": ["2026-08-18"], "temperature_2m_max": [24.0], "precipitation_sum": [3.0]}}),
                content_type="application/json",
            )
        return await _fake_17(url)

    monkeypatch.setattr(svc, "_fetch_url", partial)
    body = await (await client.get(f"{OPS}/weather/oblasts/kyiv", headers=_hdr(org))).json()
    item = body["item"]
    assert item["temperature"] == 24.0
    assert item.get("humidity") is None
    assert item.get("soil_temperature") is None
    assert item.get("pressure") is None
