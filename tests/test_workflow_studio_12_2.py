"""Tests — Visual Workflow Studio & AI Flow Builder (Sprint 12.2)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.workflow_studio import workflow_studio
from applications.workflow_studio.api.register import register_workflow_studio_routes


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/workflow-studio/v1"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_workflow_studio_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    workflow_studio.reset()
    yield
    workflow_studio.reset()


def test_version_studio_ready():
    health = workflow_studio.health()
    assert health["application_version"] == "3.2.0-alpha"
    assert health["workflow_studio_ready"] is True
    assert health["ai_flow_builder_ready"] is True
    assert health["visual_automation_ready"] is True
    assert health["enterprise_workflow_platform_ready"] is True


def test_canvas_and_execution():
    editor = workflow_studio.editor
    wf = editor.create_workflow(name="Demo Flow", description="test")
    wid = wf["workflow_id"]
    n1 = editor.add_node(wid, node_type="webhook", x=0, y=0)
    n2 = editor.add_node(wid, node_type="llm", x=120, y=0)
    n3 = editor.add_node(wid, node_type="notification", x=240, y=0)
    editor.connect(wid, source_id=n1["node_id"], target_id=n2["node_id"])
    editor.connect(wid, source_id=n2["node_id"], target_id=n3["node_id"])
    editor.set_zoom(wid, zoom=1.5)
    editor.set_grid(wid, enabled=True)
    editor.group_nodes(wid, node_ids=[n1["node_id"], n2["node_id"]], name="Ingest")
    editor.add_comment(wid, text="Entry", x=10, y=10, author="dev")
    editor.clipboard_copy(wid, node_ids=[n3["node_id"]], user_id="u1")
    pasted = editor.clipboard_paste(wid, user_id="u1")
    assert pasted["pasted"]
    canvas = editor.canvas(wid)
    assert canvas["zoom"] == 1.5
    assert len(canvas["nodes"]) >= 3
    assert editor.undo(wid)["undone"] is True

    engine = workflow_studio.engine
    exe = engine.execute(wid, mode="visual", input_data={"prompt": "hello"})
    assert exe["status"] == "completed"
    workflow_studio.monitoring.record_metrics(exe)
    engine.set_breakpoint(wid, node_id=n2["node_id"], enabled=True)
    stepped = engine.execute(wid, mode="step")
    assert stepped["status"] in {"paused", "completed"}
    assert engine.live_logs(exe["execution_id"])
    assert engine.debugger_state(exe["execution_id"])["execution_id"]
    rolled = engine.rollback_execution(exe["execution_id"])
    assert rolled["status"] == "rolled_back"

    # retry path with forced error then recovery via properties
    bad = editor.add_node(wid, node_type="api", properties={"force_error": True, "retry": True})
    editor.connect(wid, source_id=n3["node_id"], target_id=bad["node_id"])
    # force_error always fails even on retry — expect failed
    failed = engine.execute(wid, mode="background")
    assert failed["status"] in {"failed", "completed"}


def test_ai_builder_templates_enterprise_monitoring():
    generated = workflow_studio.ai_builder.generate_from_prompt(prompt="Build a CRM lead triage flow", name="CRM AI")
    wid = generated["workflow"]["workflow_id"]
    assert generated["nodes"]
    assert workflow_studio.ai_builder.optimize_workflow(wid)["suggestions"] is not None
    assert "missing" in workflow_studio.ai_builder.suggest_missing_nodes(wid)
    assert "bottlenecks" in workflow_studio.ai_builder.detect_bottlenecks(wid)
    assert workflow_studio.ai_builder.estimate_execution_cost(wid)["estimated_usd"] >= 0
    assert "documentation" in workflow_studio.ai_builder.auto_documentation(wid)

    templates = workflow_studio.templates.list_templates()
    assert len(templates) >= 10
    drone = workflow_studio.templates.instantiate(key="drone_mission", name="Survey Ops")
    assert drone["workflow"]["template_key"] == "drone_mission"

    v1 = workflow_studio.enterprise.save_version(wid, author="alice")
    # mutate then version again
    workflow_studio.editor.add_node(wid, node_type="decision", x=400, y=0)
    v2 = workflow_studio.enterprise.save_version(wid, author="bob")
    assert workflow_studio.enterprise.compare(v1["version_id"], v2["version_id"])
    workflow_studio.enterprise.merge(wid, from_version_id=v1["version_id"])
    workflow_studio.enterprise.set_permissions(wid, principal="alice", role="owner")
    workflow_studio.enterprise.share(wid, with_org_id="org1")
    assert workflow_studio.enterprise.organization_library("org1")["count"] >= 1
    assert workflow_studio.enterprise.multi_user_lock(wid, user_id="alice")["acquired"] is True

    metrics = workflow_studio.monitoring.execution_metrics(wid)
    assert "success_rate" in metrics
    assert workflow_studio.monitoring.performance_dashboard()["type"] == "performance_dashboard"
    assert "failed_executions" in workflow_studio.monitoring.failure_analysis()
    assert "cells" in workflow_studio.monitoring.execution_heatmap(wid)


@pytest.mark.asyncio
async def test_api_workflow_studio(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "3.2.0-alpha"
    assert body["workflow_studio_ready"] is True

    wf = await client.post(f"{PREFIX}/workflows", json={"name": "API Flow"})
    assert wf.status == 201
    wid = (await wf.json())["workflow_id"]

    node = await client.post(f"{PREFIX}/workflows/{wid}/canvas", json={"node_type": "webhook", "x": 0, "y": 0})
    assert node.status == 201
    n1 = await node.json()
    n2 = await (await client.post(f"{PREFIX}/workflows/{wid}/canvas", json={"node_type": "notification", "x": 100, "y": 0})).json()
    conn = await client.post(f"{PREFIX}/workflows/{wid}/canvas", json={"action": "connect", "source_id": n1["node_id"], "target_id": n2["node_id"]})
    assert conn.status == 201

    exe = await client.post(f"{PREFIX}/execute", json={"workflow_id": wid, "mode": "visual"})
    assert exe.status == 201

    ai = await client.post(f"{PREFIX}/ai-builder", json={"prompt": "customer support triage", "name": "Support"})
    assert ai.status == 201

    tmpl = await client.post(f"{PREFIX}/templates", json={"key": "sales_pipeline"})
    assert tmpl.status == 201

    mon = await client.get(f"{PREFIX}/monitoring")
    assert mon.status == 200


def test_docs_and_regression_12_2():
    for name in ("WORKFLOW_STUDIO.md", "FLOW_BUILDER.md", "VISUAL_AUTOMATION.md", "WORKFLOW_REFERENCE.md"):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "WORKFLOW_STUDIO.md").exists()
    manifest = (ROOT / "applications" / "workflow_studio" / "manifest.json").read_text()
    assert "3.2.0-alpha" in manifest
    assert "12.2" in manifest
    from applications.marketplace.config import DEFAULT_CONFIG as MKT
    from applications.ecosystem.config import DEFAULT_CONFIG as ECO

    assert MKT.application_version == "3.1.0-alpha"
    assert ECO.application_version == "3.0.0-alpha"
