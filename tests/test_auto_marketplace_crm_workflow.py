"""Sprint 3 — Auto Marketplace CRM workflow: tasks, activities, pipeline, conversion."""

from __future__ import annotations

import time

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.register import register_auto_marketplace_routes
from applications.auto_marketplace.crm.models import (
    CRMDeal,
    CRMLead,
    CRMLeadStatus,
    CRMTask,
    CustomerProfile,
    DealStage,
    Interaction,
    InteractionType,
    TaskPriority,
    TaskStatus,
)
from applications.auto_marketplace.crm.tenant import bind_crm_tenant
from applications.auto_marketplace.shared.exceptions import NotFoundError


AUTH = {"Authorization": "Bearer test"}


@pytest.fixture
def app() -> web.Application:
    application = web.Application()
    register_auto_marketplace_routes(application)
    return application


@pytest.fixture
async def client(app: web.Application):
    async with TestClient(TestServer(app)) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_store():
    bind_crm_tenant("default")
    auto_marketplace.reset()
    yield
    auto_marketplace.reset()
    bind_crm_tenant("default")


@pytest.mark.asyncio
async def test_task_crud_complete_reopen_and_filters():
    engine = auto_marketplace.crm_engine
    customer = await engine.customers.create(CustomerProfile(first_name="Pat", last_name="Lee"))
    lead = await engine.leads.create(CRMLead(customer_id=customer.customer_id, notes="hot"))
    deal = await engine.deals.create(CRMDeal(customer_id=customer.customer_id, amount=1000))

    overdue = await engine.tasks.create(
        CRMTask(
            title="Overdue call",
            customer_id=customer.customer_id,
            lead_id=lead.lead_id,
            deal_id=deal.deal_id,
            assigned_agent_id="agent-1",
            priority=TaskPriority.URGENT,
            due_at=time.time() - 3600,
        )
    )
    upcoming = await engine.tasks.create(
        CRMTask(
            title="Later call",
            assigned_agent_id="agent-1",
            priority=TaskPriority.LOW,
            due_at=time.time() + 86400,
        )
    )
    fetched = await engine.tasks.get(overdue.task_id)
    assert fetched.title == "Overdue call"
    updated = await engine.tasks.update(overdue.task_id, description="ring twice")
    assert updated.description == "ring twice"

    listed = await engine.tasks.list_tasks(status=TaskStatus.PENDING, assigned_to="agent-1")
    assert {t.task_id for t in listed} >= {overdue.task_id, upcoming.task_id}
    by_lead = await engine.tasks.list_tasks(lead_id=lead.lead_id)
    assert [t.task_id for t in by_lead] == [overdue.task_id]
    by_priority = await engine.tasks.list_tasks(priority=TaskPriority.URGENT)
    assert [t.task_id for t in by_priority] == [overdue.task_id]
    overdue_items = await engine.tasks.list_tasks(overdue=True)
    assert overdue.task_id in {t.task_id for t in overdue_items}
    assert upcoming.task_id not in {t.task_id for t in overdue_items}
    due_items = await engine.tasks.list_tasks(due=True)
    assert upcoming.task_id in {t.task_id for t in due_items}

    completed = await engine.tasks.complete(overdue.task_id)
    assert completed.status == TaskStatus.COMPLETED
    assert completed.completed_at is not None
    again = await engine.tasks.complete(overdue.task_id)
    assert again.task_id == completed.task_id
    reopened = await engine.tasks.reopen(overdue.task_id)
    assert reopened.status == TaskStatus.PENDING
    assert reopened.completed_at is None
    deleted = await engine.tasks.delete(upcoming.task_id)
    assert deleted is True
    with pytest.raises(NotFoundError):
        await engine.tasks.get(upcoming.task_id)


@pytest.mark.asyncio
async def test_task_invalid_relation_rejected():
    with pytest.raises(NotFoundError):
        await auto_marketplace.crm_engine.tasks.create(CRMTask(title="bad", lead_id="missing-lead"))


