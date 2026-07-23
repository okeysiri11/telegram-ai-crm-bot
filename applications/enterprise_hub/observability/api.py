"""API handlers — Enterprise Observability (Sprint 19.9)."""

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
    return enterprise_hub.observability


async def obs_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "enterprise_observability_ready": health.get("enterprise_observability_ready"),
            "metrics_platform_ready": health.get("metrics_platform_ready"),
            "distributed_tracing_ready": health.get("distributed_tracing_ready"),
            "incident_management_ready": health.get("incident_management_ready"),
            "suite": _suite().status(),
        }
    )


async def obs_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def obs_metrics_handler(request: web.Request) -> web.Response:
    try:
        metrics = _suite().metrics
        if request.method == "GET":
            return json_response(metrics.status())
        body = await _read_json(request)
        return json_response(
            metrics.record(
                kind=body.get("kind", "cpu"),
                value=float(body.get("value", 0) or 0),
                labels=body.get("labels") if isinstance(body.get("labels"), dict) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def obs_healthcheck_handler(request: web.Request) -> web.Response:
    try:
        health = _suite().health
        if request.method == "GET":
            return json_response(health.status())
        body = await _read_json(request)
        return json_response(
            health.check(
                target=body.get("target", ""),
                target_type=body.get("target_type", "service"),
                status=body.get("status", "healthy"),
                detail=body.get("detail", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def obs_services_handler(request: web.Request) -> web.Response:
    try:
        services = _suite().services
        if request.method == "GET":
            return json_response(services.status())
        body = await _read_json(request)
        action = body.get("action", "register")
        if action == "health":
            return json_response(
                services.set_health(
                    service_id=body.get("service_id", ""),
                    health_status=body.get("health_status", "healthy"),
                ),
                status=201,
            )
        return json_response(
            services.register(
                name=body.get("name", ""),
                kind=body.get("kind", "microservice"),
                version=body.get("version", "1.0"),
                owners=body.get("owners") if isinstance(body.get("owners"), list) else None,
                dependencies=body.get("dependencies") if isinstance(body.get("dependencies"), list) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def obs_logs_handler(request: web.Request) -> web.Response:
    try:
        logging = _suite().logging
        if request.method == "GET":
            return json_response(logging.status())
        body = await _read_json(request)
        action = body.get("action", "write")
        if action == "search":
            return json_response(
                logging.search(
                    query=body.get("query", ""),
                    correlation_id=body.get("correlation_id", ""),
                    user=body.get("user", ""),
                    service=body.get("service", ""),
                    ai_agent=body.get("ai_agent", ""),
                ),
                status=201,
            )
        return json_response(
            logging.write(
                kind=body.get("kind", "application"),
                message=body.get("message", ""),
                service=body.get("service", ""),
                user=body.get("user", ""),
                ai_agent=body.get("ai_agent", ""),
                correlation_id=body.get("correlation_id", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def obs_tracing_handler(request: web.Request) -> web.Response:
    try:
        tracing = _suite().tracing
        if request.method == "GET":
            return json_response(tracing.status())
        body = await _read_json(request)
        action = body.get("action", "start")
        if action == "span":
            return json_response(
                tracing.span(
                    trace_id=body.get("trace_id", ""),
                    service=body.get("service", ""),
                    operation=body.get("operation", ""),
                    duration_ms=float(body.get("duration_ms", 0) or 0),
                ),
                status=201,
            )
        if action == "finish":
            return json_response(
                tracing.finish(trace_id=body.get("trace_id", ""), status=body.get("status", "ok")),
                status=201,
            )
        return json_response(
            tracing.start(name=body.get("name", ""), correlation_id=body.get("correlation_id", "")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def obs_alerts_handler(request: web.Request) -> web.Response:
    try:
        alerting = _suite().alerting
        if request.method == "GET":
            return json_response(alerting.status())
        body = await _read_json(request)
        return json_response(
            alerting.fire(
                title=body.get("title", ""),
                level=body.get("level", "warning"),
                channel=body.get("channel", "telegram"),
                service=body.get("service", ""),
                escalate=bool(body.get("escalate", False)),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def obs_incidents_handler(request: web.Request) -> web.Response:
    try:
        incidents = _suite().incidents
        if request.method == "GET":
            return json_response(incidents.status())
        body = await _read_json(request)
        action = body.get("action", "open")
        if action == "update":
            return json_response(
                incidents.update(
                    incident_id=body.get("incident_id", ""),
                    status=body.get("status", ""),
                    root_cause=body.get("root_cause", ""),
                    resolution=body.get("resolution", ""),
                    note=body.get("note", ""),
                ),
                status=201,
            )
        return json_response(
            incidents.open(
                service=body.get("service", ""),
                severity=body.get("severity", "error"),
                owner=body.get("owner", "ops"),
                root_cause=body.get("root_cause", ""),
                sla_minutes=int(body.get("sla_minutes", 60) or 60),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def obs_diagnostics_handler(request: web.Request) -> web.Response:
    try:
        diagnostics = _suite().diagnostics
        if request.method == "GET":
            return json_response(diagnostics.status())
        body = await _read_json(request)
        return json_response(
            diagnostics.analyze(
                subject=body.get("subject", ""),
                error=body.get("error", ""),
                logs=body.get("logs") if isinstance(body.get("logs"), list) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def obs_monitoring_handler(request: web.Request) -> web.Response:
    try:
        monitoring = _suite().monitoring
        if request.method == "GET":
            return json_response(monitoring.status())
        body = await _read_json(request)
        action = body.get("action", "collect")
        if action == "export":
            return json_response(
                monitoring.export(
                    exporter=body.get("exporter", "prometheus"),
                    payload=body.get("payload") if isinstance(body.get("payload"), dict) else None,
                ),
                status=201,
            )
        return json_response(
            monitoring.collect(
                collector=body.get("collector", "system"),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def obs_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dashboard = _suite().dashboard
        if request.method == "GET":
            return json_response(dashboard.status())
        body = await _read_json(request)
        return json_response(
            dashboard.render(dashboard_type=body.get("dashboard_type", "platform")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
