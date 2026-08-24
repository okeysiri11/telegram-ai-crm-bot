"""AGRO 1.9 — source health, operational counts, quality, pipeline, charts."""

from __future__ import annotations

import uuid

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.agro_enterprise.api.register import register_agro_enterprise_routes
from services.agro_ops import get_agro_ops_service, reset_agro_ops_for_tests
from services.agro_ops.engines import build_logistics_status, production_observations
from services.agro_ops.quality import (
    PIPELINE_VERSION,
    detect_anomalies,
    operational_counts,
    provider_health_summary,
    sanitize_chart_series,
    validate_observations,
)
from services.pg_scheduler_engine import DEFAULT_JOBS, SchedulerEngineV1
from tests.test_sprint_agro_1_7 import _fake_fetch

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


async def test_health_sprint_1_9(client: TestClient):
    body = await (await client.get(f"{OPS}/health")).json()
    assert body["sprint"] == "agro-2.0"
    assert body["status"] == "ok"
    assert body["pipeline_version"] == "AGRO_1_9"
    assert PIPELINE_VERSION == "AGRO_1_9"


def test_provider_health_summary_and_numeric_counts():
    providers = [
        {"id": "weather_provider", "health_state": "CONNECTED"},
        {"id": "fx_rates", "health_state": "PARTIAL"},
        {"id": "market_prices", "health_state": "NEEDS_KEY"},
        {"id": "weather_provider_secondary", "health_state": "OPTIONAL_NOT_CONFIGURED"},
        {"id": "ua_agro_ministry", "health_state": "FAILED"},
        {"id": "manual_import", "health_state": "CONNECTED"},
    ]
    summary = provider_health_summary(providers, last_full_refresh_at="2026-08-18T06:00:00+00:00", last_full_refresh_duration_sec=12.5)
    assert summary["title_ru"] == "ЗДОРОВЬЕ ИСТОЧНИКОВ"
    assert summary["healthy"] == 1
    assert summary["partial"] == 1
    assert summary["needs_key"] == 1
    assert summary["optional"] == 1
    assert summary["failed"] == 1
    assert summary["refresh_duration_sec"] == 12.5

    obs = [
        {"normalized_value": 10, "data_class": "numeric", "series_kind": "price", "observed_at": "2026-08-18T08:00:00+00:00"},
        {"normalized_value": None, "data_class": "metadata", "canonical_type": "page_signal", "source_reference": "html-title", "title": "Catalog"},
        {"normalized_value": 3, "data_class": "numeric", "series_kind": "weather", "observed_at": "2020-01-01T00:00:00+00:00"},
        {"normalized_value": 8, "data_class": "numeric", "series_kind": "trade", "observed_at": "2026-08-15T00:00:00+00:00"},
    ]
    counts = operational_counts(
        obs,
        trips=[{"rate": 40, "is_demo": False}],
        market_prices=[{"price_kind": "freight", "price": 55, "is_demo": False}],
    )
    assert counts["numeric_observations"] == 3
    assert counts["metadata_excluded"] is True
    assert counts["price"] == 1
    assert counts["weather"] == 1
    assert counts["trade"] == 1
    assert counts["logistics"] == 2


