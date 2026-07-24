"""Tests — Enterprise Data Contracts (Sprint 21.3 / v6.0.0-rc6)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes
from applications.enterprise_hub.shared.exceptions import ValidationError
from platform_contracts.dto.base import BaseDTO
from platform_contracts.dto.crm import ContactDTO


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
EDC = "/api/enterprise-edc/v1"


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


def test_version_edc_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "6.0.0-rc6"
    assert health["enterprise_foundation"] == "Enterprise Platform v6.0.0-rc5"
    assert health["data_contracts_ready"] is True
    assert health["dto_registry_ready"] is True
    assert health["schema_registry_ready"] is True
    assert health["contract_testing_ready"] is True
    assert health["api_standardization_ready"] is True
    assert health["engines"]["data_contracts"] == "1.0"


def test_base_dto_and_validation():
    dto = ContactDTO(name="Ada", tenant_id="t1")
    assert dto.id.startswith("dto_")
    assert isinstance(dto, BaseDTO)
    suite = enterprise_hub.data_contracts
    ok = suite.validate_dto(dto.to_dict())
    assert ok["valid"] is True
    mapped = suite.map_dto_to_event(dto.to_dict())
    assert mapped["event"]["aggregate_id"] == dto.id
    with pytest.raises(ValidationError):
        suite.serialize({"x": 1}, format="xml")


def test_bootstrap_contract_tests():
    suite = enterprise_hub.data_contracts
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "6.0.0-rc6"
    assert boot["dtos_registered"] >= 5
    assert boot["contract_tests_passed"] is True
    assert boot["json_roundtrip_ok"] is True
    assert "json" in boot["serialization_formats"]
    assert boot["doc_id"]
    assert boot["integrations"]["linked"] is True
    tests = suite.run_contract_tests()
    assert tests["passed"] is True


@pytest.mark.asyncio
async def test_api_edc(client):
    health = await client.get(f"{EDC}/health")
    body = await health.json()
    assert body["application_version"] == "6.0.0-rc6"
    assert body["data_contracts_ready"] is True

    boot = await client.post(f"{EDC}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    dtos = await client.get(f"{EDC}/dtos")
    assert dtos.status == 200
    assert (await dtos.json())["dtos"] >= 5

    for prefix in (
        HUB, ORCH, KG, AA, CM, WF, EIP, EDP, ISAM, OBS, TN, AOP, ATS, EKP, AIOS, EVP, SDP, EDF, EDT, ESI, EPM, EBC, ECC, EAS
    ):
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        payload = await resp.json()
        # EAS uses unified envelope
        version = payload.get("application_version") or payload.get("data", {}).get("application_version")
        assert version == "6.0.0-rc6"

    assert boot_body["schema_compatible"] is True


def test_docs_and_regression_21_3():
    for name in (
        "ENTERPRISE_DATA_CONTRACTS.md",
        "EDC_DTO.md",
        "EDC_EVENTS_SCHEMAS.md",
        "EDC_MAPPING_TESTING.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_DATA_CONTRACTS.md").exists()
    assert (ROOT / "platform_contracts" / "facade.py").exists()
    assert (ROOT / "platform_contracts" / "dto" / "crm" / "models.py").exists()
    assert (ROOT / "platform_contracts" / "events" / "base" / "__init__.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "data_contracts" / "facade.py").exists()

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
    assert "6.0.0-rc6" in manifest
    assert "21.6" in manifest
