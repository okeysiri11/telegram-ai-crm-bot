# CRM API handlers — Sprint 6.3.

from __future__ import annotations

from aiohttp import web

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.middleware import error_response, json_response
from applications.auto_marketplace.crm.tenant import bind_crm_tenant, tenant_from_request
from applications.auto_marketplace.crm.models import (
    CRMDeal,
    CRMLead,
    CRMLeadStatus,
    CRMRole,
    CRMTask,
    CustomerProfile,
    DealStage,
    EmailMessage,
    Interaction,
    InteractionType,
    LeadSource,
    Meeting,
    PhoneCall,
    Reminder,
    TaskPriority,
    TaskStatus,
)
from applications.auto_marketplace.shared.exceptions import (
    AuthenticationError,
    AuthorizationError,
    AutoMarketplaceError,
    NotFoundError,
    ValidationError,
)

_MUTATING_MARKERS = (".write", ".manage", ".delete", ".create", ".update")


def _parse_lead_status(raw: object) -> CRMLeadStatus | None:
    if raw is None or raw == "":
        return None
    try:
        return CRMLeadStatus(str(raw))
    except ValueError as exc:
        raise ValidationError(f"invalid lead status: {raw!r}") from exc


def _parse_deal_stage(raw: object) -> DealStage | None:
    if raw is None or raw == "":
        return None
    try:
        return DealStage(str(raw))
    except ValueError as exc:
        raise ValidationError(f"invalid deal stage: {raw!r}") from exc


def _parse_task_status(raw: object) -> TaskStatus | None:
    if raw is None or raw == "":
        return None
    try:
        return TaskStatus(str(raw))
    except ValueError as exc:
        raise ValidationError(f"invalid task status: {raw!r}") from exc


def _parse_task_priority(raw: object) -> TaskPriority | None:
    if raw is None or raw == "":
        return None
    try:
        return TaskPriority(str(raw))
    except ValueError as exc:
        raise ValidationError(f"invalid task priority: {raw!r}") from exc


def _parse_interaction_type(raw: object) -> InteractionType:
    if raw is None or raw == "":
        return InteractionType.NOTE
    try:
        return InteractionType(str(raw))
    except ValueError as exc:
        raise ValidationError(f"invalid activity type: {raw!r}") from exc


def _query_flag(request: web.Request, name: str) -> bool:
    return str(request.query.get(name) or "").strip().lower() in {"1", "true", "yes"}


def _optional_float(value: object, field: str) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field} must be a unix timestamp") from exc


_LEAD_SOURCE_METADATA_KEYS = (
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "channel",
    "referrer",
    "intake_key",
    "idempotency_key",
)


def _lead_intake_metadata(data: dict) -> dict:
    meta: dict = {}
    raw = data.get("metadata")
    if isinstance(raw, dict):
        meta.update(raw)
    elif raw not in (None, ""):
        raise ValidationError("metadata must be an object")
    for key in _LEAD_SOURCE_METADATA_KEYS:
        value = data.get(key)
        if value not in (None, ""):
            meta[key] = value
    return meta


def _parse_lead_source(raw: object) -> LeadSource:
    if raw is None or raw == "":
        return LeadSource.WEB
    try:
        return LeadSource(str(raw))
    except ValueError as exc:
        allowed = ", ".join(s.value for s in LeadSource)
        raise ValidationError(f"invalid lead source: {raw!r}; allowed: {allowed}") from exc


def _check_perm(request: web.Request, permission: str) -> None:
    bind_crm_tenant(tenant_from_request(request))
    principal = request.get("principal")
    mutating = any(marker in permission for marker in _MUTATING_MARKERS)
    if mutating and (not isinstance(principal, dict) or not principal.get("authenticated")):
        raise AuthenticationError("Authentication required")
    principal = principal if isinstance(principal, dict) else {}
    role = principal.get("role", CRMRole.SALES_AGENT.value)
    if not auto_marketplace.crm_engine.security.authorize(role, permission):
        raise AuthorizationError(f"Permission denied: {permission}")


def _require_authenticated_read(request: web.Request, permission: str) -> None:
    _check_perm(request, permission)
    principal = request.get("principal")
    if not isinstance(principal, dict) or not principal.get("authenticated"):
        raise AuthenticationError("Authentication required")


async def crm_metrics_handler(_request: web.Request) -> web.Response:
    bind_crm_tenant(tenant_from_request(_request))
    return json_response(await auto_marketplace.crm_engine.metrics())


async def list_customers_handler(request: web.Request) -> web.Response:
    _check_perm(request, "customers.read")
    segment = request.query.get("segment")
    email = request.query.get("email") or None
    items = await auto_marketplace.crm_engine.customers.list_profiles(segment=segment, email=email)
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
    profile = await auto_marketplace.crm_engine.customers.get(request.match_info["customer_id"])
    return json_response(profile.to_dict())


async def update_customer_handler(request: web.Request) -> web.Response:
    _check_perm(request, "customers.write")
    data = await request.json()
    allowed = ("first_name", "last_name", "email", "phone", "preferences", "tags", "owner_agent_id", "segment")
    updates = {k: data[k] for k in allowed if k in data}
    if not updates:
        raise ValidationError("no updatable fields provided")
    updated = await auto_marketplace.crm_engine.customers.update(request.match_info["customer_id"], **updates)
    return json_response(updated.to_dict())


