# Portal API handlers — Sprint 6.7.

from __future__ import annotations

from aiohttp import web

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.middleware import error_response, json_response
from applications.auto_marketplace.authentication.models import PortalRole
from applications.auto_marketplace.shared.exceptions import AuthorizationError, ValidationError


def _portal_user(request: web.Request) -> dict:
    auth_header = request.headers.get("Authorization", "")
    token = auth_header[7:] if auth_header.startswith("Bearer ") else auth_header
    user = auto_marketplace.portal_engine.auth.validate_token(token)
    if user is None:
        principal = request.get("principal") or {}
        if principal.get("authenticated"):
            return {"role": principal.get("role", PortalRole.CUSTOMER.value), "user_id": "", "customer_id": "", "dealer_id": ""}
        raise AuthorizationError("Authentication required")
    return {
        "user_id": user.user_id,
        "role": user.role.value,
        "customer_id": user.customer_id,
        "dealer_id": user.dealer_id,
    }


def _check_perm(role: str, permission: str) -> None:
    if not auto_marketplace.portal_engine.security.authorize(role, permission):
        raise AuthorizationError(f"Permission denied: {permission}")


# --- Auth ---

async def register_customer_handler(request: web.Request) -> web.Response:
    data = await request.json()
    user, token = await auto_marketplace.portal_engine.auth.register_customer(
        email=data["email"], password=data["password"],
        first_name=data.get("first_name", ""), last_name=data.get("last_name", ""),
    )
    return json_response({"user": user.to_dict(), "token": token.to_dict()}, status=201)


async def login_handler(request: web.Request) -> web.Response:
    data = await request.json()
    user, token = await auto_marketplace.portal_engine.auth.login(data["email"], data["password"])
    return json_response({"user": user.to_dict(), "token": token.to_dict()})


async def oauth_login_handler(request: web.Request) -> web.Response:
    data = await request.json()
    user, token = await auto_marketplace.portal_engine.auth.oauth_login(
        data.get("provider", "google"), data.get("external_id", ""), data["email"]
    )
    return json_response({"user": user.to_dict(), "token": token.to_dict()})


# --- Customer Portal ---

async def customer_profile_handler(request: web.Request) -> web.Response:
    ctx = _portal_user(request)
    _check_perm(ctx["role"], "profile.read")
    if request.method == "GET":
        user = auto_marketplace.portal_engine.profiles.get_portal_user(ctx["user_id"])
        profile = auto_marketplace.portal_engine.profiles.get_customer_profile(ctx["customer_id"])
        return json_response({"user": user.to_dict(), "profile": profile.to_dict() if profile else {}})
    data = await request.json()
    user = auto_marketplace.portal_engine.profiles.update_portal_user(ctx["user_id"], display_name=data.get("display_name", ""))
    return json_response(user.to_dict())


async def customer_search_handler(request: web.Request) -> web.Response:
    ctx = _portal_user(request)
    _check_perm(ctx["role"], "search.read")
    criteria = dict(request.query)
    if request.method == "POST":
        criteria = await request.json()
    vehicles = await auto_marketplace.portal_engine.customer.search_vehicles(criteria)
    return json_response({"items": vehicles})


async def smart_search_handler(request: web.Request) -> web.Response:
    ctx = _portal_user(request)
    _check_perm(ctx["role"], "search.smart")
    data = await request.json()
    result = await auto_marketplace.portal_engine.customer.smart_search(data.get("query", ""), ctx["user_id"])
    return json_response(result)


async def favorites_list_handler(request: web.Request) -> web.Response:
    ctx = _portal_user(request)
    _check_perm(ctx["role"], "favorites.manage")
    if request.method == "POST":
        data = await request.json()
        fav = await auto_marketplace.portal_engine.favorites.add_favorite(ctx["user_id"], data["vehicle_id"])
        return json_response(fav.to_dict(), status=201)
    items = auto_marketplace.portal_engine.favorites.list_favorites(ctx["user_id"])
    return json_response({"items": [f.to_dict() for f in items]})


async def saved_searches_handler(request: web.Request) -> web.Response:
    ctx = _portal_user(request)
    _check_perm(ctx["role"], "favorites.manage")
    if request.method == "POST":
        data = await request.json()
        s = auto_marketplace.portal_engine.favorites.save_search(ctx["user_id"], data["name"], data.get("criteria", {}))
        return json_response(s.to_dict(), status=201)
    items = auto_marketplace.portal_engine.favorites.list_saved_searches(ctx["user_id"])
    return json_response({"items": [s.to_dict() for s in items]})


async def garage_handler(request: web.Request) -> web.Response:
    ctx = _portal_user(request)
    _check_perm(ctx["role"], "garage.manage")
    if request.method == "POST":
        data = await request.json()
        gv = auto_marketplace.portal_engine.garage.add_vehicle(ctx["user_id"], **data)
        return json_response(gv.to_dict(), status=201)
    items = auto_marketplace.portal_engine.garage.list_vehicles(ctx["user_id"])
    return json_response({"items": [g.to_dict() for g in items]})


