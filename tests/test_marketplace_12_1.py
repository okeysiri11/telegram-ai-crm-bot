"""Tests — AI Marketplace & Plugin Store (Sprint 12.1)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.marketplace import marketplace
from applications.marketplace.api.register import register_marketplace_routes
from applications.marketplace.shared.exceptions import CompatibilityError


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/marketplace/v1"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_marketplace_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    marketplace.reset()
    yield
    marketplace.reset()


def test_version_marketplace_ready():
    health = marketplace.health()
    assert health["application_version"] == "3.1.0-alpha"
    assert health["ai_marketplace_ready"] is True
    assert health["plugin_store_ready"] is True
    assert health["developer_portal_ready"] is True
    assert health["enterprise_marketplace_ready"] is True
    assert health["engines"]["marketplace_core"] == "1.0"


def test_marketplace_core_install_update_rollback():
    core = marketplace.core
    pkg = core.publish_package(name="crm-assist", kind="plugin", category="crm", version="1.0.0", publisher="dev")
    assert pkg["package_id"]
    assert core.check_compatibility(pkg["package_id"])["compatible"] is True
    assert core.resolve_dependencies(pkg["package_id"])["ok"] is True
    inst = core.install(pkg["package_id"], org_id="org1", user_id="u1")
    assert inst["status"] == "installed"
    updated = core.update(inst["installation_id"], to_version="1.1.0")
    assert updated["version"] == "1.1.0"
    rolled = core.rollback(inst["installation_id"])
    assert rolled["version"] == "1.0.0"
    lic = core.issue_license(pkg["package_id"], org_id="org1", seats=5)
    assert lic["status"] == "active"
    rating = core.rate(pkg["package_id"], score=5, reviewer="u1")
    assert rating["score"] == 5
    assert "crm" in core.categories

    bad = core.publish_package(name="needs-dep", kind="plugin", category="erp", dependencies=["missing-pack"])
    with pytest.raises(CompatibilityError):
        core.install(bad["package_id"])


def test_ai_workflow_connector_security_portal_enterprise():
    agent = marketplace.ai.publish_agent(name="Chief Helper", category="custom_enterprise", permissions=["assist"])
    inst = marketplace.ai.install_agent(agent["package_id"], org_id="org1")
    marketplace.ai.update_agent(inst["installation_id"], to_version="1.0.1")
    marketplace.ai.share_agent(agent["package_id"], with_org_id="org2")
    assert "assist" in marketplace.ai.agent_permissions(agent["package_id"])["permissions"]
    marketplace.ai.rate_agent(agent["package_id"], score=4, reviewer="r1")

    wf = marketplace.workflows.publish_workflow(name="Onboard", steps=[{"step": "create_lead"}], pack_type="template")
    exported = marketplace.workflows.export_workflow(wf["package_id"])
    imported = marketplace.workflows.import_workflow(payload=exported["payload"], publisher="dev")
    assert imported["kind"] == "workflow"
    assert marketplace.workflows.list_templates()

    connectors = marketplace.connectors.list_connectors()
    assert len(connectors) >= 10
    assert "telegram" in marketplace.connectors.catalog()["connectors"]
    marketplace.connectors.install_connector(connectors[0]["package_id"], org_id="org1")

    scan = marketplace.security.full_scan(agent["package_id"])
    assert scan["passed"] is True
    assert marketplace.security.verify_plugin(agent["package_id"])["passed"] is True
    assert marketplace.security.digital_signature(agent["package_id"])["signature"]

    pub = marketplace.portal.publish(
        name="Finance Pack",
        kind="plugin",
        category="finance",
        publisher="studio",
        documentation="Install then configure API keys.",
        api_reference="/api/marketplace/v1",
    )
    assert pub["validation"]["valid"] is True
    assert marketplace.portal.analytics(pub["package"]["package_id"])["documentation"]

    market = marketplace.enterprise.create_org_marketplace(org_id="org1", name="Acme Private")
    marketplace.enterprise.grant_role(market["market_id"], principal="admin@acme", role="admin")
    internal = marketplace.enterprise.publish_internal(org_id="org1", name="Internal Bot", kind="agent")
    assert internal["private"] is True
    repo = marketplace.enterprise.company_repository("org1")
    assert repo["count"] >= 1


@pytest.mark.asyncio
async def test_api_marketplace(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "3.1.0-alpha"
    assert body["ai_marketplace_ready"] is True

    pkg = await client.post(
        f"{PREFIX}/packages",
        json={"name": "drone-tools", "kind": "plugin", "category": "drone", "version": "1.0.0"},
    )
    assert pkg.status == 201
    pid = (await pkg.json())["package_id"]

    inst = await client.post(f"{PREFIX}/packages", json={"action": "install", "package_id": pid, "org_id": "o1"})
    assert inst.status == 201

    agent = await client.post(f"{PREFIX}/agents", json={"name": "Agro AI Pack", "category": "agro"})
    assert agent.status == 201

    wf = await client.post(f"{PREFIX}/workflows", json={"name": "Harvest Flow", "pack_type": "business", "category": "agro"})
    assert wf.status == 201

    conns = await client.get(f"{PREFIX}/connectors")
    assert conns.status == 200
    assert len((await conns.json())["connectors"]) >= 10

    sec = await client.post(f"{PREFIX}/security", json={"package_id": pid, "action": "full"})
    assert sec.status == 200
    assert (await sec.json())["passed"] is True

    portal = await client.post(
        f"{PREFIX}/portal",
        json={"name": "Legal Helper", "kind": "agent", "category": "legal", "documentation": "docs"},
    )
    assert portal.status == 201

    ent = await client.post(f"{PREFIX}/enterprise", json={"org_id": "org9", "name": "Org Market"})
    assert ent.status == 201


def test_docs_and_manifest_12_1():
    for name in ("MARKETPLACE.md", "PLUGIN_STORE.md", "DEVELOPER_PORTAL.md", "PACKAGE_MANAGER.md"):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "MARKETPLACE.md").exists()
    manifest = (ROOT / "applications" / "marketplace" / "manifest.json").read_text()
    assert "3.1.0-alpha" in manifest
    assert "12.1" in manifest


def test_regression_existing_apps_untouched():
    from applications.ecosystem.config import DEFAULT_CONFIG as ECO
    from ecosystem.config import DEFAULT_CONFIG as TOP_ECO

    assert ECO.application_version == "3.0.0-alpha"
    assert TOP_ECO.ecosystem_version == "1.5.0-alpha"
