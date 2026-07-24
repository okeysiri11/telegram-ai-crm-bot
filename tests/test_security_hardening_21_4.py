"""Tests — Enterprise Security Hardening (Sprint 21.4 / v6.0.0)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes
from applications.enterprise_hub.shared.exceptions import ValidationError
from platform_security.authentication import IdentitySecurity
from platform_security.zero_trust import ZeroTrustEngine


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
]
ESH = "/api/enterprise-esh/v1"


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


def test_version_esh_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "7.7.0"
    assert health["enterprise_foundation"] == "Enterprise Platform v7.6.0"
    assert health["security_hardening_ready"] is True
    assert health["zero_trust_ready"] is True
    assert health["secrets_management_ready"] is True
    assert health["compliance_ready"] is True
    assert health["data_contracts_ready"] is True
    assert health["engines"]["security_hardening"] == "1.0"


def test_auth_zero_trust_secrets():
    suite = enterprise_hub.security_hardening
    sess = suite.authenticate(method="jwt", principal="alice", secret="s3cret")
    assert sess["access_token"]
    zt = suite.zero_trust(
        {
            "user": "alice",
            "device": "laptop",
            "token": sess["access_token"],
            "ip": "10.1.1.1",
            "context": "office",
            "risk_level": 0.2,
            "security_policy": "default",
        }
    )
    assert zt["allowed"] is True
    secret = suite.put_secret(name="demo-key", kind="api_key", value="abc")
    assert secret["fingerprint"]
    with pytest.raises(ValidationError):
        suite.authenticate(method="mfa", principal="bob")


def test_bootstrap_dashboard():
    suite = enterprise_hub.security_hardening
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "7.7.0"
    assert boot["secrets"] >= 6
    assert boot["audit_entries"] >= 7
    assert boot["compliance_ready"] is True
    assert boot["security_tests_passed"] is True
    assert boot["hardening_level"] == "production_ready"
    assert boot["dashboard_id"]
    assert boot["integrations"]["linked"] is True
    dash = suite.dashboard()
    assert dash["executive_summary"]


@pytest.mark.asyncio
async def test_api_esh(client):
    health = await client.get(f"{ESH}/health")
    body = await health.json()
    assert body["application_version"] == "7.7.0"
    assert body["security_hardening_ready"] is True

    boot = await client.post(f"{ESH}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    comp = await client.get(f"{ESH}/compliance")
    assert comp.status == 200
    assert (await comp.json())["overall_ready"] is True

    for prefix in PREFIXES:
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        payload = await resp.json()
        version = payload.get("application_version") or payload.get("data", {}).get("application_version")
        assert version == "7.7.0"

    assert boot_body["zero_trust_allowed"] is True


def test_docs_and_regression_21_4():
    for name in (
        "ENTERPRISE_SECURITY_HARDENING.md",
        "ESH_IDENTITY_ACCESS.md",
        "ESH_ZERO_TRUST_SECRETS.md",
        "ESH_COMPLIANCE_DASHBOARD.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_SECURITY_HARDENING.md").exists()
    assert (ROOT / "platform_security" / "facade.py").exists()
    assert (ROOT / "platform_security" / "zero_trust" / "__init__.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "security_hardening" / "facade.py").exists()
    assert IdentitySecurity().methods()
    assert "user" in ZeroTrustEngine().evaluate(
        {
            "user": "x",
            "device": "d",
            "token": "t",
            "ip": "1",
            "context": "c",
            "risk_level": 0.1,
            "security_policy": "p",
        }
    )["checks"]

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
    assert "7.7.0" in manifest
    assert "24.7" in manifest
