"""API handlers — Enterprise Process Mining Platform (Sprint 20.10)."""

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
    return enterprise_hub.process_mining


async def epm_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "process_mining_ready": health.get("process_mining_ready"),
            "process_discovery_ready": health.get("process_discovery_ready"),
            "conformance_ready": health.get("conformance_ready"),
            "bottleneck_detection_ready": health.get("bottleneck_detection_ready"),
            "suite": _suite().status(),
        }
    )


async def epm_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def epm_events_handler(request: web.Request) -> web.Response:
    try:
        suite = _suite()
        if request.method == "GET":
            return json_response({**suite.collector.status(), **suite.normalizer.status()})
        body = await _read_json(request)
        if isinstance(body.get("events"), list):
            created = suite.collector.collect_batch(body["events"])
            suite.normalizer.normalize()
            return json_response({"events": created}, status=201)
        created = suite.collector.collect(
            source=body.get("source", "crm"),
            activity=body.get("activity", ""),
            case_id=body.get("case_id", ""),
            actor=body.get("actor", "system"),
            ts=body.get("ts"),
            payload=body.get("payload") if isinstance(body.get("payload"), dict) else None,
        )
        suite.normalizer.normalize(event_id=created["event_id"])
        return json_response(created, status=201)
    except Exception as exc:
        return _handle_error(exc)


async def epm_discover_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(_suite().discovery.discover(name=body.get("name", "discovered-process")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def epm_conformance_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().conformance.check(
                process_id=body.get("process_id", ""),
                reference_steps=body.get("reference_steps") if isinstance(body.get("reference_steps"), list) else None,
                sla_hours=float(body.get("sla_hours", 48) or 48),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def epm_bottlenecks_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(_suite().bottlenecks.detect(process_id=body.get("process_id", "")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def epm_optimize_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().optimization.optimize(
                process_id=body.get("process_id", ""),
                bottleneck_id=body.get("bottleneck_id"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def epm_dashboard_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request) if request.method == "POST" else {}
        process_id = body.get("process_id") or request.rel_url.query.get("process_id", "")
        return json_response(_suite().dashboard.render(process_id=process_id))
    except Exception as exc:
        return _handle_error(exc)


async def epm_analytics_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request) if request.method == "POST" else {}
        process_id = body.get("process_id") or request.rel_url.query.get("process_id", "")
        suite = _suite()
        return json_response(
            {
                "kpi": suite.kpi.report(process_id=process_id),
                "efficiency": suite.efficiency.report(process_id=process_id),
                "sla": suite.sla.report(process_id=process_id),
                "recommendations": suite.recommendations.report(process_id=process_id),
            }
        )
    except Exception as exc:
        return _handle_error(exc)
