# Port ERP REST handlers — Sprint 9.1 foundation.

from __future__ import annotations

from aiohttp import web

from applications.port_erp import port_erp
from applications.port_erp.api.middleware import error_response, json_response
from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.models import (
    Berth,
    Cargo,
    Carrier,
    Container,
    Customer,
    CustomsBroker,
    Forwarder,
    Gate,
    Port,
    PortOperator,
    ShippingLine,
    Terminal,
    Vessel,
    Voyage,
    Warehouse,
)


async def health_handler(_request: web.Request) -> web.Response:
    return json_response(port_erp.health())


async def roles_handler(_request: web.Request) -> web.Response:
    return json_response({"items": port_erp.permissions.roles()})


async def list_ports_handler(request: web.Request) -> web.Response:
    items = port_erp.core.ports.list_ports(country=request.query.get("country") or None)
    return json_response({"items": [p.to_dict() for p in items]})


async def create_port_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        port = port_erp.core.ports.register(
            Port(
                name=data.get("name", ""),
                code=data.get("code", ""),
                country=data.get("country", ""),
                city=data.get("city", ""),
                timezone=data.get("timezone", "UTC"),
            )
        )
        return json_response(port.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def get_port_handler(request: web.Request) -> web.Response:
    try:
        return json_response(port_erp.core.ports.get(request.match_info["port_id"]).to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def list_terminals_handler(request: web.Request) -> web.Response:
    items = port_erp.core.terminals.list_terminals(port_id=request.query.get("port_id") or None)
    return json_response({"items": [t.to_dict() for t in items]})


async def create_terminal_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        terminal = port_erp.core.terminals.register(
            Terminal(
                port_id=data.get("port_id", ""),
                name=data.get("name", ""),
                terminal_type=data.get("terminal_type", "container"),
                capacity_teu=int(data.get("capacity_teu", 0)),
            )
        )
        return json_response(terminal.to_dict(), status=201)
    except (ValidationError, NotFoundError) as exc:
        status = 404 if isinstance(exc, NotFoundError) else 400
        return error_response(str(exc), status=status)


async def list_berths_handler(request: web.Request) -> web.Response:
    items = port_erp.core.berths.list_berths(terminal_id=request.query.get("terminal_id") or None)
    return json_response({"items": [b.to_dict() for b in items]})


async def create_berth_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        berth = port_erp.core.berths.register(
            Berth(
                terminal_id=data.get("terminal_id", ""),
                port_id=data.get("port_id", ""),
                name=data.get("name", ""),
                length_m=float(data.get("length_m", 0)),
                max_draft_m=float(data.get("max_draft_m", 0)),
            )
        )
        return json_response(berth.to_dict(), status=201)
    except (ValidationError, NotFoundError) as exc:
        status = 404 if isinstance(exc, NotFoundError) else 400
        return error_response(str(exc), status=status)


async def assign_berth_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        berth = await port_erp.core.berths.assign(
            request.match_info["berth_id"],
            vessel_id=data.get("vessel_id", ""),
            voyage_id=data.get("voyage_id", ""),
        )
        return json_response(berth.to_dict())
    except (ValidationError, NotFoundError) as exc:
        status = 404 if isinstance(exc, NotFoundError) else 400
        return error_response(str(exc), status=status)


async def list_containers_handler(request: web.Request) -> web.Response:
    items = port_erp.core.containers.list_containers()
    return json_response({"items": [c.to_dict() for c in items]})


async def create_container_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        container = port_erp.core.containers.register(
            Container(
                container_number=data.get("container_number", ""),
                container_type=data.get("container_type", "40HC"),
                iso_code=data.get("iso_code", "45G1"),
                owner=data.get("owner", ""),
                voyage_id=data.get("voyage_id", ""),
                vessel_id=data.get("vessel_id", ""),
                terminal_id=data.get("terminal_id", ""),
                weight_kg=float(data.get("weight_kg", 0)),
            )
        )
        return json_response(container.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def receive_container_handler(request: web.Request) -> web.Response:
    data = {}
    try:
        data = await request.json()
    except Exception:
        data = {}
    try:
        container = await port_erp.core.containers.receive(
            request.match_info["container_id"],
            terminal_id=data.get("terminal_id", ""),
        )
        return json_response(container.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def list_cargo_handler(request: web.Request) -> web.Response:
    items = port_erp.core.cargo.list_cargo(customer_id=request.query.get("customer_id") or None)
    return json_response({"items": [c.to_dict() for c in items]})


async def create_cargo_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        cargo = port_erp.core.cargo.register(
            Cargo(
                description=data.get("description", ""),
                hs_code=data.get("hs_code", ""),
                container_id=data.get("container_id", ""),
                voyage_id=data.get("voyage_id", ""),
                customer_id=data.get("customer_id", ""),
                weight_tons=float(data.get("weight_tons", 0)),
                volume_cbm=float(data.get("volume_cbm", 0)),
            )
        )
        return json_response(cargo.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def list_customers_handler(_request: web.Request) -> web.Response:
    return json_response({"items": [c.to_dict() for c in port_erp.core.customers.list_customers()]})


async def create_customer_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        customer = port_erp.core.customers.register(
            Customer(
                name=data.get("name", ""),
                email=data.get("email", ""),
                company=data.get("company", ""),
                country=data.get("country", ""),
            )
        )
        return json_response(customer.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def list_companies_handler(_request: web.Request) -> web.Response:
    return json_response(port_erp.core.companies.list_companies())


async def create_shipping_line_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        line = port_erp.core.companies.register_shipping_line(
            ShippingLine(
                name=data.get("name", ""),
                scac=data.get("scac", ""),
                country=data.get("country", ""),
                contact_email=data.get("contact_email", ""),
            )
        )
        return json_response(line.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def create_forwarder_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        fwd = port_erp.core.companies.register_forwarder(
            Forwarder(
                name=data.get("name", ""),
                license_number=data.get("license_number", ""),
                email=data.get("email", ""),
                country=data.get("country", ""),
            )
        )
        return json_response(fwd.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def create_broker_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        broker = port_erp.core.companies.register_broker(
            CustomsBroker(
                name=data.get("name", ""),
                license_number=data.get("license_number", ""),
                email=data.get("email", ""),
                country=data.get("country", ""),
            )
        )
        return json_response(broker.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def create_carrier_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        carrier = port_erp.core.companies.register_carrier(
            Carrier(
                name=data.get("name", ""),
                mode=data.get("mode", "truck"),
                contact_email=data.get("contact_email", ""),
            )
        )
        return json_response(carrier.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def create_operator_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        operator = port_erp.core.companies.register_operator(
            PortOperator(
                name=data.get("name", ""),
                port_id=data.get("port_id", ""),
                email=data.get("email", ""),
                role=data.get("role", "operator"),
            )
        )
        return json_response(operator.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def list_vessels_handler(_request: web.Request) -> web.Response:
    return json_response({"items": [v.to_dict() for v in port_erp.core.vessels.list_vessels()]})


async def create_vessel_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        vessel = port_erp.core.vessels.register(
            Vessel(
                name=data.get("name", ""),
                imo=data.get("imo", ""),
                call_sign=data.get("call_sign", ""),
                flag=data.get("flag", ""),
                vessel_type=data.get("vessel_type", "container"),
                loa_m=float(data.get("loa_m", 0)),
                draft_m=float(data.get("draft_m", 0)),
                shipping_line_id=data.get("shipping_line_id", ""),
            )
        )
        return json_response(vessel.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def create_voyage_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        voyage = port_erp.core.vessels.create_voyage(
            Voyage(
                vessel_id=data.get("vessel_id", ""),
                voyage_number=data.get("voyage_number", ""),
                origin_port_id=data.get("origin_port_id", ""),
                destination_port_id=data.get("destination_port_id", ""),
                eta=float(data.get("eta", 0)),
                etd=float(data.get("etd", 0)),
            )
        )
        return json_response(voyage.to_dict(), status=201)
    except (ValidationError, NotFoundError) as exc:
        status = 404 if isinstance(exc, NotFoundError) else 400
        return error_response(str(exc), status=status)


async def voyage_arrive_handler(request: web.Request) -> web.Response:
    data = {}
    try:
        data = await request.json()
    except Exception:
        data = {}
    try:
        voyage = await port_erp.core.vessels.arrive(
            request.match_info["voyage_id"],
            port_id=data.get("port_id", ""),
        )
        return json_response(voyage.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def voyage_depart_handler(request: web.Request) -> web.Response:
    data = {}
    try:
        data = await request.json()
    except Exception:
        data = {}
    try:
        voyage = await port_erp.core.vessels.depart(
            request.match_info["voyage_id"],
            port_id=data.get("port_id", ""),
        )
        return json_response(voyage.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def operations_metrics_handler(_request: web.Request) -> web.Response:
    return json_response(port_erp.core.operations.metrics())


async def create_warehouse_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        wh = port_erp.core.operations.register_warehouse(
            Warehouse(
                port_id=data.get("port_id", ""),
                terminal_id=data.get("terminal_id", ""),
                name=data.get("name", ""),
                capacity_tons=float(data.get("capacity_tons", 0)),
            )
        )
        return json_response(wh.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def create_gate_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        gate = port_erp.core.operations.register_gate(
            Gate(
                port_id=data.get("port_id", ""),
                terminal_id=data.get("terminal_id", ""),
                name=data.get("name", ""),
                gate_type=data.get("gate_type", "in"),
            )
        )
        return json_response(gate.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def open_gate_handler(request: web.Request) -> web.Response:
    try:
        gate = await port_erp.core.operations.open_gate(request.match_info["gate_id"])
        return json_response(gate.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def close_gate_handler(request: web.Request) -> web.Response:
    try:
        gate = await port_erp.core.operations.close_gate(request.match_info["gate_id"])
        return json_response(gate.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)
