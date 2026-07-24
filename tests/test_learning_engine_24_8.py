"""Tests — Enterprise Learning & Continuous Improvement Engine (Sprint 24.8 / v7.8.0)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes
from applications.enterprise_hub.shared.exceptions import ValidationError
from platform_enterprise_learning_engine.models import (
    AI_SAFETY,
    COLLECTOR_SOURCES,
    FEEDBACK_CLASSES,
    INTEGRATION_TARGETS,
    KPI_TARGETS,
    PRINCIPLES,
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
]
ELE = "/api/enterprise-ele/v1"


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


def test_version_ele_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "7.8.0"
    assert health["enterprise_foundation"] == "Enterprise Platform v7.7.0"
    assert health["learning_engine_ready"] is True
    assert health["confirmed_learning_ready"] is True
    assert health["cross_tenant_learning_ready"] is True
    assert health["owner_learning_ready"] is True
    assert health["engines"]["learning_engine"] == "1.0"
    assert health["strategy_intelligence_ready"] is True
    assert "commerce" in COLLECTOR_SOURCES
    assert "success_case" in FEEDBACK_CLASSES
    assert "strategy_intelligence" in INTEGRATION_TARGETS
    assert KPI_TARGETS["confirmed_learning_only"] is True
    assert "no_self_modify_algorithms" in AI_SAFETY
    assert set(PRINCIPLES)


def test_confirmed_learning_flow():
    suite = enterprise_hub.learning_engine
    collected = suite.collect(
        events=[
            {"source": "crm", "confirmed": True, "kind": "success"},
            {"source": "erp", "confirmed": False, "kind": "error"},
        ]
    )
    assert collected["accepted_count"] == 1
    assert collected["rejected_count"] == 1
    assert collected["confirmed_only"] is True

    with pytest.raises(ValidationError):
        suite.register(
            learning_id="lrn_bad",
            source="crm",
            tenant="t1",
            module="crm",
            knowledge_type="pattern",
            confirmed=False,
        )

    record = suite.register(
        learning_id="lrn_ok",
        source="commerce",
        tenant="t1",
        module="commerce_core",
        knowledge_type="best_practice",
        confirmed=True,
        payload={"pattern": "upsell"},
    )
    assert record["confirmed"] is True
    assert record["pii_stripped"] is True

    fb = suite.classify_feedback(text="This is a complaint about slow checkout")
    assert fb["class"] == "complaint"

    patterns = suite.detect_patterns(items=[{"kind": "error"}, {"kind": "error"}, {"kind": "success"}, {"kind": "success"}])
    assert any(p["pattern"] == "repeating_errors" for p in patterns["patterns"])

    with pytest.raises(ValidationError):
        suite.cross_tenant(anonymized_signals=[{"pattern": "x", "pii": True}])

    cross = suite.cross_tenant(anonymized_signals=[{"pattern": "upsell", "anonymized": True}, {"pattern": "upsell", "anonymized": True}])
    assert cross["pii_transferred"] is False
    assert cross["anonymized_only"] is True

    evo = suite.evolve(past_success_rate=0.8, acceptance_rate=0.7, completion_rate=0.6, outcome_score=0.75, industry="beauty")
    assert evo["uses_confirmed_history"] is True

    score = suite.score_agent(agent_id="finance_ai", accuracy=0.9, user_trust=0.8)
    assert score["overall"] > 0

    decision = suite.owner_decide(action="approve", actor="platform_owner", learning_id="lrn_ok")
    assert decision["status"] == "approved"
    assert decision["may_change_algorithms"] is False

    with pytest.raises(ValidationError):
        suite.owner_decide(action="approve", actor="agent", learning_id="lrn_ok")

    product = suite.product_push(improvement="Faster checkout", confirmed=True)
    assert product["requires_owner_before_dev"] is True
    assert product["auto_deploy"] is False

    with pytest.raises(ValidationError):
        suite.product_push(improvement="Unconfirmed idea", confirmed=False)

    safety = suite.safety_check(intent="modify_algorithms")
    assert safety["allowed"] is False

    dash = suite.owner_dashboard()
    assert dash["ai_may_act"] is False
    assert dash["autonomous_learn"] is False


def test_bootstrap_ele():
    suite = enterprise_hub.learning_engine
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "7.8.0"
    assert boot["learning_engine_ready"] is True
    assert boot["confirmed_learning_ready"] is True
    assert boot["cross_tenant_learning_ready"] is True
    assert boot["owner_learning_ready"] is True
    assert boot["ai_may_act"] is False
    assert boot["autonomous_learn"] is False
    assert boot["confirmed_only"] is True
    assert boot["pii_transferred"] is False
    assert boot["may_change_algorithms"] is False
    assert boot["duplicates_core_logic"] is False
    assert boot["integrations"]["linked"] is True


@pytest.mark.asyncio
async def test_api_ele(client):
    health = await client.get(f"{ELE}/health")
    body = await health.json()
    assert body["application_version"] == "7.8.0"
    assert body["learning_engine_ready"] is True

    boot = await client.post(f"{ELE}/bootstrap", json={})
    assert boot.status == 201
    assert (await boot.json())["owner_learning_ready"] is True

    for prefix in PREFIXES:
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        payload = await resp.json()
        version = payload.get("application_version") or payload.get("data", {}).get("application_version")
        assert version == "7.8.0"


def test_docs_and_regression_24_8():
    for name in (
        "ENTERPRISE_LEARNING_ENGINE.md",
        "ELE_REGISTRY_COLLECTOR.md",
        "ELE_FEEDBACK_PATTERNS.md",
        "ELE_SCORE_OWNER_SAFETY.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_LEARNING_ENGINE.md").exists()
    assert (ROOT / "platform_enterprise_learning_engine" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "learning_engine" / "facade.py").exists()

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
    assert '"application_version": "7.8.0"' in manifest
    assert "24.8" in manifest
