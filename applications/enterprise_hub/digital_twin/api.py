"""API handlers — Enterprise Digital Twin Platform (Sprint 20.8)."""

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
    return enterprise_hub.digital_twin


async def edt_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "digital_twin_ready": health.get("digital_twin_ready"),
            "twin_registry_ready": health.get("twin_registry_ready"),
            "realtime_sync_ready": health.get("realtime_sync_ready"),
            "twin_analytics_ready": health.get("twin_analytics_ready"),
            "suite": _suite().status(),
        }
    )


async def edt_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def edt_twins_handler(request: web.Request) -> web.Response:
    try:
        suite = _suite()
        if request.method == "GET":
            twin_type = request.rel_url.query.get("type")
            return json_response({"twins": suite.registry.list_all(twin_type=twin_type), **suite.registry.status()})
        body = await _read_json(request)
        return json_response(
            suite.registry.register(
                name=body.get("name", ""),
                twin_type=body.get("twin_type", "custom"),
                owner=body.get("owner", "system"),
                state=body.get("state") if isinstance(body.get("state"), dict) else None,
                access=body.get("access", "internal"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def edt_state_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().states.update_state(
                twin_id=body.get("twin_id", ""),
                state=body.get("state") if isinstance(body.get("state"), dict) else {},
                actor=body.get("actor", "system"),
                source=body.get("source", "manual"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def edt_relationships_handler(request: web.Request) -> web.Response:
    try:
        suite = _suite()
        if request.method == "GET":
            root = request.rel_url.query.get("root_id")
            return json_response(suite.relationships.graph(root_id=root))
        body = await _read_json(request)
        return json_response(
            suite.relationships.link(
                source_id=body.get("source_id", ""),
                target_id=body.get("target_id", ""),
                kind=body.get("kind", "depends_on"),
                label=body.get("label", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def edt_sync_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().sync.ingest(
                source=body.get("source", "event_bus"),
                event_type=body.get("event_type", "Updated"),
                twin_id=body.get("twin_id", ""),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def edt_timeline_handler(request: web.Request) -> web.Response:
    try:
        suite = _suite()
        if request.method == "GET":
            twin_id = request.rel_url.query.get("twin_id", "")
            return json_response({"history": suite.timeline.history(twin_id=twin_id), **suite.timeline.status()})
        body = await _read_json(request)
        return json_response(
            suite.timeline.append(
                twin_id=body.get("twin_id", ""),
                event=body.get("event", ""),
                actor=body.get("actor", "system"),
                detail=body.get("detail") if isinstance(body.get("detail"), dict) else None,
                ai_decision=bool(body.get("ai_decision", False)),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def edt_snapshots_handler(request: web.Request) -> web.Response:
    try:
        suite = _suite()
        if request.method == "GET":
            return json_response(suite.snapshots.status())
        body = await _read_json(request)
        action = (body.get("action") or "capture").lower()
        if action == "capture":
            return json_response(
                suite.snapshots.capture(kind=body.get("kind", "manual"), label=body.get("label", ""), actor=body.get("actor", "system")),
                status=201,
            )
        if action == "restore":
            return json_response(suite.snapshots.restore(snapshot_id=body.get("snapshot_id", "")), status=201)
        if action == "compare":
            return json_response(
                suite.snapshots.compare(snapshot_a=body.get("snapshot_a", ""), snapshot_b=body.get("snapshot_b", "")),
                status=201,
            )
        raise ValidationError(f"unknown action: {action}")
    except Exception as exc:
        return _handle_error(exc)


async def edt_visualize_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request) if request.method == "POST" else {}
        view = body.get("view") or request.rel_url.query.get("view", "organization")
        root_id = body.get("root_id") or request.rel_url.query.get("root_id")
        return json_response(_suite().visualization.render(view=view, root_id=root_id))
    except Exception as exc:
        return _handle_error(exc)


async def edt_analytics_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().analytics())
    except Exception as exc:
        return _handle_error(exc)


async def edt_prediction_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().predictions.build(
                twin_ids=body.get("twin_ids") if isinstance(body.get("twin_ids"), list) else None,
                horizon=body.get("horizon", "7d"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
