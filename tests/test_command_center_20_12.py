"""Tests — Enterprise Command Center (Sprint 20.12)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes
from applications.enterprise_hub.shared.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
HUB = "/api/enterprise-hub/v1"
ORCH = "/api/enterprise-orch/v1"
KG = "/api/enterprise-kg/v1"
AA = "/api/enterprise-agents/v1"
CM = "/api/enterprise-comms/v1"
WF = "/api/enterprise-workflow/v1"
EIP = "/api/enterprise-eip/v1"
EDP = "/api/enterprise-edp/v1"
ISAM = "/api/enterprise-isam/v1"
OBS = "/api/enterprise-obs/v1"
TN = "/api/enterprise-tenancy/v1"
AOP = "/api/enterprise-aop/v1"
ATS = "/api/enterprise-ats/v1"
EKP = "/api/enterprise-ekp/v1"
AIOS = "/api/enterprise-aios/v1"
EVP = "/api/enterprise-evp/v1"
SDP = "/api/enterprise-sdp/v1"
EDF = "/api/enterprise-edf/v1"
EDT = "/api/enterprise-edt/v1"
ESI = "/api/enterprise-esi/v1"
EPM = "/api/enterprise-epm/v1"
EBC = "/api/enterprise-ebc/v1"
ECC = "/api/enterprise-ecc/v1"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_enterprise_hub_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    enterprise_hub.reset()
    yield
    enterprise_hub.reset()


def test_version_ecc_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "7.2.0"
    assert health["enterprise_foundation"] == "Enterprise Platform v7.1.0"
    assert health["command_center_ready"] is True
    assert health["executive_dashboard_ready"] is True
    assert health["health_monitor_ready"] is True
    assert health["action_center_ready"] is True
    assert health["business_capabilities_ready"] is True
    assert health["engines"]["command_center"] == "1.0"


def test_health_alerts_actions():
    suite = enterprise_hub.command_center
    health = suite.health.evaluate()
    assert 0.0 < health["enterprise_health_score"] <= 1.0
    alert = suite.alerts.raise_alert(kind="financial_risk", severity="critical", message="Cash gap")
    assert alert["alert_id"]
    action = suite.actions.dispatch(kind="approve", payload={"doc": "PO-1"})
    assert action["status"] == "accepted"
    cmd = suite.dispatcher.dispatch_command(command="Run simulation for berth plan")
    assert cmd["resolved_kind"] == "run_simulation"
    with pytest.raises(ValidationError):
        suite.alerts.raise_alert(kind="financial_risk", severity="critical", message="")


def test_bootstrap_dashboard():
    suite = enterprise_hub.command_center
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "7.2.0"
    assert boot["enterprise_health_score"] > 0
    assert boot["executive_id"]
    assert boot["situation_id"]
    assert boot["daily_brief"]
    assert boot["map_entities"] >= 8
    assert boot["alerts_open"] >= 2
    assert boot["dashboards"] >= 5
    assert boot["integrations"]["linked"] is True


@pytest.mark.asyncio
async def test_api_ecc(client):
    health = await client.get(f"{ECC}/health")
    body = await health.json()
    assert body["application_version"] == "7.2.0"
    assert body["command_center_ready"] is True

    boot = await client.post(f"{ECC}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    dash = await client.get(f"{ECC}/dashboards")
    assert dash.status == 200
    assert (await dash.json())["dashboards"] >= 5

    for prefix in (
        HUB, ORCH, KG, AA, CM, WF, EIP, EDP, ISAM, OBS, TN, AOP, ATS, EKP, AIOS, EVP, SDP, EDF, EDT, ESI, EPM, EBC
    ):
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        assert (await resp.json())["application_version"] == "7.2.0"

    assert boot_body["map_id"]


def test_docs_and_regression_20_12():
    for name in (
        "ENTERPRISE_COMMAND_CENTER.md",
        "ECC_DASHBOARDS.md",
        "ECC_HEALTH_ACTIONS.md",
        "ECC_SITUATION_MAP.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_COMMAND_CENTER.md").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "command_center" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "command_center" / "dashboards" / "maritime.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "command_center" / "widgets" / "ai_summary.py").exists()

    from applications.ai_os.config import DEFAULT_CONFIG as AIOS_CFG
    from applications.enterprise.config import DEFAULT_CONFIG as ENT
    from applications.auto_marketplace.config import DEFAULT_CONFIG as AUTO
    from applications.agro_enterprise.config import DEFAULT_CONFIG as AGRO
    from applications.port_enterprise.config import DEFAULT_CONFIG as PORT
    from applications.port_erp.config import DEFAULT_CONFIG as PORT_ERP
    from applications.crypto_enterprise.config import DEFAULT_CONFIG as CRYPTO
    from applications.legal_enterprise.config import DEFAULT_CONFIG as LEGAL
    from applications.finance_enterprise.config import DEFAULT_CONFIG as FINANCE

    assert AIOS_CFG.application_version == "3.4.0-alpha"
    assert ENT.application_version == "4.0.0-enterprise"
    assert AUTO.application_version == "4.2.0-enterprise"
    assert AGRO.application_version == "4.4.0-enterprise"
    assert PORT.application_version == "4.6.0-enterprise"
    assert PORT_ERP.application_version == "2.0.0"
    assert CRYPTO.application_version == "4.8.0-enterprise"
    assert LEGAL.application_version == "5.0.0-enterprise"
    assert FINANCE.application_version == "5.2.0-enterprise"
    manifest = (ROOT / "applications" / "enterprise_hub" / "manifest.json").read_text()
    assert "7.2.0" in manifest
    assert "24.2" in manifest
