"""API handlers — Enterprise Onboarding (Sprint 22.9)."""

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
    return enterprise_hub.onboarding


async def eon_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "onboarding_ready": health.get("onboarding_ready"),
            "data_migration_ready": health.get("data_migration_ready"),
            "validation_ready": health.get("validation_ready"),
            "go_live_ready": health.get("go_live_ready"),
            "suite": _suite().status(),
        }
    )


async def eon_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def eon_wizard_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        if body.get("wizard_id"):
            return json_response(
                _suite().advance_wizard(
                    wizard_id=body["wizard_id"],
                    step_data=body.get("step_data") or body,
                )
            )
        return json_response(
            _suite().start_wizard(
                company_name=body.get("company_name", ""),
                industry=body.get("industry", "beauty"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def eon_import_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().import_data(
                entity=body.get("entity", ""),
                source=body.get("source", "csv"),
                rows=list(body.get("rows") or []),
                payload=body.get("payload"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def eon_validate_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().validate_import(
                import_id=body.get("import_id"),
                entity=body.get("entity", ""),
                rows=body.get("rows"),
            )
        )
    except Exception as exc:
        return _handle_error(exc)


async def eon_assistant_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().migration_advise(
                columns=list(body.get("columns") or []),
                target_fields=list(body.get("target_fields") or []),
                validation_report=body.get("validation_report"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def eon_config_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(_suite().apply_initial_config(wizard_id=body.get("wizard_id", "")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def eon_readiness_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request) if request.method == "POST" else {}
        wizard_id = body.get("wizard_id") or request.rel_url.query.get("wizard_id", "")
        return json_response(_suite().analyze_readiness(wizard_id=wizard_id))
    except Exception as exc:
        return _handle_error(exc)


async def eon_go_live_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().go_live(
                wizard_id=body.get("wizard_id", ""),
                completed=body.get("completed"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
