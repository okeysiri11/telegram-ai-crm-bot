"""API handlers — Buyer AI (Sprint 13.4)."""

from __future__ import annotations

from aiohttp import web

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.middleware import json_response
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError


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


def _suite():
    return auto_marketplace.buyer_ai


async def ba_health_handler(request: web.Request) -> web.Response:
    health = auto_marketplace.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "buyer_ai_ready": health.get("buyer_ai_ready"),
            "negotiation_ai_ready": health.get("negotiation_ai_ready"),
            "ownership_assistant_ready": health.get("ownership_assistant_ready"),
            "purchase_intelligence_ready": health.get("purchase_intelligence_ready"),
            "suite": _suite().status(),
        }
    )


async def ba_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ba_profile_handler(request: web.Request) -> web.Response:
    try:
        profile = _suite().profile
        if request.method == "GET":
            buyer_id = request.rel_url.query.get("buyer_id")
            if buyer_id:
                return json_response(profile.get(buyer_id))
            return json_response(profile.status())
        body = await _read_json(request)
        action = body.get("action", "create")
        if action == "budget":
            return json_response(profile.update_budget(body.get("buyer_id", ""), budget_min=body.get("budget_min"), budget_max=body.get("budget_max")))
        if action == "purchase":
            return json_response(profile.add_purchase(body.get("buyer_id", ""), vin=body.get("vin", ""), price=float(body.get("price", 0) or 0), dealer=body.get("dealer", "")), status=201)
        return json_response(
            profile.create(
                name=body.get("name", ""),
                budget_max=float(body.get("budget_max", 25000) or 25000),
                budget_min=float(body.get("budget_min", 0) or 0),
                preferred_brands=body.get("preferred_brands"),
                preferred_models=body.get("preferred_models"),
                fuel=body.get("fuel"),
                ev_preference=bool(body.get("ev_preference", False)),
                body_styles=body.get("body_styles"),
                transmission=body.get("transmission"),
                regions=body.get("regions"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ba_search_handler(request: web.Request) -> web.Response:
    try:
        search = _suite().search
        if request.method == "GET":
            return json_response(search.status())
        body = await _read_json(request)
        action = body.get("action", "nl")
        if action == "index":
            return json_response(
                search.index_listing(
                    vin=body.get("vin", ""),
                    make=body.get("make", ""),
                    model=body.get("model", ""),
                    year=body.get("year"),
                    price=float(body.get("price", 0) or 0),
                    dealer=body.get("dealer", ""),
                    fuel=body.get("fuel", "gasoline"),
                    body_style=body.get("body_style", "sedan"),
                    region=body.get("region", ""),
                    available=bool(body.get("available", True)),
                ),
                status=201,
            )
        if action == "recommend":
            return json_response(search.recommend(buyer_id=body.get("buyer_id", ""), limit=int(body.get("limit", 5) or 5)), status=201)
        if action == "compare":
            return json_response(search.compare(listing_ids=body.get("listing_ids") or []), status=201)
        return json_response(search.natural_language_search(query=body.get("query", ""), buyer_id=body.get("buyer_id", "")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ba_negotiation_handler(request: web.Request) -> web.Response:
    try:
        negotiation = _suite().negotiation
        if request.method == "GET":
            nid = request.rel_url.query.get("negotiation_id")
            if nid:
                return json_response(negotiation.strategy(nid))
            return json_response(negotiation.status())
        body = await _read_json(request)
        action = body.get("action", "start")
        if action == "offer":
            return json_response(negotiation.generate_offer(body.get("negotiation_id", ""), strategy=body.get("strategy", "fair")), status=201)
        if action == "counter":
            return json_response(negotiation.generate_counter(body.get("negotiation_id", ""), seller_offer=body.get("seller_offer")), status=201)
        if action == "strategy":
            return json_response(negotiation.strategy(body.get("negotiation_id", "")))
        return json_response(
            negotiation.start(buyer_id=body.get("buyer_id", ""), listing_id=body.get("listing_id", ""), list_price=body.get("list_price")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ba_purchase_handler(request: web.Request) -> web.Response:
    try:
        purchase = _suite().purchase
        if request.method == "GET":
            return json_response(purchase.status())
        body = await _read_json(request)
        return json_response(
            purchase.analyze(
                price=float(body.get("price", 0) or 0),
                mileage=int(body.get("mileage", 50000) or 50000),
                fuel=body.get("fuel", "gasoline"),
                years=int(body.get("years", 5) or 5),
                loan_rate=float(body.get("loan_rate", 0.06) or 0.06),
                down_payment=float(body.get("down_payment", 0) or 0),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ba_protection_handler(request: web.Request) -> web.Response:
    try:
        protection = _suite().protection
        if request.method == "GET":
            return json_response(protection.status())
        body = await _read_json(request)
        return json_response(
            protection.assess(
                vin=body.get("vin", ""),
                listing_id=body.get("listing_id", ""),
                listing_price=float(body.get("listing_price", 0) or 0),
                inspection_ref=body.get("inspection_ref", ""),
                fraud_flags=body.get("fraud_flags"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ba_ownership_handler(request: web.Request) -> web.Response:
    try:
        ownership = _suite().ownership
        if request.method == "GET":
            return json_response(ownership.status())
        body = await _read_json(request)
        action = body.get("action", "create")
        if action == "reminder":
            return json_response(ownership.add_reminder(body.get("ownership_id", ""), title=body.get("title", ""), due_at=body.get("due_at", "")), status=201)
        if action == "document":
            return json_response(ownership.store_document(body.get("ownership_id", ""), name=body.get("name", ""), doc_type=body.get("doc_type", "general")), status=201)
        return json_response(
            ownership.create_plan(buyer_id=body.get("buyer_id", ""), vin=body.get("vin", ""), purchase_date=body.get("purchase_date", "")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ba_assistant_handler(request: web.Request) -> web.Response:
    try:
        assistant = _suite().assistant
        if request.method == "GET":
            return json_response(assistant.status())
        body = await _read_json(request)
        return json_response(
            assistant.ask(mode=body.get("mode", "chat"), message=body.get("message", ""), buyer_id=body.get("buyer_id", "")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ba_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dash = _suite().dashboard
        if request.method == "GET":
            return json_response(
                dash.render(
                    dashboard_type=request.rel_url.query.get("type", "buyer"),
                    buyer_id=request.rel_url.query.get("buyer_id", ""),
                )
            )
        body = await _read_json(request)
        return json_response(
            dash.render(dashboard_type=body.get("dashboard_type", "buyer"), buyer_id=body.get("buyer_id", "")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
