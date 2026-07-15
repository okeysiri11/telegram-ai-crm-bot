# REST API — CRM marketplace endpoints with JWT auth.

from __future__ import annotations

import logging
import time
from typing import Any

from aiohttp import web

logger = logging.getLogger(__name__)


def _json_error(message: str, status: int = 400) -> web.Response:
    return web.json_response({"ok": False, "error": message}, status=status)


def _encode_jwt(payload: dict[str, Any]) -> str:
    try:
        import jwt
    except ImportError:
        # Minimal fallback token (not cryptographically strong — for offline tests)
        import base64
        import json

        raw = json.dumps(payload).encode()
        return "dev." + base64.urlsafe_b64encode(raw).decode().rstrip("=")

    from config import JWT_ALGORITHM, JWT_EXPIRE_MINUTES, JWT_SECRET

    data = dict(payload)
    data["exp"] = int(time.time()) + JWT_EXPIRE_MINUTES * 60
    return jwt.encode(data, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _decode_jwt(token: str) -> dict[str, Any] | None:
    try:
        import jwt
        from config import JWT_ALGORITHM, JWT_SECRET

        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except ImportError:
        import base64
        import json

        if not token.startswith("dev."):
            return None
        raw = token[4:] + "=" * (-len(token[4:]) % 4)
        return json.loads(base64.urlsafe_b64decode(raw.encode()))
    except Exception:
        return None


def require_auth(handler):
    async def wrapper(request: web.Request) -> web.Response:
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return _json_error("Missing Bearer token", 401)
        claims = _decode_jwt(auth.removeprefix("Bearer ").strip())
        if claims is None:
            return _json_error("Invalid token", 401)
        request["jwt"] = claims
        return await handler(request)

    return wrapper


async def api_auth_handler(request: web.Request) -> web.Response:
    body = await request.json() if request.can_read_body else {}
    telegram_id = body.get("telegram_id")
    api_key = body.get("api_key") or request.headers.get("X-API-Key")
    from config import JWT_SECRET, OWNER_ID

    if api_key != JWT_SECRET and telegram_id != OWNER_ID:
        # Allow owner telegram id OR matching JWT_SECRET as simple bootstrap auth
        if not api_key:
            return _json_error("Unauthorized", 401)
        if api_key != JWT_SECRET:
            return _json_error("Unauthorized", 401)

    token = _encode_jwt({"sub": str(telegram_id or "api"), "role": "ADMIN"})
    return web.json_response({"ok": True, "access_token": token, "token_type": "Bearer"})


@require_auth
async def api_leads_list(request: web.Request) -> web.Response:
    from services.pg_client_request_crm_engine import ClientRequestCrmEngineV1

    status = request.query.get("status")
    if status == "NEW":
        leads = await ClientRequestCrmEngineV1.list_new_leads(limit=50)
    else:
        leads = await ClientRequestCrmEngineV1.list_new_leads(limit=50)
    return web.json_response({"ok": True, "items": leads})


@require_auth
async def api_lead_detail(request: web.Request) -> web.Response:
    from services.pg_client_request_crm_engine import ClientRequestCrmEngineV1

    number = request.match_info["request_number"]
    detail = await ClientRequestCrmEngineV1.get_request_detail(number)
    if detail is None:
        return _json_error("Not found", 404)
    return web.json_response({"ok": True, "item": detail})


@require_auth
async def api_clients_list(request: web.Request) -> web.Response:
    from services.pg_client_request_crm_engine import ClientRequestCrmEngineV1

    leads = await ClientRequestCrmEngineV1.list_new_leads(limit=100)
    clients = {}
    for lead in leads:
        tid = lead.get("client_telegram_id")
        if tid and tid not in clients:
            clients[tid] = {
                "telegram_id": tid,
                "username": lead.get("client_username"),
                "phone": lead.get("client_phone"),
            }
    return web.json_response({"ok": True, "items": list(clients.values())})


@require_auth
async def api_managers_list(request: web.Request) -> web.Response:
    from config import DEFAULT_AUTO_MANAGER_ID, DEFAULT_DEALER_MANAGER_ID, OWNER_ID

    items = []
    for tid, role in (
        (OWNER_ID, "OWNER"),
        (DEFAULT_AUTO_MANAGER_ID, "AUTO_MANAGER"),
        (DEFAULT_DEALER_MANAGER_ID, "DEALER_MANAGER"),
    ):
        if tid:
            items.append({"telegram_id": tid, "role": role})
    return web.json_response({"ok": True, "items": items})


@require_auth
async def api_inventory_list(request: web.Request) -> web.Response:
    from services.pg_marketplace_inventory_engine import InventoryEngineV1

    q = request.query
    items = await InventoryEngineV1.search(
        brand=q.get("brand"),
        model=q.get("model"),
        year_from=int(q["year_from"]) if q.get("year_from") else None,
        year_to=int(q["year_to"]) if q.get("year_to") else None,
        price_from=float(q["price_from"]) if q.get("price_from") else None,
        price_to=float(q["price_to"]) if q.get("price_to") else None,
        fuel=q.get("fuel"),
        transmission=q.get("transmission"),
        mileage_max=int(q["mileage_max"]) if q.get("mileage_max") else None,
        city=q.get("city"),
        limit=int(q.get("limit", "50")),
    )
    return web.json_response({"ok": True, "items": items})


@require_auth
async def api_inventory_create(request: web.Request) -> web.Response:
    from services.pg_marketplace_inventory_engine import InventoryEngineV1

    body = await request.json()
    item = await InventoryEngineV1.create(**body)
    return web.json_response({"ok": True, "item": item}, status=201)


@require_auth
async def api_recommendations(request: web.Request) -> web.Response:
    from services.pg_marketplace_inventory_engine import InventoryEngineV1

    q = request.query
    result = await InventoryEngineV1.recommend(
        brand=q.get("brand"),
        model=q.get("model"),
        year=int(q["year"]) if q.get("year") else None,
        price=float(q["price"]) if q.get("price") else None,
        city=q.get("city"),
        fuel=q.get("fuel"),
    )
    return web.json_response({"ok": True, **result})


@require_auth
async def api_analytics(request: web.Request) -> web.Response:
    from services.pg_owner_analytics_engine import OwnerAnalyticsEngineV1

    metrics = await OwnerAnalyticsEngineV1.get_dashboard_metrics()
    return web.json_response({"ok": True, "metrics": metrics})


async def openapi_spec_handler(request: web.Request) -> web.Response:
    spec = {
        "openapi": "3.0.3",
        "info": {
            "title": "Auto CRM Marketplace API",
            "version": "1.0.0",
            "description": "REST API for leads, clients, managers, inventory, analytics",
        },
        "components": {
            "securitySchemes": {
                "bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
            }
        },
        "security": [{"bearerAuth": []}],
        "paths": {
            "/api/auth/token": {"post": {"summary": "Issue JWT"}},
            "/api/leads": {"get": {"summary": "List leads"}},
            "/api/leads/{request_number}": {"get": {"summary": "Lead detail"}},
            "/api/clients": {"get": {"summary": "List clients"}},
            "/api/managers": {"get": {"summary": "List managers"}},
            "/api/inventory": {
                "get": {"summary": "Search inventory"},
                "post": {"summary": "Create inventory item"},
            },
            "/api/recommendations": {"get": {"summary": "Recommendations"}},
            "/api/analytics": {"get": {"summary": "Owner analytics"}},
        },
    }
    return web.json_response(spec)


async def swagger_ui_handler(request: web.Request) -> web.Response:
    html = """<!DOCTYPE html>
<html><head><title>Auto CRM API</title>
<link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
</head><body>
<div id="swagger-ui"></div>
<script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
<script>
SwaggerUIBundle({url: '/api/openapi.json', dom_id: '#swagger-ui'});
</script>
</body></html>"""
    return web.Response(text=html, content_type="text/html")


def register_crm_api_routes(app: web.Application) -> None:
    app.router.add_post("/api/auth/token", api_auth_handler)
    app.router.add_get("/api/leads", api_leads_list)
    app.router.add_get("/api/leads/{request_number}", api_lead_detail)
    app.router.add_get("/api/clients", api_clients_list)
    app.router.add_get("/api/managers", api_managers_list)
    app.router.add_get("/api/inventory", api_inventory_list)
    app.router.add_post("/api/inventory", api_inventory_create)
    app.router.add_get("/api/recommendations", api_recommendations)
    app.router.add_get("/api/analytics", api_analytics)
    app.router.add_get("/api/openapi.json", openapi_spec_handler)
    app.router.add_get("/api/docs", swagger_ui_handler)
    app.router.add_get("/swagger", swagger_ui_handler)
