"""Tests — Customs, Border Control & International Trade (Sprint 15.4)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.port_enterprise import port_enterprise
from applications.port_enterprise.api.register import register_port_enterprise_routes
from applications.port_enterprise.shared.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/port-customs/v1"
ML = "/api/port-multimodal/v1"
CM = "/api/port-containers/v1"
NAV = "/api/port-navigation/v1"
PE = "/api/port-enterprise/v1"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_port_enterprise_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    port_enterprise.reset()
    yield
    port_enterprise.reset()


def test_version_customs_ready():
    health = port_enterprise.health()
    assert health["application_version"] == "4.5.7-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v4.5.6-enterprise"
    assert health["customs_platform_ready"] is True
    assert health["border_control_ready"] is True
    assert health["international_trade_ready"] is True
    assert health["trade_compliance_ready"] is True
    assert health["ai_trade_intelligence_ready"] is True


def test_customs_and_border():
    suite = port_enterprise.customs_trade
    office = suite.customs.register_office(name="Test Customs", code="T1")
    decl = suite.customs.declare(
        declaration_type="export",
        reference="DEC-T1",
        office_id=office["office_id"],
        value=5000,
    )
    duty = suite.customs.calculate_duty(declaration_id=decl["declaration_id"], duty_rate=0.05)
    assert duty["total"] > 0
    suite.customs.clear(decl["declaration_id"])
    cp = suite.border.register_checkpoint(name="Gate 1")
    suite.border.crossing(checkpoint_id=cp["checkpoint_id"], direction="out", subject_ref="V1")
    with pytest.raises(ValidationError):
        suite.customs.declare(declaration_type="smuggle", reference="X")


def test_trade_compliance_ai():
    suite = port_enterprise.customs_trade
    boot = suite.bootstrap()
    assert boot["declaration_id"] and boot["import_id"] and boot["fraud_id"]
    assert suite.trade.status()["imports"] >= 1
    assert suite.compliance.status()["licenses"] >= 1
    assert suite.documents.status()["signatures"] >= 1
    assert suite.ai.status()["risk_scores"] >= 1
    with pytest.raises(ValidationError):
        suite.trade.set_incoterm(trade_ref="x", incoterm="ZZZ")
    for dtype in ("customs", "border", "trade", "compliance", "ai_trade"):
        assert suite.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_customs(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "4.5.7-enterprise"
    assert body["customs_platform_ready"] is True
    assert body["ai_trade_intelligence_ready"] is True

    assert (await client.get(f"{ML}/health")).status == 200
    assert (await client.get(f"{CM}/health")).status == 200
    assert (await client.get(f"{NAV}/health")).status == 200
    assert (await client.get(f"{PE}/health")).status == 200

    boot = await client.post(f"{PREFIX}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    clear = await client.post(
        f"{PREFIX}/customs",
        json={"action": "clear", "declaration_id": boot_body["declaration_id"], "status": "cleared"},
    )
    assert clear.status == 201

    fraud = await client.post(
        f"{PREFIX}/ai",
        json={"action": "fraud", "trade_ref": boot_body["import_id"], "anomaly_score": 0.1},
    )
    assert fraud.status == 201

    dash = await client.get(f"{PREFIX}/dashboard?type=compliance")
    assert dash.status == 200


def test_docs_and_regression_15_4():
    for name in (
        "CUSTOMS_MANAGEMENT.md",
        "BORDER_CONTROL.md",
        "INTERNATIONAL_TRADE.md",
        "TRADE_COMPLIANCE.md",
        "TRADE_DOCUMENTS.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "PORT_CUSTOMS.md").exists()
    assert (ROOT / "applications" / "port_enterprise" / "customs_trade" / "facade.py").exists()
    assert (ROOT / "applications" / "port_enterprise" / "multimodal_logistics" / "facade.py").exists()

    from applications.ai_os.config import DEFAULT_CONFIG as AIOS
    from applications.enterprise.config import DEFAULT_CONFIG as ENT
    from applications.auto_marketplace.config import DEFAULT_CONFIG as AUTO
    from applications.agro_enterprise.config import DEFAULT_CONFIG as AGRO
    from applications.port_erp.config import DEFAULT_CONFIG as PORT_ERP

    assert AIOS.application_version == "3.4.0-alpha"
    assert ENT.application_version == "4.0.0-enterprise"
    assert AUTO.application_version == "4.2.0-enterprise"
    assert AGRO.application_version == "4.4.0-enterprise"
    assert PORT_ERP.application_version == "2.0.0"
    manifest = (ROOT / "applications" / "port_enterprise" / "manifest.json").read_text()
    assert "4.5.7-enterprise" in manifest
    assert "15.7" in manifest
