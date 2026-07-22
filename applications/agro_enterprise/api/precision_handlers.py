"""API handlers — Precision Agriculture (Sprint 14.1)."""

from __future__ import annotations

from aiohttp import web

from applications.agro_enterprise import agro_enterprise
from applications.agro_enterprise.api.middleware import json_response
from applications.agro_enterprise.shared.exceptions import NotFoundError, ValidationError


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
    return agro_enterprise.precision


async def pa_health_handler(request: web.Request) -> web.Response:
    health = agro_enterprise.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "precision_agriculture_ready": health.get("precision_agriculture_ready"),
            "gis_platform_ready": health.get("gis_platform_ready"),
            "drone_integration_ready": health.get("drone_integration_ready"),
            "satellite_intelligence_ready": health.get("satellite_intelligence_ready"),
            "smart_fields_ready": health.get("smart_fields_ready"),
            "suite": _suite().status(),
        }
    )


async def pa_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def pa_fields_handler(request: web.Request) -> web.Response:
    try:
        fields = _suite().fields
        if request.method == "GET":
            fid = request.rel_url.query.get("field_id")
            if fid:
                return json_response(fields.analytics(fid))
            return json_response(fields.status())
        body = await _read_json(request)
        action = body.get("action", "register")
        if action == "boundary":
            return json_response(
                fields.set_boundary(body.get("field_id", ""), coordinates=body.get("coordinates") or []),
                status=201,
            )
        if action == "crop":
            return json_response(
                fields.assign_crop(body.get("field_id", ""), crop_id=body.get("crop_id", "")),
                status=201,
            )
        if action == "history":
            return json_response(
                fields.record_history(
                    body.get("field_id", ""),
                    event=body.get("event", ""),
                    details=body.get("details"),
                ),
                status=201,
            )
        return json_response(
            fields.register_field(
                name=body.get("name", ""),
                farm_id=body.get("farm_id", ""),
                hectares=float(body.get("hectares", 0) or 0),
                soil_type=body.get("soil_type", "loam"),
                owner=body.get("owner", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def pa_gis_handler(request: web.Request) -> web.Response:
    try:
        gis = _suite().gis
        if request.method == "GET":
            return json_response(gis.status())
        body = await _read_json(request)
        action = body.get("action", "map")
        if action == "layer":
            return json_response(
                gis.add_layer(
                    body.get("map_id", ""),
                    layer=body.get("layer", "ndvi"),
                    opacity=float(body.get("opacity", 0.7) or 0.7),
                ),
                status=201,
            )
        return json_response(
            gis.create_map(
                name=body.get("name", ""),
                field_id=body.get("field_id", ""),
                basemap=body.get("basemap", "satellite"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def pa_drone_handler(request: web.Request) -> web.Response:
    try:
        drone = _suite().drone
        if request.method == "GET":
            return json_response(drone.status())
        body = await _read_json(request)
        action = body.get("action", "plan")
        if action == "complete":
            return json_response(
                drone.complete_survey(
                    body.get("mission_id", ""),
                    orthomosaic=bool(body.get("orthomosaic", True)),
                    multispectral=bool(body.get("multispectral", True)),
                    thermal=bool(body.get("thermal", False)),
                    plant_count=int(body.get("plant_count", 0) or 0),
                ),
                status=201,
            )
        return json_response(
            drone.plan_mission(
                field_id=body.get("field_id", ""),
                mission_type=body.get("mission_type", "survey"),
                altitude_m=float(body.get("altitude_m", 80) or 80),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def pa_satellite_handler(request: web.Request) -> web.Response:
    try:
        satellite = _suite().satellite
        if request.method == "GET":
            fid = request.rel_url.query.get("field_id")
            if fid:
                return json_response({"timeline": satellite.timeline(fid)})
            return json_response(satellite.status())
        body = await _read_json(request)
        action = body.get("action", "ingest")
        if action == "analyze":
            return json_response(satellite.analyze(body.get("imagery_id", "")), status=201)
        return json_response(
            satellite.ingest_imagery(
                field_id=body.get("field_id", ""),
                source=body.get("source", "sentinel-2"),
                captured_at=body.get("captured_at", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def pa_iot_handler(request: web.Request) -> web.Response:
    try:
        iot = _suite().iot
        if request.method == "GET":
            fid = request.rel_url.query.get("field_id", "")
            if request.rel_url.query.get("dashboard"):
                return json_response(iot.dashboard(fid))
            return json_response(iot.status())
        body = await _read_json(request)
        action = body.get("action", "sensor")
        if action == "reading":
            return json_response(
                iot.reading(
                    body.get("sensor_id", ""),
                    value=float(body.get("value", 0) or 0),
                    unit=body.get("unit", ""),
                ),
                status=201,
            )
        if action == "irrigate":
            return json_response(
                iot.irrigate(
                    field_id=body.get("field_id", ""),
                    duration_min=int(body.get("duration_min", 30) or 30),
                ),
                status=201,
            )
        return json_response(
            iot.register_sensor(
                field_id=body.get("field_id", ""),
                kind=body.get("kind", "soil_moisture"),
                name=body.get("name", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def pa_ai_handler(request: web.Request) -> web.Response:
    try:
        ai = _suite().ai
        if request.method == "GET":
            return json_response(ai.status())
        body = await _read_json(request)
        return json_response(
            ai.analyze(
                field_id=body.get("field_id", ""),
                ndvi=float(body.get("ndvi", 0.6) or 0.6),
                stress_index=float(body.get("stress_index", 0.2) or 0.2),
                growth_day=int(body.get("growth_day", 60) or 60),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def pa_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dash = _suite().dashboard
        if request.method == "GET":
            return json_response(dash.render(dashboard_type=request.rel_url.query.get("type", "field")))
        body = await _read_json(request)
        return json_response(dash.render(dashboard_type=body.get("dashboard_type", "field")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def pa_knowledge_handler(request: web.Request) -> web.Response:
    try:
        knowledge = _suite().knowledge
        if request.method == "GET":
            return json_response(knowledge.status())
        body = await _read_json(request)
        return json_response(
            knowledge.publish(
                registry_type=body.get("registry_type", "field"),
                key=body.get("key", ""),
                payload=body.get("payload"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