async def delete_customer_handler(request: web.Request) -> web.Response:
    _check_perm(request, "customers.write")
    customer_id = request.match_info["customer_id"]
    deleted = await auto_marketplace.crm_engine.customers.delete(customer_id)
    return json_response({"customer_id": customer_id, "deleted": deleted})


async def customer_timeline_handler(request: web.Request) -> web.Response:
    _check_perm(request, "crm.read")
    timeline = await auto_marketplace.crm_engine.activities.customer_timeline(request.match_info["customer_id"])
    return json_response(timeline)


async def customer_360_handler(request: web.Request) -> web.Response:
    _require_authenticated_read(request, "crm.read")
    limit_raw = request.query.get("limit") or "100"
    try:
        limit = int(limit_raw)
    except (TypeError, ValueError):
        raise ValidationError("limit must be an integer")
    report = await auto_marketplace.crm_engine.customer_360.get_360(
        request.match_info["customer_id"],
        timeline_limit=limit,
    )
    return json_response(report)


async def list_leads_handler(request: web.Request) -> web.Response:
    _check_perm(request, "leads.read")
    status = request.query.get("status")
    from applications.auto_marketplace.crm.models import CRMLeadStatus

    st = None
    if status:
        try:
            st = CRMLeadStatus(status)
        except ValueError as exc:
            raise ValidationError(f"invalid lead status: {status!r}") from exc
    items = await auto_marketplace.crm_engine.leads.list_leads(
        status=st,
        dealer_id=request.query.get("dealer_id"),
        customer_id=request.query.get("customer_id") or None,
    )
    return json_response({"items": [lead.to_dict() for lead in items]})


async def create_lead_handler(request: web.Request) -> web.Response:
    _check_perm(request, "leads.write")
    data = await request.json()
    source = data.get("source", "web")
    lead = CRMLead(
        customer_id=data.get("customer_id", ""),
        vehicle_id=data.get("vehicle_id", ""),
        dealer_id=data.get("dealer_id", ""),
        source=_parse_lead_source(source),
        assigned_agent_id=str(data.get("assigned_agent_id") or data.get("assigned_to") or ""),
        notes=data.get("notes", ""),
        metadata=_lead_intake_metadata(data),
    )
    customer = None
    if lead.customer_id:
        try:
            customer = await auto_marketplace.crm_engine.customers.get(lead.customer_id)
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


async def get_lead_handler(request: web.Request) -> web.Response:
    _check_perm(request, "leads.read")
    lead = await auto_marketplace.crm_engine.leads.get(request.match_info["lead_id"])
    return json_response(lead.to_dict())


async def update_lead_handler(request: web.Request) -> web.Response:
    _check_perm(request, "leads.write")
    data = await request.json()
    lead_id = request.match_info["lead_id"]
    updates: dict = {}
    if "notes" in data:
        updates["notes"] = str(data["notes"])
    if "customer_id" in data:
        updates["customer_id"] = str(data["customer_id"] or "")
    if "vehicle_id" in data:
        updates["vehicle_id"] = str(data["vehicle_id"] or "")
    if "dealer_id" in data:
        updates["dealer_id"] = str(data["dealer_id"] or "")
    if "assigned_agent_id" in data:
        updates["assigned_agent_id"] = str(data["assigned_agent_id"] or "")
    if "source" in data:
        updates["source"] = _parse_lead_source(data["source"])
    if "status" in data:
        st = _parse_lead_status(data["status"])
        if st is None:
            raise ValidationError("status cannot be empty")
        updates["status"] = st
    if "metadata" in data:
        if not isinstance(data["metadata"], dict):
            raise ValidationError("metadata must be an object")
        existing = await auto_marketplace.crm_engine.leads.get(lead_id)
        merged = dict(existing.metadata)
        merged.update(data["metadata"])
        updates["metadata"] = merged
    if not updates:
        raise ValidationError("no updatable fields provided")
    updated = await auto_marketplace.crm_engine.leads.update(lead_id, **updates)
    return json_response(updated.to_dict())


async def delete_lead_handler(request: web.Request) -> web.Response:
    _check_perm(request, "leads.write")
    lead_id = request.match_info["lead_id"]
    deleted = await auto_marketplace.crm_engine.leads.delete(lead_id)
    return json_response({"lead_id": lead_id, "deleted": deleted})


async def convert_lead_handler(request: web.Request) -> web.Response:
    _check_perm(request, "leads.write")
    try:
        data = await request.json()
    except Exception:
        data = {}
    if not isinstance(data, dict):
        data = {}
    deal = await auto_marketplace.crm_engine.pipeline.convert_lead_to_deal(
        request.match_info["lead_id"],
        amount=float(data.get("amount", 0) or 0),
        agent_id=str(data.get("agent_id") or data.get("assigned_agent_id") or ""),
    )
    return json_response(deal.to_dict(), status=201)


async def list_deals_handler(request: web.Request) -> web.Response:
    _check_perm(request, "deals.read")
    stage = request.query.get("stage")
    st = None
    if stage:
        try:
            st = DealStage(stage)
        except ValueError as exc:
            raise ValidationError(f"invalid deal stage: {stage!r}") from exc
    items = await auto_marketplace.crm_engine.deals.list_deals(
        stage=st,
        dealer_id=request.query.get("dealer_id"),
        customer_id=request.query.get("customer_id") or None,
    )
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