async def purchase_history_handler(request: web.Request) -> web.Response:
    ctx = _portal_user(request)
    _check_perm(ctx["role"], "history.read")
    history = auto_marketplace.portal_engine.customer.purchase_history(ctx["customer_id"])
    return json_response(history)


async def test_drive_handler(request: web.Request) -> web.Response:
    ctx = _portal_user(request)
    _check_perm(ctx["role"], "bookings.create")
    data = await request.json()
    booking = await auto_marketplace.portal_engine.customer.book_test_drive(
        ctx["user_id"], customer_id=ctx["customer_id"] or data.get("customer_id", ""),
        vehicle_id=data["vehicle_id"], dealer_id=data.get("dealer_id", ""), scheduled_at=float(data.get("scheduled_at", 0)),
    )
    return json_response(booking.to_dict(), status=201)


async def trade_in_handler(request: web.Request) -> web.Response:
    ctx = _portal_user(request)
    _check_perm(ctx["role"], "bookings.create")
    data = await request.json()
    req = await auto_marketplace.portal_engine.customer.request_trade_in(
        ctx["user_id"], customer_id=ctx["customer_id"], **data
    )
    return json_response(req.to_dict(), status=201)


async def offer_request_handler(request: web.Request) -> web.Response:
    ctx = _portal_user(request)
    _check_perm(ctx["role"], "offers.create")
    data = await request.json()
    req = await auto_marketplace.portal_engine.customer.request_offer(
        ctx["user_id"], customer_id=ctx["customer_id"], vehicle_id=data["vehicle_id"],
        dealer_id=data.get("dealer_id", ""), proposed_amount=float(data.get("proposed_amount", 0)),
    )
    return json_response(req.to_dict(), status=201)


async def customer_ai_handler(request: web.Request) -> web.Response:
    ctx = _portal_user(request)
    _check_perm(ctx["role"], "assistant.chat")
    data = await request.json()
    result = await auto_marketplace.portal_engine.customer.ai_assistant(ctx["user_id"], data.get("message", ""))
    return json_response(result)


async def customer_recommendations_handler(request: web.Request) -> web.Response:
    ctx = _portal_user(request)
    _check_perm(ctx["role"], "recommendations.read")
    items = await auto_marketplace.portal_engine.customer.recommendations(ctx["customer_id"])
    return json_response({"items": items})


async def portal_notifications_handler(request: web.Request) -> web.Response:
    ctx = _portal_user(request)
    _check_perm(ctx["role"], "portal.read")
    items = auto_marketplace.portal_engine.notifications.list_notifications(ctx["user_id"])
    return json_response({"items": [n.to_dict() for n in items]})


async def view_vehicle_handler(request: web.Request) -> web.Response:
    ctx = _portal_user(request)
    data = await auto_marketplace.portal_engine.customer.view_vehicle(ctx["user_id"], request.match_info["vehicle_id"])
    return json_response(data)


# --- Dealer Portal ---

async def dealer_dashboard_handler(request: web.Request) -> web.Response:
    ctx = _portal_user(request)
    _check_perm(ctx["role"], "dealer.dashboard")
    dealer_id = ctx["dealer_id"] or request.query.get("dealer_id", "")
    return json_response(auto_marketplace.portal_engine.dealer.dashboard(dealer_id))


async def dealer_inventory_handler(request: web.Request) -> web.Response:
    ctx = _portal_user(request)
    _check_perm(ctx["role"], "inventory.manage")
    dealer_id = ctx["dealer_id"]
    if request.method == "POST":
        data = await request.json()
        vehicle = await auto_marketplace.portal_engine.dealer.publish_vehicle(dealer_id, data)
        return json_response(vehicle, status=201)
    return json_response({"items": auto_marketplace.portal_engine.dealer.list_inventory(dealer_id)})


async def dealer_leads_handler(request: web.Request) -> web.Response:
    ctx = _portal_user(request)
    _check_perm(ctx["role"], "leads.manage")
    return json_response({"items": auto_marketplace.portal_engine.dealer.manage_leads(ctx["dealer_id"])})


async def dealer_sales_handler(request: web.Request) -> web.Response:
    ctx = _portal_user(request)
    _check_perm(ctx["role"], "sales.read")
    return json_response(auto_marketplace.portal_engine.dealer.sales_tracking(ctx["dealer_id"]))


async def dealer_analytics_handler(request: web.Request) -> web.Response:
    ctx = _portal_user(request)
    _check_perm(ctx["role"], "analytics.read")
    return json_response(auto_marketplace.portal_engine.dealer.analytics_overview(ctx["dealer_id"]))


