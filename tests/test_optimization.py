"""Tests — Continuous Learning & Ecosystem Optimization (Sprint 7.5)."""

from __future__ import annotations

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from ecosystem import ecosystem
from ecosystem.api.register import register_ecosystem_routes
from ecosystem.config import DEFAULT_CONFIG
from ecosystem.optimization.models import MetricDomain, RecommendationCategory, SimulationType


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_ecosystem_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    ecosystem.reset()
    DEFAULT_CONFIG.registered_applications[:] = ["auto_marketplace"]
    yield
    ecosystem.reset()
    DEFAULT_CONFIG.registered_applications[:] = ["auto_marketplace"]


def test_optimization_version():
    assert DEFAULT_CONFIG.ecosystem_version == "1.5.0-alpha"
    assert DEFAULT_CONFIG.optimization_layer == "1.0"
    assert DEFAULT_CONFIG.continuous_learning == "1.0"


@pytest.mark.asyncio
async def test_continuous_learning_cycle():
    learning = ecosystem.engine.optimization.learning
    learning.record_execution("workforce", "execute", duration_ms=80, outcome="success", agent_id="sales")
    learning.record_execution("assistant", "invoke", duration_ms=600, outcome="success")
    learning.record_execution("workflow", "pipeline", duration_ms=90, outcome="failed", agent_id="ops")
    learning.track_decision("dec-1", "executive", expected="approve", actual="reject", success=False, lessons=["Improve criteria"])
    ecosystem.engine.optimization.feedback.submit(2.0, "Slow routing", target_id="wf-1")

    analysis = learning.analyze_history()
    assert analysis["total"] >= 3
    assert "success_rate" in analysis

    cycle = await learning.run_learning_cycle()
    assert cycle.records_analyzed >= 3
    assert cycle.insights
    assert cycle.replayed >= 1


@pytest.mark.asyncio
async def test_performance_and_benchmarks():
    snaps = await ecosystem.engine.optimization.performance.collect_ecosystem_metrics()
    assert len(snaps) >= 5
    assert any(s.domain == MetricDomain.LATENCY for s in snaps)

    await ecosystem.engine.optimization.performance.record(
        "custom_kpi",
        42.0,
        domain=MetricDomain.BUSINESS,
        unit="count",
        target=40,
    )
    dashboard = ecosystem.engine.optimization.performance.dashboard()
    assert dashboard["total_snapshots"] >= 1

    benches = ecosystem.engine.optimization.benchmark.run_suite()
    assert len(benches) >= 4


@pytest.mark.asyncio
async def test_simulation_types():
    sim = ecosystem.engine.optimization.simulation
    what_if = await sim.run("Spike", SimulationType.WHAT_IF, {"load_factor": 1.5, "capacity": 100})
    assert what_if.results
    business = await sim.run("Campaign", SimulationType.BUSINESS, {"budget": 5000, "load_factor": 1.2})
    assert "projected_revenue" in business.results
    capacity = await sim.run("Growth", SimulationType.CAPACITY, {"load_factor": 0.9, "capacity": 100})
    assert capacity.risk_score >= 0
    risk = await sim.run("Outage", SimulationType.RISK, {"failure_rate": 0.1})
    assert risk.simulation_type == SimulationType.RISK


@pytest.mark.asyncio
async def test_recommendations_and_strategy():
    ecosystem.engine.optimization.learning.record_execution("api", "slow", duration_ms=800, outcome="success")
    recs = await ecosystem.engine.optimization.recommendations.generate(force=True)
    assert recs
    assert any(r.category == RecommendationCategory.ARCHITECTURE for r in recs)

    strategy = await ecosystem.engine.optimization.strategy.update_from_recommendations(
        "Q3 Optimization",
        recommendation_ids=[recs[0].recommendation_id],
    )
    assert strategy.strategy_id
    assert ecosystem.engine.optimization.strategy.latest() is not None


@pytest.mark.asyncio
async def test_full_optimize_run():
    ecosystem.engine.optimization.learning.record_execution("prep", "seed", duration_ms=40)
    result = await ecosystem.engine.optimization.optimize(scope="ecosystem")
    assert result["run"]["status"] == "completed"
    assert result["learning_cycle"]["cycle_id"]
    assert result["recommendations"]
    assert result["simulation"]["simulation_id"]
    assert result["strategy"]["strategy_id"]
    assert result["integrations"]["learning"] is True


@pytest.mark.asyncio
async def test_optimization_api(client: TestClient):
    resp = await client.get("/api/ecosystem/v1/health")
    assert resp.status == 200
    health = await resp.json()
    assert health["ecosystem_version"] == "1.5.0-alpha"
    assert health["optimization_layer"] == "1.0"
    assert health["continuous_learning"] == "1.0"

    resp = await client.post(
        "/api/ecosystem/v1/learning/executions",
        json={"action": "test_action", "duration_ms": 55, "source": "api"},
    )
    assert resp.status == 201

    resp = await client.post(
        "/api/ecosystem/v1/simulation",
        json={"name": "API sim", "simulation_type": "workflow", "assumptions": {"steps": 4, "load_factor": 1.0}},
    )
    assert resp.status == 201

    resp = await client.post("/api/ecosystem/v1/recommendations")
    assert resp.status == 201
    recs = await resp.json()
    assert recs["recommendations"]

    resp = await client.post("/api/ecosystem/v1/optimization", json={"scope": "ecosystem"})
    assert resp.status == 201
    payload = await resp.json()
    assert payload["run"]["status"] == "completed"

    resp = await client.get("/api/ecosystem/v1/performance")
    assert resp.status == 200

    resp = await client.get("/api/ecosystem/v1/manifest")
    assert resp.status == 200
    manifest = await resp.json()
    assert manifest["ecosystem_version"] == "1.5.0-alpha"
    assert manifest["optimization_layer"] == "1.0"
    assert manifest["continuous_learning"] == "1.0"
