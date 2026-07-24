"""Tests — Enterprise Process Mining Platform (Sprint 20.10)."""

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


def test_version_epm_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "7.6.0"
    assert health["enterprise_foundation"] == "Enterprise Platform v7.5.0"
    assert health["process_mining_ready"] is True
    assert health["process_discovery_ready"] is True
    assert health["conformance_ready"] is True
    assert health["bottleneck_detection_ready"] is True
    assert health["simulation_engine_ready"] is True
    assert health["engines"]["process_mining"] == "1.0"


def test_collect_discover_conformance():
    suite = enterprise_hub.process_mining
    suite.collector.collect(source="crm", activity="create_request", case_id="X1")
    suite.collector.collect(source="workflow", activity="approve", case_id="X1")
    suite.collector.collect(source="crm", activity="close", case_id="X1")
    suite.normalizer.normalize()
    disc = suite.discovery.discover(name="mini")
    conf = suite.conformance.check(process_id=disc["process_id"])
    assert conf["conformance_id"]
    bn = suite.bottlenecks.detect(process_id=disc["process_id"])
    assert bn["count"] >= 1
    enterprise_hub.reset()
    with pytest.raises(ValidationError):
        suite.discovery.discover(name="empty")


def test_bootstrap_dashboard():
    suite = enterprise_hub.process_mining
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "7.6.0"
    assert boot["events_collected"] >= 20
    assert boot["variant_count"] >= 2
    assert boot["top_cause"]
    assert boot["dashboard_id"]
    assert boot["expected_effect"]
    assert boot["integrations"]["linked"] is True


@pytest.mark.asyncio
async def test_api_epm(client):
    health = await client.get(f"{EPM}/health")
    body = await health.json()
    assert body["application_version"] == "7.6.0"
    assert body["process_mining_ready"] is True

    boot = await client.post(f"{EPM}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    created = await client.post(
        f"{EPM}/events",
        json={"source": "crm", "activity": "create_request", "case_id": "API1"},
    )
    assert created.status == 201

    for prefix in (HUB, ORCH, KG, AA, CM, WF, EIP, EDP, ISAM, OBS, TN, AOP, ATS, EKP, AIOS, EVP, SDP, EDF, EDT, ESI):
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        assert (await resp.json())["application_version"] == "7.6.0"

    assert boot_body["process_id"]


def test_docs_and_regression_20_10():
    for name in (
        "ENTERPRISE_PROCESS_MINING.md",
        "EPM_DISCOVERY.md",
        "EPM_CONFORMANCE.md",
        "EPM_OPTIMIZATION_DASHBOARD.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_PROCESS_MINING.md").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "process_mining" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "process_mining" / "mining" / "variants.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "process_mining" / "visualization" / "dashboards.py").exists()

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
    assert "7.6.0" in manifest
    assert "24.6" in manifest