@pytest.mark.asyncio
async def test_activities_timeline_and_lifecycle_events():
    engine = auto_marketplace.crm_engine
    customer = await engine.customers.create(CustomerProfile(first_name="Kim", email="kim@test.com"))
    lead = await engine.leads.create(CRMLead(customer_id=customer.customer_id, notes="convert me"))
    await engine.leads.set_status(lead.lead_id, CRMLeadStatus.CONTACTED)
    deal = await engine.pipeline.convert_lead_to_deal(lead.lead_id, amount=2500)
    task = await engine.tasks.create(CRMTask(title="Prep", deal_id=deal.deal_id, customer_id=customer.customer_id))
    await engine.tasks.complete(task.task_id)
    note = await engine.activities.record(
        Interaction(
            customer_id=customer.customer_id,
            lead_id=lead.lead_id,
            deal_id=deal.deal_id,
            interaction_type=InteractionType.NOTE,
            subject="Talked",
            body="interested",
        )
    )
    listed = await engine.activities.list_activities(customer_id=customer.customer_id)
    types = {item.interaction_type for item in listed}
    assert InteractionType.CUSTOMER_CREATED in types
    assert InteractionType.LEAD_CREATED in types
    assert InteractionType.LEAD_CONVERTED in types
    assert InteractionType.DEAL_CREATED in types
    assert InteractionType.TASK_CREATED in types
    assert InteractionType.TASK_COMPLETED in types
    assert InteractionType.NOTE in types
    timeline = await engine.activities.entity_timeline(lead_id=lead.lead_id)
    assert any(item["activity_id"] == note.interaction_id for item in timeline)
    converted = await engine.activities.list_activities(lead_id=lead.lead_id, activity_type=InteractionType.LEAD_CONVERTED)
    assert len(converted) == 1
    await engine.pipeline.convert_lead_to_deal(lead.lead_id, amount=1)
    converted_again = await engine.activities.list_activities(
        lead_id=lead.lead_id, activity_type=InteractionType.LEAD_CONVERTED
    )
    assert len(converted_again) == 1
    customer_board = await engine.activities.customer_timeline(customer.customer_id)
    assert "items" in customer_board
    assert "interactions" in customer_board


@pytest.mark.asyncio
async def test_conversion_without_customer_is_idempotent():
    engine = auto_marketplace.crm_engine
    lead = await engine.leads.create(CRMLead(notes="Walk-in buyer", dealer_id="d1"))
    deal = await engine.pipeline.convert_lead_to_deal(lead.lead_id, amount=8800)
    again = await engine.pipeline.convert_lead_to_deal(lead.lead_id, amount=1)
    assert again.deal_id == deal.deal_id
    restored_lead = await engine.leads.get(lead.lead_id)
    assert restored_lead.status.value == "converted"
    assert restored_lead.customer_id == deal.customer_id
    assert restored_lead.metadata.get("converted_deal_id") == deal.deal_id
    assert restored_lead.metadata.get("converted_customer_id") == deal.customer_id
    customers = await engine.customers.list_profiles()
    assert sum(1 for item in customers if item.customer_id == deal.customer_id) == 1
    deals = await engine.deals.list_deals(customer_id=deal.customer_id)
    assert len(deals) == 1


@pytest.mark.asyncio
async def test_pipeline_stage_grouping_uses_durable_deals():
    engine = auto_marketplace.crm_engine
    deal = await engine.deals.create(CRMDeal(amount=4100, stage=DealStage.PROSPECT))
    await engine.deals.update_stage(deal.deal_id, DealStage.PROPOSAL)
    view = await engine.pipeline.pipeline_view()
    assert any(item["deal_id"] == deal.deal_id for item in view["stages"].get("proposal", []))
    assert all(item["deal_id"] != deal.deal_id for item in view["stages"].get("prospect", []))


@pytest.mark.asyncio
async def test_follow_up_board_lists_due_overdue_and_activity():
    engine = auto_marketplace.crm_engine
    await engine.tasks.create(CRMTask(title="late", assigned_agent_id="me", due_at=time.time() - 10))
    await engine.tasks.create(CRMTask(title="soon", assigned_agent_id="me", due_at=time.time() + 10))
    board = await engine.follow_up()
    titles_overdue = {t["title"] for t in board["overdue_tasks"]}
    titles_due = {t["title"] for t in board["due_tasks"]}
    assert "late" in titles_overdue
    assert "soon" in titles_due
    assert "recent_activities" in board


