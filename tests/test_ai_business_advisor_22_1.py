"""Tests — Enterprise AI Business Advisor (Sprint 22.1 / v7.1.0)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes
from applications.enterprise_hub.shared.exceptions import ValidationError
from platform_ai_business_advisor.models import INDUSTRIES, PRINCIPLES, RECOMMENDATION_KINDS


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
]
ABA = "/api/enterprise-aba/v1"


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


def test_version_aba_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "7.1.0"
    assert health["enterprise_foundation"] == "Enterprise Platform v7.0.0"
    assert health["ai_business_advisor_ready"] is True
    assert health["business_health_ready"] is True
    assert health["daily_brief_ready"] is True
    assert health["advisor_owner_approval_ready"] is True
    assert health["product_intelligence_ready"] is True
    assert health["engines"]["ai_business_advisor"] == "1.0"
    assert set(PRINCIPLES)
    assert "beauty" in INDUSTRIES and "crypto" in INDUSTRIES


def test_health_daily_owner_gate():
    suite = enterprise_hub.ai_business_advisor
    health = suite.analyze_health(
        industry="cafe",
        snapshot={"sales": 0.6, "customers": 0.55, "schedule_load": 0.5},
    )
    assert health["industry"] == "cafe"
    assert "sales" in health["problems"]
    daily = suite.run_daily(industry="beauty", snapshot={"repeat_visits": 0.4, "marketing_campaigns": 0.5})
    assert daily["requires_owner_review"] is True
    assert daily["ai_decision_authority"] is False
    assert daily["recommended_actions"]
    assert daily["recommendation_set_id"]
    rejected = suite.owner_decide(
        recommendation_set_id=daily["recommendation_set_id"],
        decision="reject",
        owner_id="business_owner",
    )
    assert rejected["execution_allowed"] is False
    assert rejected["ai_may_execute"] is False
    approved = suite.owner_decide(
        recommendation_set_id=daily["recommendation_set_id"],
        decision="approve",
        owner_id="business_owner",
    )
    assert approved["execution_allowed"] is True
    assert approved["ai_may_execute"] is False
    with pytest.raises(ValidationError):
        suite.analyze_health(industry="spaceships")
    assert set(RECOMMENDATION_KINDS)


def test_bootstrap_brief():
    suite = enterprise_hub.ai_business_advisor
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "7.1.0"
    assert boot["ai_never_executes"] is True
    assert boot["owner_approval_required"] is True
    assert boot["brief_ready"] is True
    assert boot["product_intelligence_handoffs"] >= 1
    assert boot["integrations"]["linked"] is True
    assert suite.latest_brief()["requires_owner_review"] is True


@pytest.mark.asyncio
async def test_api_aba(client):
    health = await client.get(f"{ABA}/health")
    body = await health.json()
    assert body["application_version"] == "7.1.0"
    assert body["ai_business_advisor_ready"] is True

    boot = await client.post(f"{ABA}/bootstrap", json={})
    assert boot.status == 201
    assert (await boot.json())["ai_never_executes"] is True

    brief = await client.get(f"{ABA}/brief")
    assert brief.status == 200
    assert (await brief.json())["requires_owner_review"] is True

    for prefix in PREFIXES:
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        payload = await resp.json()
        version = payload.get("application_version") or payload.get("data", {}).get("application_version")
        assert version == "7.1.0"


def test_docs_and_regression_22_1():
    for name in (
        "ENTERPRISE_AI_BUSINESS_ADVISOR.md",
        "ABA_HEALTH_OPPORTUNITIES.md",
        "ABA_RECOMMENDATIONS_FORECAST.md",
        "ABA_DAILY_BRIEF_INTEGRATION.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_AI_BUSINESS_ADVISOR.md").exists()
    assert (ROOT / "platform_ai_business_advisor" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "ai_business_advisor" / "facade.py").exists()

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
    assert '"application_version": "7.1.0"' in manifest
    assert "24.1" in manifest
