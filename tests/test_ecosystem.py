"""Tests — Unified Identity & Workspace (Sprint 7.1)."""

from __future__ import annotations

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from ecosystem import ecosystem
from ecosystem.api.register import register_ecosystem_routes
from ecosystem.config import DEFAULT_CONFIG
from ecosystem.permissions.models import SystemRole


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
    yield
    ecosystem.reset()


def test_ecosystem_version():
    assert DEFAULT_CONFIG.ecosystem_version == "1.5.0-alpha"
    assert DEFAULT_CONFIG.platform_dependency == "AI Platform Core v3.0"


@pytest.mark.asyncio
async def test_identity_register_and_login():
    user, session = await ecosystem.engine.identity.register(
        email="user@example.com",
        password="secret123",
        display_name="Test User",
    )
    assert user.email == "user@example.com"
    assert session.access_token

    logged_in, new_session = await ecosystem.engine.identity.login("user@example.com", "secret123")
    assert logged_in.user_id == user.user_id
    assert new_session.access_token

    validated = ecosystem.engine.identity.validate_session(new_session.access_token)
    assert validated is not None
    assert validated.user_id == user.user_id


@pytest.mark.asyncio
async def test_sso_and_mfa():
    user, session = await ecosystem.engine.identity.sso_login("oauth", "ext-1", "sso@example.com")
    assert user.sso_provider.value == "oauth"
    assert session.access_token

    enrollment = ecosystem.engine.identity.enroll_mfa(user.user_id)
    verified = ecosystem.engine.identity.verify_mfa(user.user_id, enrollment.enrollment_id)
    assert verified.mfa_enabled


@pytest.mark.asyncio
async def test_organization_and_workspace():
    user, _ = await ecosystem.engine.identity.register(email="owner@example.com", password="pass")
    org = await ecosystem.engine.organizations.create_organization(name="Acme Motors", owner_id=user.user_id)
    assert org.organization_id

    workspace = await ecosystem.engine.organizations.create_workspace(
        organization_id=org.organization_id,
        name="Main Workspace",
        owner_id=user.user_id,
        is_default=True,
    )
    assert workspace.organization_id == org.organization_id

    dept = ecosystem.engine.organizations.create_department(org.organization_id, "Sales")
    team = ecosystem.engine.organizations.create_team(org.organization_id, "West Team", department_id=dept.department_id)
    project = ecosystem.engine.organizations.create_project(
        org.organization_id, "Q3 Launch", workspace_id=workspace.workspace_id, team_id=team.team_id
    )
    assert project.project_id


@pytest.mark.asyncio
async def test_roles_and_permissions():
    roles = ecosystem.engine.permissions.list_roles()
    system_names = {r.system_role for r in roles if r.system_role}
    assert SystemRole.PLATFORM_OWNER in system_names
    assert SystemRole.DEALER in system_names
    assert SystemRole.AI_AGENT in system_names

    user, _ = await ecosystem.engine.identity.register(email="admin@example.com", password="pass")
    custom = ecosystem.engine.permissions.create_custom_role("Regional Lead", ["org:read", "workspace:write"])
    await ecosystem.engine.permissions.assign_role(user.user_id, custom.role_id)
    assert ecosystem.engine.permissions.check_permission(user.user_id, "workspace:write")


@pytest.mark.asyncio
async def test_workspace_dashboard_and_search():
    user, _ = await ecosystem.engine.identity.register(email="ws@example.com", password="pass")
    ecosystem.engine.workspace.add_favorite(user.user_id, "application", "auto_marketplace", label="Auto Marketplace")
    ecosystem.engine.workspace.record_activity(user.user_id, "viewed_dashboard", application_id="ecosystem")

    dashboard = ecosystem.engine.workspace.dashboard(user.user_id)
    assert "auto_marketplace" in dashboard["applications"]
    assert dashboard["favorites_count"] >= 1

    results = ecosystem.engine.workspace.global_search(user.user_id, "auto")
    assert results["results"]


@pytest.mark.asyncio
async def test_navigation_and_assistant():
    user, _ = await ecosystem.engine.identity.register(email="nav@example.com", password="pass")
    tree = ecosystem.engine.navigation.navigation_tree(user_id=user.user_id)
    assert any(a["application_id"] == "auto_marketplace" for a in tree["applications"])

    opened = await ecosystem.engine.navigation.open_application(user.user_id, "auto_marketplace")
    assert opened["opened"] is True

    response = await ecosystem.engine.assistant.invoke(user.user_id, "Find SUVs near me", application_id="auto_marketplace")
    assert response["session_id"]
    assert "reply" in response


@pytest.mark.asyncio
async def test_cross_application_services():
    user, _ = await ecosystem.engine.identity.register(email="shared@example.com", password="pass")
    file = ecosystem.engine.shared.add_file(user.user_id, "contract.pdf", application_id="auto_marketplace")
    event = ecosystem.engine.shared.add_calendar_event(user.user_id, "Demo Drive")
    contact = ecosystem.engine.shared.add_contact(user.user_id, "Jane Dealer", email="jane@dealer.com")
    task = ecosystem.engine.shared.add_task(user.user_id, "Follow up lead")
    memory = await ecosystem.engine.shared.remember(user.user_id, "Prefers electric vehicles", application_id="auto_marketplace")

    assert len(ecosystem.engine.shared.list_files(user.user_id)) == 1
    assert len(ecosystem.engine.shared.list_calendar(user.user_id)) == 1
    assert len(ecosystem.engine.shared.list_contacts(user.user_id)) == 1
    assert len(ecosystem.engine.shared.list_tasks(user.user_id)) == 1
    assert len(ecosystem.engine.shared.recall(user.user_id)) == 1
    assert file.file_id and event.event_id and contact.contact_id and task.task_id and memory.memory_id


@pytest.mark.asyncio
async def test_tenant_and_profile():
    tenant = ecosystem.engine.tenants.create("Enterprise Tenant", plan="enterprise")
    user, _ = await ecosystem.engine.identity.register(email="profile@example.com", password="pass")
    profile = ecosystem.engine.profiles.update(user.user_id, first_name="Alex", last_name="Rivera", locale="en-US")
    linked = ecosystem.engine.profiles.link_application(user.user_id, "auto_marketplace", "portal-user-1")
    assert tenant.tenant_id
    assert profile.first_name == "Alex"
    assert linked.application_links["auto_marketplace"] == "portal-user-1"


@pytest.mark.asyncio
async def test_ecosystem_api(client: TestClient):
    resp = await client.get("/api/ecosystem/v1/health")
    assert resp.status == 200
    data = await resp.json()
    assert data["ecosystem_version"] == "1.5.0-alpha"

    resp = await client.post(
        "/api/ecosystem/v1/identity/auth/register",
        json={"email": "api@example.com", "password": "secret", "display_name": "API User"},
    )
    assert resp.status == 201
    payload = await resp.json()
    token = payload["session"]["access_token"]

    resp = await client.get(
        "/api/ecosystem/v1/workspace/dashboard",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status == 200
    dashboard = await resp.json()
    assert "applications" in dashboard

    resp = await client.get("/api/ecosystem/v1/navigation")
    assert resp.status == 200
    nav = await resp.json()
    assert nav["applications"]

    resp = await client.get("/api/ecosystem/v1/manifest")
    assert resp.status == 200
    manifest = await resp.json()
    assert manifest["ecosystem_version"] == "1.5.0-alpha"
