"""API handlers — Cafe Operating System (Sprint 31.0)."""

from __future__ import annotations

from aiohttp import web

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.middleware import json_response
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError


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
    return enterprise_hub.cafe_os


async def cos_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "cafe_os_ready": health.get("cafe_os_ready"),
            "cafe_kitchen_ready": health.get("cafe_kitchen_ready"),
            "cafe_dashboard_ready": health.get("cafe_dashboard_ready"),
            "suite": _suite().status(),
        }
    )


async def cos_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def cos_tables_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            return json_response(_suite().list_tables())
        body = await _read_json(request)
        return json_response(
            _suite().create_table(
                name=body.get("name", ""),
                seats=int(body.get("seats", 2) or 2),
                zone=body.get("zone", "main"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def cos_menu_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            return json_response(_suite().list_menu())
        body = await _read_json(request)
        return json_response(
            _suite().create_menu_item(
                name=body.get("name", ""),
                category=body.get("category", "food"),
                price=float(body.get("price", 0) or 0),
                prep_min=int(body.get("prep_min", 5) or 5),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def cos_staff_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().create_staff(
                name=body.get("name", ""),
                role=body.get("role", "waiter"),
                station=body.get("station", "floor"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def cos_customers_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().create_customer(
                name=body.get("name", ""),
                preferences=body.get("preferences"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def cos_reservations_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        if body.get("reservation_id") and body.get("status"):
            return json_response(
                _suite().transition_reservation(
                    reservation_id=body["reservation_id"],
                    status=body["status"],
                )
            )
        return json_response(
            _suite().reserve_table(
                table_id=body.get("table_id", ""),
                customer_id=body.get("customer_id", ""),
                party_size=int(body.get("party_size", body.get("covers", 2)) or 2),
                start=body.get("start", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def cos_orders_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().place_order(
                customer_id=body.get("customer_id", ""),
                table_id=body.get("table_id", ""),
                items=list(body.get("items") or []),
                reservation_id=body.get("reservation_id", ""),
                channel=body.get("channel", "dine_in"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def cos_kitchen_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            return json_response(_suite().kitchen_queue())
        body = await _read_json(request)
        return json_response(
            _suite().transition_kitchen(
                ticket_id=body.get("ticket_id", ""),
                status=body.get("status", "preparing"),
            )
        )
    except Exception as exc:
        return _handle_error(exc)


async def cos_qr_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request) if request.method == "POST" else {}
        return json_response(
            _suite().qr_menu(restaurant_id=body.get("restaurant_id", "")),
            status=201 if request.method == "POST" else 200,
        )
    except Exception as exc:
        return _handle_error(exc)


async def cos_delivery_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().create_delivery(
                order_id=body.get("order_id", ""),
                customer_id=body.get("customer_id", ""),
                address=body.get("address", "Pilot Ave 1"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def cos_crm_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().crm_update(
                customer_id=body.get("customer_id", ""),
                event=body.get("event", "visit"),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else {},
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def cos_dashboard_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().dashboard())
    except Exception as exc:
        return _handle_error(exc)
