"""Tests — Enterprise Vertical Federation (Sprint 27.3 / v9.4.0)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.register import register_enterprise_hub_routes
from platform_vertical_federation.models import (
    ARCHITECTURE,
    CORE_VERTICALS,
    CROSS_VERTICAL_LINKS,
    KPI_TARGETS,
    KNOWLEDGE_SCOPES,
    MARKETPLACE_ASSET_TYPES,
    PRINCIPLES,
    VERSION,
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
    "/api/enterprise-ele/v1",
    "/api/enterprise-aph/v1",
    "/api/enterprise-ees/v1",
    "/api/enterprise-eti/v1",
    "/api/enterprise-epl/v1",
    "/api/enterprise-ece/v1",
    "/api/enterprise-emr/v1",
    "/api/enterprise-esv/v1",
    "/api/enterprise-epd/v1",
    "/api/enterprise-ecf/v1",
    "/api/enterprise-ewf/v1",
    "/api/enterprise-eds/v1",
    "/api/enterprise-eic/v1",
    "/api/enterprise-ews/v1",
    "/api/enterprise-enp/v1",
    "/api/enterprise-command/v1",
    "/api/enterprise-navigation/v1",
    "/api/release/v1",
    "/api/ai-os/v1/maos",
    "/api/organization-brain/v1",
]
VF = "/api/verticals/v1"


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


def test_version_vertical_federation_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "9.4.0"
    assert health["vertical_federation_ready"] is True
    assert health["vertical_registry_ready"] is True
    assert health["vertical_executive_ai_ready"] is True
    assert health["cross_vertical_communication_ready"] is True
    assert health["unified_vertical_dashboard_ready"] is True
    assert health["vertical_marketplace_ready"] is True
    assert health["knowledge_federation_ready"] is True
    assert health["engines"]["vertical_federation"] == "1.0"
    assert VERSION == "9.4.0"
    assert "vertical_registry" in ARCHITECTURE
    assert "Auto" in CORE_VERTICALS
    assert "Drone" in CORE_VERTICALS
    assert ("CRM", "Finance") in CROSS_VERTICAL_LINKS
    assert "workflows" in MARKETPLACE_ASSET_TYPES
    assert "semantic" in KNOWLEDGE_SCOPES
    assert KPI_TARGETS["knowledge_federation_ready"] is True
    assert "phase4_vertical_federation" in PRINCIPLES


def test_registry_directors_comms_marketplace_knowledge():
    suite = enterprise_hub.vertical_federation
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["hub_version"] == "9.4.0"
    assert boot["vertical_registry_ready"] is True
    assert boot["vertical_executive_ai_ready"] is True
    assert boot["cross_vertical_communication_ready"] is True
    assert boot["vertical_federation_path_exists"] is True
    assert boot["dashboard_page_exists"] is True
    assert boot["hub_suite_exists"] is True

    registry = suite.registry()
    assert registry["ready"] is True
    assert registry["count"] >= len(CORE_VERTICALS)
    sample = registry["items"][0]
    for key in (
        "status",
        "owner",
        "ai_director",
        "workspace",
        "kpi",
        "applications",
        "agents",
        "api",
        "knowledge_base",
    ):
        assert key in sample

    custom = suite.register_custom(name="Smart Cities", owner="city_ops")
    assert custom["ok"] is True
    assert custom["custom"] is True
    assert suite.registry()["count"] >= len(CORE_VERTICALS) + 1

    directors = suite.directors()
    assert directors["executive_ai_connected"] is True
    assert directors["count"] >= len(CORE_VERTICALS)
    act = suite.director_act(vertical="Auto", action="talk_to_executive_ai", payload={"topic": "KPI"})
    assert act["ok"] is True
    assert act["executive_ai"] == "acknowledged"

    links = suite.links()
    assert links["count"] == len(CROSS_VERTICAL_LINKS)
    msg = suite.communicate(source="CRM", target="Finance", message="Invoice batch ready")
    assert msg["ok"] is True
    assert msg["routed"] is True
    assert suite.messages()["count"] >= 1

    published = suite.marketplace_publish(
        vertical="Beauty",
        asset_type="widgets",
        name="Booking Pulse Widget",
    )
    assert published["ok"] is True
    market = suite.marketplace()
    assert market["ready"] is True
    assert "applications" in market["asset_types"]
    assert market["counts"]["widgets"] >= 1

    kg = suite.knowledge_write(scope="industry", content="Agro drone spray schedule policy")
    assert kg["ok"] is True
    snap = suite.knowledge()
    assert snap["counts"]["industry"] >= 1
    search = suite.semantic_search("drone")
    assert search["ok"] is True
    assert search["mode"] == "semantic"
    assert search["count"] >= 1

    dash = suite.dashboard()
    assert dash["title"] == "Vertical Federation Dashboard"
    assert dash["executive_ai_connected"] is True
    assert "vertical_states" in dash
    assert "kpi" in dash
    assert "events" in dash
    assert "alerts" in dash
    assert "recommendations" in dash


@pytest.mark.asyncio
async def test_api_vertical_federation(client):
    health = await client.get(f"{VF}/health")
    body = await health.json()
    assert body["application_version"] == "9.4.0"
    assert body["vertical_federation_ready"] is True

    boot = await client.post(f"{VF}/bootstrap", json={})
    assert boot.status == 201
    assert (await boot.json())["vertical_registry_ready"] is True

    inv = await client.get(f"{VF}/inventory")
    assert inv.status == 200

    reg = await client.get(f"{VF}/registry")
    assert reg.status == 200
    assert (await reg.json())["count"] >= 17

    custom = await client.post(f"{VF}/registry", json={"name": "Energy Grid"})
    assert custom.status == 201

    dirs = await client.get(f"{VF}/directors")
    assert dirs.status == 200
    assert (await dirs.json())["executive_ai_connected"] is True

    act = await client.post(
        f"{VF}/directors/act",
        json={"vertical": "Finance", "action": "analyze_kpi"},
    )
    assert act.status == 200

    links = await client.get(f"{VF}/links")
    assert links.status == 200

    comm = await client.post(
        f"{VF}/communicate",
        json={"source": "Agro", "target": "Drone", "message": "Scout field B"},
    )
    assert comm.status == 200

    mkt = await client.post(
        f"{VF}/marketplace",
        json={"vertical": "Drone", "asset_type": "ai_agents", "name": "Vision Scout"},
    )
    assert mkt.status == 201

    kg = await client.post(
        f"{VF}/knowledge",
        json={"scope": "shared", "content": "Shared CRM finance bridge"},
    )
    assert kg.status == 200

    search = await client.post(f"{VF}/search", json={"query": "CRM"})
    assert search.status == 200

    dash = await client.get(f"{VF}/exec-dashboard")
    assert dash.status == 200

    for prefix in (
        "/api/organization-brain/v1",
        "/api/ai-os/v1/maos",
        "/api/release/v1",
        "/api/enterprise-navigation/v1",
    ):
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        assert (await resp.json())["application_version"] == "9.4.0"

    for prefix in PREFIXES:
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        data = await resp.json()
        version = data.get("application_version") or data.get("data", {}).get("application_version")
        assert version == "9.4.0"


def test_docs_and_regression_27_3():
    assert (ROOT / "docs" / "ENTERPRISE_VERTICAL_FEDERATION.md").exists()
    assert (ROOT / "platform_vertical_federation" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "vertical_federation" / "facade.py").exists()
    assert (
        ROOT / "src" / "web" / "vertical-federation" / "pages" / "VerticalFederationPage.tsx"
    ).exists()
    assert (
        ROOT / "knowledge" / "applications" / "enterprise_hub" / "vertical_federation" / "README.md"
    ).exists()

    docs = (ROOT / "docs" / "ENTERPRISE_VERTICAL_FEDERATION.md").read_text()
    for key in (
        "Vertical Registry",
        "Vertical Executive AI",
        "Cross-Vertical Communication",
        "Knowledge Federation",
    ):
        assert key in docs

    from applications.ai_os.config import DEFAULT_CONFIG as AIOS_CFG
    from applications.enterprise.config import DEFAULT_CONFIG as ENT
    from applications.auto_marketplace.config import DEFAULT_CONFIG as AUTO

    assert AIOS_CFG.api_prefix == "/api/ai-os/v1"
    assert ENT.application_version == "4.0.0-enterprise"
    assert AUTO.application_version == "4.2.0-enterprise"
    manifest = (ROOT / "applications" / "enterprise_hub" / "manifest.json").read_text()
    assert '"application_version": "9.4.0"' in manifest
    assert "27.3" in manifest