def test_quality_flags_never_delete_and_anomalies():
    rows = [
        {"id": "a", "normalized_value": 100, "data_class": "numeric", "series_kind": "price", "series_id": "wheat", "unit": "EUR/t", "currency": "EUR", "commodity": "wheat", "observed_at": "2026-08-01", "provider_id": "ec"},
        {"id": "b", "normalized_value": 100, "data_class": "numeric", "series_kind": "price", "series_id": "wheat", "unit": "EUR/t", "currency": "EUR", "commodity": "wheat", "observed_at": "2026-08-01", "provider_id": "ec"},
        {"id": "c", "normalized_value": -4, "data_class": "numeric", "series_kind": "price", "series_id": "wheat", "unit": "EUR/t", "currency": "EUR", "commodity": "wheat", "observed_at": "2099-01-01", "provider_id": "ec"},
        {"id": "d", "normalized_value": 12, "data_class": "manual", "manual_status": "UNCONFIRMED", "series_kind": "price", "observed_at": "2026-08-02"},
    ]
    flags = validate_observations(rows)
    assert flags
    assert all(f.get("kept") is True for f in flags)
    codes = {f["code"] for f in flags}
    assert "duplicate" in codes
    assert "negative_impossible" in codes
    assert "future_date" in codes
    assert "unconfirmed_manual" in codes

    too_few = [
        {"normalized_value": 10, "data_class": "numeric", "series_kind": "price", "series_id": "fx", "unit": "UAH", "observed_at": "2026-01-01"},
        {"normalized_value": 20, "data_class": "numeric", "series_kind": "price", "series_id": "fx", "unit": "UAH", "observed_at": "2026-02-01"},
    ]
    assert detect_anomalies(too_few) == []
    enough = too_few + [
        {"normalized_value": 22, "data_class": "numeric", "series_kind": "price", "series_id": "fx", "unit": "UAH", "observed_at": "2026-03-01"},
    ]
    hits = detect_anomalies(enough, threshold_pct=8)
    assert hits
    assert hits[0]["kind"] == "ANOMALY"
    assert hits[0]["comparable_n"] == 3


def test_sanitize_chart_one_metric_ordered_unique_dates():
    buckets = {
        "weather": [
            {"t": "2026-08-03", "v": 5, "unit": "mm", "series_id": "precip"},
            {"t": "2026-08-01", "v": 28, "unit": "°C", "series_id": "tmax"},
            {"t": "2026-08-02", "v": 0, "unit": "mm", "series_id": "precip"},
            {"t": "2026-08-02", "v": 30, "unit": "°C", "series_id": "tmax"},
            {"t": "2026-08-03", "v": 27, "unit": "°C", "series_id": "tmax"},
            {"t": "2026-08-01", "v": 1, "unit": "mm", "series_id": "precip"},
        ]
    }
    cleaned = sanitize_chart_series(buckets)["weather"]
    assert cleaned
    units = {str(r.get("unit") or "") for r in cleaned}
    assert len(units) == 1
    ts = [str(r.get("t") or "")[:16] for r in cleaned]
    assert ts == sorted(ts)
    assert len(ts) == len(set(ts))
    metrics = {str(r.get("metric") or r.get("series_id")) for r in cleaned}
    assert len(metrics) == 1


def test_confirmed_manual_is_first_class():
    confirmed = {
        "normalized_value": 48,
        "data_class": "manual",
        "manual_status": "CONFIRMED",
        "series_kind": "price",
        "source_class": "UNKNOWN",
    }
    unconfirmed = {**confirmed, "manual_status": "UNCONFIRMED", "normalized_value": 10}
    prod = production_observations([confirmed, unconfirmed])
    assert len(prod) == 1
    assert prod[0]["normalized_value"] == 48
    logi = build_logistics_status([], [], [], quotes=[{"price_kind": "freight", "price": 62, "currency": "USD", "title": "test freight", "manual_status": "CONFIRMED"}])
    assert logi["status_ru"] != "Нет актуальной коммерческой ставки"
    assert logi["commercial_rate"] or logi["findings"]


def test_scheduler_keys_kept_and_pipeline_handlers():
    keys = {j["job_key"] for j in DEFAULT_JOBS}
    assert "agro.providers.dawn" in keys
    assert "agro.providers.noon" in keys
    assert "agro.providers.full" in keys
    assert "agro.analysis.morning" in keys
    handlers = SchedulerEngineV1.job_handlers()
    assert handlers["agro.providers.dawn"] is SchedulerEngineV1._run_agro_providers_light
    assert handlers["agro.analysis.morning"] is SchedulerEngineV1._run_agro_analysis_morning
    assert handlers["agro.analysis.outlook"] is SchedulerEngineV1._run_agro_analysis_outlook


