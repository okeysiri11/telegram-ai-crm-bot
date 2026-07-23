"""Tests — Executive Legal Intelligence (Sprint 17.7)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.legal_enterprise import legal_enterprise
from applications.legal_enterprise.api.register import register_legal_enterprise_routes
from applications.legal_enterprise.shared.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/legal-enterprise/v1"
LI = "/api/legal-li/v1"
JI = "/api/legal-ji/v1"
CM = "/api/legal-cm/v1"
DI = "/api/legal-di/v1"
CP = "/api/legal-cp/v1"
AA = "/api/legal-aa/v1"
EI = "/api/legal-ei/v1"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_legal_enterprise_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    legal_enterprise.reset()
    yield
    legal_enterprise.reset()


def test_version_executive_ready():
    health = legal_enterprise.health()
    assert health["application_version"] == "4.9.7-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v4.9.6-enterprise"
    assert health["executive_legal_intelligence_ready"] is True
    assert health["decision_support_ready"] is True
    assert health["enterprise_legal_analytics_ready"] is True
    assert health["regulatory_forecasting_ready"] is True
    assert health["ai_legal_assistant_ready"] is True


def test_executive_dashboard_and_risk():
    suite = legal_enterprise.executive_intelligence
    snap = suite.executive.snapshot(section="overview")
    assert snap["section"] == "overview"
    risk = suite.risk.score(score_type="enterprise", subject="QA Corp", value=70)
    assert risk["band"] == "high"
    an = suite.analytics.report(kind="case_success")
    assert "win_rate" in an["metrics"]
    with pytest.raises(ValidationError):
        suite.executive.snapshot(section="invalid")


def test_forecast_decisions_ai_bootstrap():
    suite = legal_enterprise.executive_intelligence
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "4.9.7-enterprise"
    assert boot["overview_id"] and boot["qa_id"] and boot["exec_rec_id"]
    fc = suite.forecasting.register(action="upcoming_change", title="QA Reg Change")
    assert fc["forecast_id"]
    rec = suite.decisions.recommend(kind="strategy", title="QA Strategy")
    assert rec["recommendation_id"]
    for dtype in ("executive", "risk", "forecast", "strategy", "operations"):
        assert suite.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_executive(client):
    health = await client.get(f"{EI}/health")
    body = await health.json()
    assert body["application_version"] == "4.9.7-enterprise"
    assert body["executive_legal_intelligence_ready"] is True
    assert body["decision_support_ready"] is True

    boot = await client.post(f"{EI}/bootstrap", json={})
    assert boot.status == 201

    risk = await client.post(
        f"{EI}/risk",
        json={"action": "score", "score_type": "department", "subject": "Compliance", "value": 45},
    )
    assert risk.status == 201

    ai = await client.post(
        f"{EI}/ai",
        json={"action": "ask", "question": "What should the board prioritize?"},
    )
    assert ai.status == 201

    for prefix in (PREFIX, LI, JI, CM, DI, CP, AA):
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        assert (await resp.json())["application_version"] == "4.9.7-enterprise"


def test_docs_and_regression_17_7():
    for name in (
        "EXECUTIVE_LEGAL_INTELLIGENCE.md",
        "LEGAL_DECISION_SUPPORT.md",
        "LEGAL_ANALYTICS.md",
        "REGULATORY_FORECASTING.md",
        "LEGAL_EXECUTIVE_REPORTING.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "EXECUTIVE_LEGAL_INTELLIGENCE.md").exists()
    assert (ROOT / "applications" / "legal_enterprise" / "executive_intelligence" / "facade.py").exists()
    assert (ROOT / "applications" / "legal_enterprise" / "ai_legal_assistant" / "facade.py").exists()

    from applications.ai_os.config import DEFAULT_CONFIG as AIOS
    from applications.enterprise.config import DEFAULT_CONFIG as ENT
    from applications.auto_marketplace.config import DEFAULT_CONFIG as AUTO
    from applications.agro_enterprise.config import DEFAULT_CONFIG as AGRO
    from applications.port_enterprise.config import DEFAULT_CONFIG as PORT
    from applications.port_erp.config import DEFAULT_CONFIG as PORT_ERP
    from applications.crypto_enterprise.config import DEFAULT_CONFIG as CRYPTO

    assert AIOS.application_version == "3.4.0-alpha"
    assert ENT.application_version == "4.0.0-enterprise"
    assert AUTO.application_version == "4.2.0-enterprise"
    assert AGRO.application_version == "4.4.0-enterprise"
    assert PORT.application_version == "4.6.0-enterprise"
    assert PORT_ERP.application_version == "2.0.0"
    assert CRYPTO.application_version == "4.8.0-enterprise"
    manifest = (ROOT / "applications" / "legal_enterprise" / "manifest.json").read_text()
    assert "4.9.7-enterprise" in manifest
    assert "17.7" in manifest
