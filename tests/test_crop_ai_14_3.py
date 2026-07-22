"""Tests — Crop AI, Disease & Autonomous Farm (Sprint 14.3)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.agro_enterprise import agro_enterprise
from applications.agro_enterprise.api.register import register_agro_enterprise_routes
from applications.agro_enterprise.shared.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/crop-ai/v1"
SI = "/api/smart-irrigation/v1"
PA = "/api/precision-agriculture/v1"
AE = "/api/agro-enterprise/v1"


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
def reset_store():
    agro_enterprise.reset()
    yield
    agro_enterprise.reset()


def test_version_crop_ai_ready():
    health = agro_enterprise.health()
    assert health["application_version"] == "4.3.6-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v4.3.5-enterprise"
    assert health["crop_ai_ready"] is True
    assert health["disease_detection_ready"] is True
    assert health["pest_intelligence_ready"] is True
    assert health["yield_intelligence_ready"] is True
    assert health["autonomous_farm_ready"] is True


def test_crop_disease_pest():
    suite = agro_enterprise.crop_ai
    crop = suite.crops.register_crop(name="Maize", variety="DK")
    suite.crops.track_stage(crop["crop_id"], stage="vegetative", phenology_day=40)
    dis = suite.disease.detect(crop_id=crop["crop_id"], part="leaf", disease_type="viral", severity=0.4)
    assert dis["treatment_recommendation"]
    pest = suite.pests.identify(crop_id=crop["crop_id"], pest_name="corn_borer", population_index=0.7)
    assert pest["risk_level"] == "high"
    with pytest.raises(ValidationError):
        suite.disease.detect(crop_id=crop["crop_id"], part="flower")


def test_yield_and_autonomous_ops():
    suite = agro_enterprise.crop_ai
    boot = suite.bootstrap()
    pred = suite.yield_intel.predict(crop_id=boot["crop_id"], hectares=20, health_score=85, ndvi=0.7)
    assert pred["total_t"] > 0
    mission = suite.ops.schedule_mission(field_id="f1", mission_type="drone_survey")
    suite.ops.assign(mission["mission_id"], asset="UAV-9", asset_kind="drone")
    rec = suite.decisions.recommend(crop_id=boot["crop_id"], intent="nutrient")
    assert rec["actions"]
    for dtype in ("crop_health", "disease", "pest", "yield", "farm_operations", "ai_recommendation"):
        assert suite.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_crop_ai(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "4.3.6-enterprise"
    assert body["crop_ai_ready"] is True
    assert body["autonomous_farm_ready"] is True

    assert (await client.get(f"{SI}/health")).status == 200
    assert (await client.get(f"{PA}/health")).status == 200
    assert (await client.get(f"{AE}/health")).status == 200

    boot = await client.post(f"{PREFIX}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    disease = await client.post(
        f"{PREFIX}/disease",
        json={"crop_id": boot_body["crop_id"], "part": "fruit", "disease_type": "fungal"},
    )
    assert disease.status == 201

    yld = await client.post(f"{PREFIX}/yield", json={"crop_id": boot_body["crop_id"], "hectares": 15})
    assert yld.status == 201

    dash = await client.get(f"{PREFIX}/dashboard?type=yield")
    assert dash.status == 200


def test_docs_and_regression_14_3():
    for name in (
        "CROP_AI.md",
        "DISEASE_DETECTION.md",
        "PEST_INTELLIGENCE.md",
        "YIELD_PREDICTION.md",
        "AUTONOMOUS_FARM.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "CROP_AI.md").exists()
    assert (ROOT / "applications" / "agro_enterprise" / "crop_ai" / "facade.py").exists()
    for pkg in ("smart_irrigation", "precision_agriculture"):
        assert (ROOT / "applications" / "agro_enterprise" / pkg / "facade.py").exists()

    from applications.ai_os.config import DEFAULT_CONFIG as AIOS
    from applications.enterprise.config import DEFAULT_CONFIG as ENT
    from applications.auto_marketplace.config import DEFAULT_CONFIG as AUTO
    from applications.agro_marketplace.config import DEFAULT_CONFIG as AGRO

    assert AIOS.application_version == "3.4.0-alpha"
    assert ENT.application_version == "4.0.0-enterprise"
    assert AUTO.application_version == "4.2.0-enterprise"
    assert AGRO.application_version == "2.0.0"
    manifest = (ROOT / "applications" / "agro_enterprise" / "manifest.json").read_text()
    assert "4.3.6-enterprise" in manifest
    assert "14.6" in manifest
