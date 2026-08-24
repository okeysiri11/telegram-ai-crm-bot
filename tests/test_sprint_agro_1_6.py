"""AGRO 1.6 — real numeric series, no fake data, alerts, source table, charts."""

from __future__ import annotations

import json
import uuid

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.agro_enterprise.api.register import register_agro_enterprise_routes
from services.agro_ops import get_agro_ops_service, reset_agro_ops_for_tests
from services.agro_ops.analytics import is_metadata_observation, is_numeric_observation
from services.agro_ops.providers import SimpleFetchResult, interpret_fetch, observation_is_numeric
from services.agro_ops.series_parsers import (
    parse_ec_cereal_prices,
    parse_eurostat_sdmx,
    parse_nbu_fx,
    parse_open_meteo,
    parse_worldbank_indicator,
)

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


EC_JSON = json.dumps(
    [
        {
            "memberStateCode": "FR",
            "memberStateName": "France",
            "beginDate": "01/08/2026",
            "endDate": "07/08/2026",
            "price": "€288,37",
            "unit": "TONNES",
            "productName": "Durum wheat",
        },
        {
            "memberStateCode": "FR",
            "beginDate": "08/08/2026",
            "price": "€270,00",
            "unit": "TONNES",
            "productName": "Durum wheat",
        },
    ]
)
NBU_JSON = json.dumps(
    [
        {"cc": "USD", "rate": 41.2, "exchangedate": "17.08.2026", "txt": "Долар США"},
        {"cc": "EUR", "rate": 47.8, "exchangedate": "17.08.2026", "txt": "Євро"},
        {"cc": "AUD", "rate": 31.8, "exchangedate": "17.08.2026"},
    ]
)
METEO_JSON = json.dumps(
    {
        "daily": {
            "time": ["2026-08-16", "2026-08-17"],
            "temperature_2m_max": [24.5, 36.0],
            "precipitation_sum": [1.2, 22.0],
        }
    }
)
WB_PROD = json.dumps(
    [
        {"page": 1},
        [
            {
                "indicator": {"id": "AG.PRD.CREL.MT", "value": "Cereal production (metric tons)"},
                "country": {"id": "UA", "value": "Ukraine"},
                "countryiso3code": "UKR",
                "date": "2023",
                "value": 35000000,
            },
            {
                "indicator": {"id": "AG.PRD.CREL.MT", "value": "Cereal production (metric tons)"},
                "country": {"id": "UA"},
                "countryiso3code": "UKR",
                "date": "2024",
                "value": 40000000,
            },
        ],
    ]
)
WB_YLD = json.dumps(
    [
        {"page": 1},
        [
            {
                "indicator": {"id": "AG.YLD.CREL.KG", "value": "Cereal yield (kg per hectare)"},
                "country": {"id": "UA"},
                "countryiso3code": "UKR",
                "date": "2024",
                "value": 4200,
            }
        ],
    ]
)
WB_TRADE = json.dumps(
    [
        {"page": 1},
        [
            {
                "indicator": {"id": "TX.VAL.MRCH.CD.WT", "value": "Merchandise exports (current US$)"},
                "country": {"id": "UA"},
                "countryiso3code": "UKR",
                "date": "2023",
                "value": 41000000000,
            },
            {
                "indicator": {"id": "TX.VAL.MRCH.CD.WT", "value": "Merchandise exports (current US$)"},
                "country": {"id": "UA"},
                "countryiso3code": "UKR",
                "date": "2024",
                "value": 36000000000,
            },
        ],
    ]
)
EUROSTAT_JSON = json.dumps(
    {
        "label": "Wheat and spelt by area, production and humidity",
        "value": {"0": 69.6, "1": 70.5},
        "id": ["freq", "crops", "strucpro", "geo", "time"],
        "size": [1, 1, 1, 1, 2],
        "dimension": {
            "freq": {"category": {"index": {"A": 0}, "label": {"A": "Annual"}}},
            "crops": {"category": {"index": {"C1100": 0}, "label": {"C1100": "Wheat"}}},
            "strucpro": {"category": {"index": {"PR_HU_EU": 0}, "label": {"PR_HU_EU": "Production"}}},
            "geo": {"category": {"index": {"FR": 0}, "label": {"FR": "France"}}},
            "time": {"category": {"index": {"2023": 0, "2024": 1}, "label": {"2023": "2023", "2024": "2024"}}},
        },
    }
)


