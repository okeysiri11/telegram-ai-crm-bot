"""Tests — Enterprise Documentation Platform (Sprint 21.6 / v6.0.0)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes
from applications.enterprise_hub.shared.exceptions import ValidationError
from platform_documentation.models import DOC_CATEGORIES


ROOT = Path(__file__).resolve().parents[1]
PREFIXES = [
    "/api/enterprise-hub/v1",
    "/api/enterprise-orch/v1",
    "/api/enterprise-kg/v1",
    "/api/enterprise-agents/v1",
    "/api/enterprise-comms/v1",
    "/api/enterprise-workflow/v1",
    "/api/enterprise-eip/v1",
    "/api/enterprise-edp/v1",
    "/api/enterprise-isam/v1",
    "/api/enterprise-obs/v1",
    "/api/enterprise-tenancy/v1",
    "/api/enterprise-aop/v1",
    "/api/enterprise-ats/v1",
    "/api/enterprise-ekp/v1",
    "/api/enterprise-aios/v1",
    "/api/enterprise-evp/v1",
    "/api/enterprise-sdp/v1",
    "/api/enterprise-edf/v1",
    "/api/enterprise-edt/v1",
    "/api/enterprise-esi/v1",
    "/api/enterprise-epm/v1",
    "/api/enterprise-ebc/v1",
    "/api/enterprise-ecc/v1",
    "/api/enterprise-eas/v1",
    "/api/enterprise-edc/v1",
    "/api/enterprise-esh/v1",
    "/api/enterprise-eqa/v1",
]
EDO = "/api/enterprise-edo/v1"


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


def test_version_edo_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "7.6.0"
    assert health["enterprise_foundation"] == "Enterprise Platform v7.5.0"
    assert health["documentation_platform_ready"] is True
    assert health["docs_registry_ready"] is True
    assert health["docs_search_ready"] is True
    assert health["docs_publishing_ready"] is True
    assert health["quality_assurance_ready"] is True
    assert health["engines"]["documentation_platform"] == "1.0"


def test_registry_search_generate():
    suite = enterprise_hub.documentation_platform
    doc = suite.register_doc(
        title="Sample Module Guide",
        category="modules",
        content="How to use the sample module",
        module="workflow",
    )
    assert doc["doc_id"]
    found = suite.search(query="sample", category="modules")
    assert found["count"] >= 1
    gen = suite.generate("api")
    assert gen["payload"]["openapi"] == "3.1.0"
    with pytest.raises(ValidationError):
        suite.register_doc(title="x", category="not-a-category")


def test_bootstrap_publish():
    suite = enterprise_hub.documentation_platform
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "7.6.0"
    assert boot["docs_registered"] >= 20
    assert boot["modules_documented"] >= 10
    assert boot["quality_passed"] is True
    assert boot["published_formats"] >= 4
    assert boot["developer_portal"] is True
    assert boot["dashboard_id"]
    assert boot["integrations"]["linked"] is True
    pub = suite.publish(formats=["html", "markdown"])
    assert len(pub["artifacts"]) == 2
    assert suite.dashboard()["status"] == "ready"
    assert set(DOC_CATEGORIES)


@pytest.mark.asyncio
async def test_api_edo(client):
    health = await client.get(f"{EDO}/health")
    body = await health.json()
    assert body["application_version"] == "7.6.0"
    assert body["documentation_platform_ready"] is True

    boot = await client.post(f"{EDO}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    docs = await client.get(f"{EDO}/docs")
    assert docs.status == 200
    assert (await docs.json())["docs"] >= 20

    search = await client.get(f"{EDO}/search?query=architecture")
    assert search.status == 200
    assert (await search.json())["count"] >= 1

    for prefix in PREFIXES:
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        payload = await resp.json()
        version = payload.get("application_version") or payload.get("data", {}).get("application_version")
        assert version == "7.6.0"

    assert boot_body["completeness"] > 0


def test_docs_and_regression_21_6():
    for name in (
        "ENTERPRISE_DOCUMENTATION_PLATFORM.md",
        "EDO_REGISTRY_GENERATORS.md",
        "EDO_SEARCH_VERSIONING.md",
        "EDO_PUBLISHING_QUALITY.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_DOCUMENTATION_PLATFORM.md").exists()
    assert (ROOT / "platform_documentation" / "facade.py").exists()
    assert (ROOT / "platform_documentation" / "generators" / "__init__.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "documentation_platform" / "facade.py").exists()

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
