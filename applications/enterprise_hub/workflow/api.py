"""API handlers — Enterprise Workflow & Business Process Engine (Sprint 19.5)."""

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
    return enterprise_hub.workflow


async def wf_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "enterprise_workflow_ready": health.get("enterprise_workflow_ready"),
            "workflow_builder_ready": health.get("workflow_builder_ready"),
            "approval_engine_ready": health.get("approval_engine_ready"),
            "workflow_scheduler_ready": health.get("workflow_scheduler_ready"),
            "suite": _suite().status(),
        }
    )


async def wf_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def wf_manager_handler(request: web.Request) -> web.Response:
    try:
        manager = _suite().manager
        if request.method == "GET":
            return json_response(manager.status())
        body = await _read_json(request)
        action = body.get("action", "create")
        if action == "add_block":
            return json_response(
                manager.add_block(
                    workflow_id=body.get("workflow_id", ""),
                    block_type=body.get("block_type", "notification"),
                    config=body.get("config") if isinstance(body.get("config"), dict) else None,
                ),
                status=201,
            )
        if action == "publish":
            return json_response(manager.publish(workflow_id=body.get("workflow_id", "")), status=201)
        if action == "version":
            return json_response(
                manager.version(workflow_id=body.get("workflow_id", ""), note=body.get("note", "")),
                status=201,
            )
        return json_response(
            manager.create(
                name=body.get("name", ""),
                trigger=body.get("trigger", "api"),
                blocks=body.get("blocks") if isinstance(body.get("blocks"), list) else None,
                module=body.get("module", "enterprise"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def wf_engine_handler(request: web.Request) -> web.Response:
    try:
        engine = _suite().engine
        if request.method == "GET":
            return json_response(engine.status())
        body = await _read_json(request)
        return json_response(
            engine.run(
                workflow_id=body.get("workflow_id", ""),
                trigger=body.get("trigger", ""),
                name=body.get("name", ""),
                executor=body.get("executor", "system"),
                context=body.get("context") if isinstance(body.get("context"), dict) else None,
                blocks=body.get("blocks") if isinstance(body.get("blocks"), list) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def wf_scheduler_handler(request: web.Request) -> web.Response:
    try:
        scheduler = _suite().scheduler
        if request.method == "GET":
            return json_response(scheduler.status())
        body = await _read_json(request)
        action = body.get("action", "schedule")
        if action == "fire":
            return json_response(scheduler.fire(schedule_id=body.get("schedule_id", "")), status=201)
        return json_response(
            scheduler.schedule(
                workflow_id=body.get("workflow_id", ""),
                kind=body.get("kind", "cron"),
                expression=body.get("expression", ""),
                delay_seconds=int(body.get("delay_seconds", 0) or 0),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def wf_templates_handler(request: web.Request) -> web.Response:
    try:
        templates = _suite().templates
        if request.method == "GET":
            return json_response(templates.status())
        body = await _read_json(request)
        return json_response(
            templates.instantiate(kind=body.get("kind", "crm_lead_processing"), name=body.get("name", "")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def wf_history_handler(request: web.Request) -> web.Response:
    try:
        history = _suite().history
        if request.method == "GET":
            eid = request.rel_url.query.get("execution_id", "")
            if eid:
                return json_response(history.get(execution_id=eid))
            return json_response({"items": history.list_recent(), **history.status()})
        body = await _read_json(request)
        return json_response(history.get(execution_id=body.get("execution_id", "")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def wf_events_handler(request: web.Request) -> web.Response:
    try:
        events = _suite().events
        if request.method == "GET":
            return json_response(events.status())
        body = await _read_json(request)
        return json_response(
            events.emit(
                event_type=body.get("event_type", ""),
                workflow_id=body.get("workflow_id", ""),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def wf_optimization_handler(request: web.Request) -> web.Response:
    try:
        optimization = _suite().optimization
        if request.method == "GET":
            return json_response(optimization.status())
        body = await _read_json(request)
        return json_response(optimization.analyze(workflow_id=body.get("workflow_id", "")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def wf_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dashboard = _suite().dashboard
        if request.method == "GET":
            return json_response(dashboard.status())
        body = await _read_json(request)
        return json_response(
            dashboard.render(dashboard_type=body.get("dashboard_type", "performance")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def wf_validator_handler(request: web.Request) -> web.Response:
    try:
        validator = _suite().validator
        if request.method == "GET":
            return json_response(validator.status())
        body = await _read_json(request)
        return json_response(validator.validate(workflow_id=body.get("workflow_id", "")), status=201)
    except Exception as exc:
        return _handle_error(exc)
