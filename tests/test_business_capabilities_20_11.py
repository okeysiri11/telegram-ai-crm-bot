"""Tests — Enterprise Business Capability Platform (Sprint 20.11)."""

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


def test_version_ebc_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "6.12.0"
    assert health["enterprise_foundation"] == "Enterprise Platform v6.11.0"
    assert health["business_capabilities_ready"] is True
    assert health["capability_registry_ready"] is True
    assert health["maturity_engine_ready"] is True
    assert health["capability_roadmap_ready"] is True
    assert health["process_mining_ready"] is True
    assert health["engines"]["business_capabilities"] == "1.0"


def test_register_hierarchy_impact():
    suite = enterprise_hub.business_capabilities
    suite.registry.register(key="enterprise", name="Enterprise", domain="custom", maturity_level=3)
    suite.registry.register(
        key="ops", name="Operations", domain="custom", parent_key="enterprise", maturity_level=2
    )
    suite.registry.register(key="sales", name="Sales", domain="sales", parent_key="ops", maturity_level=2)
    suite.registry.register(key="crm", name="CRM", domain="crm", parent_key="ops", maturity_level=3)
    suite.dependencies.link("sales", "crm")
    hier = suite.mapper.hierarchy(root_key="enterprise")
    assert hier["node_count"] == 4
    impact = suite.impact.analyze("sales")
    assert "crm" in impact["downstream"]
    mat = suite.maturity.assess()
    assert mat["average_maturity"] > 0
    with pytest.raises(ValidationError):
        suite.registry.register(key="sales", name="dup", domain="sales")


def test_bootstrap_dashboard():
    suite = enterprise_hub.business_capabilities
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "6.12.0"
    assert boot["capabilities_total"] >= 20
    assert boot["dependencies_linked"] >= 5
    assert boot["dashboard_id"]
    assert boot["roadmap_id"]
    assert boot["recommendation_count"] >= 1
    assert boot["integrations"]["linked"] is True


@pytest.mark.asyncio
async def test_api_ebc(client):
    health = await client.get(f"{EBC}/health")
    body = await health.json()
    assert body["application_version"] == "6.12.0"
    assert body["business_capabilities_ready"] is True

    boot = await client.post(f"{EBC}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    caps = await client.get(f"{EBC}/capabilities")
    assert caps.status == 200
    caps_body = await caps.json()
    assert caps_body["capabilities"] >= 20
    assert len(caps_body["items"]) >= 20

    for prefix in (HUB, ORCH, KG, AA, CM, WF, EIP, EDP, ISAM, OBS, TN, AOP, ATS, EKP, AIOS, EVP, SDP, EDF, EDT, ESI, EPM):
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        assert (await resp.json())["application_version"] == "6.12.0"

    assert boot_body["dashboard_id"]


def test_docs_and_regression_20_11():
    for name in (
        "ENTERPRISE_BUSINESS_CAPABILITIES.md",
        "EBC_REGISTRY.md",
        "EBC_MATURITY_IMPACT.md",
        "EBC_ROADMAP_DASHBOARD.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_BUSINESS_CAPABILITIES.md").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "business_capabilities" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "business_capabilities" / "capabilities" / "maritime.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "business_capabilities" / "visualization" / "dashboards.py").exists()

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
    assert "6.12.0" in manifest
    assert "23.1" in manifest
