"""API handlers — Enterprise Organization Brain (Sprint 27.2)."""

from __future__ import annotations

from aiohttp import web

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.middleware import json_response
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError


def _handle_error(exc: Exception) -> web.Response:
    if isinstance(exc, NotFoundError):
        return json_response({"error": str(exc)}, status=404)
    if isinstance(exc, ValidationError):
        return json_response({"error": str(exc)}, status=400)
    return json_response({"error": str(exc)}, status=500)


def _suite():
    return enterprise_hub.organization_brain


async def obr_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "organization_brain_ready": health.get("organization_brain_ready"),
            "executive_board_ready": health.get("executive_board_ready"),
            "decision_engine_ready": health.get("decision_engine_ready"),
            "suite": _suite().status(),
        }
    )


async def obr_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def obr_inventory_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().inventory())
    except Exception as exc:
        return _handle_error(exc)


async def obr_dashboard_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().dashboard())
    except Exception as exc:
        return _handle_error(exc)


async def obr_organization_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().organization())
    except Exception as exc:
        return _handle_error(exc)


async def obr_board_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().board())
    except Exception as exc:
        return _handle_error(exc)


async def obr_departments_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().departments())
    except Exception as exc:
        return _handle_error(exc)


async def obr_orchestrate_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json()
        department = body.get("department")
        if not department:
            raise ValidationError("department is required")
        return json_response(
            _suite().orchestrate_department(
                department=department,
                objective=body.get("objective"),
            )
        )
    except Exception as exc:
        return _handle_error(exc)


async def obr_decisions_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json()
        topic = body.get("topic") or body.get("decision")
        if not topic:
            raise ValidationError("topic is required")
        return json_response(
            _suite().decide(
                topic=topic,
                metrics=body.get("metrics"),
                allocate=bool(body.get("allocate", True)),
            )
        )
    except Exception as exc:
        return _handle_error(exc)


async def obr_meetings_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            topic = body.get("topic")
            if not topic:
                raise ValidationError("topic is required")
            return json_response(
                _suite().meeting(topic=topic, proposals=body.get("proposals"))
            )
        return json_response(_suite().meetings())
    except Exception as exc:
        return _handle_error(exc)


async def obr_knowledge_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "POST":
            body = await request.json()
            content = body.get("content")
            if not content:
                raise ValidationError("content is required")
            return json_response(
                _suite().knowledge_write(
                    kind=body.get("kind") or "policies",
                    content=content,
                )
            )
        kind = request.rel_url.query.get("kind")
        return json_response(_suite().knowledge(kind))
    except Exception as exc:
        return _handle_error(exc)
