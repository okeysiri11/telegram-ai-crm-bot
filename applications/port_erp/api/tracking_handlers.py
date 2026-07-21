# Port ERP tracking REST handlers — Sprint 9.2.

from __future__ import annotations

from aiohttp import web

from applications.port_erp import port_erp
from applications.port_erp.api.middleware import error_response, json_response
from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.models import GeofenceType
from applications.port_erp.tracking.models import Geofence, TruckTrack


async def tracking_health_handler(_request: web.Request) -> web.Response:
    return json_response(
        {
            "tracking_engine": port_erp.config.tracking_engine,
            "application_version": port_erp.config.application_version,
            "metrics": port_erp.tracking.metrics(),
            "operations": port_erp.live_operations.dashboard(),
        }
    )


async def tracking_live_handler(request: web.Request) -> web.Response:
    asset_type = request.query.get("asset_type")
    items = port_erp.tracking.live.list_live()
    if asset_type:
        items = [p for p in items if p.asset_type.value == asset_type]
    return json_response({"items": [p.to_dict() for p in items]})


async def tracking_fleet_handler(_request: web.Request) -> web.Response:
    return json_response(port_erp.tracking.fleet.snapshot())


async def tracking_route_handler(request: web.Request) -> web.Response:
    asset_type = request.match_info["asset_type"]
    asset_id = request.match_info["asset_id"]
    return json_response(port_erp.tracking.routes.summary(asset_type, asset_id))


async def tracking_predict_eta_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        pred = await port_erp.tracking.eta.predict_arrival(
            asset_type=data.get("asset_type", "vessel"),
            asset_id=data["asset_id"],
            dest_lat=float(data.get("dest_lat", 0)),
            dest_lon=float(data.get("dest_lon", 0)),
            destination=data.get("destination", ""),
            planned_eta=float(data.get("planned_eta", 0) or 0),
        )
        return json_response(pred.to_dict())
    except (KeyError, TypeError, ValueError) as exc:
        return error_response(str(exc), status=400)


async def vessel_position_handler(request: web.Request) -> web.Response:
    vessel_id = request.match_info["vessel_id"]
    data = await request.json()
    try:
        live = await port_erp.tracking.ais.update_vessel_position(
            vessel_id,
            latitude=float(data["latitude"]),
            longitude=float(data["longitude"]),
            speed_knots=float(data.get("speed_knots", 0) or 0),
            heading_deg=float(data.get("heading_deg", 0) or 0),
            destination=data.get("destination", ""),
            last_checkpoint=data.get("last_checkpoint", ""),
            eta=data.get("eta"),
            etd=data.get("etd"),
        )
        return json_response(live.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)
    except (KeyError, TypeError, ValueError) as exc:
        return error_response(str(exc), status=400)


async def vessel_live_position_handler(request: web.Request) -> web.Response:
    vessel_id = request.match_info["vessel_id"]
    live = port_erp.tracking.ais.get_position(vessel_id)
    if live is None:
        return error_response("position not found", status=404)
    return json_response(live.to_dict())


async def list_vessel_positions_handler(_request: web.Request) -> web.Response:
    return json_response({"items": [p.to_dict() for p in port_erp.tracking.ais.list_positions()]})


async def container_position_handler(request: web.Request) -> web.Response:
    container_id = request.match_info["container_id"]
    data = await request.json()
    try:
        live = await port_erp.tracking.containers.update_position(
            container_id,
            latitude=float(data["latitude"]),
            longitude=float(data["longitude"]),
            status=data.get("status"),
            last_checkpoint=data.get("last_checkpoint", ""),
            destination=data.get("destination", ""),
        )
        return json_response(live.to_dict())
    except (NotFoundError, ValidationError) as exc:
        return error_response(str(exc), status=400 if isinstance(exc, ValidationError) else 404)
    except (KeyError, TypeError, ValueError) as exc:
        return error_response(str(exc), status=400)


