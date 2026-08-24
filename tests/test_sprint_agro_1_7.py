"""AGRO 1.7 — coverage card, FAO FPI numeric, no demo fallback, honest gaps."""

from __future__ import annotations

import json
import uuid

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.agro_enterprise.api.register import register_agro_enterprise_routes
from services.agro_ops import get_agro_ops_service, reset_agro_ops_for_tests
from services.agro_ops.providers import SimpleFetchResult
from services.agro_ops.series_parsers import parse_fao_food_price_index
from tests.test_sprint_agro_1_6 import (
    EC_JSON,
    EUROSTAT_JSON,
    METEO_JSON,
    NBU_JSON,
    WB_PROD,
    WB_TRADE,
    WB_YLD,
    _fake_fetch as _fake_16,
)

OPS = "/api/agro-ops/v1"

FPI_CSV = """MONTHLY FOOD PRICE INDICES (2002-2004=100),,,,,,
,,,,,,
Date,Food Price Index,Meat Price Index,Dairy Price Index,Cereals Price Index,Oils Price Index,Sugar Price Index
Jun-24,120.1,110,100,125.5,90,80
Jul-24,121.0,111,101,126.2,91,81
"""

WB_IMPORT = json.dumps(
    [
        {"page": 1},
        [
            {
                "indicator": {"id": "TM.VAL.MRCH.CD.WT", "value": "Merchandise imports (current US$)"},
                "country": {"id": "UA"},
                "countryiso3code": "UKR",
                "date": "2024",
                "value": 88000000000,
            }
        ],
    ]
)


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


async def _fake_fetch(url: str, headers=None, **kwargs) -> SimpleFetchResult:
    if "food_price_indices" in url.lower():
        return SimpleFetchResult(status=200, text=FPI_CSV, content_type="text/csv")
    if "TM.VAL.MRCH" in url:
        return SimpleFetchResult(status=200, text=WB_IMPORT, content_type="application/json")
    if "fenixservices.fao.org" in url:
        return SimpleFetchResult(error="timeout", unavailable=True, timed_out=True)
    return await _fake_16(url, headers, **kwargs)


async def test_health_sprint_1_7(client: TestClient):
    body = await (await client.get(f"{OPS}/health")).json()
    assert body["sprint"] == "agro-2.0"


def test_fao_fpi_parser_numeric():
    rows = parse_fao_food_price_index(FPI_CSV, "fao", "https://www.fao.org/fileadmin/x.csv")
    assert rows
    assert rows[-1]["normalized_value"] == pytest.approx(126.2)
    assert rows[-1]["series_id"] == "faostat-fpi-cereals"
    assert rows[-1]["series_kind"] == "price"
    modern = parse_fao_food_price_index(
        "FAO Food Price Index,,,,\n2014-2016=100,,,,\nDate,Food Price Index,Meat,Dairy,Cereals,Oils,Sugar\n2026-06,120.1,110,100,125.5,90,80\n2026-07,121.0,111,101,126.2,91,81\n",
        "fao",
        "https://www.fao.org/media/docs/food_price_indices_data.csv",
    )
    assert modern[-1]["normalized_value"] == pytest.approx(126.2)
    assert modern[-1]["observed_at"].startswith("2026-07")


async def test_coverage_fao_nbu_reports_no_demo_fallback(client: TestClient):
    org = f"org-a17-{uuid.uuid4().hex[:8]}"
    svc = get_agro_ops_service()
    svc.set_provider_fetch(_fake_fetch)
    h = _hdr(org)
    refresh = await (await client.post(f"{OPS}/providers/refresh-all", json={}, headers=h)).json()
    assert refresh["ok"]
    by_id = {i["provider_id"]: i for i in refresh["items"]}
    assert by_id["fao"]["probe_result"] == "CONNECTED"
    assert by_id["fao"]["numeric_count"] >= 1
    assert by_id["eurostat"]["probe_result"] == "CONNECTED"
    assert by_id["fx_rates"]["probe_result"] == "CONNECTED"
    assert by_id["weather_provider"]["probe_result"] == "CONNECTED"
    assert by_id["world_bank"]["probe_result"] == "CONNECTED"
    assert "morning" in (refresh.get("reports_generated") or [])

    dash = await (await client.get(f"{OPS}/analytics/dashboard", headers=h)).json()
    cov = dash["coverage"]
    assert cov["connected_sources"] >= 5
    assert cov["numeric_observations"] >= 6
    assert cov["coverage_pct"] >= 80
    assert "unresolved_gaps" in cov
    weather = next(f for f in dash["freshness"] if f["provider_id"] == "weather_provider")
    assert weather["age_ru"] != "нет данных"
    assert any("QCL" in g or "fenix" in g.lower() for g in dash["gaps"])
    assert dash["series"]["fx"]
    assert dash["series"]["trade"]
    assert dash["series"]["price"]
    price_series = dash["series"]["price"]
    price_ts = [str(p.get("t") or "") for p in price_series]
    assert price_ts == sorted(price_ts)
    assert len({t[:16] for t in price_ts}) == len(price_ts)
    price_units = {str(p.get("unit") or "") for p in price_series if p.get("unit")}
    assert len(price_units) <= 1
    assert by_id["fao"]["numeric_count"] >= 1
    assert by_id["eurostat"]["probe_result"] == "CONNECTED"
    assert dash["series"]["production"] or dash["series"]["yield_or_area"]

    reports = await (await client.get(f"{OPS}/reports", headers=h)).json()
    morning = next(i for i in reports["items"] if i.get("report_kind") == "morning")
    assert int(morning["sources_count"]) >= 1
    note = str(morning.get("sources_note_ru") or morning.get("summary") or "")
    assert "0 источников" not in note
    assert "Внешние источники не подключены" not in note

    demo = await (await client.post(f"{OPS}/bootstrap", json={}, headers=h)).json()
    assert demo["demo_mode"] is True
    home = await (await client.get(f"{OPS}/dashboard", headers=h)).json()
    assert home["demo_mode"] is True

    await (
        await client.post(
            f"{OPS}/entities/market_price",
            json={"commodity": "Пшеница", "price": 9999, "is_demo": True, "data_class": "demo"},
            headers=h,
        )
    ).json()
    run = await (await client.post(f"{OPS}/analytics/run", json={"analysis_type": "operational"}, headers=h)).json()
    dumped = json.dumps(run["item"])
    assert "9999" not in dumped
    assert run["item"]["numeric_observation_count"] >= 1
    assert run["item"]["chief"].get("economic_data") is True
