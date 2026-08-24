"""Sprint 4 — durable CRM communications, reminders, and deal-backed opportunities."""

from __future__ import annotations

import time

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.register import register_auto_marketplace_routes
from applications.auto_marketplace.crm.models import (
    CRMLead,
    EmailMessage,
    InteractionType,
    Meeting,
    PhoneCall,
    Reminder,
)
from applications.auto_marketplace.crm.tenant import bind_crm_tenant
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError

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
async def test_call_email_meeting_crud_and_timeline():
    engine = auto_marketplace.crm_engine
    call = await engine.communications.log_call(PhoneCall(direction="outbound", duration_sec=30, notes="intro"))
    fetched = await engine.communications.get_call(call.call_id)
    assert fetched.duration_sec == 30
    updated = await engine.communications.update_call(call.call_id, status="completed", notes="done")
    assert updated.status == "completed"
    listed = await engine.communications.list_calls(status="completed")
    assert any(item.call_id == call.call_id for item in listed)

    email = await engine.communications.log_email(EmailMessage(subject="Quote", body="preview", status="logged"))
    emailed = await engine.communications.update_email(email.email_id, status="sent")
    assert emailed.status == "sent"
    with pytest.raises(ValidationError):
        await engine.communications.update_email(email.email_id, status="not-a-status")

    meeting = await engine.calendar.schedule_meeting(Meeting(title="Showroom", location="lot-1"))
    cancelled = await engine.calendar.cancel_meeting(meeting.meeting_id)
    assert cancelled.status == "cancelled"
    activities = await engine.activities.list_activities()
    types = {item.interaction_type for item in activities}
    assert InteractionType.CALL in types
    assert InteractionType.EMAIL in types
    assert InteractionType.MEETING in types
    assert InteractionType.MEETING_CANCELLED in types
    await engine.communications.delete_call(call.call_id)
    with pytest.raises(NotFoundError):
        await engine.communications.get_call(call.call_id)


@pytest.mark.asyncio
async def test_reminders_due_complete_dismiss():
    engine = auto_marketplace.crm_engine
    late = await engine.calendar.create_reminder(Reminder(message="overdue ping", trigger_at=time.time() - 50))
    soon = await engine.calendar.create_reminder(Reminder(message="upcoming ping", trigger_at=time.time() + 50))
    overdue = await engine.calendar.list_reminders(overdue=True)
    upcoming = await engine.calendar.list_reminders(upcoming=True)
    assert late.reminder_id in {r.reminder_id for r in overdue}
    assert soon.reminder_id in {r.reminder_id for r in upcoming}
    completed = await engine.calendar.complete_reminder(late.reminder_id)
    assert completed.status == "completed"
    again = await engine.calendar.complete_reminder(late.reminder_id)
    assert again.reminder_id == completed.reminder_id
    dismissed = await engine.calendar.dismiss_reminder(soon.reminder_id)
    assert dismissed.status == "dismissed"
    types = {a.interaction_type for a in await engine.activities.list_activities()}
    assert InteractionType.REMINDER_CREATED in types
    assert InteractionType.REMINDER_COMPLETED in types
    board = await engine.follow_up()
    assert "overdue_reminders" in board
    assert "upcoming_reminders" in board


@pytest.mark.asyncio
async def test_opportunities_are_deal_backed_and_idempotent():
    engine = auto_marketplace.crm_engine
    lead = await engine.leads.create(CRMLead(notes="buyer"))
    first = await engine.pipeline.convert_lead_to_opportunity(lead.lead_id, amount=6400)
    second = await engine.pipeline.convert_lead_to_opportunity(lead.lead_id, amount=1)
    assert first.opportunity_id == second.opportunity_id
    deal = await engine.pipeline.open_deal_from_opportunity(first.opportunity_id)
    assert deal.amount == 6400
    listed = await engine.pipeline.list_opportunities()
    assert any(item.opportunity_id == first.opportunity_id for item in listed)
    fetched = await engine.pipeline.get_opportunity(first.opportunity_id)
    assert fetched.amount == 6400
    assert fetched.lead_id == lead.lead_id


