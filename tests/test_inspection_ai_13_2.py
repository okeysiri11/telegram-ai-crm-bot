"""Tests — Inspection AI & Damage Assessment (Sprint 13.2)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.register import register_auto_marketplace_routes
from applications.auto_marketplace.shared.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/inspection-ai/v1"
VI = "/api/vin-intelligence/v1"
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


def test_version_inspection_ai_ready():
    health = auto_marketplace.health()
    assert health["application_version"] == "4.1.7-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v4.1.6-enterprise"
    assert health["inspection_ai_ready"] is True
    assert health["damage_detection_ready"] is True
    assert health["vehicle_health_ai_ready"] is True
    assert health["repair_estimation_ready"] is True


def test_image_analysis_and_damage():
    suite = auto_marketplace.inspection_ai
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["report_id"]

    photo = suite.photo.analyze(
        vin="WBA3A5C50EF000001",
        zone="undercarriage",
        media_uri="media://u1.mp4",
        media_type="video",
        signals={"quality": 0.7},
    )
    assert photo["zone"] == "undercarriage"
    with pytest.raises(ValidationError):
        suite.photo.analyze(zone="roof", media_type="photo")

    dent = suite.damage.detect(vin="WBA3A5C50EF000001", damage_type="dent", severity=0.6, location="door")
    assert dent["detected"] is True
    flood = suite.damage.detect(vin="WBA3A5C50EF000001", damage_type="flood", severity=0.8)
    assert flood["level"] == "high"
    assert suite.damage.list_for_vin("WBA3A5C50EF000001")


def test_ai_scoring_and_estimation():
    suite = auto_marketplace.inspection_ai
    vin = "1HGCM82633A000001"
    damages = suite.damage.scan_all(vin=vin, signals={"scratch": 0.5, "dent": 0.4})
    detected = [d for d in damages if d["detected"]]
    estimate = suite.estimation.estimate(vin=vin, damages=detected, market_value=17000)
    assert estimate["repair_cost"] > 0
    assert estimate["parts_cost"] >= 0
    health = suite.health.score(vin=vin, damages=detected)
    assert 0 <= health["overall_condition_score"] <= 100
    report = suite.report.generate(vin=vin, health=health, estimate=estimate, damages=detected, format="pdf")
    assert report["professional_pdf"] is True
    assert report["ai_recommendations"]["purchase"]
    suite.knowledge.link(vin=vin, source="dealer_database", ref_id="d1")
    for dtype in ("inspection", "damage", "repair", "vehicle_health"):
        assert suite.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_inspection_ai(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "4.1.7-enterprise"
    assert body["inspection_ai_ready"] is True

    # Prior sprints still present
    assert (await client.get(f"{VI}/health")).status == 200
    assert (await client.get(f"{EA}/health")).status == 200

    boot = await client.post(f"{PREFIX}/bootstrap", json={})
    assert boot.status == 201

    photo = await client.post(
        f"{PREFIX}/photo",
        json={"vin": "JN1TBNT31U0000001", "zone": "wheel", "media_uri": "media://w.jpg"},
    )
    assert photo.status == 201

    damage = await client.post(
        f"{PREFIX}/damage",
        json={"vin": "JN1TBNT31U0000001", "damage_type": "scratch", "severity": 0.55},
    )
    assert damage.status == 201
    damage_body = await damage.json()

    estimate = await client.post(
        f"{PREFIX}/estimate",
        json={"vin": "JN1TBNT31U0000001", "damages": [damage_body], "market_value": 14000},
    )
    assert estimate.status == 201
    estimate_body = await estimate.json()

    score = await client.post(
        f"{PREFIX}/score",
        json={"vin": "JN1TBNT31U0000001", "damages": [damage_body]},
    )
    assert score.status == 201
    score_body = await score.json()

    report = await client.post(
        f"{PREFIX}/report",
        json={
            "vin": "JN1TBNT31U0000001",
            "health": score_body,
            "estimate": estimate_body,
            "damages": [damage_body],
            "format": "pdf",
        },
    )
    assert report.status == 201

    knowledge = await client.post(
        f"{PREFIX}/knowledge",
        json={"vin": "JN1TBNT31U0000001", "source": "insurance_database", "ref_id": "pol1"},
    )
    assert knowledge.status == 201

    dash = await client.get(f"{PREFIX}/dashboard?type=damage")
    assert dash.status == 200


def test_docs_and_regression_13_2():
    for name in ("INSPECTION_AI.md", "DAMAGE_DETECTION.md", "VEHICLE_HEALTH.md", "REPAIR_ESTIMATION.md"):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "INSPECTION_AI.md").exists()
    assert (ROOT / "applications" / "auto_marketplace" / "inspection_ai" / "facade.py").exists()
    assert (ROOT / "applications" / "auto_marketplace" / "vin_intelligence" / "facade.py").exists()
    assert (ROOT / "applications" / "auto_marketplace" / "enterprise_automotive" / "facade.py").exists()
    manifest = (ROOT / "applications" / "auto_marketplace" / "manifest.json").read_text()
    assert "4.1.7-enterprise" in manifest
    assert "13.7" in manifest

    from applications.ai_os.config import DEFAULT_CONFIG as AIOS
    from applications.enterprise.config import DEFAULT_CONFIG as ENT

    assert AIOS.application_version == "3.4.0-alpha"
    assert ENT.application_version == "4.0.0-enterprise"
