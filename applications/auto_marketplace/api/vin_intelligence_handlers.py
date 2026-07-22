"""API handlers — VIN Intelligence (Sprint 13.1)."""

from __future__ import annotations

from aiohttp import web

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.middleware import json_response
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError


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
    return auto_marketplace.vin_intelligence


async def vi_health_handler(request: web.Request) -> web.Response:
    health = auto_marketplace.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "vin_intelligence_ready": health.get("vin_intelligence_ready"),
            "digital_passport_ready": health.get("digital_passport_ready"),
            "vehicle_history_ai_ready": health.get("vehicle_history_ai_ready"),
            "fraud_detection_ready": health.get("fraud_detection_ready"),
            "suite": _suite().status(),
        }
    )


async def vi_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def vi_decode_handler(request: web.Request) -> web.Response:
    try:
        decoder = _suite().decoder
        if request.method == "GET":
            wmi = request.rel_url.query.get("wmi")
            if wmi:
                return json_response(decoder.manufacturer_lookup(wmi))
            return json_response(decoder.status())
        body = await _read_json(request)
        action = body.get("action", "decode")
        if action == "validate":
            return json_response(decoder.validate_format(body.get("vin", "")))
        if action == "manufacturer":
            return json_response(decoder.manufacturer_lookup(body.get("wmi", "")))
        return json_response(decoder.decode(body.get("vin", "")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def vi_passport_handler(request: web.Request) -> web.Response:
    try:
        passport = _suite().passport
        if request.method == "GET":
            pid = request.rel_url.query.get("passport_id")
            vin = request.rel_url.query.get("vin")
            if pid:
                return json_response(passport.get(pid))
            if vin:
                return json_response(passport.get_by_vin(vin))
            return json_response(passport.status())
        body = await _read_json(request)
        action = body.get("action", "create")
        if action == "timeline":
            return json_response(
                passport.add_timeline_event(
                    passport_id=body.get("passport_id", ""),
                    timeline=body.get("timeline", "ownership"),
                    event=body.get("event") or {},
                    at=body.get("at"),
                ),
                status=201,
            )
        return json_response(
            passport.create(vin=body.get("vin", ""), decode_id=body.get("decode_id", ""), title=body.get("title", "")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def vi_analysis_handler(request: web.Request) -> web.Response:
    try:
        analysis = _suite().analysis
        if request.method == "GET":
            return json_response(analysis.status())
        body = await _read_json(request)
        kind = body.get("kind") or body.get("action", "fraud_detection")
        return json_response(analysis.run(kind=kind, **{k: v for k, v in body.items() if k not in ("kind", "action")}), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def vi_history_handler(request: web.Request) -> web.Response:
    try:
        history = _suite().history
        if request.method == "GET":
            vin = request.rel_url.query.get("vin", "")
            if vin:
                return json_response({"records": history.list_for_vin(vin, request.rel_url.query.get("type"))})
            return json_response(history.status())
        body = await _read_json(request)
        return json_response(
            history.add(
                vin=body.get("vin", ""),
                history_type=body.get("history_type", "service"),
                detail=body.get("detail"),
                source=body.get("source", "api"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def vi_recommendations_handler(request: web.Request) -> web.Response:
    try:
        rec = _suite().recommendations
        if request.method == "GET":
            return json_response(rec.status())
        body = await _read_json(request)
        return json_response(
            rec.score(
                vin=body.get("vin", ""),
                fraud_score=float(body.get("fraud_score", 0) or 0),
                accident_prob=float(body.get("accident_prob", 0.2) or 0.2),
                market_value=float(body.get("market_value", 20000) or 20000),
                mileage=int(body.get("mileage", 50000) or 50000),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def vi_graph_handler(request: web.Request) -> web.Response:
    try:
        graph = _suite().graph
        if request.method == "GET":
            return json_response(graph.status())
        body = await _read_json(request)
        action = body.get("action", "node")
        if action == "link":
            return json_response(
                graph.link(graph=body.get("graph", "vehicle"), source=body.get("source", ""), target=body.get("target", ""), relation=body.get("relation", "related")),
                status=201,
            )
        return json_response(
            graph.upsert_node(graph=body.get("graph", "vehicle"), node_id=body.get("node_id", ""), label=body.get("label", ""), props=body.get("props")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def vi_integrations_handler(request: web.Request) -> web.Response:
    try:
        integ = _suite().integrations
        if request.method == "GET":
            return json_response({"connections": integ.list_connections(), "status": integ.status()})
        body = await _read_json(request)
        return json_response(integ.connect(channel=body.get("channel", "vin_providers"), endpoint=body.get("endpoint", "")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def vi_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dash = _suite().dashboard
        if request.method == "GET":
            return json_response(dash.render(dashboard_type=request.rel_url.query.get("type", "vin")))
        body = await _read_json(request)
        return json_response(dash.render(dashboard_type=body.get("dashboard_type", "vin")), status=201)
    except Exception as exc:
        return _handle_error(exc)