async def get_deal_handler(request: web.Request) -> web.Response:
    _check_perm(request, "deals.read")
    deal = await auto_marketplace.crm_engine.deals.get(request.match_info["deal_id"])
    return json_response(deal.to_dict())


async def update_deal_handler(request: web.Request) -> web.Response:
    _check_perm(request, "deals.write")
    data = await request.json()
    deal_id = request.match_info["deal_id"]
    if "stage" in data:
        stage = _parse_deal_stage(data["stage"])
        if stage is None:
            raise ValidationError("stage cannot be empty")
        updated = await auto_marketplace.crm_engine.deals.update_stage(deal_id, stage)
        return json_response(updated.to_dict())
    updates: dict = {}
    for key in ("customer_id", "dealer_id", "vehicle_id", "owner_agent_id"):
        if key in data:
            updates[key] = str(data[key] or "")
    if "amount" in data:
        try:
            updates["amount"] = float(data["amount"])
        except (TypeError, ValueError) as exc:
            raise ValidationError("amount must be a number") from exc
    if not updates:
        raise ValidationError("no updatable fields provided")
    updated = await auto_marketplace.crm_engine.deals.update(deal_id, **updates)
    return json_response(updated.to_dict())


async def delete_deal_handler(request: web.Request) -> web.Response:
    _check_perm(request, "deals.write")
    deal_id = request.match_info["deal_id"]
    deleted = await auto_marketplace.crm_engine.deals.delete(deal_id)
    return json_response({"deal_id": deal_id, "deleted": deleted})


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
    return json_response(await auto_marketplace.crm_engine.pipeline.pipeline_view(dealer_id=request.query.get("dealer_id")))


async def pipeline_forecast_handler(_request: web.Request) -> web.Response:
    _check_perm(_request, "reports.view")
    return json_response(await auto_marketplace.crm_engine.pipeline.forecast())


async def pipeline_conversion_handler(_request: web.Request) -> web.Response:
    _check_perm(_request, "reports.view")
    return json_response(await auto_marketplace.crm_engine.pipeline.conversion_analytics())


async def list_tasks_handler(request: web.Request) -> web.Response:
    _check_perm(request, "tasks.read")
    items = await auto_marketplace.crm_engine.tasks.list_tasks(
        agent_id=request.query.get("agent_id") or None,
        assigned_to=request.query.get("assigned_to") or None,
        customer_id=request.query.get("customer_id") or None,
        lead_id=request.query.get("lead_id") or None,
        deal_id=request.query.get("deal_id") or None,
        status=_parse_task_status(request.query.get("status")),
        priority=_parse_task_priority(request.query.get("priority")),
        overdue=_query_flag(request, "overdue"),
        due=_query_flag(request, "due"),
    )
    return json_response({"items": [t.to_dict() for t in items]})


async def create_task_handler(request: web.Request) -> web.Response:
    _check_perm(request, "tasks.write")
    data = await request.json()
    principal = request.get("principal") if isinstance(request.get("principal"), dict) else {}
    task = CRMTask(
        title=str(data.get("title") or ""),
        description=str(data.get("description") or ""),
        customer_id=str(data.get("customer_id") or ""),
        lead_id=str(data.get("lead_id") or ""),
        deal_id=str(data.get("deal_id") or ""),
        assigned_agent_id=str(data.get("assigned_to") or data.get("assigned_agent_id") or ""),
        created_by=str(data.get("created_by") or principal.get("user_id") or principal.get("sub") or ""),
        status=_parse_task_status(data.get("status")) or TaskStatus.PENDING,
        priority=_parse_task_priority(data.get("priority")) or TaskPriority.NORMAL,
        due_at=_optional_float(data.get("due_at"), "due_at"),
    )
    created = await auto_marketplace.crm_engine.tasks.create(task)
    return json_response(created.to_dict(), status=201)


async def get_task_handler(request: web.Request) -> web.Response:
    _check_perm(request, "tasks.read")
    task = await auto_marketplace.crm_engine.tasks.get(request.match_info["task_id"])
    return json_response(task.to_dict())


async def update_task_handler(request: web.Request) -> web.Response:
    _check_perm(request, "tasks.write")
    data = await request.json()
    updates: dict = {}
    for key in ("title", "description", "customer_id", "lead_id", "deal_id", "created_by"):
        if key in data:
            updates[key] = str(data[key] or "")
    if "assigned_to" in data or "assigned_agent_id" in data:
        updates["assigned_agent_id"] = str(data.get("assigned_to") or data.get("assigned_agent_id") or "")
    if "status" in data:
        status = _parse_task_status(data["status"])
        if status is None:
            raise ValidationError("status cannot be empty")
        updates["status"] = status
    if "priority" in data:
        priority = _parse_task_priority(data["priority"])
        if priority is None:
            raise ValidationError("priority cannot be empty")
        updates["priority"] = priority
    if "due_at" in data:
        updates["due_at"] = _optional_float(data.get("due_at"), "due_at")
    if not updates:
        raise ValidationError("no updatable fields provided")
    updated = await auto_marketplace.crm_engine.tasks.update(request.match_info["task_id"], **updates)
    return json_response(updated.to_dict())


