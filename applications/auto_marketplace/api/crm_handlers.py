# CRM API handlers — Sprint 6.3.

from __future__ import annotations

from aiohttp import web

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.middleware import error_response, json_response
from applications.auto_marketplace.crm.models import (
    CRMDeal,
    CRMLead,
    CRMRole,
    CRMTask,
    CustomerProfile,
    DealStage,
    EmailMessage,
    LeadSource,
    Meeting,
    PhoneCall,
    Reminder,
)
from applications.auto_marketplace.shared.exceptions import AuthorizationError, AutoMarketplaceError, NotFoundError


def _check_perm(request: web.Request, permission: str) -> None:
    principal = request.get("principal") or {}
    role = principal.get("role", CRMRole.SALES_AGENT.value)
    if not auto_marketplace.crm_engine.security.authorize(role, permission):
        raise AuthorizationError(f"Permission denied: {permission}")


async def crm_metrics_handler(_request: web.Request) -> web.Response:
    return json_response(auto_marketplace.crm_engine.metrics())


async def list_customers_handler(request: web.Request) -> web.Response:
    _check_perm(request, "customers.read")
    segment = request.query.get("segment")
    items = auto_marketplace.crm_engine.customers.list_profiles(segment=segment)
    return json_response({"items": [c.to_dict() for c in items]})


async def create_customer_handler(request: web.Request) -> web.Response:
    _check_perm(request, "customers.write")
    data = await request.json()
    profile = CustomerProfile(
        first_name=data.get("first_name", ""),
        last_name=data.get("last_name", ""),
        email=data.get("email", ""),
        phone=data.get("phone", ""),
        preferences=data.get("preferences", {}),
    )
    created = await auto_marketplace.crm_engine.customers.create(profile)
    return json_response(created.to_dict(), status=201)


async def get_customer_handler(request: web.Request) -> web.Response:
    _check_perm(request, "customers.read")
    profile = auto_marketplace.crm_engine.customers.get(request.match_info["customer_id"])
    return json_response(profile.to_dict())


async def customer_timeline_handler(request: web.Request) -> web.Response:
    _check_perm(request, "crm.read")
    timeline = auto_marketplace.crm_engine.activities.customer_timeline(request.match_info["customer_id"])
    return json_response(timeline)


async def list_leads_handler(request: web.Request) -> web.Response:
    _check_perm(request, "leads.read")
    status = request.query.get("status")
    from applications.auto_marketplace.crm.models import CRMLeadStatus

    st = CRMLeadStatus(status) if status else None
    items = auto_marketplace.crm_engine.leads.list_leads(status=st, dealer_id=request.query.get("dealer_id"))
    return json_response({"items": [l.to_dict() for l in items]})


async def create_lead_handler(request: web.Request) -> web.Response:
    _check_perm(request, "leads.write")
    data = await request.json()
    source = data.get("source", "web")
    lead = CRMLead(
        customer_id=data.get("customer_id", ""),
        vehicle_id=data.get("vehicle_id", ""),
        dealer_id=data.get("dealer_id", ""),
        source=LeadSource(source) if source else LeadSource.WEB,
        notes=data.get("notes", ""),
    )
    customer = None
    if lead.customer_id:
        try:
            customer = auto_marketplace.crm_engine.customers.get(lead.customer_id)
        except NotFoundError:
            pass
    created = await auto_marketplace.crm_engine.leads.create(lead, customer)
    nba = await auto_marketplace.crm_engine.ai.next_best_action(created)
    return json_response({**created.to_dict(), "next_best_action": nba}, status=201)


async def qualify_lead_handler(request: web.Request) -> web.Response:
    _check_perm(request, "leads.manage")
    data = await request.json()
    lead = await auto_marketplace.crm_engine.pipeline.qualify_lead(
        request.match_info["lead_id"],
        agent_id=data.get("agent_id", ""),
    )
    return json_response(lead.to_dict())


async def list_deals_handler(request: web.Request) -> web.Response:
    _check_perm(request, "deals.read")
    stage = request.query.get("stage")
    st = DealStage(stage) if stage else None
    items = auto_marketplace.crm_engine.deals.list_deals(stage=st, dealer_id=request.query.get("dealer_id"))
    return json_response({"items": [d.to_dict() for d in items]})


async def create_deal_handler(request: web.Request) -> web.Response:
    _check_perm(request, "deals.write")
    data = await request.json()
    deal = CRMDeal(
        customer_id=data.get("customer_id", ""),
        dealer_id=data.get("dealer_id", ""),
        vehicle_id=data.get("vehicle_id", ""),
        amount=float(data.get("amount", 0)),
        owner_agent_id=data.get("owner_agent_id", ""),
    )
    created = await auto_marketplace.crm_engine.deals.create(deal)
    return json_response(created.to_dict(), status=201)


