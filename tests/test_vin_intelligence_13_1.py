"""Tests — VIN Intelligence & Digital Passport (Sprint 13.1)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.register import register_auto_marketplace_routes
from applications.auto_marketplace.shared.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/vin-intelligence/v1"
EA = "/api/auto-marketplace/v1"


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


def test_version_vin_intelligence_ready():
    health = auto_marketplace.health()
    assert health["application_version"] == "4.1.1-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v4.1.0-enterprise"
    assert health["vin_intelligence_ready"] is True
    assert health["digital_passport_ready"] is True
    assert health["vehicle_history_ai_ready"] is True
    assert health["fraud_detection_ready"] is True


def test_vin_decode_and_passport():
    suite = auto_marketplace.vin_intelligence
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["passport_id"]

    decoded = suite.decoder.decode("5YJ3E1EA1KF000001")
    assert decoded["manufacturer"] == "Tesla"
    assert decoded["engine"]["fuel"] == "electric"
    assert decoded["market_region"] == "NA"

    passport = suite.passport.create(vin="5YJ3E1EA1KF000001", decode_id=decoded["decode_id"])
    suite.passport.add_timeline_event(
        passport_id=passport["passport_id"],
        timeline="accident",
        event={"severity": "minor"},
    )
    suite.passport.add_timeline_event(
        passport_id=passport["passport_id"],
        timeline="warranty",
        event={"status": "active"},
    )
    loaded = suite.passport.get_by_vin("5YJ3E1EA1KF000001")
    assert loaded["timelines"]["accident"]
    assert suite.decoder.manufacturer_lookup("WBA")["manufacturer"] == "BMW"


def test_history_and_fraud():
    suite = auto_marketplace.vin_intelligence
    vin = "WBA3A5C50EF000001"
    suite.history.add(vin=vin, history_type="auction", detail={"lot": 12}, source="auction")
    suite.history.add(vin=vin, history_type="police", detail={"note": "clear"}, source="gov")
    suite.history.add(vin=vin, history_type="recall", detail={"campaign": "airbag"}, source="oem")
    assert len(suite.history.list_for_vin(vin)) == 3

    fake = suite.analysis.detect_fake_vin("AAAA")
    assert fake["fake"] is True
    fraud = suite.analysis.detect_fraud(vin=vin, listing_price=500, claimed_mileage=50)
    assert fraud["fraudulent"] is True
    odo = suite.analysis.predict_odometer_fraud(vin=vin, mileage=1000, year=2015)
    assert odo["rollback_suspected"] is True
    assert suite.analysis.accident_probability(vin=vin, age_years=8)["probability"] > 0
    with pytest.raises(ValidationError):
        suite.analysis.run(kind="telepathy")


def test_ai_recommendations_graph_dashboard():
    suite = auto_marketplace.vin_intelligence
    vin = "1HGCM82633A000001"
    suite.decoder.decode(vin)
    value = suite.analysis.market_value(vin=vin, mileage=30000, base_price=18000)
    scores = suite.recommendations.score(vin=vin, market_value=float(value["estimate"]), mileage=30000)
    assert scores["purchase_score"] >= 0
    assert scores["maintenance_plan"]

    suite.graph.upsert_node(graph="owner", node_id="o1", label="Owner")
    suite.graph.upsert_node(graph="part", node_id="p1", label="Brake Pad")
    suite.graph.link(graph="repair", source="o1", target="p1", relation="installed")
    suite.integrations.connect(channel="telematics", endpoint="gps://fleet")
    for dtype in ("vin", "fraud", "market", "passport"):
        assert suite.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_vin_intelligence(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "4.1.1-enterprise"
    assert body["vin_intelligence_ready"] is True

    # Sprint 13.0 API still present
    ea_health = await client.get(f"{EA}/health")
    assert ea_health.status == 200

    boot = await client.post(f"{PREFIX}/bootstrap", json={})
    assert boot.status == 201

    decode = await client.post(f"{PREFIX}/decode", json={"vin": "JN1TBNT31U0000001"})
    assert decode.status == 201

    passport = await client.post(f"{PREFIX}/passport", json={"vin": "JN1TBNT31U0000001", "title": "Leaf"})
    assert passport.status == 201

    analysis = await client.post(f"{PREFIX}/analysis", json={"kind": "fraud_detection", "vin": "JN1TBNT31U0000001", "listing_price": 14000})
    assert analysis.status == 201

    history = await client.post(f"{PREFIX}/history", json={"vin": "JN1TBNT31U0000001", "history_type": "inspection", "detail": {"result": "pass"}})
    assert history.status == 201

    rec = await client.post(f"{PREFIX}/recommendations", json={"vin": "JN1TBNT31U0000001", "mileage": 40000})
    assert rec.status == 201

    graph = await client.post(f"{PREFIX}/graph", json={"graph": "insurance", "node_id": "pol1", "label": "Policy"})
    assert graph.status == 201

    integ = await client.post(f"{PREFIX}/integrations", json={"channel": "insurance_apis", "endpoint": "https://ins.example"})
    assert integ.status == 201

    dash = await client.get(f"{PREFIX}/dashboard?type=fraud")
    assert dash.status == 200


def test_docs_and_regression_13_1():
    for name in ("VIN_INTELLIGENCE.md", "DIGITAL_PASSPORT.md", "VEHICLE_HISTORY.md", "FRAUD_DETECTION.md"):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "VIN_INTELLIGENCE.md").exists()
    assert (ROOT / "applications" / "auto_marketplace" / "vin_intelligence" / "facade.py").exists()
    # Sprint 13.0 package untouched as a module tree
    assert (ROOT / "applications" / "auto_marketplace" / "enterprise_automotive" / "facade.py").exists()

    from applications.ai_os.config import DEFAULT_CONFIG as AIOS
    from applications.enterprise.config import DEFAULT_CONFIG as ENT

    assert AIOS.application_version == "3.4.0-alpha"
    assert ENT.application_version == "4.0.0-enterprise"