@pytest.mark.asyncio
async def test_crm_api_task_activity_follow_up_and_security(client: TestClient):
    created_task = await client.post(
        "/api/auto/v1/crm/tasks",
        json={"title": "API follow", "priority": "high", "assigned_to": "agent-api", "due_at": time.time() - 5},
        headers=AUTH,
    )
    assert created_task.status == 201, await created_task.text()
    task = await created_task.json()
    task_id = task["task_id"]
    assert task["assigned_to"] == "agent-api"
    assert task["priority"] == "high"

    got = await client.get(f"/api/auto/v1/crm/tasks/{task_id}", headers=AUTH)
    assert got.status == 200
    patched = await client.patch(f"/api/auto/v1/crm/tasks/{task_id}", json={"description": "call"}, headers=AUTH)
    assert patched.status == 200
    listed = await client.get("/api/auto/v1/crm/tasks?status=pending&priority=high&overdue=true", headers=AUTH)
    assert listed.status == 200
    assert any(item["task_id"] == task_id for item in (await listed.json())["items"])

    completed = await client.post(f"/api/auto/v1/crm/tasks/{task_id}/complete", json={}, headers=AUTH)
    assert completed.status == 200
    assert (await completed.json())["status"] == "completed"
    reopened = await client.post(f"/api/auto/v1/crm/tasks/{task_id}/reopen", json={}, headers=AUTH)
    assert reopened.status == 200
    assert (await reopened.json())["status"] == "pending"

    note = await client.post(
        "/api/auto/v1/crm/activities",
        json={"activity_type": "note", "subject": "hello", "body": "world", "lead_id": ""},
        headers=AUTH,
    )
    assert note.status == 201, await note.text()
    activity = await note.json()
    listed_act = await client.get("/api/auto/v1/crm/activities?activity_type=note", headers=AUTH)
    assert listed_act.status == 200
    assert any(item["activity_id"] == activity["activity_id"] for item in (await listed_act.json())["items"])
    got_act = await client.get(f"/api/auto/v1/crm/activities/{activity['activity_id']}", headers=AUTH)
    assert got_act.status == 200

    follow = await client.get("/api/auto/v1/crm/follow-up", headers=AUTH)
    assert follow.status == 200
    body = await follow.json()
    assert "overdue_tasks" in body
    assert "due_tasks" in body
    assert "recent_activities" in body

    missing = await client.post(
        "/api/auto/v1/crm/tasks",
        json={"title": "ghost", "lead_id": "no-such-lead"},
        headers=AUTH,
    )
    assert missing.status == 404

    unauth = await client.post("/api/auto/v1/crm/tasks", json={"title": "nope"})
    assert unauth.status == 401
    unauth_complete = await client.post(f"/api/auto/v1/crm/tasks/{task_id}/complete", json={})
    assert unauth_complete.status == 401
    unauth_note = await client.post("/api/auto/v1/crm/activities", json={"subject": "x"})
    assert unauth_note.status == 401

    deleted = await client.delete(f"/api/auto/v1/crm/tasks/{task_id}", headers=AUTH)
    assert deleted.status == 200


@pytest.mark.asyncio
async def test_crm_api_cross_tenant_tasks_and_activities_rejected(client: TestClient):
    headers_a = {**AUTH, "X-Tenant-Id": "wf-a"}
    headers_b = {**AUTH, "X-Tenant-Id": "wf-b"}
    created = await client.post("/api/auto/v1/crm/tasks", json={"title": "tenant-a"}, headers=headers_a)
    assert created.status == 201
    task_id = (await created.json())["task_id"]
    hidden = await client.get(f"/api/auto/v1/crm/tasks/{task_id}", headers=headers_b)
    assert hidden.status == 404
    mutate = await client.patch(f"/api/auto/v1/crm/tasks/{task_id}", json={"title": "hack"}, headers=headers_b)
    assert mutate.status == 404
    note = await client.post(
        "/api/auto/v1/crm/activities",
        json={"activity_type": "note", "subject": "a-only"},
        headers=headers_a,
    )
    assert note.status == 201
    activity_id = (await note.json())["activity_id"]
    hidden_note = await client.get(f"/api/auto/v1/crm/activities/{activity_id}", headers=headers_b)
    assert hidden_note.status == 404


@pytest.mark.asyncio
async def test_crm_api_lead_conversion_creates_customer(client: TestClient):
    created = await client.post(
        "/api/auto/v1/crm/leads",
        json={"notes": "No customer yet", "dealer_id": "d-api"},
        headers=AUTH,
    )
    assert created.status == 201
    lead_id = (await created.json())["lead_id"]
    converted = await client.post(
        f"/api/auto/v1/crm/leads/{lead_id}/convert",
        json={"amount": 12000},
        headers=AUTH,
    )
    assert converted.status == 201, await converted.text()
    deal = await converted.json()
    assert deal["customer_id"]
    again = await client.post(
        f"/api/auto/v1/crm/leads/{lead_id}/convert",
        json={"amount": 1},
        headers=AUTH,
    )
    assert (await again.json())["deal_id"] == deal["deal_id"]
    customer = await client.get(f"/api/auto/v1/crm/customers/{deal['customer_id']}", headers=AUTH)
    assert customer.status == 200
    timeline = await client.get(f"/api/auto/v1/crm/customers/{deal['customer_id']}/timeline", headers=AUTH)
    assert timeline.status == 200
    items = (await timeline.json())["items"]
    assert any(item.get("activity_type") == "lead_converted" for item in items)
    pipeline = await client.get("/api/auto/v1/crm/pipeline", headers=AUTH)
    assert pipeline.status == 200
    stages = (await pipeline.json())["stages"]
    assert any(item["deal_id"] == deal["deal_id"] for item in stages.get("qualification", []))