async def delete_task_handler(request: web.Request) -> web.Response:
    _check_perm(request, "tasks.write")
    task_id = request.match_info["task_id"]
    deleted = await auto_marketplace.crm_engine.tasks.delete(task_id)
    return json_response({"task_id": task_id, "deleted": deleted})


async def complete_task_handler(request: web.Request) -> web.Response:
    _check_perm(request, "tasks.write")
    task = await auto_marketplace.crm_engine.tasks.complete(request.match_info["task_id"])
    return json_response(task.to_dict())


async def reopen_task_handler(request: web.Request) -> web.Response:
    _check_perm(request, "tasks.write")
    task = await auto_marketplace.crm_engine.tasks.reopen(request.match_info["task_id"])
    return json_response(task.to_dict())


async def list_activities_handler(request: web.Request) -> web.Response:
    _check_perm(request, "crm.read")
    type_raw = request.query.get("activity_type") or request.query.get("interaction_type")
    activity_type = _parse_interaction_type(type_raw) if type_raw else None
    items = await auto_marketplace.crm_engine.activities.list_activities(
        customer_id=request.query.get("customer_id") or None,
        lead_id=request.query.get("lead_id") or None,
        deal_id=request.query.get("deal_id") or None,
        task_id=request.query.get("task_id") or None,
        activity_type=activity_type,
    )
    return json_response({"items": [i.to_dict() for i in items]})


async def get_activity_handler(request: web.Request) -> web.Response:
    _check_perm(request, "crm.read")
    item = await auto_marketplace.crm_engine.activities.get_interaction(request.match_info["activity_id"])
    return json_response(item.to_dict())


async def create_activity_handler(request: web.Request) -> web.Response:
    _check_perm(request, "crm.write")
    data = await request.json()
    principal = request.get("principal") if isinstance(request.get("principal"), dict) else {}
    created = await auto_marketplace.crm_engine.activities.record(
        Interaction(
            customer_id=str(data.get("customer_id") or ""),
            lead_id=str(data.get("lead_id") or ""),
            deal_id=str(data.get("deal_id") or ""),
            task_id=str(data.get("task_id") or ""),
            interaction_type=_parse_interaction_type(data.get("activity_type") or data.get("interaction_type")),
            subject=str(data.get("subject") or data.get("title") or ""),
            body=str(data.get("body") or data.get("note") or ""),
            agent_id=str(data.get("agent_id") or principal.get("user_id") or principal.get("sub") or ""),
            idempotency_key=str(data.get("idempotency_key") or ""),
        )
    )
    return json_response(created.to_dict(), status=201)


async def follow_up_handler(request: web.Request) -> web.Response:
    _check_perm(request, "crm.read")
    return json_response(await auto_marketplace.crm_engine.follow_up())


async def list_follow_ups_handler(request: web.Request) -> web.Response:
    _check_perm(request, "crm.read")
    items = await auto_marketplace.crm_engine.automation.list_follow_ups(
        due=_query_flag(request, "due"),
        overdue=_query_flag(request, "overdue"),
    )
    return json_response({"items": items})


async def schedule_follow_up_handler(request: web.Request) -> web.Response:
    _check_perm(request, "crm.write")
    data = await request.json()
    created = await auto_marketplace.crm_engine.automation.schedule_follow_up(
        lead_id=str(data.get("lead_id") or ""),
        deal_id=str(data.get("deal_id") or ""),
        customer_id=str(data.get("customer_id") or ""),
        action_type=data.get("action_type") or data.get("next_action_type") or "manual_follow_up",
        due_at=data.get("due_at") or data.get("remind_at") or data.get("next_action_at"),
        delay_hours=data.get("delay_hours"),
        assigned_to=str(data.get("assigned_to") or data.get("assigned_agent_id") or ""),
        message=str(data.get("message") or data.get("title") or ""),
        source=str(data.get("source") or "api"),
        priority=data.get("priority") or data.get("next_action_priority"),
        idempotency_key=str(data.get("idempotency_key") or ""),
    )
    return json_response(created, status=201)


async def get_follow_up_handler(request: web.Request) -> web.Response:
    _check_perm(request, "crm.read")
    item = await auto_marketplace.crm_engine.automation.get_follow_up(request.match_info["follow_up_id"])
    return json_response(item)


async def reschedule_follow_up_handler(request: web.Request) -> web.Response:
    _check_perm(request, "crm.write")
    data = await request.json()
    due_at = data.get("due_at") or data.get("remind_at") or data.get("next_action_at")
    if due_at in (None, ""):
        raise ValidationError("due_at is required")
    updated = await auto_marketplace.crm_engine.automation.reschedule_follow_up(
        request.match_info["follow_up_id"],
        due_at=due_at,
    )
    return json_response(updated)


async def complete_follow_up_handler(request: web.Request) -> web.Response:
    _check_perm(request, "crm.write")
    try:
        await request.json()
    except Exception:
        pass
    item = await auto_marketplace.crm_engine.automation.complete_follow_up(request.match_info["follow_up_id"])
    return json_response(item)


