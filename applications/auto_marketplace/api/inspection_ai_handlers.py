"""API handlers — Inspection AI (Sprint 13.2)."""

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
    return auto_marketplace.inspection_ai


async def ia_health_handler(request: web.Request) -> web.Response:
    health = auto_marketplace.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "inspection_ai_ready": health.get("inspection_ai_ready"),
            "damage_detection_ready": health.get("damage_detection_ready"),
            "vehicle_health_ai_ready": health.get("vehicle_health_ai_ready"),
            "repair_estimation_ready": health.get("repair_estimation_ready"),
            "suite": _suite().status(),
        }
    )


async def ia_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ia_photo_handler(request: web.Request) -> web.Response:
    try:
        photo = _suite().photo
        if request.method == "GET":
            return json_response(photo.status())
        body = await _read_json(request)
        return json_response(
            photo.analyze(
                vin=body.get("vin", ""),
                zone=body.get("zone", "exterior"),
                media_uri=body.get("media_uri", ""),
                media_type=body.get("media_type", "photo"),
                signals=body.get("signals"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ia_damage_handler(request: web.Request) -> web.Response:
    try:
        damage = _suite().damage
        if request.method == "GET":
            vin = request.rel_url.query.get("vin")
            if vin:
                return json_response({"detections": damage.list_for_vin(vin)})
            return json_response(damage.status())
        body = await _read_json(request)
        action = body.get("action", "detect")
        if action == "scan":
            return json_response({"detections": damage.scan_all(vin=body.get("vin", ""), signals=body.get("signals"))}, status=201)
        return json_response(
            damage.detect(
                vin=body.get("vin", ""),
                damage_type=body.get("damage_type", "scratch"),
                location=body.get("location", "body"),
                severity=float(body.get("severity", 0.3) or 0.3),
                evidence=body.get("evidence"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ia_estimate_handler(request: web.Request) -> web.Response:
    try:
        estimation = _suite().estimation
        if request.method == "GET":
            return json_response(estimation.status())
        body = await _read_json(request)
        return json_response(
            estimation.estimate(
                vin=body.get("vin", ""),
                damages=body.get("damages"),
                market_value=float(body.get("market_value", 20000) or 20000),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ia_score_handler(request: web.Request) -> web.Response:
    try:
        health = _suite().health
        if request.method == "GET":
            return json_response(health.status())
        body = await _read_json(request)
        return json_response(
            health.score(
                vin=body.get("vin", ""),
                damages=body.get("damages"),
                photo_quality_avg=float(body.get("photo_quality_avg", 0.85) or 0.85),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ia_report_handler(request: web.Request) -> web.Response:
    try:
        report = _suite().report
        if request.method == "GET":
            rid = request.rel_url.query.get("report_id")
            if rid:
                return json_response(report.get(rid))
            return json_response(report.status())
        body = await _read_json(request)
        return json_response(
            report.generate(
                vin=body.get("vin", ""),
                health=body.get("health"),
                estimate=body.get("estimate"),
                damages=body.get("damages"),
                format=body.get("format", "pdf"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ia_knowledge_handler(request: web.Request) -> web.Response:
    try:
        knowledge = _suite().knowledge
        if request.method == "GET":
            return json_response(knowledge.status())
        body = await _read_json(request)
        return json_response(
            knowledge.link(
                vin=body.get("vin", ""),
                source=body.get("source", "vin_intelligence"),
                ref_id=body.get("ref_id", ""),
                payload=body.get("payload"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ia_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dash = _suite().dashboard
        if request.method == "GET":
            return json_response(dash.render(dashboard_type=request.rel_url.query.get("type", "inspection")))
        body = await _read_json(request)
        return json_response(dash.render(dashboard_type=body.get("dashboard_type", "inspection")), status=201)
    except Exception as exc:
        return _handle_error(exc)
