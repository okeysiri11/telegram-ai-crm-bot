"""Tests — AI Ecosystem Enterprise Edition (Sprint 12.5)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.enterprise import enterprise
from applications.enterprise.api.register import register_enterprise_routes
from applications.enterprise.shared.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/enterprise/v1"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_enterprise_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    enterprise.reset()
    yield
    enterprise.reset()


def test_version_enterprise_ready():
    health = enterprise.health()
    assert health["application_version"] == "4.0.0-enterprise"
    assert health["enterprise_edition_ready"] is True
    assert health["enterprise_administration_ready"] is True
    assert health["enterprise_ai_ready"] is True
    assert health["ai_ecosystem_enterprise_ready"] is True


def test_organization_platform():
    boot = enterprise.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["organization_id"]
    assert boot["project_id"]

    org = enterprise.platform.create_organization(name="Beta Inc", domain="beta.io")
    tenant = enterprise.platform.create_tenant(organization_id=org["organization_id"], name="eu")
    ws = enterprise.platform.create_workspace(tenant_id=tenant["tenant_id"], name="ops")
    assert ws["workspace_id"]
    enterprise.platform.set_global_setting(key="theme", value="enterprise")
    assert enterprise.platform.get_global_setting("theme")["value"] == "enterprise"


def test_security_compliance():
    role = enterprise.administration.define_role(name="auditor", permissions=["audit:read"])
    enterprise.administration.assign_role(principal="audit-bot", role_id=role["role_id"])
    for provider in ("sso", "ldap", "active_directory", "oauth"):
        sess = enterprise.administration.authenticate(provider=provider, principal="user1")
        assert sess["status"] == "authenticated"
    enterprise.administration.audit(actor="admin", action="login", resource="portal")
    enterprise.administration.security_alert(severity="high", message="brute force")
    policy = enterprise.administration.set_policy(name="mfa", rules={"required": True})
    assert policy["status"] == "active"
    comp = enterprise.administration.compliance_check(framework="ISO27001", status="compliant")
    assert comp["status"] == "compliant"
    with pytest.raises(ValidationError):
        enterprise.administration.authenticate(provider="kerberos", principal="x")


def test_enterprise_ai_and_services():
    agents = enterprise.ai.ensure_suite()
    assert len(agents) == 8
    chief = agents[0]
    result = enterprise.ai.invoke(agent_id=chief["agent_id"], prompt="summarize Q3")
    assert result["status"] == "completed"

    enterprise.services.register_route(path="/v1/reports", target="analytics.reports")
    enterprise.services.schedule(name="nightly-backup", cron="@daily")
    enterprise.services.publish_event(topic="org.created", payload={"id": "1"})
    enterprise.services.search_index(key="handbook", document={"title": "Enterprise Handbook"})
    assert enterprise.services.search("handbook")
    bak = enterprise.services.backup(label="nightly")
    assert bak["status"] == "completed"


def test_infrastructure_analytics_knowledge():
    region = enterprise.infrastructure.add_region(name="EU-West", code="euw")
    cluster = enterprise.infrastructure.create_cluster(name="euw-1", region_id=region["region_id"], nodes=2)
    scaled = enterprise.infrastructure.scale(cluster["cluster_id"], nodes=5)
    assert scaled["nodes"] == 5
    assert enterprise.infrastructure.load_balance(cluster["cluster_id"])["selected"]
    assert enterprise.infrastructure.disaster_recovery(cluster["cluster_id"])["status"] == "recovered"
    assert enterprise.infrastructure.monitoring_snapshot()["type"] == "monitoring_center"

    for rt in ("enterprise", "financial", "predictive", "ai_analytics"):
        rpt = enterprise.analytics.generate_report(report_type=rt, title=f"{rt} pack")
        assert rpt["report_type"] == rt

    pages = enterprise.knowledge.bootstrap_centers()
    assert len(pages) == 5
    wiki = enterprise.knowledge.publish_page(center="wiki", title="Onboarding", body="Start here")
    assert wiki["page_id"]


@pytest.mark.asyncio
async def test_api_enterprise(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "4.0.0-enterprise"
    assert body["enterprise_edition_ready"] is True

    boot = await client.post(f"{PREFIX}/bootstrap", json={})
    assert boot.status == 201

    org = await client.post(f"{PREFIX}/platform", json={"name": "Gamma", "domain": "gamma.io"})
    assert org.status == 201

    admin = await client.post(f"{PREFIX}/administration", json={"name": "ops", "permissions": ["read"]})
    assert admin.status == 201

    ai = await client.post(f"{PREFIX}/ai", json={"action": "ensure_suite"})
    assert ai.status == 201

    svc = await client.post(f"{PREFIX}/services", json={"action": "event", "topic": "ping", "payload": {"ok": True}})
    assert svc.status == 201

    region = await client.post(f"{PREFIX}/infrastructure", json={"name": "US", "code": "us"})
    assert region.status == 201
    region_body = await region.json()

    cluster = await client.post(
        f"{PREFIX}/infrastructure",
        json={"action": "cluster", "name": "us-1", "region_id": region_body["region_id"], "nodes": 2},
    )
    assert cluster.status == 201

    analytics = await client.post(f"{PREFIX}/analytics", json={"report_type": "executive", "title": "Board"})
    assert analytics.status == 201

    knowledge = await client.get(f"{PREFIX}/knowledge")
    assert knowledge.status == 200


def test_docs_and_regression_12_5():
    for name in ("ENTERPRISE.md", "ORGANIZATION.md", "ADMINISTRATION.md", "COMPLIANCE.md", "ENTERPRISE_AI.md"):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE.md").exists()
    manifest = (ROOT / "applications" / "enterprise" / "manifest.json").read_text()
    assert "4.0.0-enterprise" in manifest
    assert "12.5" in manifest

    from applications.ai_os.config import DEFAULT_CONFIG as AIOS
    from applications.executive_center.config import DEFAULT_CONFIG as EX

    assert AIOS.application_version == "3.4.0-alpha"
    assert EX.application_version == "3.3.0-alpha"
    assert AIOS.api_prefix == "/api/ai-os/v1"
    assert EX.api_prefix == "/api/executive/v1"
