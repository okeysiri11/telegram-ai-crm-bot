"""Tests — Legal Intelligence Platform Foundation (Sprint 17.0)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.legal_enterprise import legal_enterprise
from applications.legal_enterprise.api.register import register_legal_enterprise_routes
from applications.legal_enterprise.shared.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/legal-enterprise/v1"
CE = "/api/crypto-enterprise/v1"
CEC = "/api/crypto-enterprise-certification/v1"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_legal_enterprise_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    legal_enterprise.reset()
    yield
    legal_enterprise.reset()


def test_version_legal_enterprise_ready():
    health = legal_enterprise.health()
    assert health["application_version"] == "4.9.0-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v4.8.0-enterprise"
    assert health["legal_enterprise_foundation_ready"] is True
    assert health["legal_registry_ready"] is True
    assert health["legislation_registry_ready"] is True
    assert health["court_infrastructure_ready"] is True
    assert health["case_management_foundation_ready"] is True
    assert health["legal_knowledge_graph_ready"] is True


def test_registries_and_legislation():
    entity = legal_enterprise.registry.register_entity(name="Acme Legal LLC")
    attorney = legal_enterprise.registry.register_attorney(
        full_name="Pat Kim", bar_number="BAR-99", firm="Kim Law"
    )
    assert entity["entity_id"] and attorney["bar_number"] == "BAR-99"
    civil = legal_enterprise.legislation.register_civil_code(title="Civil Code", code="CIV-X")
    assert civil["legislation_type"] == "civil"
    assert legal_enterprise.legislation.status()["versions"] >= 1
    with pytest.raises(ValidationError):
        legal_enterprise.registry.register_role(role_code="unknown_role")
    with pytest.raises(ValidationError):
        legal_enterprise.legislation.register(legislation_type="unknown", title="X")


def test_cases_and_knowledge_graph():
    boot = legal_enterprise.bootstrap()
    assert boot["case_id"] and boot["civil_code_id"] and boot["regional_court_id"]
    assert legal_enterprise.cases.status()["cases"] >= 1
    assert legal_enterprise.courts.status()["courts"] == 3
    assert legal_enterprise.knowledge.status()["entries"] >= 4
    assert legal_enterprise.knowledge.status()["relationships"] >= 3
    with pytest.raises(ValidationError):
        legal_enterprise.cases.register_case(title="", status="filed")
    for dtype in ("legal", "case", "court", "legislation"):
        assert legal_enterprise.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_legal_enterprise(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "4.9.0-enterprise"
    assert body["legislation_registry_ready"] is True
    assert body["case_management_foundation_ready"] is True

    boot = await client.post(f"{PREFIX}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    case = await client.post(
        f"{PREFIX}/cases",
        json={
            "action": "document",
            "case_id": boot_body["case_id"],
            "title": "Answer",
            "document_type": "filing",
        },
    )
    assert case.status == 201

    law = await client.post(
        f"{PREFIX}/legislation",
        json={"action": "tax", "title": "Tax Code Amendment", "code": "TAX-2"},
    )
    assert law.status == 201

    dash = await client.get(f"{PREFIX}/dashboard?type=case")
    assert dash.status == 200


def test_docs_and_regression_17_0():
    for name in (
        "LEGAL_ENTERPRISE.md",
        "LEGAL_FOUNDATION.md",
        "CASE_MANAGEMENT.md",
        "LEGISLATION_REGISTRY.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "LEGAL_ENTERPRISE.md").exists()
    assert (ROOT / "applications" / "legal_enterprise" / "application.py").exists()
    assert (ROOT / "applications" / "legal_enterprise" / "legal_registry.py").exists()
    assert (ROOT / "applications" / "legal_enterprise" / "cases.py").exists()

    from applications.ai_os.config import DEFAULT_CONFIG as AIOS
    from applications.enterprise.config import DEFAULT_CONFIG as ENT
    from applications.auto_marketplace.config import DEFAULT_CONFIG as AUTO
    from applications.agro_enterprise.config import DEFAULT_CONFIG as AGRO
    from applications.port_enterprise.config import DEFAULT_CONFIG as PORT
    from applications.port_erp.config import DEFAULT_CONFIG as PORT_ERP
    from applications.crypto_enterprise.config import DEFAULT_CONFIG as CRYPTO

    assert AIOS.application_version == "3.4.0-alpha"
    assert ENT.application_version == "4.0.0-enterprise"
    assert AUTO.application_version == "4.2.0-enterprise"
    assert AGRO.application_version == "4.4.0-enterprise"
    assert PORT.application_version == "4.6.0-enterprise"
    assert PORT_ERP.application_version == "2.0.0"
    assert CRYPTO.application_version == "4.8.0-enterprise"
    manifest = (ROOT / "applications" / "legal_enterprise" / "manifest.json").read_text()
    assert "4.9.0-enterprise" in manifest
    assert "17.0" in manifest
    assert (ROOT / "applications" / "crypto_enterprise" / "enterprise_certification" / "facade.py").exists()
    _ = (CE, CEC)
