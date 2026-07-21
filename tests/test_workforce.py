"""Tests — Autonomous AI Workforce & Executive Orchestration (Sprint 7.4)."""

from __future__ import annotations

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from ecosystem import ecosystem
from ecosystem.api.register import register_ecosystem_routes
from ecosystem.config import DEFAULT_CONFIG
from ecosystem.workforce.models import (
    DepartmentType,
    ExecutiveRole,
    PlanHorizon,
    SpecialistType,
    TaskPriority,
    TaskStatus,
)


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


def test_workforce_version():
    assert DEFAULT_CONFIG.ecosystem_version == "1.5.0-alpha"
    assert DEFAULT_CONFIG.workforce_layer == "1.0"
    assert DEFAULT_CONFIG.executive_ai == "1.0"


def test_executive_and_department_layers():
    executives = ecosystem.engine.workforce.executives.list_executives()
    roles = {e.role for e in executives}
    assert ExecutiveRole.CEO in roles
    assert ExecutiveRole.CFO in roles
    assert len(executives) == 8

    depts = ecosystem.engine.workforce.departments.list_departments()
    types = {d.department_type for d in depts}
    assert DepartmentType.SALES in types
    assert DepartmentType.LEGAL in types
    assert len(depts) == 8

    specialists = ecosystem.engine.workforce.specialists.list_specialists()
    assert SpecialistType.SALES in {s.specialist_type for s in specialists}
    assert len(specialists) == 8


@pytest.mark.asyncio
async def test_delegation_execution_and_approval():
    task = await ecosystem.engine.workforce.coordination.delegate(
        "Qualify inbound lead",
        description="CRM lead from portal",
        priority=TaskPriority.HIGH,
        requires_approval=True,
    )
    assert task.status == TaskStatus.AWAITING_APPROVAL
    assert task.department_type == DepartmentType.SALES

    await ecosystem.engine.workforce.executives.approve_task(task.executive_role or ExecutiveRole.CSO, task)
    completed = await ecosystem.engine.workforce.coordination.execute(task.task_id)
    assert completed.status == TaskStatus.COMPLETED

    done = await ecosystem.engine.workforce.execution.run(
        "Generate invoice for deal",
        priority=TaskPriority.NORMAL,
        application_id="auto_marketplace",
    )
    assert done.status == TaskStatus.COMPLETED
    assert done.department_type == DepartmentType.FINANCE


@pytest.mark.asyncio
async def test_escalation_balance_and_collaboration():
    task = await ecosystem.engine.workforce.coordination.delegate("Blocked support ticket")
    escalation = await ecosystem.engine.workforce.coordination.escalate(
        task.task_id,
        "Customer SLA risk",
        to_role=ExecutiveRole.COO,
    )
    assert escalation.to_role == ExecutiveRole.COO

    t1 = await ecosystem.engine.workforce.coordination.delegate("Low priority report", priority=TaskPriority.LOW)
    t2 = await ecosystem.engine.workforce.coordination.delegate("Critical outage", priority=TaskPriority.CRITICAL)
    resolution = ecosystem.engine.workforce.coordination.resolve_conflict([t1.task_id, t2.task_id])
    assert resolution["winner_task_id"] == t2.task_id

    balance = ecosystem.engine.workforce.coordination.balance_work()
    assert "recommendation" in balance

    session = await ecosystem.engine.workforce.coordination.collaborate(
        "Launch campaign",
        ["sales", "marketing"],
        shared_memory={"budget": 10000},
    )
    assert session.decisions


@pytest.mark.asyncio
async def test_strategic_planning():
    planning = ecosystem.engine.workforce.planning
    obj = planning.set_objective(
        "Grow GMV",
        horizon=PlanHorizon.QUARTERLY,
        target_value=100,
        owner_role=ExecutiveRole.CEO.value,
    )
    completed = await planning.update_progress(obj.objective_id, 100)
    assert completed.status == "completed"

    plan = await planning.create_plan(
        "Week 30",
        PlanHorizon.WEEKLY,
        [{"item": "Close deals"}],
        department_type=DepartmentType.SALES,
    )
    assert plan.plan_id
    report = planning.performance_report()
    assert report["objectives_completed"] >= 1


def test_governance_and_management():
    chart = ecosystem.engine.workforce.management.org_chart()
    assert len(chart["departments"]) == 8
    roster = ecosystem.engine.workforce.management.department_roster(DepartmentType.DEVELOPMENT)
    assert roster["specialists"]

    audit = ecosystem.engine.workforce.governance.audit_trail()
    assert "decisions" in audit
    compliance = ecosystem.engine.workforce.governance.compliance_check()
    assert compliance["compliant"] is True
    assert ecosystem.engine.workforce.governance.escalation_policy()


@pytest.mark.asyncio
async def test_executive_decision_support():
    decision = await ecosystem.engine.workforce.executives.decide(
        ExecutiveRole.CTO,
        "Approve API rollout",
        rationale="Low risk",
    )
    assert decision.approved is True
    support = ecosystem.engine.workforce.executives.decision_support("Expand dealer network")
    assert support["recommendation"]


@pytest.mark.asyncio
async def test_workforce_api(client: TestClient):
    resp = await client.get("/api/ecosystem/v1/health")
    assert resp.status == 200
    health = await resp.json()
    assert health["ecosystem_version"] == "1.5.0-alpha"
    assert health["workforce_layer"] == "1.0"
    assert health["executive_ai"] == "1.0"

    resp = await client.get("/api/ecosystem/v1/executive")
    assert resp.status == 200
    data = await resp.json()
    assert len(data["executives"]) == 8

    resp = await client.get("/api/ecosystem/v1/departments")
    assert resp.status == 200

    resp = await client.post(
        "/api/ecosystem/v1/workforce/run",
        json={"title": "Sync inventory", "priority": "normal", "application_id": "auto_marketplace"},
    )
    assert resp.status == 201
    task = await resp.json()
    assert task["status"] == "completed"

    resp = await client.post(
        "/api/ecosystem/v1/planning/objectives",
        json={"title": "NPS 70", "horizon": "quarterly", "target_value": 70},
    )
    assert resp.status == 201

    resp = await client.get("/api/ecosystem/v1/governance")
    assert resp.status == 200

    resp = await client.get("/api/ecosystem/v1/manifest")
    assert resp.status == 200
    manifest = await resp.json()
    assert manifest["ecosystem_version"] == "1.5.0-alpha"
    assert manifest["workforce_layer"] == "1.0"
    assert manifest["executive_ai"] == "1.0"
