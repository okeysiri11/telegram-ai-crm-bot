# Port ERP logistics REST handlers — Sprint 9.5.

from __future__ import annotations

from aiohttp import web

from applications.port_erp import port_erp
from applications.port_erp.api.middleware import error_response, json_response
from applications.port_erp.multimodal.models import (
    CarrierContract,
    HubType,
    LogisticsRoute,
    ShippingSchedule,
    TransportBooking,
    TransportMode,
    TransportOrder,
    RouteHub,
)
from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.models import Carrier, Forwarder, ShippingLine


async def shipping_health_handler(_request: web.Request) -> web.Response:
    return json_response(
        {
            "logistics_engine": port_erp.config.logistics_engine,
            "application_version": port_erp.config.application_version,
            "metrics": port_erp.logistics.metrics(),
        }
    )


async def shipping_create_line_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        line = port_erp.logistics.shipping.register_line(
            ShippingLine(name=data.get("name", ""), scac=data.get("scac", ""), country=data.get("country", ""))
        )
        return json_response(line.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def shipping_list_lines_handler(_request: web.Request) -> web.Response:
    return json_response({"items": [l.to_dict() for l in port_erp.logistics.shipping.list_lines()]})


async def shipping_create_schedule_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        schedule = port_erp.logistics.shipping.create_schedule(
            ShippingSchedule(
                shipping_line_id=data.get("shipping_line_id", ""),
                service_name=data.get("service_name", ""),
                vessel_name=data.get("vessel_name", ""),
                voyage_number=data.get("voyage_number", ""),
                origin_port=data.get("origin_port", ""),
                destination_port=data.get("destination_port", ""),
                etd=float(data.get("etd", 0) or 0),
                eta=float(data.get("eta", 0) or 0),
            )
        )
        return json_response(schedule.to_dict(), status=201)
    except (ValidationError, NotFoundError) as exc:
        return error_response(str(exc), status=400 if isinstance(exc, ValidationError) else 404)


async def shipping_list_schedules_handler(request: web.Request) -> web.Response:
    items = port_erp.logistics.shipping.list_schedules(
        shipping_line_id=request.query.get("shipping_line_id") or None
    )
    return json_response({"items": [s.to_dict() for s in items]})


async def shipping_plan_voyage_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        schedule = port_erp.logistics.shipping.plan_voyage(
            request.match_info["schedule_id"],
            voyage_number=data.get("voyage_number", ""),
            vessel_name=data.get("vessel_name", ""),
        )
        return json_response(schedule.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def forwarders_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        fwd = port_erp.logistics.forwarders.register(
            Forwarder(name=data.get("name", ""), country=data.get("country", ""))
        )
        return json_response(fwd.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def forwarders_list_handler(_request: web.Request) -> web.Response:
    return json_response({"items": [f.to_dict() for f in port_erp.logistics.forwarders.list_forwarders()]})


async def forwarders_consolidate_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        batch = port_erp.logistics.forwarders.consolidate(
            forwarder_id=data.get("forwarder_id", ""),
            route_id=data.get("route_id", ""),
            booking_ids=list(data.get("booking_ids") or []),
            container_ids=list(data.get("container_ids") or []),
        )
        return json_response(batch.to_dict(), status=201)
    except (ValidationError, NotFoundError) as exc:
        return error_response(str(exc), status=400 if isinstance(exc, ValidationError) else 404)


async def carriers_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        carrier = port_erp.logistics.carriers.register(
            Carrier(
                name=data.get("name", ""),
                mode=data.get("mode", "truck"),
                contact_email=data.get("contact_email", ""),
            )
        )
        return json_response(carrier.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def carriers_list_handler(request: web.Request) -> web.Response:
    items = port_erp.logistics.carriers.list_carriers(mode=request.query.get("mode") or None)
    return json_response({"items": [c.to_dict() for c in items]})


async def carriers_contract_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        contract = port_erp.logistics.carriers.create_contract(
            CarrierContract(
                carrier_id=data.get("carrier_id", ""),
                partner_id=data.get("partner_id", ""),
                mode=TransportMode(data.get("mode", "sea")),
                rate_per_unit=float(data.get("rate_per_unit", 0) or 0),
                currency=data.get("currency", "USD"),
                terms=data.get("terms", ""),
            )
        )
        return json_response(contract.to_dict(), status=201)
    except (ValidationError, NotFoundError, ValueError) as exc:
        return error_response(str(exc), status=400 if not isinstance(exc, NotFoundError) else 404)


async def routes_create_hub_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        hub = port_erp.logistics.routes.create_hub(
            RouteHub(
                name=data.get("name", ""),
                hub_type=HubType(data.get("hub_type", "port")),
                country=data.get("country", ""),
                latitude=float(data.get("latitude", 0) or 0),
                longitude=float(data.get("longitude", 0) or 0),
            )
        )
        return json_response(hub.to_dict(), status=201)
    except (ValidationError, ValueError) as exc:
        return error_response(str(exc), status=400)


async def routes_list_hubs_handler(request: web.Request) -> web.Response:
    hub_type = request.query.get("hub_type")
    items = port_erp.logistics.routes.list_hubs(hub_type=HubType(hub_type) if hub_type else None)
    return json_response({"items": [h.to_dict() for h in items]})


async def routes_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        route = port_erp.logistics.routes.create_route(
            LogisticsRoute(
                name=data.get("name", ""),
                origin_hub_id=data.get("origin_hub_id", ""),
                destination_hub_id=data.get("destination_hub_id", ""),
                door_to_door=bool(data.get("door_to_door", False)),
            )
        )
        for leg_data in data.get("legs") or []:
            leg = port_erp.logistics.routes.build_leg(
                mode=leg_data.get("mode", "road"),
                from_hub_id=leg_data.get("from_hub_id", ""),
                to_hub_id=leg_data.get("to_hub_id", ""),
                distance_km=float(leg_data.get("distance_km", 0) or 0),
                duration_hours=float(leg_data.get("duration_hours", 0) or 0),
                cost=float(leg_data.get("cost", 0) or 0),
                carrier_id=leg_data.get("carrier_id", ""),
            )
            route = port_erp.logistics.routes.add_leg(route.route_id, leg)
        return json_response(route.to_dict(), status=201)
    except (ValidationError, NotFoundError, ValueError) as exc:
        return error_response(str(exc), status=400 if not isinstance(exc, NotFoundError) else 404)


async def routes_list_handler(_request: web.Request) -> web.Response:
    return json_response({"items": [r.to_dict() for r in port_erp.logistics.routes.list_routes()]})


async def routes_optimize_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
    except Exception:
        data = {}
    try:
        route = await port_erp.logistics.routes.optimize(
            request.match_info["route_id"],
            optimize_for=(data or {}).get("optimize_for", "eta"),
        )
        return json_response(route.to_dict())
    except (ValidationError, NotFoundError) as exc:
        return error_response(str(exc), status=400 if isinstance(exc, ValidationError) else 404)


async def bookings_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        booking = await port_erp.logistics.bookings.create(
            TransportBooking(
                forwarder_id=data.get("forwarder_id", ""),
                customer_id=data.get("customer_id", ""),
                shipping_line_id=data.get("shipping_line_id", ""),
                carrier_id=data.get("carrier_id", ""),
                route_id=data.get("route_id", ""),
                container_id=data.get("container_id", ""),
                mode=TransportMode(data.get("mode", "sea")),
                origin=data.get("origin", ""),
                destination=data.get("destination", ""),
                notes=data.get("notes", ""),
            )
        )
        return json_response(booking.to_dict(), status=201)
    except (ValidationError, ValueError) as exc:
        return error_response(str(exc), status=400)


async def bookings_list_handler(_request: web.Request) -> web.Response:
    return json_response(
        {
            "items": [b.to_dict() for b in port_erp.logistics.bookings.list_bookings()],
            "workflow": port_erp.logistics.bookings.workflow_statuses(),
        }
    )


async def bookings_quote_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        booking = port_erp.logistics.bookings.quote(
            request.match_info["booking_id"],
            amount=float(data.get("amount", 0) or 0),
            currency=data.get("currency", "USD"),
        )
        return json_response(booking.to_dict())
    except (ValidationError, NotFoundError) as exc:
        return error_response(str(exc), status=400 if isinstance(exc, ValidationError) else 404)


async def bookings_confirm_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
    except Exception:
        data = {}
    try:
        booking = await port_erp.logistics.bookings.confirm(
            request.match_info["booking_id"],
            carrier_id=(data or {}).get("carrier_id", ""),
        )
        return json_response(booking.to_dict())
    except (ValidationError, NotFoundError) as exc:
        return error_response(str(exc), status=400 if isinstance(exc, ValidationError) else 404)


async def bookings_execute_handler(request: web.Request) -> web.Response:
    try:
        booking = port_erp.logistics.bookings.execute(request.match_info["booking_id"])
        return json_response(booking.to_dict())
    except (ValidationError, NotFoundError) as exc:
        return error_response(str(exc), status=400 if isinstance(exc, ValidationError) else 404)


async def bookings_complete_handler(request: web.Request) -> web.Response:
    try:
        booking = port_erp.logistics.bookings.complete(request.match_info["booking_id"])
        return json_response(booking.to_dict())
    except (ValidationError, NotFoundError) as exc:
        return error_response(str(exc), status=400 if isinstance(exc, ValidationError) else 404)


async def bookings_cancel_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
    except Exception:
        data = {}
    try:
        booking = port_erp.logistics.bookings.cancel(
            request.match_info["booking_id"],
            notes=(data or {}).get("notes", ""),
        )
        return json_response(booking.to_dict())
    except (ValidationError, NotFoundError) as exc:
        return error_response(str(exc), status=400 if isinstance(exc, ValidationError) else 404)


async def transport_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        order = port_erp.logistics.transport.create(
            TransportOrder(
                booking_id=data.get("booking_id", ""),
                carrier_id=data.get("carrier_id", ""),
                route_id=data.get("route_id", ""),
                container_id=data.get("container_id", ""),
                mode=TransportMode(data.get("mode", "road")),
                origin=data.get("origin", ""),
                destination=data.get("destination", ""),
            )
        )
        return json_response(order.to_dict(), status=201)
    except (ValidationError, ValueError) as exc:
        return error_response(str(exc), status=400)


async def transport_list_handler(_request: web.Request) -> web.Response:
    return json_response({"items": [o.to_dict() for o in port_erp.logistics.transport.list_orders()]})


async def transport_assign_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        order = await port_erp.logistics.transport.assign(
            request.match_info["order_id"],
            carrier_id=data.get("carrier_id", ""),
            fleet_asset_id=data.get("fleet_asset_id", ""),
        )
        return json_response(order.to_dict())
    except (ValidationError, NotFoundError) as exc:
        return error_response(str(exc), status=400 if isinstance(exc, ValidationError) else 404)


async def transport_dispatch_handler(request: web.Request) -> web.Response:
    try:
        order = await port_erp.logistics.transport.dispatch(request.match_info["order_id"])
        return json_response(order.to_dict())
    except (ValidationError, NotFoundError) as exc:
        return error_response(str(exc), status=400 if isinstance(exc, ValidationError) else 404)


async def transport_complete_handler(request: web.Request) -> web.Response:
    try:
        order = await port_erp.logistics.transport.complete(request.match_info["order_id"])
        return json_response(order.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def transport_transfer_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        order = await port_erp.logistics.multimodal.transfer_mode(
            request.match_info["order_id"],
            to_mode=data.get("to_mode", "rail"),
            hub_id=data.get("hub_id", ""),
        )
        return json_response(order.to_dict())
    except (ValidationError, NotFoundError, ValueError) as exc:
        return error_response(str(exc), status=400 if not isinstance(exc, NotFoundError) else 404)
