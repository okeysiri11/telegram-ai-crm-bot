"""Tests — Enterprise API Standardization (Sprint 21.2 / v6.0.0)."""

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
EAS = "/api/enterprise-eas/v1"


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


def test_version_eas_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "7.0.0"
    assert health["enterprise_foundation"] == "Enterprise Platform v6.12.0"
    assert health["api_standardization_ready"] is True
    assert health["api_inventory_ready"] is True
    assert health["openapi_ready"] is True
    assert health["api_governance_ready"] is True
    assert health["command_center_ready"] is True
    assert health["engines"]["api_standardization"] == "1.0"


def test_inventory_response_events():
    suite = enterprise_hub.api_standardization
    inv = suite.inventory.scan()
    assert inv["total"] >= 20
    assert inv["by_category"]["public"] >= 1
    ok = suite.success({"hello": "world"})
    assert ok["success"] is True
    assert ok["request_id"]
    assert ok["timestamp"]
    err = suite.error(error_code="bad_request", message="nope")
    assert err["success"] is False
    assert err["trace_id"]
    evt = suite.events.publish(
        {
            "id": "evt_t1",
            "type": "test.created",
            "source": "test",
            "aggregate": "task",
            "version": 1,
            "payload": {},
            "timestamp": ok["timestamp"],
            "correlation_id": "c1",
        }
    )
    assert evt["id"] == "evt_t1"
    with pytest.raises(ValidationError):
        suite.events.validate_event({"id": "x"})


def test_bootstrap_governance():
    suite = enterprise_hub.api_standardization
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "7.0.0"
    assert boot["openapi_version"] == "3.1.0"
    assert boot["swagger_id"]
    assert boot["redoc_id"]
    assert boot["gateways_compatible"] is True
    assert boot["governance_passed"] is True
    assert boot["unified_response"]["success"] is True
    assert boot["integrations"]["linked"] is True


@pytest.mark.asyncio
async def test_api_eas(client):
    health = await client.get(f"{EAS}/health")
    body = await health.json()
    assert body["success"] is True
    assert body["data"]["application_version"] == "7.0.0"
    assert body["data"]["api_standardization_ready"] is True

    boot = await client.post(f"{EAS}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    inv = await client.get(f"{EAS}/inventory")
    assert inv.status == 200
    inv_body = await inv.json()
    assert inv_body["success"] is True
    assert inv_body["data"]["endpoints"] >= 20

    for prefix in (
        HUB, ORCH, KG, AA, CM, WF, EIP, EDP, ISAM, OBS, TN, AOP, ATS, EKP, AIOS, EVP, SDP, EDF, EDT, ESI, EPM, EBC, ECC
    ):
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        assert (await resp.json())["application_version"] == "7.0.0"

    assert boot_body["governance_passed"] is True


def test_docs_and_regression_21_2():
    for name in (
        "ENTERPRISE_API_STANDARDIZATION.md",
        "EAS_INVENTORY.md",
        "EAS_RESPONSE_AUTH.md",
        "EAS_OPENAPI_GOVERNANCE.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_API_STANDARDIZATION.md").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "api_standardization" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "api_standardization" / "docs_gen" / "openapi.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "api_standardization" / "governance" / "naming.py").exists()

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
