"""Tests — Enterprise Identity, Security & Access Management (Sprint 19.8)."""

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


def test_version_isam_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "6.0.0-rc3"
    assert health["enterprise_foundation"] == "Enterprise Platform v6.0.0-rc2"
    assert health["enterprise_isam_ready"] is True
    assert health["authentication_ready"] is True
    assert health["authorization_ready"] is True
    assert health["security_monitoring_ready"] is True
    assert health["enterprise_data_platform_ready"] is True
    assert health["engines"]["isam"] == "1.0"
    assert health["engines"]["enterprise_identity"] == "1.0"


def test_identity_auth_rbac_session():
    suite = enterprise_hub.isam
    user = suite.identity.register(
        subject="qa@bidex.io", identity_type="user", roles=["manager"]
    )
    login = suite.authentication.login(subject="qa@bidex.io", provider="local")
    suite.permissions.grant(identity_id=user["identity_id"], permission="approve")
    authz = suite.authorization.authorize(
        identity_id=user["identity_id"], permission="approve", mode="rbac"
    )
    assert authz["allowed"] is True
    sess = suite.sessions.create(identity_id=user["identity_id"], device="linux", ip="127.0.0.1")
    tok = suite.tokens.issue(identity_id=user["identity_id"], token_type="access")
    assert login["auth_id"] and sess["session_id"] and tok["token_id"]
    with pytest.raises(ValidationError):
        suite.identity.register(subject="", identity_type="user")


def test_mfa_monitor_audit_bootstrap():
    suite = enterprise_hub.isam
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "6.0.0-rc3"
    assert boot["identity_admin_id"] and boot["intrusion_id"] and boot["mfa_totp_id"]
    mfa = suite.mfa.challenge(method="totp", subject="qa")
    assert mfa["verified"] is True
    for dtype in ("identity", "sessions", "access", "monitoring", "audit"):
        assert suite.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_isam(client):
    health = await client.get(f"{ISAM}/health")
    body = await health.json()
    assert body["application_version"] == "6.0.0-rc3"
    assert body["enterprise_isam_ready"] is True
    assert body["authentication_ready"] is True

    boot = await client.post(f"{ISAM}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    created = await client.post(
        f"{ISAM}/identity",
        json={"subject": "api@bidex.io", "identity_type": "user", "roles": ["employee"]},
    )
    assert created.status == 201

    for prefix in (HUB, ORCH, KG, AA, CM, WF, EIP, EDP):
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        assert (await resp.json())["application_version"] == "6.0.0-rc3"

    assert boot_body["policy_ip_id"]


def test_docs_and_regression_19_8():
    for name in (
        "ENTERPRISE_ISAM.md",
        "IDENTITY_PROVIDER.md",
        "AUTHENTICATION.md",
        "AUTHORIZATION.md",
        "SECURITY_MONITORING.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_ISAM.md").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "security" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "security" / "providers" / "oauth2.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "security" / "mfa" / "totp.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "security" / "monitoring" / "intrusion.py").exists()

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
