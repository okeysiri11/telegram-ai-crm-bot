"""Tests — Judicial Intelligence (Sprint 17.2)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.legal_enterprise import legal_enterprise
from applications.legal_enterprise.api.register import register_legal_enterprise_routes
from applications.legal_enterprise.judicial_intelligence.search import SEARCH_MODES
from applications.legal_enterprise.shared.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/legal-enterprise/v1"
LI = "/api/legal-li/v1"
JI = "/api/legal-ji/v1"


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


def test_version_judicial_intelligence_ready():
    health = legal_enterprise.health()
    assert health["application_version"] == "4.9.7-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v4.9.6-enterprise"
    assert health["judicial_intelligence_ready"] is True
    assert health["court_decision_repository_ready"] is True
    assert health["ai_judicial_analysis_ready"] is True
    assert health["case_law_intelligence_ready"] is True
    assert health["legislation_intelligence_ready"] is True


def test_court_repository_and_search():
    suite = legal_enterprise.judicial_intelligence
    judgment = suite.repository.register_judgment(
        title="Sample Judgment",
        decision_number="JUD-1",
        case_number="C-1",
        court_name="Trial Court",
        judge_name="Judge A",
        outcome="plaintiff_win",
        body="breach of contract",
    )
    assert judgment["decision_id"]
    hit = suite.search.keyword(query="breach", limit=5)
    assert hit["hit_count"] >= 1
    for mode in SEARCH_MODES:
        assert suite.search.search(mode=mode, query="JUD", limit=3)["mode"] == mode
    with pytest.raises(ValidationError):
        suite.repository.register(decision_type="unknown", title="X")


def test_analysis_analytics_and_bootstrap():
    suite = legal_enterprise.judicial_intelligence
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "4.9.7-enterprise"
    assert boot["judgment_id"] and boot["summary_id"] and boot["timeline_id"]
    assert suite.analysis.summarize(decision_id=boot["judgment_id"])["kind"] == "summarize"
    assert suite.analytics.report(kind="outcome")["kind"] == "outcome"
    assert suite.knowledge.status()["entries"] >= 5
    for dtype in ("court", "decision", "judge", "ai_judicial"):
        assert suite.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_judicial_intelligence(client):
    health = await client.get(f"{JI}/health")
    body = await health.json()
    assert body["application_version"] == "4.9.7-enterprise"
    assert body["judicial_intelligence_ready"] is True
    assert body["court_decision_repository_ready"] is True

    boot = await client.post(f"{JI}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    search = await client.post(
        f"{JI}/search",
        json={"action": "semantic", "query": "contract damages", "limit": 5},
    )
    assert search.status == 201

    analysis = await client.post(
        f"{JI}/analysis",
        json={"action": "similar_case", "decision_id": boot_body["judgment_id"]},
    )
    assert analysis.status == 201

    analytics = await client.post(f"{JI}/analytics", json={"kind": "court"})
    assert analytics.status == 201

    for prefix in (PREFIX, LI):
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        assert (await resp.json())["application_version"] == "4.9.7-enterprise"


def test_docs_and_regression_17_2():
    for name in (
        "JUDICIAL_INTELLIGENCE.md",
        "COURT_DECISIONS.md",
        "CASE_LAW_ANALYSIS.md",
        "JUDGE_ANALYTICS.md",
        "AI_JUDICIAL_ANALYSIS.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "JUDICIAL_INTELLIGENCE.md").exists()
    assert (ROOT / "applications" / "legal_enterprise" / "judicial_intelligence" / "facade.py").exists()
    assert (ROOT / "applications" / "legal_enterprise" / "legislation_intelligence" / "facade.py").exists()

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
