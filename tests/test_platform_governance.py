"""Tests — Platform Governance, Compliance & Lifecycle (Sprint 7.6)."""

from __future__ import annotations

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from ecosystem import ecosystem
from ecosystem.api.register import register_ecosystem_routes
from ecosystem.config import DEFAULT_CONFIG
from ecosystem.governance.models import (
    ComplianceStatus,
    GovernanceDomain,
    LifecycleKind,
    LifecycleState,
    RiskCategory,
    RiskSeverity,
)


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_ecosystem_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    ecosystem.reset()
    DEFAULT_CONFIG.registered_applications[:] = ["auto_marketplace"]
    yield
    ecosystem.reset()
    DEFAULT_CONFIG.registered_applications[:] = ["auto_marketplace"]


def test_governance_version():
    assert DEFAULT_CONFIG.ecosystem_version == "1.5.0-alpha"
    assert DEFAULT_CONFIG.governance_layer == "1.0"
    assert DEFAULT_CONFIG.compliance_layer == "1.0"


@pytest.mark.asyncio
async def test_policies_and_compliance():
    gov = ecosystem.engine.governance
    policies = gov.policies.list_policies()
    assert len(policies) >= 6
    assert any(p.domain == GovernanceDomain.KNOWLEDGE for p in policies)

    custom = await gov.policies.create(
        "Marketplace Release Gate",
        GovernanceDomain.APPLICATION,
        rules=["versioned_releases", "approval_for_prod"],
    )
    updated = await gov.policies.update(custom.policy_id, description="Updated gate")
    assert updated.description == "Updated gate"

    passed = await gov.compliance.evaluate(
        custom.policy_id,
        "application",
        "auto_marketplace",
        context={"versioned": True, "environment": "prod", "approved": True},
    )
    assert passed.status == ComplianceStatus.PASSED

    failed = await gov.compliance.evaluate(
        custom.policy_id,
        "application",
        "auto_marketplace",
        context={"versioned": False, "environment": "prod", "approved": False},
    )
    assert failed.status == ComplianceStatus.FAILED
    assert failed.findings

    review = gov.compliance.access_review("auto_marketplace")
    assert review.review_id
    assert gov.audit.trail()


@pytest.mark.asyncio
async def test_lifecycle_and_catalog():
    gov = ecosystem.engine.governance
    record = await gov.lifecycle.register(LifecycleKind.AGENT, "sales-specialist", version="1.0.0")
    assert record.state == LifecycleState.REGISTERED
    active = await gov.lifecycle.transition(record.record_id, LifecycleState.ACTIVE)
    assert active.state == LifecycleState.ACTIVE
    versioned = await gov.lifecycle.set_version(record.record_id, "1.1.0")
    assert versioned.version == "1.1.0"

    plugin = await gov.lifecycle.register(LifecycleKind.PLUGIN, "pricing-plugin")
    workflow = await gov.lifecycle.register(LifecycleKind.WORKFLOW, "deal-pipeline")
    knowledge = await gov.lifecycle.register(LifecycleKind.KNOWLEDGE, "ev-incentives")
    assert plugin.kind == LifecycleKind.PLUGIN
    assert workflow and knowledge

    entry = gov.catalog.register("auto_marketplace", entry_type="application", version="2.0.0")
    synced = gov.catalog.sync_from_lifecycle()
    assert entry.entry_id
    assert len(gov.catalog.list_entries()) >= 1 + len(synced)


@pytest.mark.asyncio
async def test_risk_and_administration():
    gov = ecosystem.engine.governance
    risk = await gov.risk.assess(
        "Security gap",
        category=RiskCategory.SECURITY,
        severity=RiskSeverity.HIGH,
        description="Missing MFA on admin",
    )
    assert risk.risk_id
    assert gov.risk.continuity_policy()["rto_minutes"] == 60
    assert gov.risk.disaster_recovery_policy()["retention_days"] == 30

    overview = gov.administration.platform_overview()
    assert overview["governance_layer"] == "1.0"
    license_rec = gov.administration.create_license("org-1", plan="enterprise", seats=50)
    assert license_rec.plan == "enterprise"
    flag = gov.administration.set_feature_flag("beta_plugins", True)
    assert flag.enabled is True
    assert gov.administration.is_enabled("continuous_auditing") is True


@pytest.mark.asyncio
async def test_governance_cycle():
    result = await ecosystem.engine.governance.run_governance_cycle()
    assert result["audit"]["total"] >= 1
    assert "integrations" in result
    assert result["administration"]["ecosystem_version"] == "1.5.0-alpha"


@pytest.mark.asyncio
async def test_platform_governance_api(client: TestClient):
    resp = await client.get("/api/ecosystem/v1/health")
    assert resp.status == 200
    health = await resp.json()
    assert health["ecosystem_version"] == "1.5.0-alpha"
    assert health["governance_layer"] == "1.0"
    assert health["compliance_layer"] == "1.0"

    resp = await client.get("/api/ecosystem/v1/governance/policies")
    assert resp.status == 200
    policies = await resp.json()
    assert len(policies["policies"]) >= 6

    resp = await client.post(
        "/api/ecosystem/v1/lifecycle",
        json={"kind": "application", "name": "crm_hub", "version": "1.0.0"},
    )
    assert resp.status == 201
    record = await resp.json()

    resp = await client.post(
        f"/api/ecosystem/v1/lifecycle/{record['record_id']}/transition",
        json={"state": "active"},
    )
    assert resp.status == 200

    resp = await client.post(
        "/api/ecosystem/v1/risk",
        json={"title": "Ops risk", "category": "operational", "severity": "medium"},
    )
    assert resp.status == 201

    resp = await client.get("/api/ecosystem/v1/administration")
    assert resp.status == 200

    resp = await client.post("/api/ecosystem/v1/governance/cycle")
    assert resp.status == 201

    # Workforce audit endpoint still works
    resp = await client.get("/api/ecosystem/v1/governance")
    assert resp.status == 200

    resp = await client.get("/api/ecosystem/v1/manifest")
    assert resp.status == 200
    manifest = await resp.json()
    assert manifest["ecosystem_version"] == "1.5.0-alpha"
    assert manifest["governance_layer"] == "1.0"
    assert manifest["compliance_layer"] == "1.0"
