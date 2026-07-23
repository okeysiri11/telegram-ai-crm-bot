"""API handlers — Enterprise Event Platform (Sprint 20.5)."""

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
    return enterprise_hub.event_platform


async def evp_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "event_platform_ready": health.get("event_platform_ready"),
            "event_bus_ready": health.get("event_bus_ready"),
            "event_replay_ready": health.get("event_replay_ready"),
            "dead_letter_queue_ready": health.get("dead_letter_queue_ready"),
            "suite": _suite().status(),
        }
    )


async def evp_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def evp_publish_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().bus.publish(
                event_type=body.get("event_type", ""),
                source=body.get("source", "custom"),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else None,
                author=body.get("author", "system"),
                severity=body.get("severity", "normal"),
                version=body.get("version", "1.0"),
                idempotency_key=body.get("idempotency_key"),
                fail_subscribers=body.get("fail_subscribers") if isinstance(body.get("fail_subscribers"), list) else None,
                max_retries=int(body.get("max_retries", 2) or 2),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def evp_subscribe_handler(request: web.Request) -> web.Response:
    try:
        subs = _suite().subscriptions
        if request.method == "GET":
            return json_response(subs.status())
        body = await _read_json(request)
        return json_response(
            subs.subscribe(
                subscriber=body.get("subscriber", ""),
                event_types=body.get("event_types") if isinstance(body.get("event_types"), list) else [],
                filter_severity=body.get("filter_severity"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def evp_events_handler(request: web.Request) -> web.Response:
    try:
        store = _suite().event_store
        if request.method == "GET":
            return json_response({"events": store.list_all(), **store.status()})
        body = await _read_json(request)
        return json_response(
            store.append(
                event_type=body.get("event_type", ""),
                source=body.get("source", "custom"),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else None,
                author=body.get("author", "system"),
                severity=body.get("severity", "normal"),
                version=body.get("version", "1.0"),
                idempotency_key=body.get("idempotency_key"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def evp_replay_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().replay.replay(
                event_ids=body.get("event_ids") if isinstance(body.get("event_ids"), list) else None,
                from_sequence=body.get("from_sequence"),
                to_sequence=body.get("to_sequence"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def evp_dlq_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().dlq.status())
    except Exception as exc:
        return _handle_error(exc)


async def evp_schemas_handler(request: web.Request) -> web.Response:
    try:
        schemas = _suite().schemas
        if request.method == "GET":
            return json_response(schemas.status())
        body = await _read_json(request)
        action = (body.get("action") or "register").lower()
        if action == "validate":
            return json_response(
                schemas.validate_payload(
                    schema_id=body.get("schema_id", ""),
                    payload=body.get("payload") if isinstance(body.get("payload"), dict) else {},
                ),
                status=201,
            )
        return json_response(
            schemas.register(
                event_type=body.get("event_type", ""),
                version=body.get("version", "1.0"),
                fields=body.get("fields") if isinstance(body.get("fields"), list) else None,
                compatible_with=body.get("compatible_with") if isinstance(body.get("compatible_with"), list) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def evp_dashboard_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().dashboard())
    except Exception as exc:
        return _handle_error(exc)


async def evp_analytics_handler(request: web.Request) -> web.Response:
    try:
        suite = _suite()
        kind = request.rel_url.query.get("kind", "statistics")
        if request.method == "POST":
            body = await _read_json(request)
            kind = body.get("kind", kind)
        if kind == "throughput":
            return json_response(suite.throughput.report())
        if kind == "latency":
            return json_response(suite.latency.report())
        return json_response(suite.statistics.report())
    except Exception as exc:
        return _handle_error(exc)