async def cancel_follow_up_handler(request: web.Request) -> web.Response:
    _check_perm(request, "crm.write")
    try:
        await request.json()
    except Exception:
        pass
    item = await auto_marketplace.crm_engine.automation.cancel_follow_up(request.match_info["follow_up_id"])
    return json_response(item)


async def automation_queue_handler(request: web.Request) -> web.Response:
    _check_perm(request, "crm.read")
    limit_raw = request.query.get("limit") or "100"
    try:
        limit = int(limit_raw)
    except ValueError as exc:
        raise ValidationError("limit must be an integer") from exc
    return json_response(await auto_marketplace.crm_engine.automation.get_action_queue(limit=limit))


async def evaluate_automation_handler(request: web.Request) -> web.Response:
    _check_perm(request, "crm.write")
    try:
        await request.json()
    except Exception:
        pass
    return json_response(await auto_marketplace.crm_engine.automation.evaluate_due_actions())


async def log_call_handler(request: web.Request) -> web.Response:
    _check_perm(request, "crm.write")
    data = await request.json()
    call = PhoneCall(
        customer_id=str(data.get("customer_id") or ""),
        lead_id=str(data.get("lead_id") or ""),
        deal_id=str(data.get("deal_id") or ""),
        agent_id=str(data.get("agent_id") or data.get("assigned_to") or ""),
        direction=str(data.get("direction") or "outbound"),
        status=str(data.get("status") or "logged"),
        duration_sec=int(data.get("duration_sec") or 0),
        summary=str(data.get("summary") or data.get("notes") or ""),
        notes=str(data.get("notes") or data.get("summary") or ""),
        started_at=_optional_float(data.get("started_at"), "started_at"),
        ended_at=_optional_float(data.get("ended_at"), "ended_at"),
    )
    saved = await auto_marketplace.crm_engine.communications.log_call(call)
    return json_response(saved.to_dict(), status=201)


async def list_calls_handler(request: web.Request) -> web.Response:
    _check_perm(request, "crm.read")
    items = await auto_marketplace.crm_engine.communications.list_calls(
        customer_id=request.query.get("customer_id") or None,
        lead_id=request.query.get("lead_id") or None,
        deal_id=request.query.get("deal_id") or None,
        agent_id=request.query.get("agent_id") or request.query.get("assigned_to") or None,
        status=request.query.get("status") or None,
    )
    return json_response({"items": [c.to_dict() for c in items]})


async def get_call_handler(request: web.Request) -> web.Response:
    _check_perm(request, "crm.read")
    call = await auto_marketplace.crm_engine.communications.get_call(request.match_info["call_id"])
    return json_response(call.to_dict())


async def update_call_handler(request: web.Request) -> web.Response:
    _check_perm(request, "crm.write")
    data = await request.json()
    allowed = ("customer_id", "lead_id", "deal_id", "agent_id", "direction", "status", "duration_sec", "summary", "notes")
    updates = {k: data[k] for k in allowed if k in data}
    if not updates:
        raise ValidationError("no updatable fields provided")
    updated = await auto_marketplace.crm_engine.communications.update_call(request.match_info["call_id"], **updates)
    return json_response(updated.to_dict())


async def delete_call_handler(request: web.Request) -> web.Response:
    _check_perm(request, "crm.write")
    call_id = request.match_info["call_id"]
    deleted = await auto_marketplace.crm_engine.communications.delete_call(call_id)
    return json_response({"call_id": call_id, "deleted": deleted})


async def log_email_handler(request: web.Request) -> web.Response:
    _check_perm(request, "crm.write")
    data = await request.json()
    email = EmailMessage(
        customer_id=str(data.get("customer_id") or ""),
        lead_id=str(data.get("lead_id") or ""),
        deal_id=str(data.get("deal_id") or ""),
        agent_id=str(data.get("agent_id") or ""),
        subject=str(data.get("subject") or ""),
        body=str(data.get("body") or data.get("preview") or ""),
        direction=str(data.get("direction") or "outbound"),
        status=str(data.get("status") or "logged"),
        sender=str(data.get("sender") or ""),
        recipient=str(data.get("recipient") or ""),
    )
    saved = await auto_marketplace.crm_engine.communications.log_email(email)
    return json_response(saved.to_dict(), status=201)


async def list_emails_handler(request: web.Request) -> web.Response:
    _check_perm(request, "crm.read")
    items = await auto_marketplace.crm_engine.communications.list_emails(
        customer_id=request.query.get("customer_id") or None,
        lead_id=request.query.get("lead_id") or None,
        deal_id=request.query.get("deal_id") or None,
        status=request.query.get("status") or None,
    )
    return json_response({"items": [e.to_dict() for e in items]})


async def get_email_handler(request: web.Request) -> web.Response:
    _check_perm(request, "crm.read")
    email = await auto_marketplace.crm_engine.communications.get_email(request.match_info["email_id"])
    return json_response(email.to_dict())


async def update_email_handler(request: web.Request) -> web.Response:
    _check_perm(request, "crm.write")
    data = await request.json()
    allowed = (
        "customer_id",
        "lead_id",
        "deal_id",
        "agent_id",
        "subject",
        "body",
        "direction",
        "status",
        "sender",
        "recipient",
    )
    updates = {k: data[k] for k in allowed if k in data}
    if not updates:
        raise ValidationError("no updatable fields provided")
    updated = await auto_marketplace.crm_engine.communications.update_email(request.match_info["email_id"], **updates)
    return json_response(updated.to_dict())


