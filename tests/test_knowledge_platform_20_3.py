"""Tests — Enterprise Knowledge Platform (Sprint 20.3)."""

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
AA = "/api/enterprise-agents/v1"
CM = "/api/enterprise-comms/v1"
WF = "/api/enterprise-workflow/v1"
EIP = "/api/enterprise-eip/v1"
EDP = "/api/enterprise-edp/v1"
ISAM = "/api/enterprise-isam/v1"
OBS = "/api/enterprise-obs/v1"
TN = "/api/enterprise-tenancy/v1"
AOP = "/api/enterprise-aop/v1"
ATS = "/api/enterprise-ats/v1"
EKP = "/api/enterprise-ekp/v1"


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


def test_version_ekp_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "7.2.0"
    assert health["enterprise_foundation"] == "Enterprise Platform v7.1.0"
    assert health["enterprise_knowledge_ready"] is True
    assert health["rag_ready"] is True
    assert health["knowledge_graph_ready"] is True
    assert health["vector_index_ready"] is True
    assert health["ai_tools_ready"] is True
    assert health["engines"]["knowledge_platform"] == "1.0"
    assert health["engines"]["unified_knowledge"] == "1.0"


def test_ingest_rag_graph_memory():
    suite = enterprise_hub.knowledge_platform
    doc = suite.documents.ingest(
        title="QA Policy",
        content="All contracts require legal review before CRM close.",
        doc_type="markdown",
        tags=["legal"],
    )
    indexed = suite.index_document(document_id=doc["document_id"])
    assert indexed["vectors"] >= 1
    answer = suite.rag.answer(query="legal review contracts", mode="hybrid")
    assert answer["citation_id"] and answer["sources"]
    ent = suite.graph.add_entity(kind="document", name="QA Policy")
    agent = suite.graph.add_entity(kind="ai_agent", name="Legal")
    link = suite.graph.link(source_id=agent["entity_id"], target_id=ent["entity_id"], relation="references")
    mem = suite.memory.store_memory(tier="organization", key="qa", value="policy")
    assert link["relation_id"] and mem["memory_id"]
    with pytest.raises(ValidationError):
        suite.documents.ingest(title="", content="x")


def test_bootstrap_analytics():
    suite = enterprise_hub.knowledge_platform
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "7.2.0"
    assert boot["answer_id"] and boot["relevance_id"] and boot["context_id"]


@pytest.mark.asyncio
async def test_api_ekp(client):
    health = await client.get(f"{EKP}/health")
    body = await health.json()
    assert body["application_version"] == "7.2.0"
    assert body["enterprise_knowledge_ready"] is True
    assert body["rag_ready"] is True

    boot = await client.post(f"{EKP}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    created = await client.post(
        f"{EKP}/documents",
        json={"title": "API Doc", "content": "vector search notes", "doc_type": "markdown"},
    )
    assert created.status == 201

    for prefix in (HUB, ORCH, KG, AA, CM, WF, EIP, EDP, ISAM, OBS, TN, AOP, ATS):
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        assert (await resp.json())["application_version"] == "7.2.0"

    assert boot_body["citation_id"]


def test_docs_and_regression_20_3():
    for name in (
        "ENTERPRISE_KNOWLEDGE_PLATFORM.md",
        "EKP_DOCUMENTS.md",
        "EKP_RAG.md",
        "EKP_GRAPH_MEMORY.md",
        "EKP_GOVERNANCE.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_KNOWLEDGE_PLATFORM.md").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "knowledge_platform" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "knowledge_platform" / "rag_engine.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "knowledge_platform" / "connectors" / "github.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "knowledge_platform" / "parsers" / "pdf.py").exists()
    # 19.2 package untouched path still exists
    assert (ROOT / "applications" / "enterprise_hub" / "knowledge" / "facade.py").exists()

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
    assert "7.2.0" in manifest
    assert "24.2" in manifest
