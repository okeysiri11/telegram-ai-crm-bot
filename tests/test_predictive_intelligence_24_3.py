"""Tests — Enterprise Predictive Intelligence Engine (Sprint 24.7 / v7.7.0)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes
from applications.enterprise_hub.shared.exceptions import ValidationError
from platform_predictive_intelligence.models import (
    FORECAST_DOMAINS,
    KPI_TARGETS,
    PRINCIPLES,
    SCENARIO_KINDS,
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
]
PIN = "/api/enterprise-pin/v1"


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


def test_version_pin_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "7.7.0"
    assert health["enterprise_foundation"] == "Enterprise Platform v7.6.0"
    assert health["predictive_intelligence_ready"] is True
    assert health["business_forecast_ready"] is True
    assert health["risk_intelligence_ready"] is True
    assert health["opportunity_detector_ready"] is True
    assert health["engines"]["predictive_intelligence"] == "1.0"
    # Product Intelligence remains distinct
    assert health["product_intelligence_ready"] is True
    assert "revenue" in FORECAST_DOMAINS
    assert set(SCENARIO_KINDS) == {"optimistic", "baseline", "conservative", "crisis"}
    assert KPI_TARGETS["early_problem_detection"] is True
    assert set(PRINCIPLES)


def test_forecasts_risks_learning_dashboard():
    suite = enterprise_hub.predictive_intelligence
    models = suite.list_models()
    assert models["count"] >= 7

    biz = suite.business_forecast(domain="revenue", horizon_days=30, baseline=10000)
    assert biz["explained"] is True
    assert biz["confidence"] >= 0.5
    assert "scenarios" in biz
    assert len(biz["scenarios"]["scenarios"]) == 4

    cust = suite.customer_predict(customer_id="c_risk", signals={"days_since_visit": 80, "visits": 2, "spend": 100})
    assert cust["churn_probability"] > 0.4

    mkt = suite.marketing_predict(channel="whatsapp", budget=150)
    assert mkt["best_channel"]

    ops = suite.operations_predict(branch_id="b1", load_pct=0.9, inventory_days=4)
    assert ops["staff_overload"] is True
    assert ops["material_shortage"] is True

    risks = suite.assess_risks(
        signals={
            "customer_loss": 0.7,
            "financial": 0.6,
            "operational": 0.55,
            "process_failure": 0.5,
            "security": 0.45,
        }
    )
    assert risks["early_warning"] is True

    opps = suite.detect_opportunities(signals={"open_slots": 10, "promo_headroom": 1})
    assert opps["count"] >= 1

    blocked = suite.learn(forecast=100, actual=90, confirmed=False)
    assert blocked["learned"] is False
    learned = suite.learn(forecast=10000, actual=9700, confirmed=True, model_id="m_revenue")
    assert learned["learned"] is True

    dash = suite.owner_dashboard()
    assert dash["ai_may_act"] is False
    assert dash["auto_actions"] is False
    assert dash["daily_forecasts"]

    with pytest.raises(ValidationError):
        suite.business_forecast(domain="astrology")


def test_bootstrap_pin():
    suite = enterprise_hub.predictive_intelligence
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "7.7.0"
    assert boot["predictive_intelligence_ready"] is True
    assert boot["ai_may_act"] is False
    assert boot["auto_actions"] is False
    assert boot["shared_prediction_layer"] is True
    assert boot["scenarios_ready"] is True
    assert boot["duplicates_core_logic"] is False
    assert boot["integrations"]["linked"] is True


@pytest.mark.asyncio
async def test_api_pin(client):
    health = await client.get(f"{PIN}/health")
    body = await health.json()
    assert body["application_version"] == "7.7.0"
    assert body["predictive_intelligence_ready"] is True

    boot = await client.post(f"{PIN}/bootstrap", json={})
    assert boot.status == 201
    assert (await boot.json())["business_forecast_ready"] is True

    for prefix in PREFIXES:
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        payload = await resp.json()
        version = payload.get("application_version") or payload.get("data", {}).get("application_version")
        assert version == "7.7.0"


def test_docs_and_regression_24_3():
    for name in (
        "ENTERPRISE_PREDICTIVE_INTELLIGENCE.md",
        "PIN_REGISTRY_BUSINESS.md",
        "PIN_MARKETING_OPS_RISK.md",
        "PIN_SCENARIOS_OWNER.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_PREDICTIVE_INTELLIGENCE.md").exists()
    assert (ROOT / "platform_predictive_intelligence" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "predictive_intelligence" / "facade.py").exists()

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
    assert '"application_version": "7.7.0"' in manifest
    assert "24.7" in manifest
