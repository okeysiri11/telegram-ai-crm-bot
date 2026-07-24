"""Tests — Enterprise Unified Data Fabric (Sprint 20.7)."""

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


def test_version_edf_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "7.0.0"
    assert health["enterprise_foundation"] == "Enterprise Platform v6.12.0"
    assert health["data_fabric_ready"] is True
    assert health["data_catalog_ready"] is True
    assert health["federation_ready"] is True
    assert health["data_governance_ready"] is True
    assert health["developer_platform_ready"] is True
    assert health["engines"]["data_fabric"] == "1.0"
    assert health["engines"]["edp"] == "1.0"


def test_catalog_federation_governance():
    suite = enterprise_hub.data_fabric
    asset = suite.catalog.register(name="crm.accounts", kind="table", source="crm")
    meta = suite.metadata.set_metadata(asset_id=asset["asset_id"], sensitivity="confidential")
    assert meta["sensitivity"] == "confidential"
    fed = suite.federation.federate(sources=["crm", "erp", "knowledge"], query="account E1")
    assert fed["result"]["entity_id"] == "E1"
    gov = suite.governance.enforce(asset_id=asset["asset_id"])
    assert gov["access_policy_id"]
    qual = suite.quality.assess(asset_id=asset["asset_id"])
    assert qual["passed"] is True
    with pytest.raises(ValidationError):
        suite.federation.federate(sources=["crm"], query="x")


def test_bootstrap_cache_dashboard():
    suite = enterprise_hub.data_fabric
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "7.0.0"
    assert boot["route_cache_hit"] is True
    assert boot["unified_from_cache"] is True
    assert boot["quality_passed"] is True
    assert boot["dashboard"]["usage_id"]
    assert boot["dashboard"]["assets"] >= 7


@pytest.mark.asyncio
async def test_api_edf(client):
    health = await client.get(f"{EDF}/health")
    body = await health.json()
    assert body["application_version"] == "7.0.0"
    assert body["data_fabric_ready"] is True

    boot = await client.post(f"{EDF}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    created = await client.post(
        f"{EDF}/catalog",
        json={"name": "api.table", "kind": "table", "source": "postgresql"},
    )
    assert created.status == 201

    for prefix in (HUB, ORCH, KG, AA, CM, WF, EIP, EDP, ISAM, OBS, TN, AOP, ATS, EKP, AIOS, EVP, SDP):
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        assert (await resp.json())["application_version"] == "7.0.0"

    assert boot_body["governance_id"]


def test_docs_and_regression_20_7():
    for name in (
        "ENTERPRISE_DATA_FABRIC.md",
        "EDF_CATALOG.md",
        "EDF_FEDERATION.md",
        "EDF_GOVERNANCE.md",
        "EDF_QUALITY_CACHE.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_DATA_FABRIC.md").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "data_fabric" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "data_fabric" / "connectors" / "postgresql.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "data_fabric" / "policies" / "masking.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "data_platform").exists()

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
    assert "7.0.0" in manifest
    assert "24.0" in manifest
