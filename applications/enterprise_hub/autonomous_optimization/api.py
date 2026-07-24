"""API handlers — Autonomous Optimization (Sprint 24.6)."""

from __future__ import annotations

import uuid

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
    return enterprise_hub.autonomous_optimization


async def eoe_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "autonomous_optimization_ready": health.get("autonomous_optimization_ready"),
            "process_optimizer_ready": health.get("process_optimizer_ready"),
            "revenue_optimizer_ready": health.get("revenue_optimizer_ready"),
            "owner_optimization_ready": health.get("owner_optimization_ready"),
            "suite": _suite().status(),
        }
    )


async def eoe_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def eoe_scan_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(_suite().scan(signals=body.get("signals")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def eoe_propose_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().propose(
                opportunity_id=body.get("opportunity_id") or f"opp_{uuid.uuid4().hex[:8]}",
                category=body.get("category", "process"),
                title=body.get("title", ""),
                priority=body.get("priority", "medium"),
                business_value=float(body.get("business_value", 0)),
                expected_roi=float(body.get("expected_roi", 0)),
                confidence=float(body.get("confidence", 0.7)),
                risk_score=float(body.get("risk_score", 0.3)),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def eoe_opportunities_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().list_opportunities())
    except Exception as exc:
        return _handle_error(exc)


async def eoe_owner_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().owner_decide(
                action=body.get("action", ""),
                actor=body.get("actor", ""),
                opportunity_id=body.get("opportunity_id", ""),
                modifications=body.get("modifications"),
                notes=body.get("notes", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def eoe_verify_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().verify(
                opportunity_id=body.get("opportunity_id", ""),
                expected=float(body.get("expected", 0)),
                actual=float(body.get("actual", 0)),
                confirmed=bool(body.get("confirmed", False)),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def eoe_dashboard_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().owner_dashboard())
    except Exception as exc:
        return _handle_error(exc)
