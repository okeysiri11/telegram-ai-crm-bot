"""API handlers — Enterprise Product Intelligence (Sprint 22.0)."""

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
    return enterprise_hub.product_intelligence


async def epi_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "product_intelligence_ready": health.get("product_intelligence_ready"),
            "feedback_collector_ready": health.get("feedback_collector_ready"),
            "expert_board_ready": health.get("expert_board_ready"),
            "owner_approval_ready": health.get("owner_approval_ready"),
            "suite": _suite().status(),
        }
    )


async def epi_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def epi_feedback_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().ingest(
                source=body.get("source", ""),
                title=body.get("title", ""),
                description=body.get("description", ""),
                module=body.get("module", "enterprise_hub"),
                severity=body.get("severity", "medium"),
                metadata=body.get("metadata") if isinstance(body.get("metadata"), dict) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def epi_analyze_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().analyze(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def epi_report_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().generate_report(
                problem=body.get("problem", ""),
                proposal=body.get("proposal", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def epi_decide_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().owner_decide(
                report_id=body.get("report_id", ""),
                decision=body.get("decision", ""),
                owner_id=body.get("owner_id", ""),
                changes=body.get("changes", ""),
                notes=body.get("notes", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def epi_validate_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().validate_release(report_id=body.get("report_id", "")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def epi_knowledge_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().knowledge_history())
    except Exception as exc:
        return _handle_error(exc)
