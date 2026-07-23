"""Tests — Legislation Intelligence (Sprint 17.1)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.legal_enterprise import legal_enterprise
from applications.legal_enterprise.api.register import register_legal_enterprise_routes
from applications.legal_enterprise.legislation_intelligence.search import SEARCH_MODES
from applications.legal_enterprise.shared.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/legal-enterprise/v1"
LI = "/api/legal-li/v1"
CE = "/api/crypto-enterprise/v1"


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


def test_version_legislation_intelligence_ready():
    health = legal_enterprise.health()
    assert health["application_version"] == "5.0.0-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v4.9.7-enterprise"
    assert health["legislation_intelligence_ready"] is True
    assert health["ai_legal_search_ready"] is True
    assert health["regulatory_intelligence_ready"] is True
    assert health["legal_knowledge_platform_ready"] is True
    assert health["legal_enterprise_foundation_ready"] is True


def test_repository_and_versions():
    suite = legal_enterprise.legislation_intelligence
    law = suite.repository.ingest_law(title="Sample Law", code="SL-1", body="sample obligations")
    assert law["document_id"]
    hist = suite.versions.record_history(document_id=law["document_id"], version="1.0")
    assert hist["version"] == "1.0"
    with pytest.raises(ValidationError):
        suite.repository.ingest(repo_type="unknown", title="X")


def test_search_analysis_and_bootstrap():
    suite = legal_enterprise.legislation_intelligence
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "5.0.0-enterprise"
    assert boot["law_id"] and boot["search_id"] and boot["summary_id"]
    for mode in SEARCH_MODES:
        row = suite.search.search(mode=mode, query="data", limit=3)
        assert row["mode"] == mode
    assert suite.analysis.summarize(document_id=boot["law_id"])["kind"] == "summarize"
    assert suite.knowledge.status()["entries"] >= 4
    for dtype in ("legislation", "regulation", "legal_search", "ai_analysis"):
        assert suite.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype
    with pytest.raises(ValidationError):
        suite.search.search(mode="unknown", query="x")


@pytest.mark.asyncio
async def test_api_legislation_intelligence(client):
    health = await client.get(f"{LI}/health")
    body = await health.json()
    assert body["application_version"] == "5.0.0-enterprise"
    assert body["legislation_intelligence_ready"] is True
    assert body["ai_legal_search_ready"] is True

    boot = await client.post(f"{LI}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    search = await client.post(
        f"{LI}/search",
        json={"action": "semantic", "query": "data protection", "limit": 5},
    )
    assert search.status == 201

    analysis = await client.post(
        f"{LI}/analysis",
        json={"action": "gap", "document_id": boot_body["law_id"]},
    )
    assert analysis.status == 201

    ce = await client.get(f"{PREFIX}/health")
    assert ce.status == 200
    assert (await ce.json())["application_version"] == "5.0.0-enterprise"


def test_docs_and_regression_17_1():
    for name in (
        "LEGISLATION_INTELLIGENCE.md",
        "LEGAL_SEARCH.md",
        "REGULATORY_ANALYSIS.md",
        "LEGAL_KNOWLEDGE_GRAPH.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "LEGISLATION_INTELLIGENCE.md").exists()
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
    assert "5.0.0-enterprise" in manifest
    assert "17.8" in manifest
    assert (ROOT / "applications" / "legal_enterprise" / "legal_registry.py").exists()
    _ = (CE,)
