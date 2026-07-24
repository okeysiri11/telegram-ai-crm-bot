"""Tests — Enterprise Digital Twin Platform (Sprint 20.8)."""

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
AIOS = "/api/enterprise-aios/v1"
EVP = "/api/enterprise-evp/v1"
SDP = "/api/enterprise-sdp/v1"
EDF = "/api/enterprise-edf/v1"
EDT = "/api/enterprise-edt/v1"


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


def test_version_edt_ready():
    health = enterprise_hub.health()
    assert health["application_version"] == "6.0.0"
    assert health["enterprise_foundation"] == "Enterprise Platform v6.0.0-rc7"
    assert health["digital_twin_ready"] is True
    assert health["twin_registry_ready"] is True
    assert health["realtime_sync_ready"] is True
    assert health["twin_analytics_ready"] is True
    assert health["data_fabric_ready"] is True
    assert health["engines"]["digital_twin"] == "1.0"


def test_registry_sync_graph():
    suite = enterprise_hub.digital_twin
    org = suite.organization.create(name="Org", state={"ok": True})
    dept = suite.department.create(name="Dept")
    suite.relationships.link(source_id=org["twin_id"], target_id=dept["twin_id"], kind="contains")
    sync = suite.sync.ingest(
        source="crm", event_type="Updated", twin_id=dept["twin_id"], payload={"headcount": 10}
    )
    assert sync["update_id"]
    graph = suite.relationships.graph(root_id=org["twin_id"])
    assert graph["node_count"] >= 2
    with pytest.raises(ValidationError):
        suite.registry.register(name="", twin_type="organization")


def test_bootstrap_snapshots_analytics():
    suite = enterprise_hub.digital_twin
    boot = suite.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["version"] == "6.0.0"
    assert boot["consistency_ok"] is True
    assert boot["compare_delta"] >= 1
    assert boot["prediction_context_id"]
    assert boot["analytics"]["active_twins"] >= 10


@pytest.mark.asyncio
async def test_api_edt(client):
    health = await client.get(f"{EDT}/health")
    body = await health.json()
    assert body["application_version"] == "6.0.0"
    assert body["digital_twin_ready"] is True

    boot = await client.post(f"{EDT}/bootstrap", json={})
    assert boot.status == 201
    boot_body = await boot.json()

    created = await client.post(
        f"{EDT}/twins",
        json={"name": "API Twin", "twin_type": "custom", "state": {"x": 1}},
    )
    assert created.status == 201

    for prefix in (HUB, ORCH, KG, AA, CM, WF, EIP, EDP, ISAM, OBS, TN, AOP, ATS, EKP, AIOS, EVP, SDP, EDF):
        resp = await client.get(f"{prefix}/health")
        assert resp.status == 200
        assert (await resp.json())["application_version"] == "6.0.0"

    assert boot_body["org_id"]


def test_docs_and_regression_20_8():
    for name in (
        "ENTERPRISE_DIGITAL_TWIN.md",
        "EDT_REGISTRY.md",
        "EDT_GRAPH.md",
        "EDT_SYNC.md",
        "EDT_TIMELINE_SNAPSHOTS.md",
    ):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "ENTERPRISE_DIGITAL_TWIN.md").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "digital_twin" / "facade.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "digital_twin" / "entities" / "vessel.py").exists()
    assert (ROOT / "applications" / "enterprise_hub" / "digital_twin" / "synchronization" / "sync_coordinator.py").exists()

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
    assert "6.0.0" in manifest
    assert "21.8" in manifest
