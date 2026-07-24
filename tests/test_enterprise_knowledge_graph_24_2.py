"""Tests — Enterprise Knowledge Graph & Semantic Memory (Sprint 24.7 / v7.7.0)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes
from applications.enterprise_hub.shared.exceptions import ValidationError
from platform_enterprise_knowledge_graph.models import (
    ENTITY_TYPES,
    KPI_TARGETS,
    PRINCIPLES,
    RELATION_TYPES,
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
]
EKG = "/api/enterprise-ekg/v1"


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


def test_version_ekg_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "7.7.0"
    assert health["enterprise_foundation"] == "Enterprise Platform v7.6.0"
    assert health["enterprise_knowledge_graph_ready"] is True
    assert health["semantic_memory_ready"] is True
    assert health["context_engine_ready"] is True
    assert health["semantic_search_ready"] is True
    assert health["engines"]["enterprise_knowledge_graph"] == "1.0"
    assert "customer" in ENTITY_TYPES and "ai_agent" in ENTITY_TYPES
    assert "approved_by_owner" in RELATION_TYPES
    assert KPI_TARGETS["unified_semantic_memory"] is True
    assert set(PRINCIPLES)


def test_graph_search_context_owner():
    suite = enterprise_hub.enterprise_knowledge_graph
    co = suite.upsert_entity(entity_id="co_x", entity_type="company", properties={"name": "X"})
    vip = suite.upsert_entity(
        entity_id="cu_vip",
        entity_type="customer",
        properties={"days_since_visit": 90},
        labels=["vip"],
    )
    camp = suite.upsert_entity(
        entity_id="camp_x",
        entity_type="campaign",
        properties={"revenue_lift_pct": 25},
    )
    suite.link(source_id="co_x", relation="owns", target_id="cu_vip")
    suite.link(source_id="camp_x", relation="approved_by_owner", target_id="co_x")
    suite.remember(kind="decision", subject_id="co_x", summary="Keep VIP outreach")

    search = suite.semantic_search(text="Все VIP-клиенты, которые не приходили 60 дней.")
    assert search["semantic"] is True
    assert search["count"] >= 1
    assert search["intent"] == "inactive_vip_customers"

    ctx = suite.build_context(task="rebook_vip", entity_ids=["cu_vip", "co_x"], elapsed_ms=4)
    assert ctx["context_in_milliseconds"] is True
    assert ctx["ai_context"]["filtered_for_ai"] is True
    assert ctx["ai_context"]["ai_may_act"] is False

    tl = suite.timeline(entity_id="cu_vip")
    assert tl["entity_id"] == "cu_vip"

    blocked = suite.learn(confirmed=False)
    assert blocked["learned"] is False
    learned = suite.learn(
        confirmed=True,
        strengthen={"source_id": "camp_x", "relation": "approved_by_owner", "target_id": "co_x"},
    )
    assert learned["learned"] is True

    owner = suite.owner_control(
        action="forbid_ai_use",
        actor="platform_owner",
        payload={"entity_id": "cu_vip"},
    )
    assert owner["approved"] is True

    with pytest.raises(ValidationError):
        suite.upsert_entity(entity_id="bad", entity_type="spaceship")


def test_bootstrap_ekg():
    suite = enterprise_hub.enterprise_knowledge_graph
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "7.7.0"
    assert boot["knowledge_graph_ready"] is True
    assert boot["semantic_memory_ready"] is True
    assert boot["context_in_milliseconds"] is True
    assert boot["ai_may_act"] is False
    assert boot["central_context_source"] is True
    assert boot["duplicates_core_logic"] is False
    assert boot["integrations"]["linked"] is True


@pytest.mark.asyncio
async def test_api_ekg(client):
    health = await client.get(f"{EKG}/health")
    body = await health.json()
    assert body["application_version"] == "7.7.0"
    assert body["enterprise_knowledge_graph_ready"] is True

    boot = await client.post(f"{EKG}/bootstrap", json={})
    assert boot.status == 201
    assert (await boot.json())["semantic_search_ready"] is True

    for prefix in PREFIXES:
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        payload = await resp.json()
        version = payload.get("application_version") or payload.get("data", {}).get("application_version")
        assert version == "7.7.0"


def test_docs_and_regression_24_2():
    for name in (
        "ENTERPRISE_KNOWLEDGE_GRAPH.md",
        "EKG_ENTITIES_RELATIONS.md",
        "EKG_CONTEXT_SEARCH.md",
        "EKG_TIMELINE_OWNER.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_KNOWLEDGE_GRAPH.md").exists()
    assert (ROOT / "platform_enterprise_knowledge_graph" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "enterprise_knowledge_graph" / "facade.py").exists()

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
