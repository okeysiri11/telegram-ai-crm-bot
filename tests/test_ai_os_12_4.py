"""Tests — AI Operating System (Sprint 12.4)."""

from __future__ import annotations

from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.ai_os import ai_os
from applications.ai_os.api.register import register_ai_os_routes
from applications.ai_os.shared.exceptions import ValidationError


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/api/ai-os/v1"


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_ai_os_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    ai_os.reset()
    yield
    ai_os.reset()


def test_version_ai_os_ready():
    health = ai_os.health()
    assert health["application_version"] == "3.4.0-alpha"
    assert health["ai_operating_system_ready"] is True
    assert health["ai_kernel_ready"] is True
    assert health["unified_runtime_ready"] is True
    assert health["enterprise_ai_os_ready"] is True


def test_kernel_process_bus_memory():
    boot = ai_os.bootstrap()
    assert boot["bootstrap"] is True
    assert len(ai_os.kernel.list_schedulers()) == 6

    job = ai_os.kernel.schedule(scheduler="agent", payload={"agent": "chief"}, priority=9, name="dispatch")
    assert job["status"] == "queued"
    tick = ai_os.kernel.tick("agent")
    assert tick["processed"] == 1
    assert tick["job"]["status"] == "completed"

    proc = ai_os.processes.start_process(name="worker-1", kind="ai_process")
    ai_os.processes.enqueue(queue="default", item={"task": 1}, priority=True)
    ai_os.processes.enqueue(queue="default", item={"task": 2}, priority=False)
    first = ai_os.processes.dequeue(queue="default")
    assert first["item"]["task"] == 1
    ai_os.processes.lifecycle(proc["process_id"], action="pause")
    assert ai_os.processes.get(proc["process_id"])["status"] == "paused"
    ai_os.processes.health_monitor(proc["process_id"], healthy=True)

    msg = ai_os.bus.publish(bus="workflow", topic="run.started", payload={"id": "w1"})
    assert msg["bus"] == "workflow"
    assert ai_os.bus.subscribe_poll(bus="workflow", topic="run.started")

    ai_os.memory.put(tier="semantic_cache", key="q1", value={"answer": 42})
    assert ai_os.memory.get(tier="semantic_cache", key="q1")["value"]["answer"] == 42
    assert ai_os.memory.list_tier("semantic_cache")


def test_runtime_communication_enterprise_observability():
    ctx = ai_os.runtime.create_context(name="session-1", data={"user": "ceo"})
    job = ai_os.runtime.execute(name="plan", payload={"goal": "scale"}, context_id=ctx["context_id"])
    assert job["status"] == "completed"
    chk = ai_os.runtime.checkpoint(job["runtime_id"])
    recovered = ai_os.runtime.recover(job["runtime_id"], checkpoint_id=chk["checkpoint_id"])
    assert recovered["status"] == "recovered"
    with pytest.raises(ValidationError):
        ai_os.runtime.execute(name="bad", payload={"unsafe": True}, sandboxed=True)

    ai_os.communication.send(channel="agent_to_agent", sender="chief", recipient="drone", body="sync twins")
    ai_os.communication.send(channel="human_to_ai", sender="ceo", recipient="ceo_assistant", body="status?")
    assert ai_os.communication.inbox("drone")

    cluster = ai_os.enterprise.create_cluster(name="eu-1", region="EU", nodes=2)
    scaled = ai_os.enterprise.scale(cluster["cluster_id"], nodes=4)
    assert len(scaled["nodes"]) == 4
    nodes = [n for n in ai_os.store.nodes.list_all() if n.get("cluster_id") == cluster["cluster_id"]]
    failed = nodes[0]["node_id"]
    fo = ai_os.enterprise.failover(cluster["cluster_id"], from_node=failed)
    assert fo["primary"]
    assert ai_os.enterprise.load_balance(cluster["cluster_id"])["selected"]
    assert ai_os.enterprise.disaster_recovery(cluster["cluster_id"])["status"] == "recovered"

    ai_os.observability.log(level="warn", message="queue depth rising")
    ai_os.observability.metric(name="queue_depth", value=12)
    ai_os.observability.trace(name="boot", spans=[{"op": "kernel.boot"}])
    ai_os.observability.alert(severity="high", message="node failed")
    assert ai_os.observability.health_dashboard()["type"] == "health_dashboard"
    assert ai_os.observability.performance_dashboard()["type"] == "performance_dashboard"


@pytest.mark.asyncio
async def test_api_ai_os(client):
    health = await client.get(f"{PREFIX}/health")
    body = await health.json()
    assert body["application_version"] == "3.4.0-alpha"
    assert body["ai_operating_system_ready"] is True

    boot = await client.post(f"{PREFIX}/bootstrap", json={})
    assert boot.status == 201

    job = await client.post(f"{PREFIX}/kernel", json={"scheduler": "task", "name": "t1", "priority": 8})
    assert job.status == 201

    proc = await client.post(f"{PREFIX}/processes", json={"name": "api-worker"})
    assert proc.status == 201

    bus = await client.post(f"{PREFIX}/bus", json={"bus": "event", "topic": "ping", "payload": {"ok": True}})
    assert bus.status == 201

    mem = await client.post(f"{PREFIX}/memory", json={"tier": "session", "key": "k1", "value": 1})
    assert mem.status == 201

    rt = await client.post(f"{PREFIX}/runtime", json={"name": "exec1", "payload": {"x": 1}})
    assert rt.status == 201

    comm = await client.post(
        f"{PREFIX}/communication",
        json={"channel": "ai_to_human", "sender": "ceo_assistant", "recipient": "ceo", "body": "report ready"},
    )
    assert comm.status == 201

    ent = await client.post(f"{PREFIX}/enterprise", json={"name": "cluster-a", "nodes": 2})
    assert ent.status == 201

    obs = await client.get(f"{PREFIX}/observability")
    assert obs.status == 200


def test_docs_and_regression_12_4():
    for name in ("AI_OS.md", "AI_KERNEL.md", "SYSTEM_BUS.md", "AI_RUNTIME.md"):
        assert (ROOT / "docs" / name).exists()
    assert (ROOT / "knowledge" / "applications" / "AI_OS.md").exists()
    manifest = (ROOT / "applications" / "ai_os" / "manifest.json").read_text()
    assert "3.4.0-alpha" in manifest
    assert "12.4" in manifest
    from applications.executive_center.config import DEFAULT_CONFIG as EX
    from applications.workflow_studio.config import DEFAULT_CONFIG as WS

    assert EX.application_version == "3.3.0-alpha"
    assert WS.application_version == "3.2.0-alpha"