async def advance_deal_handler(request: web.Request) -> web.Response:
    _check_perm(request, "deals.write")
    deal = await auto_marketplace.crm_engine.pipeline.advance_stage(request.match_info["deal_id"])
    return json_response(deal.to_dict())


async def win_deal_handler(request: web.Request) -> web.Response:
    _check_perm(request, "deals.manage")
    data = await request.json()
    deal = await auto_marketplace.crm_engine.deals.mark_won(
        request.match_info["deal_id"],
        amount=float(data.get("amount", 0)) or None,
    )
    return json_response(deal.to_dict())


async def lose_deal_handler(request: web.Request) -> web.Response:
    _check_perm(request, "deals.manage")
    data = await request.json()
    deal = await auto_marketplace.crm_engine.deals.mark_lost(request.match_info["deal_id"], reason=data.get("reason", ""))
    return json_response(deal.to_dict())


async def pipeline_view_handler(request: web.Request) -> web.Response:
    _check_perm(request, "pipeline.read")
    return json_response(auto_marketplace.crm_engine.pipeline.pipeline_view(dealer_id=request.query.get("dealer_id")))


async def pipeline_forecast_handler(_request: web.Request) -> web.Response:
    _check_perm(_request, "reports.view")
    return json_response(auto_marketplace.crm_engine.pipeline.forecast())


async def pipeline_conversion_handler(_request: web.Request) -> web.Response:
    _check_perm(_request, "reports.view")
    return json_response(auto_marketplace.crm_engine.pipeline.conversion_analytics())


async def list_tasks_handler(request: web.Request) -> web.Response:
    _check_perm(request, "tasks.read")
    items = auto_marketplace.crm_engine.tasks.list_tasks(
        agent_id=request.query.get("agent_id"),
        customer_id=request.query.get("customer_id"),
    )
    return json_response({"items": [t.to_dict() for t in items]})


async def create_task_handler(request: web.Request) -> web.Response:
    _check_perm(request, "tasks.write")
    data = await request.json()
    task = CRMTask(
        title=data.get("title", ""),
        description=data.get("description", ""),
        customer_id=data.get("customer_id", ""),
        lead_id=data.get("lead_id", ""),
        deal_id=data.get("deal_id", ""),
        assigned_agent_id=data.get("assigned_agent_id", ""),
        due_at=data.get("due_at"),
    )
    created = await auto_marketplace.crm_engine.tasks.create(task)
    return json_response(created.to_dict(), status=201)


async def log_call_handler(request: web.Request) -> web.Response:
    _check_perm(request, "crm.write")
    data = await request.json()
    call = PhoneCall(
        customer_id=data.get("customer_id", ""),
        agent_id=data.get("agent_id", ""),
        direction=data.get("direction", "outbound"),
        duration_sec=int(data.get("duration_sec", 0)),
    )
    saved = await auto_marketplace.crm_engine.communications.log_call(call)
    return json_response(saved.to_dict(), status=201)


async def log_email_handler(request: web.Request) -> web.Response:
    _check_perm(request, "crm.write")
    data = await request.json()
    email = EmailMessage(
        customer_id=data.get("customer_id", ""),
        agent_id=data.get("agent_id", ""),
        subject=data.get("subject", ""),
        body=data.get("body", ""),
    )
    saved = auto_marketplace.crm_engine.communications.log_email(email)
    return json_response(saved.to_dict(), status=201)


async def schedule_meeting_handler(request: web.Request) -> web.Response:
    _check_perm(request, "crm.write")
    data = await request.json()
    meeting = Meeting(
        customer_id=data.get("customer_id", ""),
        agent_id=data.get("agent_id", ""),
        title=data.get("title", ""),
        scheduled_at=float(data.get("scheduled_at", 0)) or __import__("time").time(),
        duration_min=int(data.get("duration_min", 30)),
        location=data.get("location", ""),
    )
    saved = auto_marketplace.crm_engine.calendar.schedule_meeting(meeting)
    return json_response(saved.to_dict(), status=201)


async def ai_next_action_handler(request: web.Request) -> web.Response:
    _check_perm(request, "crm.read")
    lead = auto_marketplace.crm_engine.leads.get(request.match_info["lead_id"])
    action = await auto_marketplace.crm_engine.ai.next_best_action(lead)
    follow_up = await auto_marketplace.crm_engine.ai.suggest_follow_up(lead)
    return json_response({"next_best_action": action, "follow_up": follow_up})


async def crm_error_middleware(request: web.Request, handler):
    try:
        return await handler(request)
    except NotFoundError as exc:
        return error_response(str(exc), status=404)
    except AuthorizationError as exc:
        return error_response(str(exc), status=403)
    except AutoMarketplaceError as exc:
        return error_response(str(exc), status=400)
