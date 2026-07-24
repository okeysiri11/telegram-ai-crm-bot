"""API handlers — Workflow Intelligence (Sprint 24.1)."""

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
    return enterprise_hub.workflow_intelligence


async def wfi_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "workflow_intelligence_ready": health.get("workflow_intelligence_ready"),
            "visual_designer_ready": health.get("visual_designer_ready"),
            "ai_execution_ready": health.get("ai_execution_ready"),
            "workflow_library_ready": health.get("workflow_library_ready"),
            "suite": _suite().status(),
        }
    )


async def wfi_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def wfi_workflow_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        if body.get("from_library"):
            return json_response(
                _suite().from_library(industry=body.get("industry", "beauty"), workflow_id=body.get("workflow_id")),
                status=201,
            )
        return json_response(
            _suite().create_workflow(
                workflow_id=body.get("workflow_id") or f"wf_{body.get('name', 'new').replace(' ', '_').lower()}",
                name=body.get("name", ""),
                description=body.get("description", ""),
                industry=body.get("industry", "beauty"),
                version=body.get("version", "1.0"),
                owner=body.get("owner", "platform_owner"),
                status=body.get("status", "draft"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def wfi_design_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().design_node(
                workflow_id=body.get("workflow_id", ""),
                node_type=body.get("node_type", ""),
                config=body.get("config"),
            )
        )
    except Exception as exc:
        return _handle_error(exc)


async def wfi_policy_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(_suite().set_policy(workflow_id=body.get("workflow_id", ""), policy=body.get("policy", "")))
    except Exception as exc:
        return _handle_error(exc)


async def wfi_analyze_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(_suite().analyze(workflow_id=body.get("workflow_id", "")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def wfi_execute_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().execute(
                workflow_id=body.get("workflow_id", ""),
                mode=body.get("mode", "async"),
                owner_approved=bool(body.get("owner_approved", False)),
                manager_approved=bool(body.get("manager_approved", False)),
                simulate=bool(body.get("simulate", False)),
                actor=body.get("actor", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def wfi_analytics_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request) if request.method == "POST" else {}
        workflow_id = body.get("workflow_id") or request.rel_url.query.get("workflow_id")
        return json_response(_suite().analytics(workflow_id=workflow_id or None))
    except Exception as exc:
        return _handle_error(exc)


async def wfi_catalog_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().catalog())
    except Exception as exc:
        return _handle_error(exc)


async def wfi_invoke_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(_suite().invoke_module(module=body.get("module", ""), action=body.get("action", "ping")))
    except Exception as exc:
        return _handle_error(exc)
