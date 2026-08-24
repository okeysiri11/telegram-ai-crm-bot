"""AGRO 1.8 — health colors, gap severity, agents, engines, lineage, scheduler."""

from __future__ import annotations

import json
import uuid

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.agro_enterprise.api.register import register_agro_enterprise_routes
from services.agro_ops import get_agro_ops_service, reset_agro_ops_for_tests
from services.agro_ops.engines import (
    NO_RATE_RU,
    build_logistics_status,
    build_opportunities,
    build_risks,
    structured_data_gaps,
)
from services.agro_ops.providers import HEALTH_COLORS, classify_source_url
from services.pg_scheduler_engine import DEFAULT_JOBS
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


async def test_health_sprint_1_8(client: TestClient):
    body = await (await client.get(f"{OPS}/health")).json()
    assert body["sprint"] == "agro-2.0"
    assert body["health_colors"]["CONNECTED"] == "green"
    assert body["health_colors"]["PARTIAL"] == "yellow"
    assert body["health_colors"]["NEEDS_KEY"] == "orange"
    assert body["health_colors"]["NEEDS_LICENSE"] == "orange"
    assert body["health_colors"]["BLOCKED"] == "red"
    assert body["health_colors"]["FAILED"] == "red"
    assert body["health_colors"]["METADATA_ONLY"] == "gray"
    assert body["health_colors"]["OPTIONAL_NOT_CONFIGURED"] == "gray"
    agent_ids = {a["id"] for a in body["agents"]}
    assert {"ukraine", "market", "logistics", "ports", "opportunity", "risk", "chief"} <= agent_ids


def test_health_color_map_and_url_class():
    assert HEALTH_COLORS["CONNECTED"] == "green"
    assert classify_source_url("https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange") == "OFFICIAL_API"
    assert classify_source_url("https://data.gov.ua/api/3/action/package_search") == "PUBLIC_DATA"
    assert classify_source_url("https://example.com/feed.rss") == "RSS"
    assert classify_source_url("https://random-blog.test/prices") == "UNKNOWN"


def test_gap_severity_and_engines():
    providers = [
        {"id": "weather_provider", "health_state": "FAILED", "label_ru": "Open-Meteo"},
        {"id": "market_prices", "health_state": "NEEDS_LICENSE"},
        {"id": "weather_provider_secondary", "health_state": "OPTIONAL_NOT_CONFIGURED"},
        {"id": "ua_agro_ministry", "health_state": "BLOCKED", "note_ru": "HTTP 403"},
        {"id": "ua_ports", "health_state": "METADATA_ONLY"},
    ]
    obs = [
        {
            "series_kind": "production",
            "normalized_value": 1,
            "data_class": "numeric",
            "provider_id": "world_bank",
            "source_class": "OFFICIAL_API",
        }
    ]
    gaps = structured_data_gaps("org", providers, obs, trips=[])
    by_code = {g["code"]: g["severity"] for g in gaps}
    assert by_code["primary_weather"] == "CRITICAL"
    assert by_code["all_prices"] == "CRITICAL"
    assert by_code["logistics_rates"] == "IMPORTANT"
    assert by_code["secondary_weather"] == "OPTIONAL"
    assert by_code["minagro_blocked"] == "OPTIONAL"

    logi = build_logistics_status([], [], providers)
    assert logi["status_ru"] == NO_RATE_RU
    assert "гарантир" not in json.dumps(logi, ensure_ascii=False).lower()

    prices = [
        {
            "series_kind": "price",
            "normalized_value": 100,
            "unit": "EUR/t",
            "currency": "EUR",
            "commodity": "Пшеница",
            "country": "FR",
            "data_class": "numeric",
            "provider_id": "ec_agri",
            "observed_at": "2026-08-01",
            "source_url": "https://api.tech.ec.europa.eu/cereal",
        },
        {
            "series_kind": "price",
            "normalized_value": 140,
            "unit": "EUR/t",
            "currency": "EUR",
            "commodity": "Пшеница",
            "country": "DE",
            "data_class": "numeric",
            "provider_id": "ec_agri",
            "observed_at": "2026-08-01",
            "source_url": "https://api.tech.ec.europa.eu/cereal",
        },
    ]
    opps = build_opportunities(prices, [])
    hit = next(o for o in opps if o.get("price_difference"))
    assert hit["label_ru"] == "Потенциальная возможность"
    assert hit["guaranteed_profit"] is False
    assert "не гарантированная прибыль" in hit["text"].lower()
    assert hit["estimated_logistics_note"] == NO_RATE_RU
    assert hit["sources"]

    risks = build_risks(prices, providers)
    assert any(r["level"] in {"LOW", "MEDIUM", "HIGH", "CRITICAL"} and r.get("reason") for r in risks)


