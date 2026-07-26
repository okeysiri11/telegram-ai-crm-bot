"""Tests — External Pilot Hardening & Tenant Onboarding (Sprint 32.1)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.platform_builder import platform_builder
from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes
from applications.platform_builder.api.register import register_platform_builder_routes
from ecosystem.api.register import register_ecosystem_routes
from ecosystem import ecosystem


ROOT = Path(__file__).resolve().parents[1]
EON = "/api/enterprise-eon/v1"
TN = "/api/enterprise-tenancy/v1"
ECO = "/api/ecosystem/v1"

DOCS = [
    "EXTERNAL_PILOT_GUIDE_32_1.md",
    "ORGANIZATION_ONBOARDING_GUIDE_32_1.md",
    "ADMINISTRATOR_GUIDE_32_1.md",
    "OPERATIONS_GUIDE_32_1.md",
    "SECURITY_CHECKLIST_32_1.md",
    "DEPLOYMENT_GUIDE_32_1.md",
    "BACKUP_DRILL_32_1.md",
    "PRODUCTION_STATUS_32_1.md",
    "SPRINT_REPORT_32_1.md",
    "RELEASE_NOTES_32_1.md",
]


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_enterprise_hub_routes(application)
    register_platform_builder_routes(application)
    register_ecosystem_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    platform_builder.reset()
    enterprise_hub.reset()
    ecosystem.reset()
    yield
    platform_builder.reset()
    enterprise_hub.reset()
    ecosystem.reset()


def test_32_1_docs_exist():
    docs = ROOT / "docs"
    for name in DOCS:
        path = docs / name
        assert path.exists(), name
        assert "32.1" in path.read_text()


def test_platform_version_32_1():
    health = platform_builder.health()
    assert health["application_version"] == "1.50.0"
    assert health["sprint"] == "32.4"
    assert "AI Operating" in health["release_status"]


def test_onboard_invite_pages_and_routes():
    app_tsx = (ROOT / "src" / "web" / "src" / "App.tsx").read_text()
    for route in ("/pilot/onboard", "/pilot/invite", "/invite/accept"):
        assert f'path="{route}"' in app_tsx
    assert "ExternalPilotOnboardPage" in app_tsx
    assert "PilotInvitePage" in app_tsx
    assert "InviteAcceptPage" in app_tsx
    assert (ROOT / "src" / "web" / "src" / "pages" / "ExternalPilotOnboardPage.tsx").exists()
    assert (ROOT / "src" / "web" / "src" / "pages" / "PilotInvitePage.tsx").exists()
    assert (ROOT / "src" / "web" / "src" / "pages" / "InviteAcceptPage.tsx").exists()
    hub = (ROOT / "src" / "web" / "src" / "integrations" / "hub.ts").read_text()
    assert 'tenancy: "/api/enterprise-tenancy/v1"' in hub
    assert 'onboarding: "/api/enterprise-eon/v1"' in hub
    assert 'ecosystem: "/api/ecosystem/v1"' in hub
    audit = (ROOT / "src" / "web" / "src" / "pilot" / "webCompletionAudit.ts").read_text()
    assert 'pilot_invite' in audit and 'status: "ready"' in audit
    assert "tenant_onboard" in audit


@pytest.mark.asyncio
async def test_tenancy_eon_and_invite_accept(client):
    tn = await client.get(f"{TN}/health")
    assert tn.status == 200

    onboard = await client.post(
        f"{TN}/onboarding",
        json={"name": "Pilot Co", "license_tier": "business"},
    )
    assert onboard.status == 201

    eon = await client.get(f"{EON}/health")
    assert eon.status == 200

    wiz = await client.post(
        f"{EON}/wizard",
        json={"company_name": "Pilot Co", "industry": "beauty"},
    )
    assert wiz.status == 201
    wizard = await wiz.json()
    assert wizard.get("wizard_id")

    reg = await client.post(
        f"{ECO}/identity/auth/register",
        json={"email": "owner32_1@example.com", "password": "Passw0rd!", "display_name": "Owner"},
    )
    assert reg.status == 201
    reg_body = await reg.json()
    token = reg_body["session"]["access_token"]

    org = await client.post(
        f"{ECO}/organizations",
        json={"name": "Pilot Org"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert org.status == 201
    org_body = await org.json()

    roles = await client.get(f"{ECO}/roles")
    assert roles.status == 200
    roles_body = await roles.json()
    role_id = roles_body["roles"][0]["role_id"]

    invite = await client.post(
        f"{ECO}/organizations/invitations",
        json={
            "organization_id": org_body["organization_id"],
            "email": "member32_1@example.com",
            "role_id": role_id,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert invite.status == 201
    invite_body = await invite.json()
    assert invite_body.get("token")
    assert invite_body.get("invite_url", "").startswith("/invite/accept")

    member = await client.post(
        f"{ECO}/identity/auth/register",
        json={"email": "member32_1@example.com", "password": "Passw0rd!", "display_name": "Member"},
    )
    assert member.status == 201
    member_token = (await member.json())["session"]["access_token"]

    accept = await client.post(
        f"{ECO}/organizations/invitations/accept",
        json={"token": invite_body["token"]},
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert accept.status == 201
    membership = await accept.json()
    assert membership.get("organization_id") == org_body["organization_id"]


def test_config_manifest_32_1():
    cfg = (ROOT / "applications" / "platform_builder" / "config.py").read_text()
    assert 'application_version: str = "1.50.0"' in cfg
    assert 'sprint: str = "32.4"' in cfg
    manifest = (ROOT / "applications" / "platform_builder" / "manifest.json").read_text()
    assert '"application_version": "1.50.0"' in manifest
    assert '"sprint": "32.4"' in manifest
    assert "invitations/accept" in (ROOT / "ecosystem" / "api" / "register.py").read_text()


def test_architecture_index_lists_32_1():
    index = (ROOT / "docs" / "ARCHITECTURE_AUDIT_INDEX.md").read_text()
    assert "32.1" in index
    assert "EXTERNAL_PILOT_GUIDE_32_1.md" in index
