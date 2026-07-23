"""Tests — Unified Knowledge Graph & AI Memory (Sprint 19.2)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes
from applications.enterprise_hub.shared.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
HUB = "/api/enterprise-hub/v1"
ORCH = "/api/enterprise-orch/v1"
KG = "/api/enterprise-kg/v1"


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


def test_version_knowledge_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "5.3.5-enterprise"
    assert health["enterprise_foundation"] == "Enterprise Platform v5.3.4-enterprise"
    assert health["unified_knowledge_graph_ready"] is True
    assert health["ai_memory_ready"] is True
    assert health["semantic_intelligence_ready"] is True
    assert health["cross_platform_context_ready"] is True
    assert health["ai_orchestrator_ready"] is True
    assert health["engines"]["unified_knowledge"] == "1.0"


def test_graph_and_memory():
    suite = enterprise_hub.unified_knowledge
    org = suite.graph.register_entity(name="QA Org", entity_type="organization")
    person = suite.graph.register_entity(name="QA User", entity_type="person")
    rel = suite.graph.relate(
        from_entity_id=person["entity_id"],
        to_entity_id=org["entity_id"],
        relation="member_of",
    )
    mem = suite.memory.remember(
        memory_type="business", subject="QA", content="Test memory"
    )
    assert rel["relationship_id"] and mem["memory_id"]
    with pytest.raises(ValidationError):
        suite.graph.register_entity(name="", entity_type="organization")


def test_semantic_sync_ai_bootstrap():
    suite = enterprise_hub.unified_knowledge
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "5.3.5-enterprise"
    assert boot["graph_id"] and boot["ai_nl_id"] and boot["sync_finance_id"]
    assert suite.semantic.operate(operation="semantic_search", query="Bidex")["operation"] == "semantic_search"
    assert suite.ai.nl_query(question="Who is Bidex?")["insight_type"] == "nl_query"
    for dtype in ("knowledge", "entity", "relationship", "ai_memory", "semantic"):
        assert suite.dashboard.render(dashboard_type=dtype)["dashboard_type"] == dtype


@pytest.mark.asyncio
async def test_api_knowledge_graph(client):
    health = await client.get(f"{KG}/health")
    body = await health.json()
    assert body["application_version"] == "5.3.5-enterprise"
    assert body["unified_knowledge_graph_ready"] is True
    assert body["ai_memory_ready"] is True

    boot = await client.post(f"{KG}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    sem = await client.post(
        f"{KG}/semantic",
        json={"operation": "entity_resolution", "query": "Acme"},
    )
    assert sem.status == 201

    ai = await client.post(
        f"{KG}/ai",
        json={"action": "nl_query", "question": "Summarize graph", "audience": "board"},
    )
    assert ai.status == 201

    for prefix in (HUB, ORCH):
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        assert (await resp.json())["application_version"] == "5.3.5-enterprise"

    assert boot_body["ontology_id"]


def test_docs_and_regression_19_2():
    for name in (
        "UNIFIED_KNOWLEDGE_GRAPH.md",
        "AI_MEMORY.md",
        "SEMANTIC_SEARCH.md",
        "ENTERPRISE_ONTOLOGY.md",
        "CROSS_PLATFORM_CONTEXT.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "UNIFIED_KNOWLEDGE_GRAPH.md").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "knowledge" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "orchestrator" / "facade.py").exists()

    from applications.ai_os.config import DEFAULT_CONFIG as AIOS
    from applications.enterprise.config import DEFAULT_CONFIG as ENT
    from applications.auto_marketplace.config import DEFAULT_CONFIG as AUTO
    from applications.agro_enterprise.config import DEFAULT_CONFIG as AGRO
    from applications.port_enterprise.config import DEFAULT_CONFIG as PORT
    from applications.port_erp.config import DEFAULT_CONFIG as PORT_ERP
    from applications.crypto_enterprise.config import DEFAULT_CONFIG as CRYPTO
    from applications.legal_enterprise.config import DEFAULT_CONFIG as LEGAL
    from applications.finance_enterprise.config import DEFAULT_CONFIG as FINANCE

    assert AIOS.application_version == "3.4.0-alpha"
    assert ENT.application_version == "4.0.0-enterprise"
    assert AUTO.application_version == "4.2.0-enterprise"
    assert AGRO.application_version == "4.4.0-enterprise"
    assert PORT.application_version == "4.6.0-enterprise"
    assert PORT_ERP.application_version == "2.0.0"
    assert CRYPTO.application_version == "4.8.0-enterprise"
    assert LEGAL.application_version == "5.0.0-enterprise"
    assert FINANCE.application_version == "5.2.0-enterprise"
    manifest = (ROOT / "applications" / "enterprise_hub" / "manifest.json").read_text()
    assert "5.3.5-enterprise" in manifest
    assert "19.5" in manifest