def test_scheduler_jobs_additive():
    keys = {j["job_key"] for j in DEFAULT_JOBS}
    assert "agro.providers.morning" in keys
    assert "agro.providers.dawn" in keys
    assert "agro.analysis.morning" in keys
    assert "agro.providers.noon" in keys
    assert "agro.providers.full" in keys
    assert "agro.analysis.evening" in keys
    assert "agro.analysis.weekly" in keys
    assert "agro.analysis.outlook" in keys


async def test_live_pipeline_colors_agents_lineage_scheduler(client: TestClient):
    org = f"org-a18-{uuid.uuid4().hex[:8]}"
    svc = get_agro_ops_service()
    svc.set_provider_fetch(_fake_fetch)
    h = _hdr(org)
    refresh = await (await client.post(f"{OPS}/providers/refresh-all", json={}, headers=h)).json()
    assert refresh["ok"]
    listed = await (await client.get(f"{OPS}/providers", headers=h)).json()
    by_id = {i["id"]: i for i in listed["items"]}
    assert by_id["weather_provider"]["health_color"] == "green"
    assert by_id["market_prices"]["health_state"] == "NEEDS_LICENSE"
    assert by_id["market_prices"]["health_color"] == "orange"
    assert by_id["weather_provider_secondary"]["health_state"] == "OPTIONAL_NOT_CONFIGURED"
    assert by_id["weather_provider_secondary"]["health_color"] == "gray"
    assert by_id["ua_customs_open_data"]["health_state"] == "METADATA_ONLY"
    assert by_id["ua_customs_open_data"]["health_color"] == "gray"
    assert by_id["ua_agro_ministry"]["health_state"] in {"BLOCKED", "METADATA_ONLY", "FAILED"}
    assert by_id["ua_agro_ministry"]["health_color"] in {"red", "gray"}

    dash = await (await client.get(f"{OPS}/analytics/dashboard", headers=h)).json()
    sevs = {g["severity"] for g in dash["gaps_structured"]}
    assert sevs <= {"CRITICAL", "IMPORTANT", "OPTIONAL"}
    assert any(g["severity"] == "OPTIONAL" for g in dash["gaps_structured"])
    critical = [g for g in dash["gaps_structured"] if g["severity"] == "CRITICAL"]
    assert len(dash["gaps_structured"]) >= len(critical)

    custom = await (
        await client.post(
            f"{OPS}/providers/custom",
            json={"url": "https://unknown-source.example/feed", "trust_level": "LOW"},
            headers=h,
        )
    ).json()
    assert custom["ok"]
    assert custom["source_class"] == "UNKNOWN"
    assert custom["trust_level"] == "LOW"
    assert custom["item"]["market_usable"] is False

    agents = await (await client.post(f"{OPS}/agents/run", json={}, headers=h)).json()
    executed = set(agents["item"]["specialists_executed"])
    assert {"ukraine", "logistics", "opportunity", "risk", "chief"} <= executed
    logi = next(a for a in agents["item"]["agents"] if a["agent"] == "logistics")
    assert NO_RATE_RU in json.dumps(logi, ensure_ascii=False)
    chief = agents["item"]["chief"]
    assert chief["observations"] is not None
    assert chief["specialist_conclusions"]
    assert chief["freshness"]
    assert chief["source_quality"]["unknown_excluded"] is True
    assert chief["data_gaps_structured"]
    assert chief["opportunities"]
    assert all(o.get("guaranteed_profit") is False for o in chief["opportunities"] if "guaranteed_profit" in o)
    assert "не гарантированная" in json.dumps(chief["opportunities"], ensure_ascii=False).lower()
    assert all(r.get("level") in {"LOW", "MEDIUM", "HIGH", "CRITICAL"} for r in chief["risks"] if isinstance(r, dict) and r.get("level"))

    run = await (await client.post(f"{OPS}/analytics/run", json={"analysis_type": "operational"}, headers=h)).json()
    item = run["item"]
    assert item["opportunities"]
    assert item["logistics"]["status_ru"] == NO_RATE_RU
    assert any((r.get("sources") or r.get("level")) for r in item["risks"])
    dumped = json.dumps(item, ensure_ascii=False)
    assert "не гарантированная" in dumped.lower()

    sched = await (await client.get(f"{OPS}/scheduler", headers=h)).json()
    assert sched["timezone"] == "Europe/Kyiv"
    assert any(j["id"] == "ops_refresh" and j["cron_kyiv"] == "45 5 * * *" for j in sched["jobs"])
    updated = await (
        await client.put(
            f"{OPS}/scheduler",
            json={
                "timezone": "Europe/Kyiv",
                "jobs": [{**j, "cron_kyiv": "40 5 * * *" if j["id"] == "ops_refresh" else j["cron_kyiv"]} for j in sched["jobs"]],
            },
            headers=h,
        )
    ).json()
    assert updated["ok"]
    dawn = next(j for j in updated["jobs"] if j["id"] == "ops_refresh")
    assert dawn["cron_kyiv"] == "40 5 * * *"
