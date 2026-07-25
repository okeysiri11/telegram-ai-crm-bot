"""Tests — Enterprise Security Verification (Sprint 26.1 / v9.0.0)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes
from applications.enterprise_hub.shared.exceptions import ValidationError
from platform_enterprise_security_verification.models import (
    AUTHN_CHECKS,
    COMPLIANCE_FRAMEWORKS,
    INTEGRATION_TARGETS,
    KPI_TARGETS,
    PRINCIPLES,
    VULN_CHECKS,
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
    "/api/enterprise-ees/v1",
    "/api/enterprise-eti/v1",
    "/api/enterprise-epl/v1",
    "/api/enterprise-ece/v1",
    "/api/enterprise-emr/v1",
]
ESV = "/api/enterprise-esv/v1"


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


def test_version_esv_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "9.0.3"
    assert health["enterprise_foundation"] == "Enterprise Platform v8.7.0"
    assert health["security_verification_ready"] is True
    assert health["vulnerability_scanner_ready"] is True
    assert health["secret_scanner_ready"] is True
    assert health["compliance_ready"] is True
    assert health["engines"]["security_verification"] == "1.0"
    assert health["migration_platform_ready"] is True
    assert health["security_hardening_ready"] is True
    assert "jwt" in AUTHN_CHECKS
    assert "sql_injection" in VULN_CHECKS
    assert "owasp_top_10" in COMPLIANCE_FRAMEWORKS
    assert "migration" in INTEGRATION_TARGETS
    assert KPI_TARGETS["block_release_on_critical"] is True
    assert "verify_never_exploit" in PRINCIPLES


def test_security_gate_blocks_critical():
    suite = enterprise_hub.security_verification
    clean = suite.run_gate(release="9.0.3")
    assert clean["release_blocked"] is False
    assert clean["production_allowed"] is True
    assert clean["reports"]["unified_security_report"] is True
    assert clean["vuln"]["checks"][0]["exploit_payload"] is None
    assert clean["authn"]["passed"] is True
    assert clean["authz"]["rbac_analyzed"] is True
    assert clean["tenancy"]["passed"] is True
    assert clean["compliance"]["passed"] is True

    blocked = suite.run_gate(
        release="9.0.3",
        vuln_findings=[{"check": "sql_injection", "severity": "critical"}],
        cves=[{"cve": "CVE-TEST-1", "package": "demo", "severity": "critical", "available_fix": "1.2.3"}],
    )
    assert blocked["release_blocked"] is True
    assert blocked["production_allowed"] is False
    assert blocked["vuln"]["blocks_release"] is True
    assert blocked["deps"]["blocks_release"] is True

    with pytest.raises(ValidationError):
        suite.run_gate(secret_hits=[{"type": "api_keys", "value": "sk-raw-secret"}])

    refs_ok = suite.run_gate(secret_hits=[{"type": "api_keys", "value": "vault://secrets/api"}])
    assert refs_ok["secrets"]["raw_secrets_exposed"] is False
    # hits present → secrets.passed False → release blocked
    assert refs_ok["release_blocked"] is True

    dash = suite.dashboard()
    assert "overall_security_score" in dash
    assert dash["ci_cd_required"] is True


def test_bootstrap_esv():
    suite = enterprise_hub.security_verification
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "9.0.3"
    assert boot["security_verification_ready"] is True
    assert boot["vulnerability_scanner_ready"] is True
    assert boot["secret_scanner_ready"] is True
    assert boot["compliance_ready"] is True
    assert boot["release_blocked"] is False
    assert boot["block_on_critical"] is True
    assert boot["ci_cd_required"] is True
    assert boot["duplicates_core_logic"] is False
    assert boot["duplicates_esh_logic"] is False
    assert boot["integrations"]["linked"] is True


@pytest.mark.asyncio
async def test_api_esv(client):
    health = await client.get(f"{ESV}/health")
    body = await health.json()
    assert body["application_version"] == "9.0.3"
    assert body["security_verification_ready"] is True

    boot = await client.post(f"{ESV}/bootstrap", json={})
    assert boot.status == 201
    assert (await boot.json())["secret_scanner_ready"] is True

    # legacy ESH remains
    esh = await client.get("/api/enterprise-esh/v1/health")
    assert esh.status == 200
    esh_body = await esh.json()
    esh_version = esh_body.get("application_version") or esh_body.get("data", {}).get("application_version")
    assert esh_version == "9.0.3"

    for prefix in PREFIXES:
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        payload = await resp.json()
        version = payload.get("application_version") or payload.get("data", {}).get("application_version")
        assert version == "9.0.3"


def test_docs_and_regression_25_5():
    for name in (
        "ENTERPRISE_SECURITY_VERIFICATION.md",
        "ESV_AUTH_TENANCY_API.md",
        "ESV_VULN_SECRETS_DEPS.md",
        "ESV_AUDIT_COMPLIANCE_DASHBOARD.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_SECURITY_VERIFICATION.md").exists()
    assert (ROOT / "platform_enterprise_security_verification" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "security_verification" / "facade.py").exists()
    assert (ROOT / "platform_security" / "facade.py").exists()

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
    assert '"application_version": "9.0.3"' in manifest
    assert "26.4" in manifest
