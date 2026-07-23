"""API handlers — Port Navigation / VTS (Sprint 15.1)."""

from __future__ import annotations

from aiohttp import web

from applications.port_enterprise import port_enterprise
from applications.port_enterprise.api.middleware import json_response
from applications.port_enterprise.shared.exceptions import NotFoundError, ValidationError


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
    return port_enterprise.navigation


async def nav_health_handler(request: web.Request) -> web.Response:
    health = port_enterprise.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "vts_platform_ready": health.get("vts_platform_ready"),
            "ais_integration_ready": health.get("ais_integration_ready"),
            "radar_intelligence_ready": health.get("radar_intelligence_ready"),
            "navigation_platform_ready": health.get("navigation_platform_ready"),
            "maritime_safety_ready": health.get("maritime_safety_ready"),
            "suite": _suite().status(),
        }
    )


async def nav_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def nav_vts_handler(request: web.Request) -> web.Response:
    try:
        vts = _suite().vts
        if request.method == "GET":
            return json_response(vts.status())
        body = await _read_json(request)
        action = body.get("action", "center")
        if action == "monitor":
            return json_response(
                vts.monitor_traffic(
                    center_id=body.get("center_id", ""),
                    vessel_count=int(body.get("vessel_count", 0) or 0),
                    density=float(body.get("density", 0) or 0),
                ),
                status=201,
            )
        if action == "arrival":
            return json_response(
                vts.arrival_queue(
                    center_id=body.get("center_id", ""),
                    vessel_id=body.get("vessel_id", ""),
                    eta=body.get("eta", ""),
                ),
                status=201,
            )
        if action == "departure":
            return json_response(
                vts.departure_queue(
                    center_id=body.get("center_id", ""),
                    vessel_id=body.get("vessel_id", ""),
                    etd=body.get("etd", ""),
                ),
                status=201,
            )
        if action == "assist":
            return json_response(
                vts.navigation_assist(
                    center_id=body.get("center_id", ""),
                    vessel_id=body.get("vessel_id", ""),
                    advice=body.get("advice", ""),
                ),
                status=201,
            )
        if action == "collision":
            return json_response(
                vts.collision_watch(
                    center_id=body.get("center_id", ""),
                    vessel_a=body.get("vessel_a", ""),
                    vessel_b=body.get("vessel_b", ""),
                    cpa_nm=float(body.get("cpa_nm", 1) or 1),
                ),
                status=201,
            )
        if action == "restricted":
            return json_response(
                vts.restricted_area(
                    center_id=body.get("center_id", ""),
                    area=body.get("area", ""),
                    vessel_id=body.get("vessel_id", ""),
                    breached=bool(body.get("breached", False)),
                ),
                status=201,
            )
        return json_response(
            vts.open_center(name=body.get("name", ""), port_id=body.get("port_id", "")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def nav_ais_handler(request: web.Request) -> web.Response:
    try:
        ais = _suite().ais
        if request.method == "GET":
            mmsi = request.rel_url.query.get("mmsi")
            if mmsi:
                return json_response(ais.route_history(mmsi))
            return json_response(ais.status())
        body = await _read_json(request)
        action = body.get("action", "receiver")
        if action == "message":
            return json_response(
                ais.process_message(
                    receiver_id=body.get("receiver_id", ""),
                    mmsi=body.get("mmsi", ""),
                    lat=float(body.get("lat", 0) or 0),
                    lon=float(body.get("lon", 0) or 0),
                    sog=float(body.get("sog", 0) or 0),
                    cog=float(body.get("cog", 0) or 0),
                    msg_type=int(body.get("msg_type", 1) or 1),
                ),
                status=201,
            )
        if action == "eta":
            return json_response(
                ais.eta_predict(
                    mmsi=body.get("mmsi", ""),
                    remaining_nm=float(body.get("remaining_nm", 0) or 0),
                    sog=float(body.get("sog", 0) or 0),
                ),
                status=201,
            )
        return json_response(
            ais.register_receiver(name=body.get("name", ""), station=body.get("station", "")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def nav_radar_handler(request: web.Request) -> web.Response:
    try:
        radar = _suite().radar
        if request.method == "GET":
            rid = request.rel_url.query.get("radar_id")
            if rid:
                return json_response(radar.analytics(rid))
            return json_response(radar.status())
        body = await _read_json(request)
        action = body.get("action", "register")
        if action == "detect":
            return json_response(
                radar.detect_target(
                    radar_id=body.get("radar_id", ""),
                    bearing=float(body.get("bearing", 0) or 0),
                    range_nm=float(body.get("range_nm", 0) or 0),
                    object_class=body.get("object_class", "vessel"),
                ),
                status=201,
            )
        if action == "blind":
            return json_response(
                radar.blind_zone(
                    radar_id=body.get("radar_id", ""),
                    sector=body.get("sector", ""),
                    severity=body.get("severity", "medium"),
                ),
                status=201,
            )
        if action == "alert":
            return json_response(
                radar.alert(
                    radar_id=body.get("radar_id", ""),
                    message=body.get("message", ""),
                    level=body.get("level", "warning"),
                ),
                status=201,
            )
        return json_response(
            radar.register_radar(
                name=body.get("name", ""), coverage_nm=float(body.get("coverage_nm", 24) or 24)
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def nav_navigation_handler(request: web.Request) -> web.Response:
    try:
        navigation = _suite().navigation
        if request.method == "GET":
            return json_response(navigation.status())
        body = await _read_json(request)
        action = body.get("action", "route")
        if action == "fairway":
            return json_response(
                navigation.fairway(name=body.get("name", ""), depth_m=float(body.get("depth_m", 14) or 14)),
                status=201,
            )
        if action == "pilot":
            return json_response(
                navigation.pilot_boarding(
                    name=body.get("name", ""),
                    lat=float(body.get("lat", 0) or 0),
                    lon=float(body.get("lon", 0) or 0),
                ),
                status=201,
            )
        if action == "anchorage":
            return json_response(
                navigation.anchorage(name=body.get("name", ""), capacity=int(body.get("capacity", 10) or 10)),
                status=201,
            )
        if action == "restriction":
            return json_response(
                navigation.restriction(
                    title=body.get("title", ""),
                    area=body.get("area", ""),
                    reason=body.get("reason", ""),
                ),
                status=201,
            )
        if action == "weather":
            return json_response(
                navigation.weather_overlay(
                    area=body.get("area", ""),
                    wind_kn=float(body.get("wind_kn", 0) or 0),
                    visibility_nm=float(body.get("visibility_nm", 0) or 0),
                ),
                status=201,
            )
        if action == "sea_state":
            return json_response(
                navigation.sea_state(
                    area=body.get("area", ""), douglas_scale=int(body.get("douglas_scale", 3) or 3)
                ),
                status=201,
            )
        waypoints = body.get("waypoints") if isinstance(body.get("waypoints"), list) else None
        return json_response(
            navigation.create_route(name=body.get("name", ""), waypoints=waypoints),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def nav_safety_handler(request: web.Request) -> web.Response:
    try:
        safety = _suite().safety
        if request.method == "GET":
            return json_response(safety.status())
        body = await _read_json(request)
        action = body.get("action", "risk")
        if action == "warning":
            return json_response(
                safety.warning(
                    title=body.get("title", ""),
                    message=body.get("message", ""),
                    kind=body.get("kind", "navigation"),
                ),
                status=201,
            )
        if action == "emergency":
            return json_response(
                safety.emergency(vessel_id=body.get("vessel_id", ""), nature=body.get("nature", "")),
                status=201,
            )
        if action == "zone":
            return json_response(
                safety.restricted_zone_alert(zone=body.get("zone", ""), vessel_id=body.get("vessel_id", "")),
                status=201,
            )
        if action == "hazard":
            return json_response(
                safety.environmental_hazard(
                    hazard=body.get("hazard", ""), severity=body.get("severity", "medium")
                ),
                status=201,
            )
        return json_response(
            safety.collision_risk(
                vessel_a=body.get("vessel_a", ""),
                vessel_b=body.get("vessel_b", ""),
                score=float(body.get("score", 0.5) or 0.5),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def nav_ai_handler(request: web.Request) -> web.Response:
    try:
        ai = _suite().ai
        if request.method == "GET":
            return json_response(ai.status())
        body = await _read_json(request)
        action = body.get("action", "traffic")
        if action == "route":
            return json_response(
                ai.optimal_route(origin=body.get("origin", ""), destination=body.get("destination", "")),
                status=201,
            )
        if action == "arrival":
            return json_response(
                ai.arrival_optimization(
                    vessel_id=body.get("vessel_id", ""), requested_eta=body.get("requested_eta", "")
                ),
                status=201,
            )
        if action == "berth":
            candidates = body.get("candidates") if isinstance(body.get("candidates"), list) else None
            return json_response(
                ai.berth_recommendation(vessel_id=body.get("vessel_id", ""), candidates=candidates),
                status=201,
            )
        if action == "risk":
            return json_response(
                ai.operational_risk(
                    vessel_id=body.get("vessel_id", ""), score=float(body.get("score", 0.5) or 0.5)
                ),
                status=201,
            )
        return json_response(
            ai.predict_traffic(
                area=body.get("area", ""), horizon_hours=int(body.get("horizon_hours", 6) or 6)
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def nav_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dash = _suite().dashboard
        if request.method == "GET":
            dtype = request.rel_url.query.get("type", "vts")
            return json_response(dash.render(dashboard_type=dtype))
        body = await _read_json(request)
        return json_response(
            dash.render(dashboard_type=body.get("dashboard_type", "vts")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def nav_knowledge_handler(request: web.Request) -> web.Response:
    try:
        knowledge = _suite().knowledge
        if request.method == "GET":
            return json_response(knowledge.status())
        body = await _read_json(request)
        return json_response(
            knowledge.publish(
                registry_type=body.get("registry_type", "navigation"),
                key=body.get("key", ""),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else {},
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