async def dealer_finance_handler(request: web.Request) -> web.Response:
    ctx = _portal_user(request)
    _check_perm(ctx["role"], "finance.read")
    return json_response(auto_marketplace.portal_engine.dealer.financial_overview(ctx["dealer_id"]))


async def dealer_documents_handler(request: web.Request) -> web.Response:
    ctx = _portal_user(request)
    _check_perm(ctx["role"], "documents.read")
    return json_response(auto_marketplace.portal_engine.dealer.documents_overview(ctx["dealer_id"]))


# --- Mobile API ---

async def mobile_info_handler(_request: web.Request) -> web.Response:
    return json_response(auto_marketplace.portal_engine.mobile.api_info())


async def mobile_feed_handler(request: web.Request) -> web.Response:
    client_id = request.headers.get("X-Client-Id", "anonymous")
    allowed, remaining = auto_marketplace.portal_engine.mobile.check_rate_limit(client_id)
    if not allowed:
        return error_response("Rate limit exceeded", status=429)
    ctx = {}
    try:
        ctx = _portal_user(request)
    except AuthorizationError:
        pass
    feed = auto_marketplace.portal_engine.mobile.mobile_feed(ctx.get("user_id", ""))
    resp = json_response(feed)
    resp.headers["X-RateLimit-Remaining"] = str(remaining)
    return resp


async def mobile_sync_handler(request: web.Request) -> web.Response:
    ctx = _portal_user(request)
    last_sync = float(request.query.get("last_sync", "0"))
    manifest = auto_marketplace.portal_engine.mobile.offline_sync_manifest(ctx["user_id"], last_sync=last_sync)
    return json_response(manifest)


async def mobile_push_register_handler(request: web.Request) -> web.Response:
    ctx = _portal_user(request)
    data = await request.json()
    result = auto_marketplace.portal_engine.notifications.register_push_device(ctx["user_id"], data["device_token"])
    return json_response(result, status=201)


# --- Public API ---

async def public_search_handler(request: web.Request) -> web.Response:
    items = auto_marketplace.portal_engine.public.search(query=request.query.get("q", ""), limit=int(request.query.get("limit", "20")))
    return json_response({"items": items})


async def public_vehicle_handler(request: web.Request) -> web.Response:
    vehicle = auto_marketplace.portal_engine.public.get_vehicle(request.match_info["vehicle_id"])
    if vehicle is None:
        return error_response("Vehicle not found", status=404)
    return json_response(vehicle)


async def public_stats_handler(_request: web.Request) -> web.Response:
    return json_response(auto_marketplace.portal_engine.public.catalog_stats())


# --- Partner API ---

async def partner_connect_handler(request: web.Request) -> web.Response:
    data = await request.json()
    conn, api_key = await auto_marketplace.portal_engine.partner.connect_partner(
        name=data["name"], partner_type=data.get("partner_type", "dealer"), webhook_url=data.get("webhook_url", "")
    )
    return json_response({**conn.to_dict(), "api_key": api_key}, status=201)


async def partner_insurance_handler(request: web.Request) -> web.Response:
    _check_partner(request)
    data = await request.json()
    result = await auto_marketplace.portal_engine.partner.insurance_quote(data["vehicle_id"], data.get("customer_id", ""))
    return json_response(result)


async def partner_financing_handler(request: web.Request) -> web.Response:
    _check_partner(request)
    data = await request.json()
    result = await auto_marketplace.portal_engine.partner.financing_quote(float(data.get("amount", 0)))
    return json_response(result)


async def partner_inspection_handler(request: web.Request) -> web.Response:
    _check_partner(request)
    data = await request.json()
    result = await auto_marketplace.portal_engine.partner.schedule_inspection(data["vehicle_id"], data.get("dealer_id", ""))
    return json_response(result)


async def partner_logistics_handler(request: web.Request) -> web.Response:
    _check_partner(request)
    data = await request.json()
    result = await auto_marketplace.portal_engine.partner.schedule_logistics(data["deal_id"], data.get("destination", ""))
    return json_response(result)


async def partner_webhook_handler(request: web.Request) -> web.Response:
    conn = _check_partner(request)
    data = await request.json()
    result = await auto_marketplace.portal_engine.partner.dispatch_webhook(conn.connection_id, data.get("event", ""), data.get("payload", {}))
    return json_response(result)


def _check_partner(request: web.Request):
    api_key = request.headers.get("X-API-Key", "")
    if not api_key and request.headers.get("Authorization", "").startswith("Bearer "):
        api_key = request.headers.get("Authorization", "")[7:]
    conn = auto_marketplace.portal_engine.partner.validate_api_key(api_key)
    if conn is None:
        raise AuthorizationError("Invalid partner API key")
    return conn


async def portal_metrics_handler(_request: web.Request) -> web.Response:
    return json_response(auto_marketplace.portal_engine.metrics())
