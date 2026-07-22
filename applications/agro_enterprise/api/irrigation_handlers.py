"""API handlers — Smart Irrigation (Sprint 14.2)."""

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
    return agro_enterprise.irrigation


async def si_health_handler(request: web.Request) -> web.Response:
    health = agro_enterprise.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "smart_irrigation_ready": health.get("smart_irrigation_ready"),
            "soil_intelligence_ready": health.get("soil_intelligence_ready"),
            "water_management_ready": health.get("water_management_ready"),
            "environmental_ai_ready": health.get("environmental_ai_ready"),
            "suite": _suite().status(),
        }
    )


async def si_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def si_soil_handler(request: web.Request) -> web.Response:
    try:
        soil = _suite().soil
        if request.method == "GET":
            fid = request.rel_url.query.get("field_id")
            if fid:
                return json_response({"history": soil.history(fid)})
            return json_response(soil.status())
        body = await _read_json(request)
        action = body.get("action", "register")
        if action == "nutrients":
            return json_response(
                soil.nutrient_analysis(
                    body.get("soil_id", ""),
                    n=float(body.get("n", 0) or 0),
                    p=float(body.get("p", 0) or 0),
                    k=float(body.get("k", 0) or 0),
                ),
                status=201,
            )
        return json_response(
            soil.register_soil(
                field_id=body.get("field_id", ""),
                composition=body.get("composition"),
                organic_matter_pct=float(body.get("organic_matter_pct", 2.5) or 2.5),
                ph=float(body.get("ph", 6.5) or 6.5),
                salinity_ds_m=float(body.get("salinity_ds_m", 0.8) or 0.8),
                compaction_mpa=float(body.get("compaction_mpa", 1.2) or 1.2),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def si_water_handler(request: web.Request) -> web.Response:
    try:
        water = _suite().water
        if request.method == "GET":
            sid = request.rel_url.query.get("source_id")
            if sid and request.rel_url.query.get("balance"):
                return json_response(water.water_balance(sid))
            return json_response(water.status())
        body = await _read_json(request)
        action = body.get("action", "source")
        if action == "level":
            return json_response(
                water.update_level(body.get("source_id", ""), level_m3=float(body.get("level_m3", 0) or 0)),
                status=201,
            )
        if action == "consume":
            return json_response(
                water.log_consumption(
                    source_id=body.get("source_id", ""),
                    volume_m3=float(body.get("volume_m3", 0) or 0),
                    zone_id=body.get("zone_id", ""),
                ),
                status=201,
            )
        if action == "balance":
            return json_response(water.water_balance(body.get("source_id", "")), status=201)
        if action == "quality":
            return json_response(
                water.quality_check(
                    body.get("source_id", ""),
                    turbidity=float(body.get("turbidity", 2) or 2),
                    ph=float(body.get("ph", 7) or 7),
                ),
                status=201,
            )
        return json_response(
            water.register_source(
                name=body.get("name", ""),
                source_type=body.get("source_type", "reservoir"),
                capacity_m3=float(body.get("capacity_m3", 0) or 0),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def si_irrigation_handler(request: web.Request) -> web.Response:
    try:
        irrigation = _suite().irrigation
        if request.method == "GET":
            return json_response(irrigation.status())
        body = await _read_json(request)
        action = body.get("action", "zone")
        if action == "schedule":
            return json_response(
                irrigation.schedule(
                    zone_id=body.get("zone_id", ""),
                    starts_at=body.get("starts_at", ""),
                    duration_min=int(body.get("duration_min", 30) or 30),
                ),
                status=201,
            )
        if action == "valve":
            return json_response(
                irrigation.set_valve(zone_id=body.get("zone_id", ""), open_valve=bool(body.get("open", True))),
                status=201,
            )
        if action == "pump":
            return json_response(
                irrigation.set_pump(
                    source_id=body.get("source_id", ""),
                    running=bool(body.get("running", True)),
                    flow_m3h=float(body.get("flow_m3h", 0) or 0),
                ),
                status=201,
            )
        if action == "flow":
            return json_response(
                irrigation.monitor_flow(
                    zone_id=body.get("zone_id", ""),
                    flow_lpm=float(body.get("flow_lpm", 0) or 0),
                    pressure_bar=float(body.get("pressure_bar", 2.5) or 2.5),
                ),
                status=201,
            )
        if action == "remote":
            return json_response(
                irrigation.remote_control(zone_id=body.get("zone_id", ""), command=body.get("command", "start")),
                status=201,
            )
        return json_response(
            irrigation.create_zone(
                name=body.get("name", ""),
                field_id=body.get("field_id", ""),
                hectares=float(body.get("hectares", 0) or 0),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def si_iot_handler(request: web.Request) -> web.Response:
    try:
        iot = _suite().iot
        if request.method == "GET":
            if request.rel_url.query.get("health"):
                return json_response(iot.sensor_health())
            return json_response(iot.status())
        body = await _read_json(request)
        action = body.get("action", "sensor")
        if action == "gateway":
            return json_response(
                iot.register_gateway(name=body.get("name", ""), field_id=body.get("field_id", "")),
                status=201,
            )
        if action == "reading":
            return json_response(
                iot.reading(
                    body.get("sensor_id", ""),
                    value=float(body.get("value", 0) or 0),
                    unit=body.get("unit", ""),
                ),
                status=201,
            )
        return json_response(
            iot.register_sensor(
                kind=body.get("kind", "soil_moisture"),
                gateway_id=body.get("gateway_id", ""),
                name=body.get("name", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def si_ai_handler(request: web.Request) -> web.Response:
    try:
        ai = _suite().ai
        if request.method == "GET":
            return json_response(ai.status())
        body = await _read_json(request)
        return json_response(
            ai.predict(
                zone_id=body.get("zone_id", ""),
                soil_moisture_pct=float(body.get("soil_moisture_pct", 30) or 30),
                et0_mm=float(body.get("et0_mm", 4.5) or 4.5),
                forecast_rain_mm=float(body.get("forecast_rain_mm", 0) or 0),
                water_cost_per_m3=float(body.get("water_cost_per_m3", 0.4) or 0.4),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def si_environment_handler(request: web.Request) -> web.Response:
    try:
        env = _suite().environment
        if request.method == "GET":
            return json_response(env.status())
        body = await _read_json(request)
        action = body.get("action", "weather")
        if action == "risks":
            return json_response(
                env.assess_risks(
                    region=body.get("region", ""),
                    soil_moisture_pct=float(body.get("soil_moisture_pct", 30) or 30),
                    temp_c=float(body.get("temp_c", 30) or 30),
                ),
                status=201,
            )
        return json_response(
            env.ingest_weather(
                region=body.get("region", ""),
                temp_c=float(body.get("temp_c", 22) or 22),
                humidity_pct=float(body.get("humidity_pct", 55) or 55),
                rain_mm=float(body.get("rain_mm", 0) or 0),
                wind_ms=float(body.get("wind_ms", 3) or 3),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def si_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dash = _suite().dashboard
        if request.method == "GET":
            return json_response(dash.render(dashboard_type=request.rel_url.query.get("type", "irrigation")))
        body = await _read_json(request)
        return json_response(dash.render(dashboard_type=body.get("dashboard_type", "irrigation")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def si_knowledge_handler(request: web.Request) -> web.Response:
    try:
        knowledge = _suite().knowledge
        if request.method == "GET":
            return json_response(knowledge.status())
        body = await _read_json(request)
        return json_response(
            knowledge.publish(
                registry_type=body.get("registry_type", "soil"),
                key=body.get("key", ""),
                payload=body.get("payload"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
