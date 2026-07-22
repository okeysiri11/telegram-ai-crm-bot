"""API handlers — Agro Enterprise (Sprint 14.0)."""

from __future__ import annotations

from aiohttp import web

from applications.agro_enterprise import agro_enterprise
from applications.agro_enterprise.api.middleware import json_response
from applications.agro_enterprise.shared.exceptions import NotFoundError, ValidationError


async def _read_json(request: web.Request) -> dict:
    try:
        data = await request.json()
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _handle_error(exc: Exception) -> web.Response:
    if isinstance(exc, NotFoundError):
        return json_response({"error": str(exc)}, status=404)
    if isinstance(exc, ValidationError):
        return json_response({"error": str(exc)}, status=400)
    return json_response({"error": str(exc)}, status=500)


async def health_handler(request: web.Request) -> web.Response:
    return json_response(agro_enterprise.health())


async def bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(agro_enterprise.bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def marketplace_handler(request: web.Request) -> web.Response:
    try:
        mp = agro_enterprise.marketplace
        if request.method == "GET":
            kind = request.rel_url.query.get("kind")
            if kind == "directories":
                return json_response(mp.directories())
            return json_response(mp.status())
        body = await _read_json(request)
        action = body.get("action", "listing")
        if action == "supplier":
            return json_response(
                mp.register_supplier(name=body.get("name", ""), region=body.get("region", "")),
                status=201,
            )
        if action == "buyer":
            return json_response(
                mp.register_buyer(name=body.get("name", ""), region=body.get("region", "")),
                status=201,
            )
        if action == "order":
            return json_response(
                mp.place_order(
                    listing_id=body.get("listing_id", ""),
                    counterparty_id=body.get("counterparty_id", ""),
                    quantity=body.get("quantity"),
                ),
                status=201,
            )
        return json_response(
            mp.create_listing(
                category=body.get("category", "crops"),
                side=body.get("side", "sell"),
                title=body.get("title", ""),
                quantity=float(body.get("quantity", 1) or 1),
                unit=body.get("unit", "t"),
                price=float(body.get("price", 0) or 0),
                party_id=body.get("party_id", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def farms_handler(request: web.Request) -> web.Response:
    try:
        farms = agro_enterprise.farms
        if request.method == "GET":
            return json_response(farms.status())
        body = await _read_json(request)
        action = body.get("action", "farm")
        if action == "company":
            return json_response(
                farms.create_company(name=body.get("name", ""), company_type=body.get("company_type", "agribusiness")),
                status=201,
            )
        if action == "farmland":
            return json_response(
                farms.register_farmland(
                    farm_id=body.get("farm_id", ""),
                    label=body.get("label", ""),
                    hectares=float(body.get("hectares", 0) or 0),
                ),
                status=201,
            )
        if action == "storage":
            return json_response(
                farms.register_storage(
                    farm_id=body.get("farm_id", ""),
                    name=body.get("name", ""),
                    capacity_t=float(body.get("capacity_t", 0) or 0),
                ),
                status=201,
            )
        if action == "equipment":
            return json_response(
                farms.register_equipment(
                    farm_id=body.get("farm_id", ""),
                    name=body.get("name", ""),
                    equipment_type=body.get("equipment_type", "tractor"),
                ),
                status=201,
            )
        if action == "livestock":
            return json_response(
                farms.register_livestock(
                    farm_id=body.get("farm_id", ""),
                    species=body.get("species", ""),
                    headcount=int(body.get("headcount", 0) or 0),
                ),
                status=201,
            )
        if action == "certification":
            return json_response(
                farms.add_certification(
                    farm_id=body.get("farm_id", ""),
                    standard=body.get("standard", ""),
                    status=body.get("status", "active"),
                ),
                status=201,
            )
        return json_response(
            farms.create_farm(
                name=body.get("name", ""),
                owner=body.get("owner", ""),
                region=body.get("region", ""),
                hectares=float(body.get("hectares", 0) or 0),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def crops_handler(request: web.Request) -> web.Response:
    try:
        crops = agro_enterprise.crops
        if request.method == "GET":
            return json_response(crops.status())
        body = await _read_json(request)
        action = body.get("action", "crop")
        if action == "season":
            return json_response(
                crops.plan_season(
                    farm_id=body.get("farm_id", ""),
                    year=int(body.get("year", 2026) or 2026),
                    crops=body.get("crops"),
                ),
                status=201,
            )
        if action == "rotation":
            return json_response(
                crops.crop_rotation(farm_id=body.get("farm_id", ""), sequence=body.get("sequence") or []),
                status=201,
            )
        if action == "assign":
            return json_response(
                crops.assign_field(
                    farm_id=body.get("farm_id", ""),
                    land_id=body.get("land_id", ""),
                    crop_id=body.get("crop_id", ""),
                ),
                status=201,
            )
        if action == "yield":
            return json_response(
                crops.yield_plan(
                    crop_id=body.get("crop_id", ""),
                    hectares=float(body.get("hectares", 0) or 0),
                    expected_t_per_ha=float(body.get("expected_t_per_ha", 0) or 0),
                ),
                status=201,
            )
        if action == "harvest":
            return json_response(
                crops.harvest_plan(
                    crop_id=body.get("crop_id", ""),
                    window_start=body.get("window_start", ""),
                    window_end=body.get("window_end", ""),
                ),
                status=201,
            )
        if action == "calendar":
            return json_response(
                crops.calendar_entry(
                    farm_id=body.get("farm_id", ""),
                    title=body.get("title", ""),
                    date=body.get("date", ""),
                    kind=body.get("kind", "production"),
                ),
                status=201,
            )
        return json_response(
            crops.add_crop(
                name=body.get("name", ""),
                variety=body.get("variety", ""),
                season=body.get("season", "summer"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def crm_handler(request: web.Request) -> web.Response:
    try:
        crm = agro_enterprise.crm
        if request.method == "GET":
            return json_response(crm.status())
        body = await _read_json(request)
        action = body.get("action", "contact")
        if action == "contract":
            return json_response(
                crm.create_contract(
                    party_id=body.get("party_id", ""),
                    title=body.get("title", ""),
                    value=float(body.get("value", 0) or 0),
                ),
                status=201,
            )
        if action == "lead":
            return json_response(
                crm.create_lead(
                    name=body.get("name", ""),
                    source=body.get("source", "marketplace"),
                    score=float(body.get("score", 0.5) or 0.5),
                ),
                status=201,
            )
        if action == "task":
            return json_response(
                crm.create_task(
                    title=body.get("title", ""),
                    assignee=body.get("assignee", ""),
                    due_at=body.get("due_at", ""),
                ),
                status=201,
            )
        if action == "calendar":
            return json_response(
                crm.calendar_event(
                    title=body.get("title", ""),
                    starts_at=body.get("starts_at", ""),
                    kind=body.get("kind", "meeting"),
                ),
                status=201,
            )
        return json_response(
            crm.create_contact(
                name=body.get("name", ""),
                crm_type=body.get("crm_type", "farmer"),
                company=body.get("company", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def knowledge_handler(request: web.Request) -> web.Response:
    try:
        knowledge = agro_enterprise.knowledge
        if request.method == "GET":
            q = request.rel_url.query.get("q")
            if q:
                return json_response({"results": knowledge.search(query=q)})
            return json_response(knowledge.status())
        body = await _read_json(request)
        return json_response(
            knowledge.publish(
                base=body.get("base", "crop"),
                title=body.get("title", ""),
                body=body.get("body", ""),
                tags=body.get("tags"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def dashboard_handler(request: web.Request) -> web.Response:
    try:
        dash = agro_enterprise.dashboard
        if request.method == "GET":
            return json_response(dash.render(dashboard_type=request.rel_url.query.get("type", "executive")))
        body = await _read_json(request)
        return json_response(dash.render(dashboard_type=body.get("dashboard_type", "executive")), status=201)
    except Exception as exc:
        return _handle_error(exc)
