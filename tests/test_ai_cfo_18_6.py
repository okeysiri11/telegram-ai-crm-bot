"""Tests — AI CFO & Financial Decision Support (Sprint 18.6)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.finance_enterprise import finance_enterprise
from applications.finance_enterprise.api.register import register_finance_enterprise_routes
from applications.finance_enterprise.shared.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/finance-enterprise/v1"
PAY = "/api/finance-pay/v1"
BIL = "/api/finance-bil/v1"
TR = "/api/finance-tr/v1"
DA = "/api/finance-da/v1"
RPT = "/api/finance-rpt/v1"
CFO = "/api/finance-cfo/v1"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_finance_enterprise_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    finance_enterprise.reset()
    yield
    finance_enterprise.reset()


def test_version_ai_cfo_ready():
    health = finance_enterprise.health()
    assert health["application_version"] == "5.1.6-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v5.1.5-enterprise"
    assert health["ai_cfo_ready"] is True
    assert health["financial_decision_support_ready"] is True
    assert health["financial_modeling_ready"] is True
    assert health["executive_financial_intelligence_ready"] is True
    assert health["financial_reporting_ready"] is True
    assert health["engines"]["ai_cfo"] == "1.0"


def test_modeling_and_risk():
    suite = finance_enterprise.ai_cfo
    roi = suite.modeling.model(
        model_type="roi",
        label="QA ROI",
        inputs={"investment": 100, "gain": 150},
    )
    assert roi["result"] == 50.0
    risk = suite.risk.assess(risk_type="liquidity", subject="QA", score=0.3)
    assert risk["severity"] == "low"
    with pytest.raises(ValidationError):
        suite.modeling.model(model_type="roi", label="")


def test_decisions_executive_bootstrap():
    suite = finance_enterprise.ai_cfo
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "5.1.6-enterprise"
    assert boot["workspace_id"] and boot["roi_id"] and boot["nl_report_id"]
    assert suite.decisions.recommend(
        recommendation_type="executive", subject="QA"
    )["recommendation_type"] == "executive"
    assert suite.executive.report(report_type="board", audience="board")["report_type"] == "board"
    for dtype in ("ai_cfo", "financial_health", "investment", "risk", "strategy"):
        assert suite.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_ai_cfo(client):
    health = await client.get(f"{CFO}/health")
    body = await health.json()
    assert body["application_version"] == "5.1.6-enterprise"
    assert body["ai_cfo_ready"] is True
    assert body["financial_modeling_ready"] is True

    boot = await client.post(f"{CFO}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    mdl = await client.post(
        f"{CFO}/modeling",
        json={"model_type": "npv", "label": "API NPV", "inputs": {"investment": 10, "present_value": 15}},
    )
    assert mdl.status == 201

    exe = await client.post(
        f"{CFO}/executive",
        json={"report_type": "nl_report", "audience": "ceo"},
    )
    assert exe.status == 201

    for prefix in (PREFIX, PAY, BIL, TR, DA, RPT):
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        assert (await resp.json())["application_version"] == "5.1.6-enterprise"

    assert boot_body["rec_priority_id"]


def test_docs_and_regression_18_6():
    for name in (
        "AI_CFO.md",
        "FINANCIAL_DECISION_SUPPORT.md",
        "FINANCIAL_MODELING.md",
        "EXECUTIVE_FINANCE.md",
        "AI_FINANCIAL_STRATEGY.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "AI_CFO.md").exists()
    assert (ROOT / "applications" / "finance_enterprise" / "ai_cfo" / "facade.py").exists()
    assert (ROOT / "applications" / "finance_enterprise" / "reporting" / "facade.py").exists()

    from applications.ai_os.config import DEFAULT_CONFIG as AIOS
    from applications.enterprise.config import DEFAULT_CONFIG as ENT
    from applications.auto_marketplace.config import DEFAULT_CONFIG as AUTO
    from applications.agro_enterprise.config import DEFAULT_CONFIG as AGRO
    from applications.port_enterprise.config import DEFAULT_CONFIG as PORT
    from applications.port_erp.config import DEFAULT_CONFIG as PORT_ERP
    from applications.crypto_enterprise.config import DEFAULT_CONFIG as CRYPTO
    from applications.legal_enterprise.config import DEFAULT_CONFIG as LEGAL

    assert AIOS.application_version == "3.4.0-alpha"
    assert ENT.application_version == "4.0.0-enterprise"
    assert AUTO.application_version == "4.2.0-enterprise"
    assert AGRO.application_version == "4.4.0-enterprise"
    assert PORT.application_version == "4.6.0-enterprise"
    assert PORT_ERP.application_version == "2.0.0"
    assert CRYPTO.application_version == "4.8.0-enterprise"
    assert LEGAL.application_version == "5.0.0-enterprise"
    manifest = (ROOT / "applications" / "finance_enterprise" / "manifest.json").read_text()
    assert "5.1.6-enterprise" in manifest
    assert "18.6" in manifest
