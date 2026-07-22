"""API handlers — Connected Cars (Sprint 13.7)."""

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
    return auto_marketplace.connected_cars


async def cc_health_handler(request: web.Request) -> web.Response:
    health = auto_marketplace.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "connected_cars_ready": health.get("connected_cars_ready"),
            "telematics_platform_ready": health.get("telematics_platform_ready"),
            "fleet_intelligence_ready": health.get("fleet_intelligence_ready"),
            "predictive_maintenance_ready": health.get("predictive_maintenance_ready"),
            "vehicle_iot_platform_ready": health.get("vehicle_iot_platform_ready"),
            "suite": _suite().status(),
        }
    )


async def cc_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def cc_core_handler(request: web.Request) -> web.Response:
    try:
        core = _suite().core
        if request.method == "GET":
            return json_response(core.status())
        body = await _read_json(request)
        action = body.get("action", "register")
        if action == "connect":
            return json_response(
                core.connect_vehicle(body.get("connected_vehicle_id", ""), protocol=body.get("protocol", "mqtt")),
                status=201,
            )
        if action == "device":
            return json_response(
                core.register_iot_device(
                    connected_vehicle_id=body.get("connected_vehicle_id", ""),
                    kind=body.get("kind", "obd"),
                    serial=body.get("serial", ""),
                ),
                status=201,
            )
        if action == "message":
            return json_response(
                core.send_message(
                    connected_vehicle_id=body.get("connected_vehicle_id", ""),
                    channel=body.get("channel", "telematics"),
                    payload=body.get("payload"),
                ),
                status=201,
            )
        return json_response(
            core.register_vehicle(
                vin=body.get("vin", ""),
                label=body.get("label", ""),
                fleet_id=body.get("fleet_id", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def cc_telematics_handler(request: web.Request) -> web.Response:
    try:
        telematics = _suite().telematics
        if request.method == "GET":
            return json_response(telematics.status())
        body = await _read_json(request)
        action = body.get("action", "gps")
        if action == "start_trip":
            return json_response(
                telematics.start_trip(
                    connected_vehicle_id=body.get("connected_vehicle_id", ""),
                    origin=body.get("origin", ""),
                ),
                status=201,
            )
        if action == "end_trip":
            return json_response(
                telematics.end_trip(
                    body.get("trip_id", ""),
                    destination=body.get("destination", ""),
                    distance_km=float(body.get("distance_km", 0) or 0),
                    fuel_liters=float(body.get("fuel_liters", 0) or 0),
                    harsh_events=int(body.get("harsh_events", 0) or 0),
                ),
                status=201,
            )
        if action == "fuel":
            return json_response(
                telematics.monitor_fuel(
                    connected_vehicle_id=body.get("connected_vehicle_id", ""),
                    level_pct=float(body.get("level_pct", 0) or 0),
                    liters=float(body.get("liters", 0) or 0),
                ),
                status=201,
            )
        if action == "battery":
            return json_response(
                telematics.monitor_battery(
                    connected_vehicle_id=body.get("connected_vehicle_id", ""),
                    soc_pct=float(body.get("soc_pct", 0) or 0),
                    voltage=float(body.get("voltage", 12.4) or 12.4),
                ),
                status=201,
            )
        if action == "obd":
            return json_response(
                telematics.obd_snapshot(
                    connected_vehicle_id=body.get("connected_vehicle_id", ""),
                    codes=body.get("codes"),
                    rpm=int(body.get("rpm", 0) or 0),
                    coolant=float(body.get("coolant", 90) or 90),
                ),
                status=201,
            )
        if action == "event":
            return json_response(
                telematics.record_event(
                    connected_vehicle_id=body.get("connected_vehicle_id", ""),
                    event_type=body.get("event_type", ""),
                    severity=body.get("severity", "info"),
                    details=body.get("details"),
                ),
                status=201,
            )
        return json_response(
            telematics.track_gps(
                connected_vehicle_id=body.get("connected_vehicle_id", ""),
                lat=float(body.get("lat", 0) or 0),
                lon=float(body.get("lon", 0) or 0),
                speed_kmh=float(body.get("speed_kmh", 0) or 0),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def cc_remote_handler(request: web.Request) -> web.Response:
    try:
        remote = _suite().remote
        if request.method == "GET":
            vid = request.rel_url.query.get("connected_vehicle_id")
            if vid:
                return json_response(remote.health(vid))
            return json_response(remote.status())
        body = await _read_json(request)
        action = body.get("action", "health")
        vid = body.get("connected_vehicle_id", "")
        if action == "diagnostics":
            return json_response(remote.remote_diagnostics(vid), status=201)
        if action == "notify":
            return json_response(
                remote.notify(connected_vehicle_id=vid, title=body.get("title", ""), body=body.get("body", "")),
                status=201,
            )
        if action == "command":
            return json_response(remote.command(connected_vehicle_id=vid, command=body.get("command", "")), status=201)
        if action == "alert":
            return json_response(
                remote.maintenance_alert(connected_vehicle_id=vid, message=body.get("message", ""), due_at=body.get("due_at", "")),
                status=201,
            )
        if action == "firmware":
            return json_response(
                remote.register_firmware(
                    connected_vehicle_id=vid,
                    component=body.get("component", ""),
                    version=body.get("version", ""),
                ),
                status=201,
            )
        return json_response(remote.health(vid), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def cc_predictive_handler(request: web.Request) -> web.Response:
    try:
        predictive = _suite().predictive
        if request.method == "GET":
            return json_response(predictive.status())
        body = await _read_json(request)
        return json_response(
            predictive.predict(
                connected_vehicle_id=body.get("connected_vehicle_id", ""),
                mileage=int(body.get("mileage", 50000) or 50000),
                battery_soc=float(body.get("battery_soc", 80) or 80),
                engine_load=float(body.get("engine_load", 0.4) or 0.4),
                brake_km=float(body.get("brake_km", 20000) or 20000),
                tire_km=float(body.get("tire_km", 25000) or 25000),
                utilization=float(body.get("utilization", 0.5) or 0.5),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def cc_fleet_handler(request: web.Request) -> web.Response:
    try:
        fleet = _suite().fleet
        if request.method == "GET":
            return json_response(fleet.dashboard(fleet_id=request.rel_url.query.get("fleet_id", "")))
        body = await _read_json(request)
        return json_response(fleet.dashboard(fleet_id=body.get("fleet_id", "")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def cc_smart_handler(request: web.Request) -> web.Response:
    try:
        smart = _suite().smart
        if request.method == "GET":
            kind = request.rel_url.query.get("kind")
            if kind:
                return json_response(
                    {
                        "results": smart.locate(
                            kind=kind,
                            near_lat=float(request.rel_url.query.get("lat", 0) or 0),
                            near_lon=float(request.rel_url.query.get("lon", 0) or 0),
                        )
                    }
                )
            return json_response(smart.status())
        body = await _read_json(request)
        return json_response(
            smart.register(
                kind=body.get("kind", ""),
                name=body.get("name", ""),
                lat=float(body.get("lat", 0) or 0),
                lon=float(body.get("lon", 0) or 0),
                meta=body.get("meta"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def cc_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dash = _suite().dashboard
        if request.method == "GET":
            return json_response(dash.render(dashboard_type=request.rel_url.query.get("type", "connected_fleet")))
        body = await _read_json(request)
        return json_response(dash.render(dashboard_type=body.get("dashboard_type", "connected_fleet")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def cc_knowledge_handler(request: web.Request) -> web.Response:
    try:
        knowledge = _suite().knowledge
        if request.method == "GET":
            return json_response(knowledge.status())
        body = await _read_json(request)
        return json_response(
            knowledge.publish(
                registry_type=body.get("registry_type", "telemetry"),
                key=body.get("key", ""),
                payload=body.get("payload"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