async def delete_email_handler(request: web.Request) -> web.Response:
    _check_perm(request, "crm.write")
    email_id = request.match_info["email_id"]
    deleted = await auto_marketplace.crm_engine.communications.delete_email(email_id)
    return json_response({"email_id": email_id, "deleted": deleted})


async def schedule_meeting_handler(request: web.Request) -> web.Response:
    _check_perm(request, "crm.write")
    data = await request.json()
    meeting = Meeting(
        customer_id=str(data.get("customer_id") or ""),
        lead_id=str(data.get("lead_id") or ""),
        deal_id=str(data.get("deal_id") or ""),
        agent_id=str(data.get("agent_id") or data.get("assigned_to") or ""),
        title=str(data.get("title") or ""),
        description=str(data.get("description") or ""),
        scheduled_at=float(data.get("scheduled_at") or 0) or __import__("time").time(),
        duration_min=int(data.get("duration_min") or 30),
        location=str(data.get("location") or ""),
        status=str(data.get("status") or "scheduled"),
    )
    saved = await auto_marketplace.crm_engine.calendar.schedule_meeting(meeting)
    return json_response(saved.to_dict(), status=201)


async def list_meetings_handler(request: web.Request) -> web.Response:
    _check_perm(request, "crm.read")
    items = await auto_marketplace.crm_engine.calendar.list_meetings(
        agent_id=request.query.get("agent_id") or None,
        customer_id=request.query.get("customer_id") or None,
        lead_id=request.query.get("lead_id") or None,
        deal_id=request.query.get("deal_id") or None,
        status=request.query.get("status") or None,
    )
    return json_response({"items": [m.to_dict() for m in items]})


async def get_meeting_handler(request: web.Request) -> web.Response:
    _check_perm(request, "crm.read")
    meeting = await auto_marketplace.crm_engine.calendar.get_meeting(request.match_info["meeting_id"])
    return json_response(meeting.to_dict())


async def update_meeting_handler(request: web.Request) -> web.Response:
    _check_perm(request, "crm.write")
    data = await request.json()
    allowed = (
        "customer_id",
        "lead_id",
        "deal_id",
        "agent_id",
        "title",
        "description",
        "scheduled_at",
        "duration_min",
        "location",
        "status",
        "completed",
    )
    updates = {k: data[k] for k in allowed if k in data}
    if not updates:
        raise ValidationError("no updatable fields provided")
    updated = await auto_marketplace.crm_engine.calendar.update_meeting(request.match_info["meeting_id"], **updates)
    return json_response(updated.to_dict())


async def cancel_meeting_handler(request: web.Request) -> web.Response:
    _check_perm(request, "crm.write")
    meeting = await auto_marketplace.crm_engine.calendar.cancel_meeting(request.match_info["meeting_id"])
    return json_response(meeting.to_dict())


async def delete_meeting_handler(request: web.Request) -> web.Response:
    _check_perm(request, "crm.write")
    meeting_id = request.match_info["meeting_id"]
    deleted = await auto_marketplace.crm_engine.calendar.delete_meeting(meeting_id)
    return json_response({"meeting_id": meeting_id, "deleted": deleted})


async def create_reminder_handler(request: web.Request) -> web.Response:
    _check_perm(request, "crm.write")
    data = await request.json()
    reminder = Reminder(
        task_id=str(data.get("task_id") or ""),
        customer_id=str(data.get("customer_id") or ""),
        lead_id=str(data.get("lead_id") or ""),
        deal_id=str(data.get("deal_id") or ""),
        title=str(data.get("title") or data.get("message") or ""),
        message=str(data.get("message") or data.get("title") or ""),
        assigned_agent_id=str(data.get("assigned_to") or data.get("assigned_agent_id") or ""),
        trigger_at=_optional_float(data.get("remind_at") or data.get("trigger_at"), "remind_at") or __import__("time").time(),
    )
    saved = await auto_marketplace.crm_engine.calendar.create_reminder(reminder)
    return json_response(saved.to_dict(), status=201)


async def list_reminders_handler(request: web.Request) -> web.Response:
    _check_perm(request, "crm.read")
    items = await auto_marketplace.crm_engine.calendar.list_reminders(
        customer_id=request.query.get("customer_id") or None,
        lead_id=request.query.get("lead_id") or None,
        deal_id=request.query.get("deal_id") or None,
        assigned_to=request.query.get("assigned_to") or request.query.get("agent_id") or None,
        status=request.query.get("status") or None,
        overdue=_query_flag(request, "overdue"),
        due=_query_flag(request, "due"),
        upcoming=_query_flag(request, "upcoming"),
    )
    return json_response({"items": [r.to_dict() for r in items]})


async def get_reminder_handler(request: web.Request) -> web.Response:
    _check_perm(request, "crm.read")
    reminder = await auto_marketplace.crm_engine.calendar.get_reminder(request.match_info["reminder_id"])
    return json_response(reminder.to_dict())


