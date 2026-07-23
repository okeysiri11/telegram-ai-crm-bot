"""API handlers — Enterprise Integration Platform (Sprint 19.6)."""

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
    return enterprise_hub.eip


async def eip_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "enterprise_integration_platform_ready": health.get(
                "enterprise_integration_platform_ready"
            ),
            "connector_engine_ready": health.get("connector_engine_ready"),
            "adapter_layer_ready": health.get("adapter_layer_ready"),
            "sync_engine_ready": health.get("sync_engine_ready"),
            "suite": _suite().status(),
        }
    )


async def eip_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def eip_manager_handler(request: web.Request) -> web.Response:
    try:
        manager = _suite().manager
        if request.method == "GET":
            return json_response(manager.status())
        body = await _read_json(request)
        action = body.get("action", "register")
        if action == "start":
            return json_response(manager.start(integration_id=body.get("integration_id", "")), status=201)
        if action == "stop":
            return json_response(manager.stop(integration_id=body.get("integration_id", "")), status=201)
        if action == "update":
            return json_response(
                manager.update(
                    integration_id=body.get("integration_id", ""),
                    version=body.get("version", ""),
                    connection=body.get("connection") if isinstance(body.get("connection"), dict) else None,
                ),
                status=201,
            )
        if action == "journal":
            return json_response(
                manager.journal(
                    integration_id=body.get("integration_id", ""),
                    detail=body.get("detail", ""),
                ),
                status=201,
            )
        return json_response(
            manager.register(
                name=body.get("name", ""),
                protocol=body.get("protocol", "rest"),
                adapter=body.get("adapter", "custom"),
                version=body.get("version", "1.0"),
                owner=body.get("owner", "system"),
                connection=body.get("connection") if isinstance(body.get("connection"), dict) else None,
                permissions=body.get("permissions") if isinstance(body.get("permissions"), list) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def eip_engine_handler(request: web.Request) -> web.Response:
    try:
        engine = _suite().engine
        if request.method == "GET":
            return json_response(engine.status())
        body = await _read_json(request)
        action = body.get("action", "connect")
        if action == "adapt":
            return json_response(
                engine.adapt(
                    adapter=body.get("adapter", "custom"),
                    operation=body.get("operation", ""),
                    payload=body.get("payload") if isinstance(body.get("payload"), dict) else None,
                ),
                status=201,
            )
        if action == "sync":
            return json_response(
                engine.sync(
                    integration_id=body.get("integration_id", ""),
                    mode=body.get("mode", "incremental"),
                    records=int(body.get("records", 0) or 0),
                ),
                status=201,
            )
        if action == "retry":
            return json_response(
                engine.retry(
                    integration_id=body.get("integration_id", ""),
                    attempt=int(body.get("attempt", 1) or 1),
                    error=body.get("error", ""),
                    fallback_route=body.get("fallback_route", ""),
                    notify_admin=bool(body.get("notify_admin", True)),
                ),
                status=201,
            )
        return json_response(
            engine.connect(
                protocol=body.get("protocol", "rest"),
                endpoint=body.get("endpoint", ""),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else None,
                method=body.get("method", "GET"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def eip_mapping_handler(request: web.Request) -> web.Response:
    try:
        suite = _suite()
        if request.method == "GET":
            return json_response(
                {
                    "mapper": suite.mapper.status(),
                    "transformer": suite.transformer.status(),
                    "validator": suite.validator.status(),
                }
            )
        body = await _read_json(request)
        action = body.get("action", "map")
        if action == "transform":
            return json_response(
                suite.transformer.transform(
                    data=body.get("data"),
                    operation=body.get("operation", "normalize"),
                    options=body.get("options") if isinstance(body.get("options"), dict) else None,
                ),
                status=201,
            )
        if action == "validate":
            return json_response(
                suite.validator.validate(
                    data=body.get("data") if isinstance(body.get("data"), dict) else {},
                    required=body.get("required") if isinstance(body.get("required"), list) else None,
                ),
                status=201,
            )
        return json_response(
            suite.mapper.map_fields(
                source_fields=body.get("source_fields") if isinstance(body.get("source_fields"), dict) else {},
                mapping=body.get("mapping") if isinstance(body.get("mapping"), dict) else {},
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def eip_security_handler(request: web.Request) -> web.Response:
    try:
        security = _suite().security
        if request.method == "GET":
            return json_response(security.status())
        body = await _read_json(request)
        action = body.get("action", "configure")
        if action == "rotate":
            return json_response(security.rotate_token(security_id=body.get("security_id", "")), status=201)
        return json_response(
            security.configure(
                integration_id=body.get("integration_id", ""),
                method=body.get("method", "api_key"),
                secret_ref=body.get("secret_ref", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def eip_monitor_handler(request: web.Request) -> web.Response:
    try:
        monitor = _suite().monitor
        if request.method == "GET":
            return json_response(monitor.status())
        body = await _read_json(request)
        return json_response(
            monitor.snapshot(
                integration_id=body.get("integration_id", ""),
                latency_ms=float(body.get("latency_ms", 0) or 0),
                errors=int(body.get("errors", 0) or 0),
                requests=int(body.get("requests", 0) or 0),
                rate_limit_remaining=int(body.get("rate_limit_remaining", 1000) or 1000),
                sync_success_rate=float(body.get("sync_success_rate", 1) or 1),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def eip_scheduler_handler(request: web.Request) -> web.Response:
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
                integration_id=body.get("integration_id", ""),
                expression=body.get("expression", "0 * * * *"),
                sync_mode=body.get("sync_mode", "incremental"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def eip_ai_handler(request: web.Request) -> web.Response:
    try:
        ai = _suite().ai
        if request.method == "GET":
            return json_response(ai.status())
        body = await _read_json(request)
        return json_response(
            ai.assist(
                action=body.get("action", "analyze_api"),
                subject=body.get("subject", ""),
                detail=body.get("detail", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def eip_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dashboard = _suite().dashboard
        if request.method == "GET":
            return json_response(dashboard.status())
        body = await _read_json(request)
        return json_response(
            dashboard.render(dashboard_type=body.get("dashboard_type", "monitoring")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
