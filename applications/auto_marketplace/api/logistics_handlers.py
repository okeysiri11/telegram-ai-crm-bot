# Sprint 10.6 REST handlers — transport, tracking, import, export, customs, carriers.

from __future__ import annotations

from aiohttp import web

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.middleware import error_response, json_response
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.transport.models import (
    Carrier,
    CarrierKind,
    CustomsDeclaration,
    FleetMovement,
    ShipmentKind,
    TradeShipment,
    TransportMode,
    VehicleShipment,
)


def _carrier_kind(value: str) -> CarrierKind:
    try:
        return CarrierKind(value or "company")
    except ValueError as exc:
        raise ValidationError(f"invalid carrier kind: {value}") from exc


def _shipment_kind(value: str) -> ShipmentKind:
    try:
        return ShipmentKind(value or "door_to_door")
    except ValueError as exc:
        raise ValidationError(f"invalid shipment kind: {value}") from exc


def _mode(value: str) -> TransportMode:
    try:
        return TransportMode(value or "truck")
    except ValueError as exc:
        raise ValidationError(f"invalid transport mode: {value}") from exc


async def transport_health_handler(_request: web.Request) -> web.Response:
    return json_response(
        {
            "transport_engine": auto_marketplace.config.transport_engine,
            "application_version": auto_marketplace.config.application_version,
            "metrics": auto_marketplace.logistics.metrics(),
        }
    )