async def update_reminder_handler(request: web.Request) -> web.Response:
    _check_perm(request, "crm.write")
    data = await request.json()
    allowed = (
        "task_id",
        "customer_id",
        "lead_id",
        "deal_id",
        "title",
        "message",
        "assigned_agent_id",
        "assigned_to",
        "trigger_at",
        "remind_at",
        "status",
    )
    updates = {k: data[k] for k in allowed if k in data}
    if not updates:
        raise ValidationError("no updatable fields provided")
    updated = await auto_marketplace.crm_engine.calendar.update_reminder(request.match_info["reminder_id"], **updates)
    return json_response(updated.to_dict())


async def complete_reminder_handler(request: web.Request) -> web.Response:
    _check_perm(request, "crm.write")
    reminder = await auto_marketplace.crm_engine.calendar.complete_reminder(request.match_info["reminder_id"])
    return json_response(reminder.to_dict())


async def dismiss_reminder_handler(request: web.Request) -> web.Response:
    _check_perm(request, "crm.write")
    reminder = await auto_marketplace.crm_engine.calendar.dismiss_reminder(request.match_info["reminder_id"])
    return json_response(reminder.to_dict())


async def delete_reminder_handler(request: web.Request) -> web.Response:
    _check_perm(request, "crm.write")
    reminder_id = request.match_info["reminder_id"]
    deleted = await auto_marketplace.crm_engine.calendar.delete_reminder(reminder_id)
    return json_response({"reminder_id": reminder_id, "deleted": deleted})


async def list_opportunities_handler(request: web.Request) -> web.Response:
    _check_perm(request, "pipeline.read")
    items = await auto_marketplace.crm_engine.pipeline.list_opportunities(
        dealer_id=request.query.get("dealer_id") or None,
        customer_id=request.query.get("customer_id") or None,
    )
    return json_response({"items": [o.to_dict() for o in items]})


async def get_opportunity_handler(request: web.Request) -> web.Response:
    _check_perm(request, "pipeline.read")
    item = await auto_marketplace.crm_engine.pipeline.get_opportunity(request.match_info["opportunity_id"])
    return json_response(item.to_dict())


async def ai_next_action_handler(request: web.Request) -> web.Response:
    _check_perm(request, "crm.read")
    lead = await auto_marketplace.crm_engine.leads.get(request.match_info["lead_id"])
    action = await auto_marketplace.crm_engine.ai.next_best_action(lead)
    follow_up = await auto_marketplace.crm_engine.ai.suggest_follow_up(lead)
    durable = await auto_marketplace.crm_engine.automation.next_action(lead_id=lead.lead_id)
    recommended = await auto_marketplace.crm_engine.intelligence.next_best_action(lead_id=lead.lead_id)
    return json_response(
        {
            "next_best_action": action,
            "follow_up": follow_up,
            "next_action": durable,
            "recommended_action": recommended,
        }
    )


async def crm_intelligence_overview_handler(request: web.Request) -> web.Response:
    _require_authenticated_read(request, "crm.read")
    overview = await auto_marketplace.crm_engine.intelligence.manager_overview()
    return json_response(overview)


async def lead_sales_intelligence_handler(request: web.Request) -> web.Response:
    _require_authenticated_read(request, "crm.read")
    report = await auto_marketplace.crm_engine.intelligence.lead_intelligence(request.match_info["lead_id"])
    return json_response(report)


async def deal_sales_intelligence_handler(request: web.Request) -> web.Response:
    _require_authenticated_read(request, "crm.read")
    report = await auto_marketplace.crm_engine.intelligence.deal_intelligence(request.match_info["deal_id"])
    return json_response(report)


async def crm_execution_summary_handler(request: web.Request) -> web.Response:
    _require_authenticated_read(request, "crm.read")
    return json_response(await auto_marketplace.crm_engine.execution.summary())


async def crm_execution_queue_handler(request: web.Request) -> web.Response:
    _require_authenticated_read(request, "crm.read")
    overdue = None
    if "overdue" in request.query:
        overdue = _query_flag(request, "overdue")
    limit_raw = request.query.get("limit") or "100"
    try:
        limit = int(limit_raw)
    except (TypeError, ValueError):
        raise ValidationError("limit must be an integer")
    queue = await auto_marketplace.crm_engine.execution.queue(
        owner=request.query.get("owner") or None,
        priority=request.query.get("priority") or None,
        temperature=request.query.get("temperature") or None,
        overdue=overdue,
        sla_status=request.query.get("sla_status") or None,
        escalation_level=request.query.get("escalation_level") or None,
        entity_type=request.query.get("entity_type") or None,
        limit=limit,
    )
    return json_response(queue)


async def lead_sales_execution_handler(request: web.Request) -> web.Response:
    _require_authenticated_read(request, "crm.read")
    report = await auto_marketplace.crm_engine.execution.lead_execution(request.match_info["lead_id"])
    return json_response(report)


async def deal_sales_execution_handler(request: web.Request) -> web.Response:
    _require_authenticated_read(request, "crm.read")
    report = await auto_marketplace.crm_engine.execution.deal_execution(request.match_info["deal_id"])
    return json_response(report)


