# Public API v1 — CRM foundation handlers (leads, clients, reports).
#
# Bridges frozen /api/v1 CRM routes to the Auto Marketplace CRM engine.
# Additive to the existing DealWorkflowService /api/v1/deals surface.

from __future__ import annotations

from typing import Any, Callable

from aiohttp import web

from api.middleware import require_api_auth
from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.crm.models import (
    CRMDeal,
    CRMLead,
    CRMLeadStatus,
    CustomerProfile,
    DealStage,
    LeadSource,
)
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from platform_api.pagination import PaginationMeta, PaginationParams
from platform_api.responses import error_response, success_response


def _ok(data: Any, *, status: int = 200) -> web.Response:
    return success_response(data, status=status)


def _err(message: str, *, status: int = 400) -> web.Response:
    return error_response(message, status=status)


def _parse_json(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValidationError("JSON body must be an object")
    return data


def _parse_lead_source(raw: object) -> LeadSource:
    if raw is None or raw == "":
        return LeadSource.WEB
    try:
        return LeadSource(str(raw))
    except ValueError as exc:
        allowed = ", ".join(s.value for s in LeadSource)
        raise ValidationError(f"invalid lead source: {raw!r}; allowed: {allowed}") from exc


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


def _sort_items(items: list[Any], *, sort: str, order: str, accessors: dict[str, Callable[[Any], Any]]) -> list[Any]:
    key_fn = accessors.get(sort) or accessors.get("created_at")
    if key_fn is None:
        return items
    reverse = order.lower() == "desc"
    try:
        return sorted(items, key=key_fn, reverse=reverse)
    except TypeError:
        return items


def _paginate(items: list[Any], params: PaginationParams) -> dict[str, Any]:
    total = len(items)
    page_items = items[params.offset : params.offset + params.page_size]
    return {
        "items": page_items,
        "pagination": PaginationMeta.build(
            page=params.page,
            page_size=params.page_size,
            total=total,
        ).model_dump(),
    }


async def _safe(handler_coro) -> web.Response:
    try:
        return await handler_coro
    except ValidationError as exc:
        return _err(str(exc), status=400)
    except ValueError as exc:
        return _err(str(exc), status=400)
    except NotFoundError as exc:
        return _err(str(exc), status=404)
    except PermissionError as exc:
        return _err(str(exc), status=403)


# ---------------------------------------------------------------------------
# Leads
# ---------------------------------------------------------------------------


@require_api_auth
async def leads_list_handler(request: web.Request) -> web.Response:
    async def _run() -> web.Response:
        params = PaginationParams.from_query(dict(request.query))
        status = _parse_lead_status(request.query.get("status"))
        dealer_id = request.query.get("dealer_id") or None
        source_raw = request.query.get("source")
        source = _parse_lead_source(source_raw) if source_raw else None
        customer_id = request.query.get("customer_id") or None
        sort = request.query.get("sort", "created_at")
        order = request.query.get("order", "desc")

        items = auto_marketplace.crm_engine.leads.list_leads(status=status, dealer_id=dealer_id)
        if source is not None:
            items = [lead for lead in items if lead.source == source]
        if customer_id:
            items = [lead for lead in items if lead.customer_id == customer_id]
        items = _sort_items(
            items,
            sort=sort,
            order=order,
            accessors={
                "created_at": lambda lead: lead.created_at,
                "score": lambda lead: lead.score,
                "status": lambda lead: lead.status.value,
                "source": lambda lead: lead.source.value,
            },
        )
        page = _paginate(items, params)
        page["items"] = [lead.to_dict() for lead in page["items"]]
        return _ok(page)

    return await _safe(_run())


@require_api_auth
async def leads_get_handler(request: web.Request) -> web.Response:
    async def _run() -> web.Response:
        lead = auto_marketplace.crm_engine.leads.get(request.match_info["lead_id"])
        return _ok(lead.to_dict())

    return await _safe(_run())


@require_api_auth
async def leads_create_handler(request: web.Request) -> web.Response:
    async def _run() -> web.Response:
        data = _parse_json(await request.json())
        lead = CRMLead(
            customer_id=str(data.get("customer_id") or ""),
            vehicle_id=str(data.get("vehicle_id") or ""),
            dealer_id=str(data.get("dealer_id") or ""),
            source=_parse_lead_source(data.get("source", "web")),
            notes=str(data.get("notes") or ""),
            assigned_agent_id=str(data.get("assigned_agent_id") or ""),
            metadata=dict(data.get("metadata") or {}) if isinstance(data.get("metadata"), dict) else {},
        )
        if data.get("status"):
            lead.status = _parse_lead_status(data["status"]) or lead.status
        # UTM / marketing fields live in metadata for GlobeFly connectors.
        for utm_key in ("utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term", "name"):
            if data.get(utm_key) is not None:
                lead.metadata[utm_key] = data[utm_key]
        customer = None
        if lead.customer_id:
            try:
                customer = auto_marketplace.crm_engine.customers.get(lead.customer_id)
            except NotFoundError:
                customer = None
        created = await auto_marketplace.crm_engine.leads.create(lead, customer)
        return _ok(created.to_dict(), status=201)

    return await _safe(_run())


@require_api_auth
async def leads_patch_handler(request: web.Request) -> web.Response:
    async def _run() -> web.Response:
        data = _parse_json(await request.json())
        lead_id = request.match_info["lead_id"]
        updates: dict[str, Any] = {}
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
            existing = auto_marketplace.crm_engine.leads.get(lead_id)
            merged = dict(existing.metadata)
            merged.update(data["metadata"])
            updates["metadata"] = merged
        if not updates:
            raise ValidationError("no updatable fields provided")
        updated = await auto_marketplace.crm_engine.leads.update(lead_id, **updates)
        return _ok(updated.to_dict())

    return await _safe(_run())


@require_api_auth
async def leads_delete_handler(request: web.Request) -> web.Response:
    async def _run() -> web.Response:
        lead_id = request.match_info["lead_id"]
        deleted = auto_marketplace.crm_engine.leads.delete(lead_id)
        return _ok({"lead_id": lead_id, "deleted": deleted})

    return await _safe(_run())


# ---------------------------------------------------------------------------
# Clients (CRM customer profiles)
# ---------------------------------------------------------------------------


@require_api_auth
async def clients_list_handler(request: web.Request) -> web.Response:
    async def _run() -> web.Response:
        params = PaginationParams.from_query(dict(request.query))
        segment = request.query.get("segment") or None
        email = (request.query.get("email") or "").lower().strip() or None
        sort = request.query.get("sort", "created_at")
        order = request.query.get("order", "desc")
        items = auto_marketplace.crm_engine.customers.list_profiles(segment=segment)
        if email:
            items = [c for c in items if (c.email or "").lower() == email]
        items = _sort_items(
            items,
            sort=sort,
            order=order,
            accessors={
                "created_at": lambda c: c.created_at,
                "email": lambda c: c.email or "",
                "last_name": lambda c: c.last_name or "",
                "lifetime_value": lambda c: c.lifetime_value,
            },
        )
        page = _paginate(items, params)
        page["items"] = [c.to_dict() for c in page["items"]]
        # Alias client_id for public API consumers.
        for item in page["items"]:
            item["client_id"] = item.get("customer_id")
        return _ok(page)

    return await _safe(_run())


@require_api_auth
async def clients_get_handler(request: web.Request) -> web.Response:
    async def _run() -> web.Response:
        profile = auto_marketplace.crm_engine.customers.get(request.match_info["client_id"])
        payload = profile.to_dict()
        payload["client_id"] = payload["customer_id"]
        return _ok(payload)

    return await _safe(_run())


@require_api_auth
async def clients_create_handler(request: web.Request) -> web.Response:
    async def _run() -> web.Response:
        data = _parse_json(await request.json())
        profile = CustomerProfile(
            first_name=str(data.get("first_name") or ""),
            last_name=str(data.get("last_name") or ""),
            email=str(data.get("email") or ""),
            phone=str(data.get("phone") or ""),
            preferences=dict(data.get("preferences") or {}) if isinstance(data.get("preferences"), dict) else {},
            tags=list(data.get("tags") or []) if isinstance(data.get("tags"), list) else [],
            owner_agent_id=str(data.get("owner_agent_id") or ""),
        )
        created = await auto_marketplace.crm_engine.customers.create(profile)
        payload = created.to_dict()
        payload["client_id"] = payload["customer_id"]
        return _ok(payload, status=201)

    return await _safe(_run())


@require_api_auth
async def clients_patch_handler(request: web.Request) -> web.Response:
    async def _run() -> web.Response:
        data = _parse_json(await request.json())
        client_id = request.match_info["client_id"]
        allowed = ("first_name", "last_name", "email", "phone", "preferences", "tags", "owner_agent_id", "segment")
        updates = {k: data[k] for k in allowed if k in data}
        if not updates:
            raise ValidationError("no updatable fields provided")
        updated = await auto_marketplace.crm_engine.customers.update(client_id, **updates)
        payload = updated.to_dict()
        payload["client_id"] = payload["customer_id"]
        return _ok(payload)

    return await _safe(_run())


@require_api_auth
async def clients_delete_handler(request: web.Request) -> web.Response:
    async def _run() -> web.Response:
        client_id = request.match_info["client_id"]
        deleted = auto_marketplace.crm_engine.customers.delete(client_id)
        return _ok({"client_id": client_id, "deleted": deleted})

    return await _safe(_run())


# ---------------------------------------------------------------------------
# CRM sales deals (additive under /api/v1/crm/deals — does not replace exchange deals)
# ---------------------------------------------------------------------------


@require_api_auth
async def crm_deals_list_handler(request: web.Request) -> web.Response:
    async def _run() -> web.Response:
        params = PaginationParams.from_query(dict(request.query))
        stage = _parse_deal_stage(request.query.get("stage"))
        dealer_id = request.query.get("dealer_id") or None
        sort = request.query.get("sort", "created_at")
        order = request.query.get("order", "desc")
        items = auto_marketplace.crm_engine.deals.list_deals(stage=stage, dealer_id=dealer_id)
        items = _sort_items(
            items,
            sort=sort,
            order=order,
            accessors={
                "created_at": lambda d: d.created_at,
                "amount": lambda d: d.amount,
                "stage": lambda d: d.stage.value,
                "probability": lambda d: d.probability,
            },
        )
        page = _paginate(items, params)
        page["items"] = [d.to_dict() for d in page["items"]]
        return _ok(page)

    return await _safe(_run())


@require_api_auth
async def crm_deals_get_handler(request: web.Request) -> web.Response:
    async def _run() -> web.Response:
        deal = auto_marketplace.crm_engine.deals.get(request.match_info["deal_id"])
        return _ok(deal.to_dict())

    return await _safe(_run())


@require_api_auth
async def crm_deals_create_handler(request: web.Request) -> web.Response:
    async def _run() -> web.Response:
        data = _parse_json(await request.json())
        stage = _parse_deal_stage(data.get("stage")) or DealStage.PROSPECT
        try:
            amount = float(data.get("amount", 0) or 0)
        except (TypeError, ValueError) as exc:
            raise ValidationError("amount must be a number") from exc
        deal = CRMDeal(
            customer_id=str(data.get("customer_id") or data.get("client_id") or ""),
            dealer_id=str(data.get("dealer_id") or ""),
            vehicle_id=str(data.get("vehicle_id") or ""),
            amount=amount,
            owner_agent_id=str(data.get("owner_agent_id") or ""),
            stage=stage,
        )
        created = await auto_marketplace.crm_engine.deals.create(deal)
        return _ok(created.to_dict(), status=201)

    return await _safe(_run())


@require_api_auth
async def crm_deals_patch_handler(request: web.Request) -> web.Response:
    async def _run() -> web.Response:
        data = _parse_json(await request.json())
        deal_id = request.match_info["deal_id"]
        if "stage" in data:
            stage = _parse_deal_stage(data["stage"])
            if stage is None:
                raise ValidationError("stage cannot be empty")
            updated = await auto_marketplace.crm_engine.deals.update_stage(deal_id, stage)
            return _ok(updated.to_dict())
        updates: dict[str, Any] = {}
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
        return _ok(updated.to_dict())

    return await _safe(_run())


@require_api_auth
async def crm_deals_delete_handler(request: web.Request) -> web.Response:
    async def _run() -> web.Response:
        deal_id = request.match_info["deal_id"]
        deleted = auto_marketplace.crm_engine.deals.delete(deal_id)
        return _ok({"deal_id": deal_id, "deleted": deleted})

    return await _safe(_run())


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

_REPORT_CATALOG = (
    {"id": "pipeline", "title": "Sales pipeline", "description": "Open deals by stage"},
    {"id": "forecast", "title": "Pipeline forecast", "description": "Weighted revenue forecast"},
    {"id": "conversion", "title": "Conversion analytics", "description": "Lead/deal conversion metrics"},
    {"id": "crm-metrics", "title": "CRM metrics", "description": "Aggregate CRM engine counters"},
)


@require_api_auth
async def reports_list_handler(_request: web.Request) -> web.Response:
    return _ok({"items": list(_REPORT_CATALOG)})


@require_api_auth
async def reports_get_handler(request: web.Request) -> web.Response:
    async def _run() -> web.Response:
        report_id = request.match_info["report_id"]
        engine = auto_marketplace.crm_engine
        if report_id == "pipeline":
            payload = engine.pipeline.pipeline_view(dealer_id=request.query.get("dealer_id"))
        elif report_id == "forecast":
            days_raw = request.query.get("days", "30")
            try:
                days = max(1, min(int(days_raw), 365))
            except ValueError as exc:
                raise ValidationError("days must be an integer") from exc
            payload = engine.pipeline.forecast(days=days)
        elif report_id == "conversion":
            payload = engine.pipeline.conversion_analytics()
        elif report_id == "crm-metrics":
            payload = engine.metrics()
        else:
            raise NotFoundError("Report", report_id)
        return _ok({"report_id": report_id, "data": payload})

    return await _safe(_run())
