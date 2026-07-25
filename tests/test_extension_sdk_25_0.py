"""Tests — Enterprise Extension SDK & Marketplace Foundation (Sprint 25.5 / v8.5.0)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes
from applications.enterprise_hub.shared.exceptions import ValidationError
from platform_enterprise_extension_sdk.models import (
    EXTENSION_TYPES,
    INTEGRATION_TARGETS,
    KPI_TARGETS,
    LIFECYCLE_STATUSES,
    PERMISSION_SCOPES,
    PRINCIPLES,
)


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
    "/api/enterprise-edo/v1",
    "/api/enterprise-epf/v1",
    "/api/enterprise-erl/v1",
    "/api/enterprise-epi/v1",
    "/api/enterprise-aba/v1",
    "/api/enterprise-bos/v1",
    "/api/enterprise-bws/v1",
    "/api/enterprise-bcj/v1",
    "/api/enterprise-amo/v1",
    "/api/enterprise-ech/v1",
    "/api/enterprise-eco/v1",
    "/api/enterprise-cpl/v1",
    "/api/enterprise-eon/v1",
    "/api/enterprise-eoc/v1",
    "/api/enterprise-epr/v1",
    "/api/enterprise-eao/v1",
    "/api/enterprise-wfi/v1",
    "/api/enterprise-ekg/v1",
    "/api/enterprise-pin/v1",
    "/api/enterprise-esl/v1",
    "/api/enterprise-etw/v1",
    "/api/enterprise-eoe/v1",
    "/api/enterprise-est/v1",
    "/api/enterprise-ele/v1",
    "/api/enterprise-aph/v1",
]
EES = "/api/enterprise-ees/v1"


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


def test_version_ees_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "8.5.0"
    assert health["enterprise_foundation"] == "Enterprise Platform v8.4.0"
    assert health["extension_sdk_ready"] is True
    assert health["marketplace_foundation_ready"] is True
    assert health["extension_permissions_ready"] is True
    assert health["extension_lifecycle_ready"] is True
    assert health["engines"]["extension_sdk"] == "1.0"
    assert health["ai_provider_hub_ready"] is True
    assert "ai_skill" in EXTENSION_TYPES
    assert "draft" in LIFECYCLE_STATUSES
    assert "knowledge_graph" in PERMISSION_SCOPES
    assert "ai_provider_hub" in INTEGRATION_TARGETS
    assert KPI_TARGETS["no_core_modification"] is True
    assert "sdk_and_public_api_only" in PRINCIPLES


def test_extension_lifecycle_marketplace_api():
    suite = enterprise_hub.extension_sdk
    scaffold = suite.scaffold(extension_type="integration", name="CRM Sync Pack")
    assert scaffold["via_sdk"] is True
    assert scaffold["modifies_core"] is False

    ext = suite.register(
        extension_id="ext_crm_sync",
        name="CRM Sync Pack",
        version="1.0.0",
        author="partner",
        publisher="partner",
        industry="services",
        extension_type="integration",
        required_permissions=["crm", "workflow"],
    )
    assert ext["status"] == "draft"

    perm = suite.request_permissions(extension_id="ext_crm_sync", scopes=["crm", "workflow"])
    assert perm["requires_approval"] is True
    assert perm["auto_granted"] is False

    with pytest.raises(ValidationError):
        suite.decide_permissions(extension_id="ext_crm_sync", actor="agent", action="approve", scopes=["crm"])

    decided = suite.decide_permissions(
        extension_id="ext_crm_sync",
        actor="admin",
        action="approve",
        scopes=["crm", "workflow"],
    )
    assert decided["status"] == "approved"

    suite.transition(extension_id="ext_crm_sync", to_status="testing")
    verified = suite.verify(extension_id="ext_crm_sync")
    assert verified["passed"] is True
    assert verified["signature"]

    listing = suite.marketplace_list(extension_id="ext_crm_sync", category="integrations")
    assert listing["status"] == "published"

    installed = suite.install(extension_id="ext_crm_sync")
    assert installed["safe_load"] is True
    assert installed["status"] == "installed"

    updated = suite.update(extension_id="ext_crm_sync", to_version="1.1.0")
    assert updated["status"] == "updated"
    rolled = suite.rollback(extension_id="ext_crm_sync", to_version="1.0.0")
    assert rolled["version"] == "1.0.0"

    api_ok = suite.public_call(method="extensions.register", payload={"extension_id": "ext_crm_sync"})
    assert api_ok["via_public_api"] is True
    assert api_ok["direct_core_access"] is False

    with pytest.raises(ValidationError):
        suite.public_call(method="core.internal")

    catalog = suite.marketplace_catalog()
    assert catalog["foundation"] is True
    assert "ai_skills" in catalog["categories"]


def test_bootstrap_ees():
    suite = enterprise_hub.extension_sdk
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "8.5.0"
    assert boot["extension_sdk_ready"] is True
    assert boot["marketplace_foundation_ready"] is True
    assert boot["extension_permissions_ready"] is True
    assert boot["extension_lifecycle_ready"] is True
    assert boot["public_api_only"] is True
    assert boot["direct_core_access"] is False
    assert boot["modifies_enterprise_core"] is False
    assert boot["signed"] is True
    assert boot["duplicates_core_logic"] is False
    assert boot["integrations"]["linked"] is True


@pytest.mark.asyncio
async def test_api_ees(client):
    health = await client.get(f"{EES}/health")
    body = await health.json()
    assert body["application_version"] == "8.5.0"
    assert body["extension_sdk_ready"] is True

    boot = await client.post(f"{EES}/bootstrap", json={})
    assert boot.status == 201
    assert (await boot.json())["marketplace_foundation_ready"] is True

    for prefix in PREFIXES:
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        payload = await resp.json()
        version = payload.get("application_version") or payload.get("data", {}).get("application_version")
        assert version == "8.5.0"


def test_docs_and_regression_25_0():
    for name in (
        "ENTERPRISE_EXTENSION_SDK.md",
        "EES_REGISTRY_SDK.md",
        "EES_PERMISSIONS_LOADER.md",
        "EES_MARKETPLACE_API.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_EXTENSION_SDK.md").exists()
    assert (ROOT / "platform_enterprise_extension_sdk" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "extension_sdk" / "facade.py").exists()

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
    assert '"application_version": "8.5.0"' in manifest
    assert "25.5" in manifest
