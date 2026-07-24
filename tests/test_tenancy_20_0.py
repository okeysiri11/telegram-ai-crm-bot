"""Tests — Enterprise Multi-Tenant Platform (Sprint 20.0)."""

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


def test_version_tenancy_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "6.0.0-rc3"
    assert health["enterprise_foundation"] == "Enterprise Platform v6.0.0-rc2"
    assert health["multi_tenant_ready"] is True
    assert health["workspace_ready"] is True
    assert health["isolation_ready"] is True
    assert health["licensing_ready"] is True
    assert health["billing_ready"] is True
    assert health["enterprise_observability_ready"] is True
    assert health["engines"]["tenancy"] == "1.0"


def test_tenants_hierarchy_isolation_billing():
    suite = enterprise_hub.tenancy
    tenant = suite.tenants.create_tenant(name="QA Corp", license_tier="business")
    holding = suite.organizations.create_node(
        tenant_id=tenant["tenant_id"], name="QA Holding", level="holding"
    )
    company = suite.company.create(
        tenant_id=tenant["tenant_id"], name="QA Co", parent_id=holding["org_id"]
    )
    assert company["level"] == "company"
    ws = suite.workspaces.create(tenant_id=tenant["tenant_id"], name="QA CRM", kind="crm")
    iso = suite.isolation.enforce(
        tenant_id=tenant["tenant_id"], scope="data", resource_key="crm"
    )
    assert iso["enforced"] is True
    lic = suite.licensing.assign(tenant_id=tenant["tenant_id"], tier="startup")
    sub = suite.billing.subscribe(tenant_id=tenant["tenant_id"], plan="startup", amount=49)
    inv = suite.billing.invoice(
        tenant_id=tenant["tenant_id"], subscription_id=sub["subscription_id"], amount=49
    )
    pay = suite.billing.pay(invoice_id=inv["invoice_id"])
    assert lic["tier"] == "startup" and pay["status"] == "succeeded"
    with pytest.raises(ValidationError):
        suite.isolation.enforce(tenant_id=tenant["tenant_id"], scope="unknown", resource_key="x")
    assert ws["workspace_id"]


def test_provisioning_bootstrap_migration():
    suite = enterprise_hub.tenancy
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "6.0.0-rc3"
    assert boot["tenant_id"] and boot["analytics_id"] and boot["export_id"]
    hier = suite.organizations.hierarchy(tenant_id=boot["tenant_id"])
    assert hier["count"] >= 6


@pytest.mark.asyncio
async def test_api_tenancy(client):
    health = await client.get(f"{TN}/health")
    body = await health.json()
    assert body["application_version"] == "6.0.0-rc3"
    assert body["multi_tenant_ready"] is True
    assert body["workspace_ready"] is True

    boot = await client.post(f"{TN}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    created = await client.post(
        f"{TN}/tenants",
        json={"name": "API Tenant", "license_tier": "enterprise"},
    )
    assert created.status == 201

    for prefix in (HUB, ORCH, KG, AA, CM, WF, EIP, EDP, ISAM, OBS):
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        assert (await resp.json())["application_version"] == "6.0.0-rc3"

    assert boot_body["payment_id"]


def test_docs_and_regression_20_0():
    for name in (
        "ENTERPRISE_TENANCY.md",
        "TENANCY_TENANTS.md",
        "TENANCY_ORGANIZATIONS.md",
        "TENANCY_WORKSPACES.md",
        "TENANCY_ISOLATION.md",
        "TENANCY_LICENSING_BILLING.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_TENANCY.md").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "tenancy" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "tenancy" / "organizations" / "company.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "tenancy" / "workspaces" / "crm.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "tenancy" / "onboarding" / "data_import.py").exists()

    from applications.ai_os.config import DEFAULT_CONFIG as AIOS
    from applications.enterprise.config import DEFAULT_CONFIG as ENT
    from applications.auto_marketplace.config import DEFAULT_CONFIG as AUTO
    from applications.agro_enterprise.config import DEFAULT_CONFIG as AGRO
    from applications.port_enterprise.config import DEFAULT_CONFIG as PORT
    from applications.port_erp.config import DEFAULT_CONFIG as PORT_ERP
    from applications.crypto_enterprise.config import DEFAULT_CONFIG as CRYPTO
    from applications.legal_enterprise.config import DEFAULT_CONFIG as LEGAL
    from applications.finance_enterprise.config import DEFAULT_CONFIG as FINANCE

    assert AIOS.application_version == "3.4.0-alpha"
    assert ENT.application_version == "4.0.0-enterprise"
    assert AUTO.application_version == "4.2.0-enterprise"
    assert AGRO.application_version == "4.4.0-enterprise"
    assert PORT.application_version == "4.6.0-enterprise"
    assert PORT_ERP.application_version == "2.0.0"
    assert CRYPTO.application_version == "4.8.0-enterprise"
    assert LEGAL.application_version == "5.0.0-enterprise"
    assert FINANCE.application_version == "5.2.0-enterprise"
    manifest = (ROOT / "applications" / "enterprise_hub" / "manifest.json").read_text()
    assert "6.0.0-rc3" in manifest
    assert "21.3" in manifest