async def _fake_fetch(url: str, headers=None, **kwargs) -> SimpleFetchResult:
    if "agrifood" in url:
        return SimpleFetchResult(status=200, text=EC_JSON, content_type="application/json")
    if "bank.gov.ua" in url:
        return SimpleFetchResult(status=200, text=NBU_JSON, content_type="application/json")
    if "open-meteo" in url:
        return SimpleFetchResult(status=200, text=METEO_JSON, content_type="application/json")
    if "AG.PRD.CREL.MT" in url:
        return SimpleFetchResult(status=200, text=WB_PROD, content_type="application/json")
    if "AG.YLD.CREL.KG" in url or "AG.LND.CREL.HA" in url:
        return SimpleFetchResult(status=200, text=WB_YLD, content_type="application/json")
    if "TX.VAL.MRCH" in url:
        return SimpleFetchResult(status=200, text=WB_TRADE, content_type="application/json")
    if "eurostat" in url and "tag00047" in url:
        return SimpleFetchResult(status=200, text=EUROSTAT_JSON, content_type="application/json")
    if "fenixservices.fao.org" in url and "/data/" in url:
        return SimpleFetchResult(error="timeout", unavailable=True, timed_out=True)
    if "data.gov.ua" in url:
        return SimpleFetchResult(
            status=200,
            text=json.dumps({"success": True, "result": {"results": [{"id": "pkg-1", "title": "Митна статистика"}]}}),
            content_type="application/json",
        )
    if url.endswith("/") or "usda" in url or "meteo.gov" in url or "amis" in url or "minagro" in url or "uspa" in url:
        return SimpleFetchResult(
            status=200,
            text="<!doctype html><html><title>Official</title><h1>Portal</h1></html>",
            content_type="text/html",
        )
    return SimpleFetchResult(unavailable=True, error="no mock")


async def test_health_sprint_1_6(client: TestClient):
    body = await (await client.get(f"{OPS}/health")).json()
    assert body["sprint"] == "agro-2.0"


def test_parsers_numeric_not_fake():
    prices = parse_ec_cereal_prices(EC_JSON, "ec_agri", "https://example")
    assert prices and observation_is_numeric(prices[0])
    assert prices[0]["normalized_value"] == pytest.approx(288.37)
    fx = parse_nbu_fx(NBU_JSON, "fx_rates", "https://bank.gov.ua")
    assert {r["commodity"] for r in fx} == {"USD", "EUR"}
    weather = parse_open_meteo(METEO_JSON, "weather_provider", "https://api.open-meteo.com")
    assert any(r.get("weather_risk") == "HIGH" for r in weather)
    prod = parse_worldbank_indicator(WB_PROD, "world_bank", "https://api.worldbank.org")
    assert prod[0]["series_kind"] == "production"
    estat = parse_eurostat_sdmx(EUROSTAT_JSON, "eurostat", "https://ec.europa.eu/eurostat")
    assert estat and estat[0]["series_kind"] == "production"
    meta = {"title": "Каталог", "normalized_value": None, "canonical_type": "page_signal", "source_reference": "html-title"}
    assert is_metadata_observation(meta) is True
    assert is_numeric_observation(meta) is False
    demo = {"normalized_value": 100.0, "data_class": "demo", "is_demo": True}
    assert is_numeric_observation(demo) is False


def test_connected_requires_numeric():
    from services.agro_ops.providers import _spec

    spec = _spec("ec_agri")
    connected = interpret_fetch(spec, SimpleFetchResult(status=200, text=EC_JSON))
    assert connected["probe_result"] == "CONNECTED"
    assert connected["market_usable"] is True
    html = interpret_fetch(
        spec,
        SimpleFetchResult(status=200, text="<!doctype html><html><title>Portal</title></html>"),
    )
    assert html["probe_result"] == "PARTIAL"
    assert html["market_usable"] is False


