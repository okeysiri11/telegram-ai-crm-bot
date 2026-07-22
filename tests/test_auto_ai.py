"""Tests — Auto Marketplace AI Intelligence (Sprint 10.3)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.register import register_auto_marketplace_routes
from applications.auto_marketplace.shared.models import Vehicle, VehicleSpecification, VehicleStatus


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_auto_marketplace_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    auto_marketplace.reset()
    yield
    auto_marketplace.reset()


def test_version_modules_docs_bridges():
    health = auto_marketplace.health()
    assert health["application_version"] == "2.0.0"
    assert health["auto_ai_engine"] == "1.0"
    assert health["recommendation_engine"] == "1.0"
    assert "auto_ai" in health
    docs = Path(__file__).resolve().parents[1] / "docs" / "AUTO_AI.md"
    assert docs.exists()
    assert "2.0.0" in docs.read_text(encoding="utf-8")
    assert auto_marketplace.platform.platform_health()["platform_dependency"] == "AI Platform Core v3"
    root = Path(__file__).resolve().parents[1] / "applications" / "auto_marketplace"
    for name in (
        "ai",
        "recommendations",
        "matching",
        "inspection_ai",
        "pricing_ai",
        "forecasting",
        "risk",
        "assistant",
        "knowledge",
        "analytics",
    ):
        assert (root / name).is_dir()


def _seed_vehicle(**kwargs) -> Vehicle:
    defaults = dict(
        specification=VehicleSpecification(make="Toyota", model="Camry", year=2021, mileage_km=30000, body_type="sedan"),
        price=22000,
        status=VehicleStatus.LISTED,
    )
    defaults.update(kwargs)
    return auto_marketplace.catalog.create_vehicle(Vehicle(**defaults))


def test_ai_recommendations():
    v1 = _seed_vehicle()
    _seed_vehicle(
        specification=VehicleSpecification(make="Toyota", model="Corolla", year=2020, mileage_km=40000, body_type="sedan"),
        price=18000,
    )
    personal = auto_marketplace.auto_ai.recommendations.personal(
        "buyer-1", {"budget_max": 25000, "make": "Toyota"}, limit=5
    )
    assert personal
    similar = auto_marketplace.auto_ai.recommendations.similar(v1.vehicle_id)
    assert isinstance(similar, list)
    alts = auto_marketplace.auto_ai.recommendations.alternatives(v1.vehicle_id)
    assert isinstance(alts, list)
    budget = auto_marketplace.auto_ai.recommendations.budget_optimize("buyer-1", 20000)
    assert isinstance(budget, list)
    ownership = auto_marketplace.auto_ai.recommendations.ownership_cost(v1.vehicle_id)
    assert ownership.payload["annual_cost"] > 0
    assert auto_marketplace.auto_ai.recommendations.family("buyer-1")
    assert auto_marketplace.auto_ai.recommendations.commercial("buyer-1")
    assert auto_marketplace.auto_ai.recommendations.fleet("buyer-1", fleet_size=3)


def test_pricing_ai_and_forecast():
    insight = auto_marketplace.auto_ai.pricing_ai.analyze(
        vehicle_id="v1", year=2021, mileage_km=30000, base_price=20000
    )
    assert insight.market_value > 0
    assert insight.retail_price >= insight.wholesale_price
    assert insight.trend in ("rising", "stable", "declining")
    assert insight.depreciation_12m >= 0
    assert insight.residual_value_36m > 0
    forecast = auto_marketplace.auto_ai.forecasting.forecast(
        vehicle_id="v1", year=2021, mileage_km=30000, base_price=20000
    )
    assert forecast.future_value > 0
    assert forecast.ownership_cost_12m > 0
    assert forecast.market_demand in ("high", "medium", "low")


def test_inspection_ai_and_assistant_knowledge():
    result = auto_marketplace.auto_ai.inspection_ai.analyze(
        vehicle_id="v1",
        photo_urls=["a.jpg", "b.jpg", "c.jpg", "d.jpg"],
        hints={"damage": [{"area": "bumper", "severity": "low"}]},
    )
    assert result.overall_score > 0
    assert result.risk_score >= 0
    assert "damage_detected" in result.findings or result.damage_detected
    reply = auto_marketplace.auto_ai.assistant.ask("Find Toyota under 25000", budget=25000)
    assert reply.intent in ("search", "purchase", "question")
    assert reply.answer
    card = auto_marketplace.auto_ai.knowledge.ensure_default("Toyota", "Camry", 2021)
    assert card.reliability_rating > 0
    assert card.service_intervals_km > 0


@pytest.mark.asyncio
async def test_rest_auto_ai_endpoints(client: TestClient):
    health = await client.get("/api/auto/v1/ai")
    assert health.status == 200
    body = await health.json()
    assert body["application_version"] == "2.0.0"
    assert body["auto_ai_engine"] == "1.0"

    rec = await client.post(
        "/api/auto/v1/recommendations/personal",
        json={"buyer_id": "b1", "preferences": {"budget_max": 30000}},
    )
    assert rec.status == 200

    pricing = await client.post(
        "/api/auto/v1/pricing-ai/analyze",
        json={"base_price": 18000, "year": 2019, "mileage_km": 60000},
    )
    assert pricing.status == 201

    inspection = await client.post(
        "/api/auto/v1/inspection/analyze",
        json={"vehicle_id": "v1", "photo_urls": ["1", "2", "3"]},
    )
    assert inspection.status == 201

    forecast = await client.post(
        "/api/auto/v1/forecast",
        json={"base_price": 18000, "year": 2019, "mileage_km": 60000},
    )
    assert forecast.status == 201

    assistant = await client.post(
        "/api/auto/v1/assistant/ask",
        json={"query": "How should I negotiate the price?"},
    )
    assert assistant.status == 201
    assistant_body = await assistant.json()
    assert assistant_body["intent"] == "negotiation"


def test_platform_core_untouched():
    root = Path(__file__).resolve().parents[1]
    assert (root / "applications" / "auto_marketplace" / "ai").is_dir()
    assert not (root / "ecosystem" / "auto_marketplace").exists()
