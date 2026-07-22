"""Tests — Executive Command Center & Digital Twin (Sprint 12.3)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.executive_center import executive_center
from applications.executive_center.api.register import register_executive_center_routes


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/executive/v1"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_executive_center_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    executive_center.reset()
    yield
    executive_center.reset()


def test_version_executive_ready():
    health = executive_center.health()
    assert health["application_version"] == "3.3.0-alpha"
    assert health["executive_command_center_ready"] is True
    assert health["digital_twin_ready"] is True
    assert health["executive_ai_ready"] is True
    assert health["enterprise_control_center_ready"] is True


def test_dashboards_and_twins_sync():
    boot = executive_center.bootstrap()
    assert boot["bootstrap"] is True
    assert boot["twins_created"] >= 1

    dash = executive_center.dashboard
    dash.publish_kpi(name="ARR", value=1.2, unit="index")
    dash.record_metric(name="active_users", value=1200)
    dash.activity(actor="ceo", action="review", detail="weekly")
    assert dash.global_dashboard()["type"] == "global"
    assert dash.company_dashboard("co1")["company_id"] == "co1"
    assert dash.finance_dashboard()["finance"]["margin_pct"] == 0.28
    assert dash.operations_dashboard()["type"] == "operations"
    assert dash.ai_dashboard()["type"] == "ai"
    assert "global" in dash.all_dashboards()

    twins = executive_center.twins
    twin = twins.create(twin_type="drone", name="UAV Twin", state={"battery": 90})
    synced = twins.live_sync(twin["twin_id"], state={"battery": 80, "mode": "MISSION"})
    assert synced["synced"] is True
    assert synced["state"]["battery"] == 80
    history = twins.state_history(twin["twin_id"])
    assert len(history) >= 2
    snap_id = history[0]["snapshot_id"]
    restored = twins.time_travel(twin["twin_id"], snapshot_id=snap_id)
    assert restored["time_travel_to"] == snap_id
    assert twins.sync_all()["synced"] >= 1
    assert twins.list_twins(twin_type="drone")


def test_monitoring_ai_analytics_viz_enterprise():
    mon = executive_center.monitoring
    sample = mon.sample(cpu_pct=40, ram_pct=50)
    assert sample["cpu_pct"] == 40
    mon.health_check(target="workflows", ok=True)
    overview = mon.overview()
    assert overview["healthy"] is True
    assert "cpu" in overview["targets"]

    ai = executive_center.ai
    assert ai.ceo_assistant(query="priorities")["agent"] == "ceo_assistant"
    assert ai.risk_analysis(signals={"failure_rate": 0.2, "cpu_pct": 90})["response"]["risk_level"] in {"medium", "high"}
    assert ai.recommendations(focus="efficiency")["response"]["recommendations"]
    assert ai.forecasting(metric="revenue")["response"]["forecast"]
    assert ai.executive_report(period="weekly")["response"]["status"] == "generated"
    assert ai.strategic_planning(goals=["scale"])["response"]["plan"]
    assert ai.assist(agent="business_advisor", query="market")["agent"] == "business_advisor"

    analytics = executive_center.analytics.all_domains()
    assert "marketplace" in analytics
    assert "infrastructure" in analytics

    viz = executive_center.visualization.interactive_bundle()
    assert viz["knowledge"]["type"] == "knowledge_graph"
    assert viz["twins"]["type"] == "digital_twin_visualization"
    assert viz["charts"]["type"] == "live_charts"

    ent = executive_center.enterprise
    company = ent.register_company(name="Acme Holdings", region="EU")
    org = ent.register_organization(company_id=company["company_id"], name="Ops Org")
    assert org["org_id"]
    ent.register_region(company_id=company["company_id"], name="Berlin", code="BER")
    ent.grant_permission(principal="ceo@acme", role="executive")
    assert "global" in ent.role_based_dashboard(role="executive")["dashboards"]
    ent.audit(actor="ceo@acme", action="view_dashboard", resource="global")
    assert ent.audit_report()["count"] >= 1
    assert ent.executive_report_pack()["companies"] >= 1


@pytest.mark.asyncio
async def test_api_executive_center(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "3.3.0-alpha"
    assert body["executive_command_center_ready"] is True

    boot = await client.post(f"{PREFIX}/bootstrap", json={})
    assert boot.status == 201

    dash = await client.get(f"{PREFIX}/dashboard?type=global")
    assert dash.status == 200
    assert (await dash.json())["type"] == "global"

    twin = await client.post(f"{PREFIX}/twins", json={"twin_type": "agent", "name": "Chief Twin"})
    assert twin.status == 201
    tid = (await twin.json())["twin_id"]
    sync = await client.post(f"{PREFIX}/twins", json={"action": "sync", "twin_id": tid, "state": {"load": 0.2}})
    assert sync.status == 200

    mon = await client.post(f"{PREFIX}/monitoring", json={"cpu_pct": 22})
    assert mon.status == 201

    ai = await client.post(f"{PREFIX}/ai", json={"agent": "ceo_assistant", "query": "status"})
    assert ai.status == 200

    an = await client.get(f"{PREFIX}/analytics")
    assert an.status == 200

    viz = await client.get(f"{PREFIX}/visualization")
    assert viz.status == 200

    ent = await client.post(f"{PREFIX}/enterprise", json={"name": "Northwind"})
    assert ent.status == 201


def test_docs_and_regression_12_3():
    for name in ("EXECUTIVE_CENTER.md", "DIGITAL_TWIN.md", "EXECUTIVE_DASHBOARD.md", "SYSTEM_MONITORING.md"):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "EXECUTIVE_CENTER.md").exists()
    manifest = (ROOT / "applications" / "executive_center" / "manifest.json").read_text()
    assert "3.3.0-alpha" in manifest
    assert "12.3" in manifest
    from applications.workflow_studio.config import DEFAULT_CONFIG as WS
    from applications.marketplace.config import DEFAULT_CONFIG as MKT

    assert WS.application_version == "3.2.0-alpha"
    assert MKT.application_version == "3.1.0-alpha"
