"""API handlers — Mobility Platform (Sprint 13.8)."""

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
    return auto_marketplace.mobility_platform


async def mp_health_handler(request: web.Request) -> web.Response:
    health = auto_marketplace.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "mobility_platform_ready": health.get("mobility_platform_ready"),
            "smart_transportation_ready": health.get("smart_transportation_ready"),
            "ev_ecosystem_ready": health.get("ev_ecosystem_ready"),
            "logistics_intelligence_ready": health.get("logistics_intelligence_ready"),
            "smart_city_integration_ready": health.get("smart_city_integration_ready"),
            "suite": _suite().status(),
        }
    )


async def mp_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def mp_hub_handler(request: web.Request) -> web.Response:
    try:
        hub = _suite().hub
        if request.method == "GET":
            return json_response(hub.status())
        body = await _read_json(request)
        action = body.get("action", "hub")
        if action == "node":
            return json_response(
                hub.add_network_node(
                    hub_id=body.get("hub_id", ""),
                    node_type=body.get("node_type", "station"),
                    name=body.get("name", ""),
                    lat=float(body.get("lat", 0) or 0),
                    lon=float(body.get("lon", 0) or 0),
                ),
                status=201,
            )
        if action == "route":
            return json_response(
                hub.route_intelligence(
                    origin=body.get("origin", ""),
                    destination=body.get("destination", ""),
                    mode=body.get("mode", "drive"),
                ),
                status=201,
            )
        if action == "plan":
            return json_response(
                hub.travel_plan(
                    origin=body.get("origin", ""),
                    destination=body.get("destination", ""),
                    preferences=body.get("preferences"),
                ),
                status=201,
            )
        if action == "optimize":
            return json_response(hub.optimize_trip(plan_id=body.get("plan_id", "")), status=201)
        if action == "traffic":
            return json_response(
                hub.traffic_snapshot(region=body.get("region", ""), congestion=float(body.get("congestion", 0.4) or 0.4)),
                status=201,
            )
        if action == "region":
            return json_response(
                hub.register_region(name=body.get("name", ""), manager=body.get("manager", "")),
                status=201,
            )
        return json_response(
            hub.create_hub(name=body.get("name", ""), region=body.get("region", ""), city=body.get("city", "")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def mp_ev_handler(request: web.Request) -> web.Response:
    try:
        ev = _suite().ev
        if request.method == "GET":
            return json_response(ev.status())
        body = await _read_json(request)
        action = body.get("action", "register")
        if action == "battery":
            return json_response(
                ev.battery_health(
                    body.get("ev_id", ""),
                    soh_pct=float(body.get("soh_pct", 92) or 92),
                    cycles=int(body.get("cycles", 200) or 200),
                ),
                status=201,
            )
        if action == "charger":
            return json_response(
                ev.register_charger(
                    name=body.get("name", ""),
                    lat=float(body.get("lat", 0) or 0),
                    lon=float(body.get("lon", 0) or 0),
                    kw=float(body.get("kw", 50) or 50),
                ),
                status=201,
            )
        if action == "start_session":
            return json_response(
                ev.start_session(
                    ev_id=body.get("ev_id", ""),
                    charger_id=body.get("charger_id", ""),
                    kwh_target=float(body.get("kwh_target", 20) or 20),
                ),
                status=201,
            )
        if action == "end_session":
            return json_response(
                ev.end_session(body.get("session_id", ""), kwh_delivered=float(body.get("kwh_delivered", 0) or 0)),
                status=201,
            )
        if action == "range":
            return json_response(
                ev.range_prediction(
                    ev_id=body.get("ev_id", ""),
                    soc_pct=float(body.get("soc_pct", 70) or 70),
                    temp_c=float(body.get("temp_c", 20) or 20),
                ),
                status=201,
            )
        if action == "charging_route":
            return json_response(
                ev.charging_route(
                    ev_id=body.get("ev_id", ""),
                    origin=body.get("origin", ""),
                    destination=body.get("destination", ""),
                ),
                status=201,
            )
        if action == "energy":
            return json_response(ev.energy_analytics(body.get("ev_id", "")), status=201)
        return json_response(
            ev.register_ev(
                vin=body.get("vin", ""),
                model=body.get("model", ""),
                battery_kwh=float(body.get("battery_kwh", 60) or 60),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def mp_maas_handler(request: web.Request) -> web.Response:
    try:
        maas = _suite().maas
        if request.method == "GET":
            return json_response(maas.status())
        body = await _read_json(request)
        action = body.get("action", "offering")
        if action == "reserve":
            return json_response(
                maas.reserve(
                    offering_id=body.get("offering_id", ""),
                    user=body.get("user", ""),
                    starts_at=body.get("starts_at", ""),
                    ends_at=body.get("ends_at", ""),
                ),
                status=201,
            )
        return json_response(
            maas.create_offering(
                name=body.get("name", ""),
                service_type=body.get("service_type", "car_share"),
                region=body.get("region", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def mp_transport_handler(request: web.Request) -> web.Response:
    try:
        transport = _suite().transport
        if request.method == "GET":
            return json_response(transport.status())
        body = await _read_json(request)
        action = body.get("action", "flow")
        if action == "congestion":
            return json_response(
                transport.congestion_prediction(
                    region=body.get("region", ""),
                    horizon_min=int(body.get("horizon_min", 30) or 30),
                ),
                status=201,
            )
        if action == "road":
            return json_response(
                transport.road_condition(road_id=body.get("road_id", ""), condition=body.get("condition", "good")),
                status=201,
            )
        if action == "parking":
            return json_response(
                transport.parking_availability(
                    zone=body.get("zone", ""),
                    available=int(body.get("available", 0) or 0),
                    capacity=int(body.get("capacity", 1) or 1),
                ),
                status=201,
            )
        if action == "public_transport":
            return json_response(
                transport.public_transport(
                    line=body.get("line", ""),
                    mode=body.get("mode", "metro"),
                    headway_min=int(body.get("headway_min", 5) or 5),
                ),
                status=201,
            )
        if action == "emergency":
            return json_response(
                transport.emergency_route(origin=body.get("origin", ""), destination=body.get("destination", "")),
                status=201,
            )
        return json_response(
            transport.traffic_flow(
                corridor=body.get("corridor", ""),
                vehicles_per_hour=int(body.get("vehicles_per_hour", 1200) or 1200),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def mp_logistics_handler(request: web.Request) -> web.Response:
    try:
        logistics = _suite().logistics
        if request.method == "GET":
            return json_response(logistics.status())
        body = await _read_json(request)
        action = body.get("action", "shipment")
        if action == "optimize":
            return json_response(
                logistics.optimize_delivery(shipment_id=body.get("shipment_id", ""), stops=body.get("stops")),
                status=201,
            )
        if action == "track":
            return json_response(
                logistics.track_cargo(
                    shipment_id=body.get("shipment_id", ""),
                    lat=float(body.get("lat", 0) or 0),
                    lon=float(body.get("lon", 0) or 0),
                ),
                status=201,
            )
        if action == "dispatch":
            return json_response(
                logistics.dispatch(vehicle_id=body.get("vehicle_id", ""), shipment_id=body.get("shipment_id", "")),
                status=201,
            )
        if action == "warehouse":
            return json_response(
                logistics.warehouse_link(warehouse=body.get("warehouse", ""), shipment_id=body.get("shipment_id", "")),
                status=201,
            )
        return json_response(
            logistics.create_shipment(
                cargo=body.get("cargo", ""),
                origin=body.get("origin", ""),
                destination=body.get("destination", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def mp_ai_handler(request: web.Request) -> web.Response:
    try:
        ai = _suite().ai
        if request.method == "GET":
            return json_response(ai.status())
        body = await _read_json(request)
        action = body.get("action", "demand")
        if action == "recommend":
            return json_response(
                ai.recommend(user=body.get("user", ""), intent=body.get("intent", "commute")),
                status=201,
            )
        if action == "travel_time":
            return json_response(
                ai.travel_time(origin=body.get("origin", ""), destination=body.get("destination", "")),
                status=201,
            )
        if action == "energy":
            return json_response(
                ai.energy_optimize(ev_id=body.get("ev_id", ""), route_km=float(body.get("route_km", 0) or 0)),
                status=201,
            )
        if action == "carbon":
            return json_response(
                ai.carbon_footprint(trips=int(body.get("trips", 1) or 1), mode=body.get("mode", "ev")),
                status=201,
            )
        return json_response(
            ai.demand_forecast(region=body.get("region", ""), horizon_h=int(body.get("horizon_h", 24) or 24)),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def mp_smart_city_handler(request: web.Request) -> web.Response:
    try:
        city = _suite().smart_city
        if request.method == "GET":
            city_name = request.rel_url.query.get("city")
            if city_name:
                return json_response(city.urban_dashboard(city=city_name))
            return json_response(city.status())
        body = await _read_json(request)
        action = body.get("action", "asset")
        if action == "dashboard":
            return json_response(city.urban_dashboard(city=body.get("city", "")), status=201)
        return json_response(
            city.register_asset(kind=body.get("kind", ""), name=body.get("name", ""), meta=body.get("meta")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def mp_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dash = _suite().dashboard
        if request.method == "GET":
            return json_response(dash.render(dashboard_type=request.rel_url.query.get("type", "mobility")))
        body = await _read_json(request)
        return json_response(dash.render(dashboard_type=body.get("dashboard_type", "mobility")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def mp_knowledge_handler(request: web.Request) -> web.Response:
    try:
        knowledge = _suite().knowledge
        if request.method == "GET":
            return json_response(knowledge.status())
        body = await _read_json(request)
        return json_response(
            knowledge.publish(
                registry_type=body.get("registry_type", "mobility"),
                key=body.get("key", ""),
                payload=body.get("payload"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