def _manager_filters(request: web.Request) -> dict[str, str | None]:
    return {
        "owner": request.query.get("owner") or None,
        "stage": request.query.get("stage") or None,
        "forecast_category": request.query.get("forecast_category") or None,
        "risk_level": request.query.get("risk_level") or None,
        "temperature": request.query.get("temperature") or None,
        "relationship_health": request.query.get("relationship_health") or None,
    }


def _parse_bounded_int(raw: str | None, *, default: int, field: str) -> int:
    value = raw or str(default)
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field} must be an integer") from exc


async def crm_manager_command_center_handler(request: web.Request) -> web.Response:
    _require_authenticated_read(request, "crm.read")
    return json_response(await auto_marketplace.crm_engine.manager.command_center(**_manager_filters(request)))


async def crm_manager_pipeline_handler(request: web.Request) -> web.Response:
    _require_authenticated_read(request, "crm.read")
    limit = _parse_bounded_int(request.query.get("limit"), default=50, field="limit")
    offset = _parse_bounded_int(request.query.get("offset"), default=0, field="offset")
    return json_response(
        await auto_marketplace.crm_engine.manager.pipeline_snapshot(
            **_manager_filters(request),
            limit=limit,
            offset=offset,
        )
    )


async def crm_manager_forecast_handler(request: web.Request) -> web.Response:
    _require_authenticated_read(request, "crm.read")
    return json_response(await auto_marketplace.crm_engine.manager.forecast(**_manager_filters(request)))


async def crm_manager_team_performance_handler(request: web.Request) -> web.Response:
    _require_authenticated_read(request, "crm.read")
    owner = request.query.get("owner") or None
    return json_response(await auto_marketplace.crm_engine.manager.team_performance(owner=owner))


async def crm_manager_operational_summary_handler(request: web.Request) -> web.Response:
    """Sprint 13 — read-only production operations summary for the manager side."""
    _require_authenticated_read(request, "crm.read")
    owner = request.query.get("owner") or None
    return json_response(await auto_marketplace.crm_engine.manager.operational_summary(owner=owner))


_CRM_WRITE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
_CRM_API_ROOT = "/api/auto/v1/crm"


def _is_auto_crm_path(path: str) -> bool:
    return path == _CRM_API_ROOT or path.startswith(_CRM_API_ROOT + "/")


def _is_crm_intelligence_path(path: str) -> bool:
    if not _is_auto_crm_path(path):
        return False
    return path == f"{_CRM_API_ROOT}/intelligence" or path.endswith("/intelligence")


def _is_crm_execution_path(path: str) -> bool:
    if not _is_auto_crm_path(path):
        return False
    if path == f"{_CRM_API_ROOT}/execution" or path.startswith(f"{_CRM_API_ROOT}/execution/"):
        return True
    return path.endswith("/execution")


def _is_crm_customer_360_path(path: str) -> bool:
    if not _is_auto_crm_path(path):
        return False
    return path.endswith("/360")


def _is_crm_manager_path(path: str) -> bool:
    if not _is_auto_crm_path(path):
        return False
    return path.startswith(f"{_CRM_API_ROOT}/manager/") or path == f"{_CRM_API_ROOT}/manager"


@web.middleware
async def crm_mutating_auth_middleware(request: web.Request, handler):
    """Require Bearer auth for mutating Auto CRM routes and intelligence/execution/360/manager reads."""
    if _is_auto_crm_path(request.path) and (
        request.method in _CRM_WRITE_METHODS
        or _is_crm_intelligence_path(request.path)
        or _is_crm_execution_path(request.path)
        or _is_crm_customer_360_path(request.path)
        or _is_crm_manager_path(request.path)
    ):
        principal = request.get("principal")
        if not isinstance(principal, dict) or not principal.get("authenticated"):
            return error_response("Authentication required", status=401)
    return await handler(request)


@web.middleware
async def crm_bearer_principal_restore_middleware(request: web.Request, handler):
    """Restore Bearer principal wiped by later vertical auth middlewares (Sprint 40.4).

    Several apps append auth middleware that sets ``request["principal"]`` to
    ``X-Principal`` or ``None``. Those run *after* auto-marketplace auth (aiohttp:
    first registered = outermost), so CRM handlers would see a cleared principal
    even when Authorization Bearer was valid. Register this middleware last
    (innermost) from ``api.server.create_app``.
    """
    if _is_auto_crm_path(request.path):
        auth = request.headers.get("Authorization")
        principal = request.get("principal")
        if auth and auth.startswith("Bearer ") and (
            not isinstance(principal, dict) or not principal.get("authenticated")
        ):
            from applications.auto_marketplace.integrations.platform_bridge import (
                platform_bridge,
            )

            request["principal"] = await platform_bridge.authenticate_request(auth)
    return await handler(request)


@web.middleware
async def crm_error_middleware(request: web.Request, handler):
    try:
        return await handler(request)
    except NotFoundError as exc:
        return error_response(str(exc), status=404)
    except AuthenticationError as exc:
        return error_response(str(exc), status=401)
    except AuthorizationError as exc:
        return error_response(str(exc), status=403)
    except ValidationError as exc:
        return error_response(str(exc), status=400)
    except ValueError as exc:
        # Enum / parse errors must never surface as 500 on CRM routes.
        return error_response(str(exc), status=400)
    except AutoMarketplaceError as exc:
        return error_response(str(exc), status=400)
