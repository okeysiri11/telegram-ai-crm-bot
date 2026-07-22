# Sprint 10.5 REST handlers — service, maintenance, parts, inventory, appointments, warranty.

from __future__ import annotations

from aiohttp import web

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.middleware import error_response, json_response
from applications.auto_marketplace.service_centers.models import (
    DiagnosticReport,
    MaintenancePlan,
    Part,
    PartKind,
    PartsWarehouse,
    PurchaseOrder,
    RepairOrder,
    ServiceAppointment,
    ServiceCenter,
    StockItem,
    Supplier,
    VehicleServiceRecord,
    WarrantyKind,
    WarrantyPolicy,
)
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError


def _part_kind(value: str) -> PartKind:
    try:
        return PartKind(value or "oem")
    except ValueError as exc:
        raise ValidationError(f"invalid part kind: {value}") from exc


async def service_health_handler(_request: web.Request) -> web.Response:
    return json_response(
        {
            "service_engine": auto_marketplace.config.service_engine,
            "application_version": auto_marketplace.config.application_version,
            "metrics": auto_marketplace.service.metrics(),
        }
    )


async def service_centers_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            return json_response({"items": [c.to_dict() for c in auto_marketplace.service.centers.list_centers()]})
        data = await request.json()
        center = auto_marketplace.service.centers.create_center(
            ServiceCenter(
                name=data.get("name", ""),
                branch_code=data.get("branch_code", ""),
                address=data.get("address", ""),
                timezone=data.get("timezone", "UTC"),
            )
        )
        return json_response(center.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def repair_orders_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            items = auto_marketplace.service.repair_orders.list_orders(
                center_id=request.query.get("center_id", ""),
                status=request.query.get("status", ""),
            )
            return json_response({"items": [o.to_dict() for o in items]})
        data = await request.json()
        order = auto_marketplace.service.repair_orders.accept(
            RepairOrder(
                center_id=data.get("center_id", ""),
                vehicle_id=data.get("vehicle_id", ""),
                vin=data.get("vin", ""),
                customer_id=data.get("customer_id", ""),
                advisor_id=data.get("advisor_id", ""),
            )
        )
        auto_marketplace.service.centers.enqueue(order.center_id, order.order_id)
        return json_response(order.to_dict(), status=201)
    except (NotFoundError, ValidationError) as exc:
        return error_response(str(exc), status=404 if isinstance(exc, NotFoundError) else 400)


async def repair_order_action_handler(request: web.Request) -> web.Response:
    try:
        order_id = request.match_info["order_id"]
        action = request.match_info["action"]
        data = {}
        try:
            data = await request.json()
        except Exception:
            data = {}
        engine = auto_marketplace.service.repair_orders
        if action == "inspect":
            order = engine.inspect(order_id, data.get("checklist") or [])
        elif action == "estimate":
            order = engine.estimate(order_id, float(data.get("amount", 0) or 0))
        elif action == "approve":
            order = engine.approve(order_id)
        elif action == "start":
            order = engine.start(
                order_id,
                mechanic_id=data.get("mechanic_id", ""),
                bay_id=data.get("bay_id", ""),
            )
        elif action == "progress":
            order = engine.progress(order_id, data.get("note", ""))
        elif action == "complete":
            order = engine.complete(order_id)
            auto_marketplace.service.history.add(
                VehicleServiceRecord(
                    vehicle_id=order.vehicle_id,
                    vin=order.vin,
                    kind="repair",
                    title="Repair completed",
                    order_id=order.order_id,
                    details={"estimate_amount": order.estimate_amount},
                )
            )
        elif action == "deliver":
            order = engine.deliver(order_id)
        else:
            return error_response("unknown action", status=404)
        return json_response(order.to_dict())
    except (NotFoundError, ValidationError) as exc:
        return error_response(str(exc), status=404 if isinstance(exc, NotFoundError) else 400)


async def diagnostics_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        report = auto_marketplace.service.diagnostics.create_report(
            DiagnosticReport(
                vehicle_id=data.get("vehicle_id", ""),
                vin=data.get("vin", ""),
                obd_codes=list(data.get("obd_codes") or []),
                inspection_notes=list(data.get("inspection_notes") or []),
                photos=list(data.get("photos") or []),
                damage=list(data.get("damage") or []),
            )
        )
        return json_response(report.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def diagnostics_ai_handler(request: web.Request) -> web.Response:
    try:
        report = await auto_marketplace.service.diagnostics.ai_analyze(request.match_info["report_id"])
        return json_response(report.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def service_history_handler(request: web.Request) -> web.Response:
    vehicle_id = request.match_info.get("vehicle_id") or request.query.get("vehicle_id", "")
    return json_response(auto_marketplace.service.history.complete_history(vehicle_id))


async def maintenance_health_handler(_request: web.Request) -> web.Response:
    return json_response(
        {
            "maintenance_engine": auto_marketplace.config.maintenance_engine,
            "metrics": auto_marketplace.service.maintenance.metrics(),
        }
    )


async def maintenance_plans_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        plan = auto_marketplace.service.maintenance.create_plan(
            MaintenancePlan(
                vehicle_id=data.get("vehicle_id", ""),
                fleet_id=data.get("fleet_id", ""),
                name=data.get("name", "Standard service"),
                interval_km=int(data.get("interval_km", 10000) or 10000),
                interval_days=int(data.get("interval_days", 365) or 365),
                tasks=list(data.get("tasks") or []),
            )
        )
        return json_response(plan.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def maintenance_schedule_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        sched = auto_marketplace.service.maintenance.schedule(
            plan_id=data.get("plan_id", ""),
            current_mileage_km=int(data.get("current_mileage_km", 0) or 0),
        )
        return json_response(sched.to_dict(), status=201)
    except (NotFoundError, ValidationError) as exc:
        return error_response(str(exc), status=404 if isinstance(exc, NotFoundError) else 400)


async def maintenance_reminders_handler(request: web.Request) -> web.Response:
    return json_response(
        {"items": auto_marketplace.service.maintenance.reminders(vehicle_id=request.query.get("vehicle_id", ""))}
    )


async def parts_health_handler(_request: web.Request) -> web.Response:
    return json_response(
        {
            "parts_engine": auto_marketplace.config.parts_engine,
            "metrics": auto_marketplace.service.parts.metrics(),
        }
    )


async def parts_list_create_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            items = auto_marketplace.service.parts.list_parts(
                kind=request.query.get("kind", ""),
                supplier_id=request.query.get("supplier_id", ""),
            )
            return json_response({"items": [p.to_dict() for p in items]})
        data = await request.json()
        part = auto_marketplace.service.parts.add_part(
            Part(
                sku=data.get("sku", ""),
                name=data.get("name", ""),
                kind=_part_kind(data.get("kind", "oem")),
                supplier_id=data.get("supplier_id", ""),
                price=float(data.get("price", 0) or 0),
                currency=data.get("currency", "USD"),
                compatible_makes=list(data.get("compatible_makes") or []),
                compatible_vins=list(data.get("compatible_vins") or []),
            )
        )
        return json_response(part.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def parts_compare_handler(request: web.Request) -> web.Response:
    data = await request.json()
    return json_response({"items": auto_marketplace.service.parts.compare_prices(data.get("query", ""))})


async def parts_vin_handler(request: web.Request) -> web.Response:
    try:
        items = auto_marketplace.service.parts.compatible_by_vin(request.match_info["vin"])
        return json_response({"items": [p.to_dict() for p in items]})
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def suppliers_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            return json_response({"items": [s.to_dict() for s in auto_marketplace.service.suppliers.list_all()]})
        data = await request.json()
        supplier = auto_marketplace.service.suppliers.register(
            Supplier(name=data.get("name", ""), country=data.get("country", ""), rating=float(data.get("rating", 0) or 0))
        )
        return json_response(supplier.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def inventory_parts_health_handler(_request: web.Request) -> web.Response:
    return json_response(
        {
            "parts_engine": auto_marketplace.config.parts_engine,
            "metrics": auto_marketplace.service.inventory.metrics(),
        }
    )


async def inventory_warehouses_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        wh = auto_marketplace.service.inventory.create_warehouse(
            PartsWarehouse(
                center_id=data.get("center_id", ""),
                name=data.get("name", ""),
                location=data.get("location", ""),
            )
        )
        return json_response(wh.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def inventory_stock_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        if data.get("delta") is not None:
            item = auto_marketplace.service.inventory.move_stock(
                warehouse_id=data.get("warehouse_id", ""),
                part_id=data.get("part_id", ""),
                delta=int(data.get("delta", 0) or 0),
                reason=data.get("reason", "adjustment"),
            )
        else:
            item = auto_marketplace.service.inventory.upsert_stock(
                StockItem(
                    warehouse_id=data.get("warehouse_id", ""),
                    part_id=data.get("part_id", ""),
                    quantity=int(data.get("quantity", 0) or 0),
                    min_quantity=int(data.get("min_quantity", 5) or 5),
                )
            )
        return json_response(item.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def inventory_reserve_parts_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        reservation = auto_marketplace.service.inventory.reserve(
            warehouse_id=data.get("warehouse_id", ""),
            part_id=data.get("part_id", ""),
            quantity=int(data.get("quantity", 1) or 1),
        )
        return json_response(reservation, status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def inventory_po_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        po = auto_marketplace.service.inventory.create_po(
            PurchaseOrder(
                supplier_id=data.get("supplier_id", ""),
                warehouse_id=data.get("warehouse_id", ""),
                lines=list(data.get("lines") or []),
            )
        )
        return json_response(po.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def inventory_po_receive_handler(request: web.Request) -> web.Response:
    try:
        po = auto_marketplace.service.inventory.receive_po(request.match_info["po_id"])
        return json_response(po.to_dict())
    except (NotFoundError, ValidationError) as exc:
        return error_response(str(exc), status=404 if isinstance(exc, NotFoundError) else 400)


async def inventory_alerts_handler(_request: web.Request) -> web.Response:
    return json_response({"items": auto_marketplace.service.inventory.low_stock_alerts()})


async def appointments_list_create_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            items = auto_marketplace.service.appointments.calendar(
                center_id=request.query.get("center_id", ""),
            )
            return json_response({"items": [a.to_dict() for a in items]})
        data = await request.json()
        appt = auto_marketplace.service.appointments.book(
            ServiceAppointment(
                center_id=data.get("center_id", ""),
                vehicle_id=data.get("vehicle_id", ""),
                customer_id=data.get("customer_id", ""),
                starts_at=float(data.get("starts_at", 0) or 0),
                ends_at=float(data.get("ends_at", 0) or 0),
                service_type=data.get("service_type", "maintenance"),
            )
        )
        return json_response(appt.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def appointments_allocate_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        appt = auto_marketplace.service.appointments.allocate(
            request.match_info["appointment_id"],
            mechanic_id=data.get("mechanic_id", ""),
            bay_id=data.get("bay_id", ""),
        )
        return json_response(appt.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def appointments_reschedule_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        appt = auto_marketplace.service.appointments.reschedule(
            request.match_info["appointment_id"],
            float(data.get("starts_at", 0) or 0),
            float(data["ends_at"]) if data.get("ends_at") is not None else None,
        )
        return json_response(appt.to_dict())
    except (NotFoundError, ValidationError) as exc:
        return error_response(str(exc), status=404 if isinstance(exc, NotFoundError) else 400)


async def warranty_health_handler(_request: web.Request) -> web.Response:
    return json_response(
        {
            "application_version": auto_marketplace.config.application_version,
            "metrics": auto_marketplace.service.warranty.metrics(),
        }
    )


async def warranty_register_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        kind = data.get("kind", "manufacturer")
        try:
            warranty_kind = WarrantyKind(kind)
        except ValueError as exc:
            raise ValidationError(f"invalid warranty kind: {kind}") from exc
        policy = auto_marketplace.service.warranty.register(
            WarrantyPolicy(
                vehicle_id=data.get("vehicle_id", ""),
                vin=data.get("vin", ""),
                kind=warranty_kind,
                provider=data.get("provider", ""),
                mileage_limit_km=int(data.get("mileage_limit_km", 100000) or 100000),
                ends_at=float(data.get("ends_at", 0) or 0),
            )
        )
        return json_response(policy.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def warranty_validate_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        result = auto_marketplace.service.warranty.validate(
            request.match_info["warranty_id"],
            mileage_km=int(data.get("mileage_km", 0) or 0),
        )
        return json_response(result)
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def warranty_claim_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        claim = auto_marketplace.service.warranty.open_claim(
            warranty_id=request.match_info["warranty_id"],
            description=data.get("description", ""),
            order_id=data.get("order_id", ""),
            amount=float(data.get("amount", 0) or 0),
        )
        return json_response(claim.to_dict(), status=201)
    except NotFoundError as exc:
        return error_response(str(exc), status=404)