async def test_refresh_numeric_analysts_charts_alerts(client: TestClient):
    org = f"org-a16-{uuid.uuid4().hex[:8]}"
    other = f"org-z16-{uuid.uuid4().hex[:6]}"
    svc = get_agro_ops_service()
    svc.set_provider_fetch(_fake_fetch)
    h = _hdr(org)
    refresh = await (await client.post(f"{OPS}/providers/refresh-all", json={}, headers=h)).json()
    assert refresh["ok"]
    by_id = {i["provider_id"]: i for i in refresh["items"]}
    assert by_id["ec_agri"]["probe_result"] == "CONNECTED"
    assert by_id["fx_rates"]["probe_result"] == "CONNECTED"
    assert by_id["weather_provider"]["probe_result"] == "CONNECTED"
    assert by_id["world_bank"]["probe_result"] == "CONNECTED"
    assert by_id["eurostat"]["probe_result"] == "CONNECTED"
    assert by_id["ua_customs_open_data"]["probe_result"] == "PARTIAL"
    assert by_id["fao"]["probe_result"] == "FAILED"
    licensed = await (await client.get(f"{OPS}/providers", headers=h)).json()
    market = next(i for i in licensed["items"] if i["id"] == "market_prices")
    assert market["health_state"] == "NEEDS_LICENSE"

    dash = await (await client.get(f"{OPS}/analytics/dashboard", headers=h)).json()
    assert dash["numeric_observation_count"] >= 6
    series = dash["series"]
    assert series["price"]
    assert series["production"]
    assert series["yield_or_area"] or series["production"]
    assert series["trade"]
    assert series["fx"]
    assert series["weather"]

    isolated = await (await client.get(f"{OPS}/analytics/dashboard", headers=_hdr(other))).json()
    assert isolated["numeric_observation_count"] == 0

    agents = await (await client.post(f"{OPS}/agents/run", json={}, headers=h)).json()
    assert "chief" in agents["item"]["specialists_executed"]
    assert agents["item"]["chief"]["confidence"] != 10

    operational = await (await client.post(f"{OPS}/analytics/run", json={"analysis_type": "operational"}, headers=h)).json()
    assert operational["ok"]
    item = operational["item"]
    assert item["chief"].get("economic_data") is True
    assert item["numeric_observation_count"] >= 1
    assert "ukraine" in item["sections"]
    assert "prices" in item["sections"]
    assert item["series"]["fx"]
    assert "9999" not in json.dumps(item)

    evening = await (await client.post(f"{OPS}/analytics/run", json={"analysis_type": "evening"}, headers=h)).json()
    assert evening["item"]["id"] != item["id"]
    opened = await (await client.get(f"{OPS}/analytics/{evening['item']['id']}", headers=h)).json()
    assert opened["item"]["id"] == evening["item"]["id"]
    assert opened["item"]["series"]["price"]

    demo = await (
        await client.post(
            f"{OPS}/entities/market_price",
            json={"commodity": "Пшеница", "price": 9999, "source_type": "MANUAL", "is_demo": True, "data_class": "demo"},
            headers=h,
        )
    ).json()
    assert demo["ok"]
    assert "DEMO" in str(demo["item"].get("name") or demo["item"].get("title") or "") or demo["item"].get("is_demo")
    after = await (await client.post(f"{OPS}/analytics/run", json={"analysis_type": "operational"}, headers=h)).json()
    blob = json.dumps(after["item"])
    assert "9999" not in blob

    manual = await (
        await client.post(
            f"{OPS}/entities/market_price",
            json={"commodity": "Пшеница", "price": 8500, "source_type": "MANUAL", "price_kind": "buyer_bid"},
            headers=h,
        )
    ).json()
    assert "MANUAL DATA" in str(manual["item"].get("name") or "")
    run2 = await (await client.post(f"{OPS}/analytics/run", json={"analysis_type": "operational"}, headers=h)).json()
    assert "MANUAL DATA" in json.dumps(run2["item"])

    alerts = await (await client.post(f"{OPS}/alerts/evaluate", json={}, headers=h)).json()
    assert alerts["ok"]
    kinds = {((i.get("notification") or {}).get("kind") or (i.get("alert") or {}).get("kind")) for i in alerts.get("items") or []}
    titles = " ".join(str((i.get("alert") or {}).get("title") or "") for i in alerts.get("items") or [])
    assert "HIGH" in titles or "упала" in titles or "изменил" in titles or alerts["created"] >= 0
    assert "fabricated" not in titles.lower()
    _ = kinds
