"""Tests — AI Legal Assistant (Sprint 17.6)."""

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


def test_version_assistant_ready():
    health = legal_enterprise.health()
    assert health["application_version"] == "5.0.0-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v4.9.7-enterprise"
    assert health["ai_legal_assistant_ready"] is True
    assert health["legal_research_engine_ready"] is True
    assert health["legal_reasoning_ready"] is True
    assert health["ai_legal_intelligence_ready"] is True
    assert health["compliance_platform_ready"] is True


def test_assistant_research_reasoning():
    suite = legal_enterprise.ai_legal_assistant
    ws = suite.assistant.create_workspace(name="QA Desk")
    conv = suite.assistant.start_conversation(workspace_id=ws["workspace_id"])
    qa = suite.assistant.ask(question="What is force majeure?", conversation_id=conv["conversation_id"])
    assert qa["message_id"]
    search = suite.research.semantic(query="force majeure")
    assert search["hit_count"] >= 1
    reasoning = suite.analysis.reason(query="Is force majeure available?")
    assert reasoning["kind"] == "reasoning"
    explanation = suite.explainability.explain(subject="force majeure", confidence=0.9)
    assert explanation["confidence_score"] == 0.9
    with pytest.raises(ValidationError):
        suite.assistant.ask(question="")


def test_knowledge_opinion_bootstrap():
    suite = legal_enterprise.ai_legal_assistant
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "5.0.0-enterprise"
    assert boot["workspace_id"] and boot["opinion_id"] and boot["explanation_id"]
    opinion = suite.opinions.draft_opinion(issue="QA opinion issue")
    assert "LEGAL OPINION" in opinion["draft"]
    for dtype in ("assistant", "research", "knowledge", "intelligence"):
        assert suite.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_assistant(client):
    health = await client.get(f"{AA}/health")
    body = await health.json()
    assert body["application_version"] == "5.0.0-enterprise"
    assert body["ai_legal_assistant_ready"] is True
    assert body["legal_research_engine_ready"] is True

    boot = await client.post(f"{AA}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    research = await client.post(
        f"{AA}/research",
        json={"action": "statute", "query": "damages"},
    )
    assert research.status == 201

    explain = await client.post(
        f"{AA}/explain",
        json={"subject": "damages", "confidence": 0.75},
    )
    assert explain.status == 201

    ask = await client.post(
        f"{AA}/assistant",
        json={
            "action": "ask",
            "question": "Summarize Art. 10",
            "conversation_id": boot_body["conversation_id"],
        },
    )
    assert ask.status == 201

    for prefix in (PREFIX, LI, JI, CM, DI, CP):
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        assert (await resp.json())["application_version"] == "5.0.0-enterprise"


def test_docs_and_regression_17_6():
    for name in (
        "AI_LEGAL_ASSISTANT.md",
        "LEGAL_RESEARCH_ENGINE.md",
        "LEGAL_REASONING_ENGINE.md",
        "AI_LEGAL_ANALYSIS.md",
        "LEGAL_OPINION_SUPPORT.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "AI_LEGAL_ASSISTANT.md").exists()
    assert (ROOT / "applications" / "legal_enterprise" / "ai_legal_assistant" / "facade.py").exists()
    assert (ROOT / "applications" / "legal_enterprise" / "compliance" / "facade.py").exists()

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