@pytest.mark.asyncio
async def test_communications_api_security_and_tenant_isolation(client: TestClient):
    created = await client.post(
        "/api/auto/v1/crm/activities/calls",
        json={"direction": "inbound", "duration_sec": 12, "notes": "hello"},
        headers=AUTH,
    )
    assert created.status == 201, await created.text()
    call_id = (await created.json())["call_id"]
    listed = await client.get("/api/auto/v1/crm/calls", headers=AUTH)
    assert listed.status == 200
    patched = await client.patch(f"/api/auto/v1/crm/calls/{call_id}", json={"status": "completed"}, headers=AUTH)
    assert patched.status == 200
    email = await client.post(
        "/api/auto/v1/crm/activities/emails",
        json={"subject": "Hi", "body": "body", "status": "logged"},
        headers=AUTH,
    )
    assert email.status == 201
    email_id = (await email.json())["email_id"]
    sent = await client.patch(f"/api/auto/v1/crm/emails/{email_id}", json={"status": "sent"}, headers=AUTH)
    assert sent.status == 200
    meeting = await client.post(
        "/api/auto/v1/crm/calendar/meetings",
        json={"title": "Test drive"},
        headers=AUTH,
    )
    assert meeting.status == 201
    meeting_id = (await meeting.json())["meeting_id"]
    cancelled = await client.post(f"/api/auto/v1/crm/calendar/meetings/{meeting_id}/cancel", json={}, headers=AUTH)
    assert cancelled.status == 200
    reminder = await client.post(
        "/api/auto/v1/crm/reminders",
        json={"message": "Call back", "remind_at": time.time() - 5},
        headers=AUTH,
    )
    assert reminder.status == 201, await reminder.text()
    reminder_id = (await reminder.json())["reminder_id"]
    due = await client.get("/api/auto/v1/crm/reminders?overdue=true", headers=AUTH)
    assert due.status == 200
    assert any(item["reminder_id"] == reminder_id for item in (await due.json())["items"])
    completed = await client.post(f"/api/auto/v1/crm/reminders/{reminder_id}/complete", json={}, headers=AUTH)
    assert completed.status == 200

    unauth = await client.post("/api/auto/v1/crm/reminders", json={"message": "x"})
    assert unauth.status == 401
    unauth_call = await client.patch(f"/api/auto/v1/crm/calls/{call_id}", json={"status": "completed"})
    assert unauth_call.status == 401

    headers_a = {**AUTH, "X-Tenant-Id": "comm-a"}
    headers_b = {**AUTH, "X-Tenant-Id": "comm-b"}
    owned = await client.post("/api/auto/v1/crm/activities/calls", json={"notes": "a-only"}, headers=headers_a)
    assert owned.status == 201
    owned_id = (await owned.json())["call_id"]
    hidden = await client.get(f"/api/auto/v1/crm/calls/{owned_id}", headers=headers_b)
    assert hidden.status == 404
    mutate = await client.patch(f"/api/auto/v1/crm/calls/{owned_id}", json={"status": "completed"}, headers=headers_b)
    assert mutate.status == 404

    missing = await client.post(
        "/api/auto/v1/crm/activities/calls",
        json={"lead_id": "no-such-lead"},
        headers=AUTH,
    )
    assert missing.status == 404

    lead = await client.post("/api/auto/v1/crm/leads", json={"notes": "from api"}, headers=AUTH)
    assert lead.status == 201
    lead_id = (await lead.json())["lead_id"]
    converted = await client.post(f"/api/auto/v1/crm/leads/{lead_id}/convert", json={"amount": 3000}, headers=AUTH)
    assert converted.status == 201
    opps = await client.get("/api/auto/v1/crm/opportunities", headers=AUTH)
    assert opps.status == 200
    items = (await opps.json())["items"]
    assert items
    opp_id = items[0]["opportunity_id"]
    got = await client.get(f"/api/auto/v1/crm/opportunities/{opp_id}", headers=AUTH)
    assert got.status == 200
    hidden_opp = await client.get(f"/api/auto/v1/crm/opportunities/{opp_id}", headers=headers_b)
    assert hidden_opp.status == 404