async def transport_shipments_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            items = auto_marketplace.logistics.transport.list_shipments(
                status=request.query.get("status", ""),
                kind=request.query.get("kind", ""),
            )
            return json_response({"items": [s.to_dict() for s in items]})
        data = await request.json()
        shipment = auto_marketplace.logistics.transport.create(
            VehicleShipment(
                vehicle_id=data.get("vehicle_id", ""),
                vin=data.get("vin", ""),
                kind=_shipment_kind(data.get("kind", "door_to_door")),
                mode=_mode(data.get("mode", "truck")),
                origin=data.get("origin", ""),
                destination=data.get("destination", ""),
                origin_country=data.get("origin_country", ""),
                destination_country=data.get("destination_country", ""),
                stops=list(data.get("stops") or []),
                currency=data.get("currency", "USD"),
            )
        )
        return json_response(shipment.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def transport_book_handler(request: web.Request) -> web.Response:
    try:
        shipment = auto_marketplace.logistics.transport.book(request.match_info["shipment_id"])
        return json_response(shipment.to_dict())
    except (NotFoundError, ValidationError) as exc:
        return error_response(str(exc), status=404 if isinstance(exc, NotFoundError) else 400)


async def transport_dispatch_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        job = auto_marketplace.logistics.dispatch.dispatch(
            request.match_info["shipment_id"],
            carrier_id=data.get("carrier_id", ""),
            driver_id=data.get("driver_id", ""),
        )
        return json_response(job)
    except (NotFoundError, ValidationError) as exc:
        return error_response(str(exc), status=404 if isinstance(exc, NotFoundError) else 400)


async def transport_transit_handler(request: web.Request) -> web.Response:
    try:
        shipment = auto_marketplace.logistics.transport.start_transit(request.match_info["shipment_id"])
        return json_response(shipment.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def transport_deliver_handler(request: web.Request) -> web.Response:
    try:
        result = auto_marketplace.logistics.delivery.complete(request.match_info["shipment_id"])
        return json_response(result)
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def transport_optimize_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        route = auto_marketplace.logistics.routes.optimize(
            shipment_id=data.get("shipment_id", ""),
            origin=data.get("origin", ""),
            destination=data.get("destination", ""),
            stops=list(data.get("stops") or []),
            border_crossings=list(data.get("border_crossings") or []),
            weather_factor=float(data.get("weather_factor", 1.0) or 1.0),
            traffic_factor=float(data.get("traffic_factor", 1.1) or 1.1),
        )
        return json_response(route.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def transport_ai_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        action = data.get("action", "carrier")
        sid = data.get("shipment_id", "")
        if action == "carrier":
            return json_response(
                {"items": auto_marketplace.logistics.transport.ai_carrier_recommendation(
                    mode=data.get("mode", "truck"), country=data.get("country", "")
                )}
            )
        if action == "delivery":
            return json_response(auto_marketplace.logistics.transport.ai_delivery_prediction(sid))
        if action == "delay":
            return json_response(auto_marketplace.logistics.transport.ai_delay_forecast(sid))
        if action == "risk":
            return json_response(auto_marketplace.logistics.transport.ai_risk_prediction(sid))
        if action == "customs":
            return json_response(auto_marketplace.logistics.customs.assistant_advice(data.get("customs_id", "")))
        return error_response("unknown ai action", status=400)
    except (NotFoundError, ValidationError) as exc:
        return error_response(str(exc), status=404 if isinstance(exc, NotFoundError) else 400)


async def transport_fleet_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        movement = auto_marketplace.logistics.fleet.plan(
            FleetMovement(
                kind=data.get("kind", "dealer"),
                vehicle_ids=list(data.get("vehicle_ids") or []),
                from_location=data.get("from_location", ""),
                to_location=data.get("to_location", ""),
                carrier_id=data.get("carrier_id", ""),
            )
        )
        return json_response(movement.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def tracking_health_handler(_request: web.Request) -> web.Response:
    return json_response(
        {
            "tracking_engine": auto_marketplace.config.tracking_engine,
            "metrics": auto_marketplace.logistics.tracking.metrics(),
        }
    )


async def tracking_get_handler(request: web.Request) -> web.Response:
    try:
        session = auto_marketplace.logistics.tracking.get(request.match_info["tracking_id"])
        return json_response(session.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def tracking_gps_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        session = auto_marketplace.logistics.tracking.update_gps(
            request.match_info["tracking_id"],
            lat=float(data.get("lat", 0) or 0),
            lon=float(data.get("lon", 0) or 0),
            status=data.get("status", "in_transit"),
        )
        return json_response(session.to_dict())
    except (NotFoundError, ValidationError) as exc:
        return error_response(str(exc), status=404 if isinstance(exc, NotFoundError) else 400)


async def tracking_eta_handler(request: web.Request) -> web.Response:
    try:
        return json_response(auto_marketplace.logistics.tracking.predict_eta(request.match_info["tracking_id"]))
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def tracking_timeline_handler(request: web.Request) -> web.Response:
    try:
        return json_response({"items": auto_marketplace.logistics.tracking.timeline(request.match_info["tracking_id"])})
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def carriers_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            items = auto_marketplace.logistics.carriers.list_carriers(
                kind=request.query.get("kind", ""),
                mode=request.query.get("mode", ""),
            )
            return json_response({"items": [c.to_dict() for c in items]})
        data = await request.json()
        carrier = auto_marketplace.logistics.carriers.register(
            Carrier(
                name=data.get("name", ""),
                kind=_carrier_kind(data.get("kind", "company")),
                modes=list(data.get("modes") or ["truck"]),
                rating=float(data.get("rating", 0) or 0),
                countries=list(data.get("countries") or []),
            )
        )
        return json_response(carrier.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def carriers_rate_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        carrier = auto_marketplace.logistics.carriers.rate(
            request.match_info["carrier_id"], float(data.get("score", 0) or 0)
        )
        return json_response(carrier.to_dict())
    except (NotFoundError, ValidationError) as exc:
        return error_response(str(exc), status=404 if isinstance(exc, NotFoundError) else 400)


async def carriers_driver_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        carrier = auto_marketplace.logistics.carriers.add_driver(
            request.match_info["carrier_id"],
            name=data.get("name", ""),
            license_id=data.get("license_id", ""),
        )
        return json_response(carrier.to_dict())
    except (NotFoundError, ValidationError) as exc:
        return error_response(str(exc), status=404 if isinstance(exc, NotFoundError) else 400)


async def import_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            items = auto_marketplace.logistics.import_export.list_trades(direction="import")
            return json_response({"items": [t.to_dict() for t in items]})
        data = await request.json()
        trade = auto_marketplace.logistics.import_export.create_trade(
            TradeShipment(
                direction="import",
                vehicle_id=data.get("vehicle_id", ""),
                vin=data.get("vin", ""),
                origin_country=data.get("origin_country", ""),
                destination_country=data.get("destination_country", ""),
                shipment_id=data.get("shipment_id", ""),
            ),
            vehicle_value=float(data.get("vehicle_value", 0) or 0),
        )
        return json_response(trade.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def export_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            items = auto_marketplace.logistics.import_export.list_trades(direction="export")
            return json_response({"items": [t.to_dict() for t in items]})
        data = await request.json()
        trade = auto_marketplace.logistics.import_export.create_trade(
            TradeShipment(
                direction="export",
                vehicle_id=data.get("vehicle_id", ""),
                vin=data.get("vin", ""),
                origin_country=data.get("origin_country", ""),
                destination_country=data.get("destination_country", ""),
                shipment_id=data.get("shipment_id", ""),
            ),
            vehicle_value=float(data.get("vehicle_value", 0) or 0),
        )
        return json_response(trade.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def trade_approve_handler(request: web.Request) -> web.Response:
    try:
        trade = auto_marketplace.logistics.import_export.approve(request.match_info["trade_id"])
        return json_response(trade.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def customs_health_handler(_request: web.Request) -> web.Response:
    return json_response(
        {
            "customs_engine": auto_marketplace.config.customs_engine,
            "metrics": auto_marketplace.logistics.customs.metrics(),
        }
    )


async def customs_create_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        declaration = auto_marketplace.logistics.customs.create(
            CustomsDeclaration(
                shipment_id=data.get("shipment_id", ""),
                vin=data.get("vin", ""),
                checkpoint=data.get("checkpoint", ""),
            )
        )
        return json_response(declaration.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def customs_submit_handler(request: web.Request) -> web.Response:
    try:
        data = {}
        try:
            data = await request.json()
        except Exception:
            data = {}
        declaration = auto_marketplace.logistics.customs.submit(
            request.match_info["customs_id"],
            checkpoint=(data or {}).get("checkpoint", ""),
        )
        return json_response(declaration.to_dict())
    except (NotFoundError, ValidationError) as exc:
        return error_response(str(exc), status=404 if isinstance(exc, NotFoundError) else 400)


async def customs_clear_handler(request: web.Request) -> web.Response:
    try:
        declaration = auto_marketplace.logistics.customs.clear(request.match_info["customs_id"])
        return json_response(declaration.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def customs_broker_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        declaration = auto_marketplace.logistics.customs.assign_broker(
            request.match_info["customs_id"],
            broker_id=data.get("broker_id", ""),
            broker_name=data.get("broker_name", ""),
        )
        return json_response(declaration.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)