async def container_lifecycle_handler(request: web.Request) -> web.Response:
    container_id = request.match_info["container_id"]
    data = await request.json()
    try:
        container = await port_erp.tracking.containers.advance(
            container_id,
            data.get("status", ""),
            location=data.get("location", ""),
            notes=data.get("notes", ""),
        )
        return json_response(container.to_dict())
    except (NotFoundError, ValidationError) as exc:
        return error_response(str(exc), status=400 if isinstance(exc, ValidationError) else 404)


async def container_history_handler(request: web.Request) -> web.Response:
    container_id = request.match_info["container_id"]
    items = port_erp.tracking.containers.history(container_id)
    return json_response({"items": [r.to_dict() for r in items]})


async def container_statuses_handler(_request: web.Request) -> web.Response:
    return json_response({"items": port_erp.tracking.containers.statuses()})


async def gps_register_truck_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        truck = port_erp.tracking.trucks.register_truck(
            TruckTrack(
                plate_number=data.get("plate_number", ""),
                carrier_id=data.get("carrier_id", ""),
                container_id=data.get("container_id", ""),
            )
        )
        return json_response(truck.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def gps_truck_position_handler(request: web.Request) -> web.Response:
    truck_id = request.match_info["truck_id"]
    data = await request.json()
    try:
        live = await port_erp.tracking.trucks.update_position(
            truck_id,
            latitude=float(data["latitude"]),
            longitude=float(data["longitude"]),
            speed_knots=float(data.get("speed_knots", 0) or 0),
            last_checkpoint=data.get("last_checkpoint", ""),
            destination=data.get("destination", ""),
        )
        return json_response(live.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)
    except (KeyError, TypeError, ValueError) as exc:
        return error_response(str(exc), status=400)


async def gps_list_trucks_handler(_request: web.Request) -> web.Response:
    return json_response({"items": [t.to_dict() for t in port_erp.tracking.trucks.list_trucks()]})


async def gps_rail_position_handler(request: web.Request) -> web.Response:
    rail_id = request.match_info["rail_id"]
    data = await request.json()
    try:
        live = await port_erp.tracking.fleet.update_rail_position(
            rail_id,
            latitude=float(data["latitude"]),
            longitude=float(data["longitude"]),
            speed_knots=float(data.get("speed_knots", 0) or 0),
            destination=data.get("destination", ""),
            last_checkpoint=data.get("last_checkpoint", ""),
        )
        return json_response(live.to_dict())
    except (KeyError, TypeError, ValueError) as exc:
        return error_response(str(exc), status=400)


async def maps_viewport_handler(request: web.Request) -> web.Response:
    q = request.query
    return json_response(
        port_erp.tracking.maps.viewport(
            center_lat=float(q.get("lat", 0) or 0),
            center_lon=float(q.get("lon", 0) or 0),
            zoom=int(q.get("zoom", 10) or 10),
        )
    )


async def maps_create_geofence_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        fence = port_erp.tracking.geofences.create(
            Geofence(
                name=data.get("name", ""),
                fence_type=GeofenceType(data.get("fence_type", "port")),
                related_id=data.get("related_id", ""),
                center_lat=float(data.get("center_lat", 0) or 0),
                center_lon=float(data.get("center_lon", 0) or 0),
                radius_m=float(data.get("radius_m", 500) or 500),
            )
        )
        return json_response(fence.to_dict(), status=201)
    except (ValidationError, ValueError) as exc:
        return error_response(str(exc), status=400)


async def maps_list_geofences_handler(_request: web.Request) -> web.Response:
    return json_response({"items": [g.to_dict() for g in port_erp.tracking.geofences.list_geofences()]})


async def timeline_recent_handler(request: web.Request) -> web.Response:
    limit = int(request.query.get("limit", 50) or 50)
    return json_response({"items": [e.to_dict() for e in port_erp.tracking.timeline.recent(limit=limit)]})


async def timeline_asset_handler(request: web.Request) -> web.Response:
    asset_type = request.match_info["asset_type"]
    asset_id = request.match_info["asset_id"]
    items = port_erp.tracking.timeline.for_asset(asset_type, asset_id)
    return json_response({"items": [e.to_dict() for e in items]})
