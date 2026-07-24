"""API handlers — Enterprise Commerce Core (Sprint 22.7)."""

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
    return enterprise_hub.commerce_core


async def eco_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "commerce_core_ready": health.get("commerce_core_ready"),
            "pos_ready": health.get("pos_ready"),
            "loyalty_commerce_ready": health.get("loyalty_commerce_ready"),
            "payment_gateway_ready": health.get("payment_gateway_ready"),
            "suite": _suite().status(),
        }
    )


async def eco_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def eco_pos_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().open_pos(
                cashier_id=body.get("cashier_id", "cashier"),
                industry=body.get("industry", "beauty"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def eco_sale_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        if body.get("refund") and body.get("sale_id"):
            return json_response(
                _suite().refund_sale(sale_id=body["sale_id"], amount=body.get("amount")),
                status=201,
            )
        return json_response(
            _suite().create_sale(
                lines=list(body.get("lines") or []),
                payments=list(body.get("payments") or []),
                customer_id=body.get("customer_id", ""),
                mode=body.get("mode", "full"),
                industry=body.get("industry", "beauty"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def eco_certificate_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        if body.get("redeem") and body.get("certificate_id"):
            return json_response(
                _suite().redeem_certificate(
                    certificate_id=body["certificate_id"],
                    amount=float(body.get("amount", 0) or 0),
                ),
                status=201,
            )
        return json_response(
            _suite().issue_certificate(
                face_value=float(body.get("face_value", 0) or 0),
                customer_id=body.get("customer_id", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def eco_membership_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().create_membership(
                customer_id=body.get("customer_id", ""),
                visits_limit=int(body.get("visits_limit", 10) or 10),
                name=body.get("name", "standard"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def eco_loyalty_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().loyalty_profile(
                customer_id=body.get("customer_id", ""),
                points=float(body.get("points", 0) or 0),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def eco_payment_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().charge(
                provider=body.get("provider", ""),
                amount=float(body.get("amount", 0) or 0),
                currency=body.get("currency", "USD"),
                reference=body.get("reference", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def eco_advisor_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().advise())
    except Exception as exc:
        return _handle_error(exc)