async def test_live_health_counts_manual_freight_pipeline_reports(client: TestClient):
    org = f"org-a19-{uuid.uuid4().hex[:8]}"
    svc = get_agro_ops_service()
    svc.set_provider_fetch(_fake_fetch)
    h = _hdr(org)

    refresh = await (await client.post(f"{OPS}/providers/refresh-all", json={}, headers=h)).json()
    assert refresh["ok"]
    assert refresh["pipeline_version"] == "AGRO_1_9"
    assert refresh["pipeline_steps"][:4] == ["FETCH", "RAW_STORE", "NORMALIZE", "VALIDATE"]
    assert "DEDUPLICATE" in refresh["pipeline_steps"]
    assert "REPORT" in refresh["pipeline_steps"]
    assert "morning" in (refresh.get("reports_generated") or [])

    listed = await (await client.get(f"{OPS}/providers", headers=h)).json()
    by_id = {i["id"]: i for i in listed["items"]}
    assert by_id["weather_provider"]["numeric_count"] >= 1
    assert by_id["fx_rates"]["numeric_count"] >= 1
    assert by_id["world_bank"]["numeric_count"] >= 1
    assert str(by_id["eurostat"].get("health_state") or by_id["eurostat"].get("probe_result") or "") in {
        "CONNECTED",
        "PARTIAL",
        "METADATA_ONLY",
    }
    assert by_id["fao"]["numeric_count"] >= 1

    quote = await (
        await client.post(
            f"{OPS}/entities/market_price",
            json={
                "commodity": "Пшеница",
                "price": 42,
                "currency": "USD",
                "unit": "т",
                "price_kind": "freight",
                "source_type": "MANUAL",
                "manual_status": "CONFIRMED",
                "title": "Тестовая ставка фрахта",
            },
            headers=h,
        )
    ).json()
    assert quote["ok"]
    assert quote["item"]["manual_status"] == "CONFIRMED"
    assert quote["item"]["data_class"] == "manual"

    logi = await (await client.get(f"{OPS}/logistics/dashboard", headers=h)).json()
    assert int(logi["cards"]["freight_quotes"]) >= 1
    assert logi["commercial_quotes"]

    dash = await (await client.get(f"{OPS}/analytics/dashboard", headers=h)).json()
    health = dash["source_health"]
    assert health["healthy"] >= 1
    counts = dash["operational_counts"]
    assert counts["numeric_observations"] >= 1
    assert counts["weather"] >= 1
    assert counts["price"] >= 1 or counts["trade"] >= 1
    assert counts["logistics"] >= 1
    assert counts["metadata_excluded"] is True
    for kind, rows in (dash.get("series") or {}).items():
        ts = [str(p.get("t") or "")[:16] for p in rows]
        assert ts == sorted(ts)
        assert len(ts) == len(set(ts))
        units = {str(p.get("unit") or "") for p in rows if p.get("unit")}
        assert len(units) <= 1, kind

    analysis = await (await client.post(f"{OPS}/analytics/run", json={"analysis_type": "operational"}, headers=h)).json()
    assert analysis["ok"]
    assert analysis["item"]["confidence"] is not None
    assert analysis["item"]["pipeline_version"] == "AGRO_1_9"
    assert analysis["item"]["logistics"]["findings"] or analysis["item"]["logistics"].get("status_ru")
    assert all(f.get("kept") is True for f in (analysis["item"].get("quality_flags") or []))

    rebuilt = await (await client.post(f"{OPS}/pipeline/rebuild", json={}, headers=h)).json()
    assert rebuilt["ok"]
    assert rebuilt["pipeline_version"] == "AGRO_1_9"
    steps = rebuilt["pipeline_steps"]
    assert steps.index("FETCH") < steps.index("VALIDATE") < steps.index("SPECIALIST_ANALYSTS") < steps.index("REPORT")
    assert set(rebuilt["reports_generated"]) >= {"morning", "evening", "weekly", "outlook"}
    for row in rebuilt["reports"]:
        assert row.get("pipeline_version") == "AGRO_1_9"
        assert int(row.get("sources_count") or row.get("source_count") or 0) >= 1
        assert row.get("confidence") is not None

    reports = await (await client.get(f"{OPS}/reports?kind=morning", headers=h)).json()
    mornings = [i for i in reports["items"] if i.get("report_kind") == "morning"]
    assert len(mornings) >= 2
    latest = next(i for i in mornings if i.get("is_latest"))
    stale = [i for i in mornings if not i.get("is_latest")]
    assert latest["latest_badge_ru"] == "АКТУАЛЬНЫЙ"
    assert stale
    assert all(i["latest_badge_ru"] == "УСТАРЕЛ" for i in stale)
