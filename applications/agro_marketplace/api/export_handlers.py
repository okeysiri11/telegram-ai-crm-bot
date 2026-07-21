# Export / Logistics / Shipment / Tracking / Documents API — Sprint 8.5.

from __future__ import annotations

from aiohttp import web

from applications.agro_marketplace import agro_marketplace
from applications.agro_marketplace.api.middleware import error_response, json_response
from applications.agro_marketplace.export.models import (
    Carrier,
    Container,
    IncotermCode,
    InsurancePolicy,
    InternationalExportShipment,
    Port,
    ShipmentItem,
    Terminal,
)
from applications.agro_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.agro_marketplace.shared.models import Delivery


async def export_health_handler(_request: web.Request) -> web.Response:
    return json_response(
        {
            "export_engine": agro_marketplace.config.export_engine,
            "application_version": agro_marketplace.config.application_version,
            "export": agro_marketplace.export_engine.metrics(),
            "logistics": agro_marketplace.logistics_engine.metrics(),
        }
    )


async def export_create_shipment_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        shipment = await agro_marketplace.export_engine.create_shipment(
            InternationalExportShipment(
                order_id=data.get("order_id", ""),
                contract_id=data.get("contract_id", ""),
                exporter_id=data.get("exporter_id", ""),
                buyer_id=data.get("buyer_id", ""),
                origin_country=data.get("origin_country", ""),
                destination_country=data.get("destination_country", ""),
                origin_port_id=data.get("origin_port_id", ""),
                destination_port_id=data.get("destination_port_id", ""),
                carrier_id=data.get("carrier_id", ""),
                warehouse_id=data.get("warehouse_id", ""),
                incoterm=IncotermCode(data.get("incoterm", "FOB")),
            )
        )
        return json_response(shipment.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def export_list_shipments_handler(request: web.Request) -> web.Response:
    items = agro_marketplace.export_engine.list_shipments()
    return json_response({"items": [s.to_dict() for s in items]})


async def export_get_shipment_handler(request: web.Request) -> web.Response:
    try:
        shipment = agro_marketplace.export_engine.get_shipment(request.match_info["shipment_id"])
        return json_response(shipment.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def export_add_item_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        item = agro_marketplace.export_engine.add_item(
            ShipmentItem(
                shipment_id=request.match_info["shipment_id"],
                product_id=data.get("product_id", ""),
                description=data.get("description", ""),
                quantity=float(data.get("quantity", 0)),
                unit_value=float(data.get("unit_value", 0)),
                hs_code=data.get("hs_code", ""),
            )
        )
        return json_response(item.to_dict(), status=201)
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def export_prepare_docs_handler(request: web.Request) -> web.Response:
    data = {}
    try:
        data = await request.json()
    except Exception:
        data = {}
    try:
        docs = await agro_marketplace.export_engine.prepare_documents(
            request.match_info["shipment_id"],
            cargo_value=float(data.get("cargo_value", 0)),
        )
        return json_response({"items": docs})
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def export_verify_docs_handler(request: web.Request) -> web.Response:
    try:
        result = await agro_marketplace.export_engine.verify_documents(request.match_info["shipment_id"])
        return json_response(result)
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def export_risk_handler(request: web.Request) -> web.Response:
    try:
        result = await agro_marketplace.export_engine.assess_risk(request.match_info["shipment_id"])
        return json_response(result)
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def export_dispatch_handler(request: web.Request) -> web.Response:
    try:
        shipment = await agro_marketplace.export_engine.dispatch(request.match_info["shipment_id"])
        return json_response(shipment.to_dict())
    except (NotFoundError, ValidationError) as exc:
        status = 404 if isinstance(exc, NotFoundError) else 400
        return error_response(str(exc), status=status)


async def export_arrive_handler(request: web.Request) -> web.Response:
    data = {}
    try:
        data = await request.json()
    except Exception:
        data = {}
    try:
        shipment = await agro_marketplace.export_engine.arrive_port(
            request.match_info["shipment_id"],
            port_id=data.get("port_id", ""),
        )
        return json_response(shipment.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def export_customs_handler(request: web.Request) -> web.Response:
    data = {}
    try:
        data = await request.json()
    except Exception:
        data = {}
    try:
        result = await agro_marketplace.export_engine.clear_customs(
            request.match_info["shipment_id"],
            country=data.get("country", ""),
        )
        return json_response(result)
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def export_deliver_handler(request: web.Request) -> web.Response:
    data = {}
    try:
        data = await request.json()
    except Exception:
        data = {}
    try:
        shipment = await agro_marketplace.export_engine.confirm_delivery(
            request.match_info["shipment_id"],
            location=data.get("location", ""),
        )
        return json_response(shipment.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def export_complete_handler(request: web.Request) -> web.Response:
    try:
        shipment = await agro_marketplace.export_engine.complete_export(request.match_info["shipment_id"])
        return json_response(shipment.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def logistics_plan_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        result = await agro_marketplace.logistics_engine.plan_shipment(
            InternationalExportShipment(
                order_id=data.get("order_id", ""),
                exporter_id=data.get("exporter_id", ""),
                buyer_id=data.get("buyer_id", ""),
                origin_country=data.get("origin_country", ""),
                destination_country=data.get("destination_country", ""),
                origin_port_id=data.get("origin_port_id", ""),
                destination_port_id=data.get("destination_port_id", ""),
                warehouse_id=data.get("warehouse_id", ""),
                incoterm=IncotermCode(data.get("incoterm", "FOB")),
            ),
            estimated_days=int(data.get("estimated_days", 18)),
        )
        return json_response(result, status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def logistics_dispatch_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        result = await agro_marketplace.logistics_engine.warehouse_dispatch(
            shipment_id=data.get("shipment_id", ""),
            warehouse_id=data.get("warehouse_id", ""),
            quantity_tons=float(data.get("quantity_tons", 0)),
            product_id=data.get("product_id", ""),
        )
        return json_response(result, status=201)
    except (NotFoundError, ValidationError) as exc:
        status = 404 if isinstance(exc, NotFoundError) else 400
        return error_response(str(exc), status=status)


async def logistics_schedule_delivery_handler(request: web.Request) -> web.Response:
    data = await request.json()
    delivery = agro_marketplace.logistics_engine.schedule_delivery(
        Delivery(
            order_id=data.get("order_id", ""),
            carrier=data.get("carrier", ""),
            origin=data.get("origin", ""),
            destination=data.get("destination", ""),
        )
    )
    return json_response(delivery.to_dict(), status=201)


async def ports_list_handler(request: web.Request) -> web.Response:
    items = agro_marketplace.ports.list_ports(country=request.query.get("country") or None)
    return json_response({"items": [p.to_dict() for p in items]})


async def ports_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        port = agro_marketplace.ports.create_port(
            Port(
                name=data.get("name", ""),
                code=data.get("code", ""),
                country=data.get("country", ""),
                city=data.get("city", ""),
                port_type=data.get("port_type", "sea"),
            )
        )
        return json_response(port.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def terminals_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        terminal = agro_marketplace.ports.create_terminal(
            Terminal(
                port_id=data.get("port_id", ""),
                name=data.get("name", ""),
                terminal_type=data.get("terminal_type", "container"),
                capacity_teu=int(data.get("capacity_teu", 0)),
            )
        )
        return json_response(terminal.to_dict(), status=201)
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def carriers_list_handler(request: web.Request) -> web.Response:
    items = agro_marketplace.shipping.list_carriers(mode=request.query.get("mode") or None)
    return json_response({"items": [c.to_dict() for c in items]})


async def carriers_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        carrier = agro_marketplace.shipping.create_carrier(
            Carrier(
                name=data.get("name", ""),
                mode=data.get("mode", "sea"),
                countries=list(data.get("countries", [])),
                rating=float(data.get("rating", 0)),
                contact_email=data.get("contact_email", ""),
            )
        )
        return json_response(carrier.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def carriers_recommend_handler(request: web.Request) -> web.Response:
    country = request.query.get("country", "")
    items = await agro_marketplace.shipping.recommend_carriers(
        country,
        mode=request.query.get("mode", "sea"),
    )
    return json_response({"items": items})


async def containers_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    container = agro_marketplace.containers.create_container(
        Container(
            container_number=data.get("container_number", ""),
            container_type=data.get("container_type", "40HC"),
            capacity_cbm=float(data.get("capacity_cbm", 67)),
            max_weight_tons=float(data.get("max_weight_tons", 26)),
        )
    )
    return json_response(container.to_dict(), status=201)


async def containers_load_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        load = await agro_marketplace.containers.load_container(
            container_id=data.get("container_id", request.match_info.get("container_id", "")),
            shipment_id=data.get("shipment_id", ""),
            product_id=data.get("product_id", ""),
            quantity_tons=float(data.get("quantity_tons", 0)),
            volume_cbm=float(data.get("volume_cbm", 0)),
        )
        return json_response(load.to_dict(), status=201)
    except (NotFoundError, ValidationError) as exc:
        status = 404 if isinstance(exc, NotFoundError) else 400
        return error_response(str(exc), status=status)


async def tracking_timeline_handler(request: web.Request) -> web.Response:
    items = agro_marketplace.tracking.timeline(request.match_info["shipment_id"])
    return json_response({"items": [e.to_dict() for e in items]})


async def documents_list_handler(request: web.Request) -> web.Response:
    items = agro_marketplace.trade_documents.list_documents(
        shipment_id=request.query.get("shipment_id") or request.match_info.get("shipment_id")
    )
    return json_response({"items": [d.to_dict() for d in items]})


async def documents_verify_handler(request: web.Request) -> web.Response:
    try:
        doc = agro_marketplace.trade_documents.verify(request.match_info["document_id"])
        return json_response(doc.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def incoterms_list_handler(_request: web.Request) -> web.Response:
    return json_response({"items": [i.to_dict() for i in agro_marketplace.incoterms.list_incoterms()]})


async def insurance_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        policy = agro_marketplace.insurance.create_policy(
            InsurancePolicy(
                shipment_id=data.get("shipment_id", ""),
                insurer=data.get("insurer", ""),
                coverage_amount=float(data.get("coverage_amount", 0)),
                currency=data.get("currency", "USD"),
            )
        )
        return json_response(policy.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def finance_estimate_handler(request: web.Request) -> web.Response:
    data = await request.json()
    record = agro_marketplace.freight_finance.estimate(
        shipment_id=data.get("shipment_id", ""),
        freight_cost=float(data.get("freight_cost", 0)),
        coverage_amount=float(data.get("coverage_amount", 0)),
        cargo_value=float(data.get("cargo_value", 0)),
        duties_rate=float(data.get("duties_rate", 0.05)),
    )
    return json_response(record.to_dict(), status=201)


async def country_requirements_handler(request: web.Request) -> web.Response:
    country = request.match_info["country"]
    req = agro_marketplace.trade_documents.country_requirements(country)
    if req is None:
        return json_response({"country": country, "required_documents": []})
    return json_response(req.to_dict())


async def trade_opportunities_handler(request: web.Request) -> web.Response:
    country = request.query.get("country", "")
    items = await agro_marketplace.export_ai.trade_opportunities(country)
    return json_response({"items": items})
