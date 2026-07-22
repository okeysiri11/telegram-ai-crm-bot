# Port ERP terminal operations REST handlers — Sprint 9.3.

from __future__ import annotations

from aiohttp import web

from applications.port_erp import port_erp
from applications.port_erp.api.middleware import error_response, json_response
from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.models import Gate, Warehouse
from applications.port_erp.terminal_operations.models import (
    CycleCount,
    DispatchJob,
    Equipment,
    EquipmentType,
    GateAppointment,
    InventoryItem,
    PlanType,
    TerminalPlan,
    WarehouseOperationType,
    WarehouseTask,
    WarehouseZone,
    YardBlock,
)


async def terminal_health_handler(_request: web.Request) -> web.Response:
    return json_response(
        {
            "terminal_engine": port_erp.config.terminal_engine,
            "application_version": port_erp.config.application_version,
            "metrics": port_erp.terminal.metrics(),
        }
    )


async def yard_create_block_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        block = port_erp.terminal.yard.create_block(
            YardBlock(
                terminal_id=data.get("terminal_id", ""),
                name=data.get("name", ""),
                rows=int(data.get("rows", 0) or 0),
                slots_per_row=int(data.get("slots_per_row", 0) or 0),
                max_tiers=int(data.get("max_tiers", 5) or 5),
            )
        )
        return json_response(block.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def yard_list_blocks_handler(request: web.Request) -> web.Response:
    items = port_erp.terminal.yard.list_blocks(terminal_id=request.query.get("terminal_id") or None)
    return json_response({"items": [b.to_dict() for b in items]})


async def yard_list_slots_handler(request: web.Request) -> web.Response:
    items = port_erp.terminal.yard.list_slots(block_id=request.query.get("block_id") or None)
    return json_response({"items": [s.to_dict() for s in items]})


async def yard_assign_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        slot = await port_erp.terminal.yard.assign_slot(
            data.get("container_id", ""),
            terminal_id=data.get("terminal_id", ""),
            block_id=data.get("block_id", ""),
        )
        return json_response(slot.to_dict())
    except (ValidationError, NotFoundError) as exc:
        return error_response(str(exc), status=400 if isinstance(exc, ValidationError) else 404)


async def yard_relocate_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        relocation = await port_erp.terminal.yard.relocate(
            data.get("container_id", ""),
            to_slot_id=data.get("to_slot_id", ""),
            reason=data.get("reason", "optimize"),
        )
        return json_response(relocation.to_dict())
    except (ValidationError, NotFoundError) as exc:
        return error_response(str(exc), status=400 if isinstance(exc, ValidationError) else 404)


async def yard_release_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        slot = await port_erp.terminal.yard.release_container(data.get("container_id", ""))
        return json_response(slot.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def yard_density_handler(request: web.Request) -> web.Response:
    terminal_id = request.query.get("terminal_id", "")
    return json_response(port_erp.terminal.yard.optimize_density(terminal_id=terminal_id))


async def warehouse_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        wh = port_erp.terminal.warehouse.register_warehouse(
            Warehouse(
                port_id=data.get("port_id", ""),
                terminal_id=data.get("terminal_id", ""),
                name=data.get("name", ""),
                capacity_tons=float(data.get("capacity_tons", 0) or 0),
            )
        )
        return json_response(wh.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def warehouse_list_handler(request: web.Request) -> web.Response:
    items = port_erp.terminal.warehouse.list_warehouses(port_id=request.query.get("port_id") or None)
    return json_response({"items": [w.to_dict() for w in items]})


async def warehouse_zone_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        zone = port_erp.terminal.warehouse.create_zone(
            WarehouseZone(
                warehouse_id=data.get("warehouse_id", ""),
                name=data.get("name", ""),
                zone_type=data.get("zone_type", "storage"),
                capacity_units=int(data.get("capacity_units", 0) or 0),
            )
        )
        return json_response(zone.to_dict(), status=201)
    except (ValidationError, NotFoundError) as exc:
        return error_response(str(exc), status=400 if isinstance(exc, ValidationError) else 404)


async def warehouse_inventory_handler(request: web.Request) -> web.Response:
    if request.method == "GET":
        items = port_erp.terminal.warehouse.list_inventory(
            warehouse_id=request.query.get("warehouse_id") or None
        )
        return json_response({"items": [i.to_dict() for i in items]})
    data = await request.json()
    try:
        item = port_erp.terminal.warehouse.upsert_inventory(
            InventoryItem(
                warehouse_id=data.get("warehouse_id", ""),
                zone_id=data.get("zone_id", ""),
                sku=data.get("sku", ""),
                description=data.get("description", ""),
                quantity=float(data.get("quantity", 0) or 0),
                unit=data.get("unit", "unit"),
            )
        )
        return json_response(item.to_dict(), status=201)
    except (ValidationError, NotFoundError) as exc:
        return error_response(str(exc), status=400 if isinstance(exc, ValidationError) else 404)


async def warehouse_task_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        task = await port_erp.terminal.warehouse.create_task(
            WarehouseTask(
                warehouse_id=data.get("warehouse_id", ""),
                operation=WarehouseOperationType(data.get("operation", "receiving")),
                reference=data.get("reference", ""),
                notes=data.get("notes", ""),
            )
        )
        return json_response(task.to_dict(), status=201)
    except (ValidationError, NotFoundError, ValueError) as exc:
        return error_response(str(exc), status=400)


async def warehouse_complete_task_handler(request: web.Request) -> web.Response:
    try:
        task = await port_erp.terminal.warehouse.complete_task(request.match_info["task_id"])
        return json_response(task.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def warehouse_cycle_count_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        count = await port_erp.terminal.warehouse.cycle_count(
            CycleCount(
                warehouse_id=data.get("warehouse_id", ""),
                zone_id=data.get("zone_id", ""),
                expected_qty=float(data.get("expected_qty", 0) or 0),
                counted_qty=float(data.get("counted_qty", 0) or 0),
            )
        )
        return json_response(count.to_dict(), status=201)
    except (ValidationError, NotFoundError) as exc:
        return error_response(str(exc), status=400 if isinstance(exc, ValidationError) else 404)


async def warehouse_move_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        movement = await port_erp.terminal.warehouse.move_stock(
            warehouse_id=data.get("warehouse_id", ""),
            item_id=data["item_id"],
            quantity=float(data.get("quantity", 0) or 0),
            movement_type=data.get("movement_type", "transfer"),
            from_zone_id=data.get("from_zone_id", ""),
            to_zone_id=data.get("to_zone_id", ""),
            reference=data.get("reference", ""),
        )
        return json_response(movement.to_dict())
    except (KeyError, ValidationError, NotFoundError) as exc:
        return error_response(str(exc), status=400 if not isinstance(exc, NotFoundError) else 404)


async def gate_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        gate = port_erp.terminal.gate.register_gate(
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


async def gate_list_handler(request: web.Request) -> web.Response:
    items = port_erp.terminal.gate.list_gates(port_id=request.query.get("port_id") or None)
    return json_response({"items": [g.to_dict() for g in items]})


async def gate_open_handler(request: web.Request) -> web.Response:
    try:
        gate = await port_erp.core.operations.open_gate(request.match_info["gate_id"])
        return json_response(gate.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def gate_appointment_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        appt = port_erp.terminal.gate.create_appointment(
            GateAppointment(
                gate_id=data.get("gate_id", ""),
                terminal_id=data.get("terminal_id", ""),
                plate_number=data.get("plate_number", ""),
                driver_name=data.get("driver_name", ""),
                container_id=data.get("container_id", ""),
                scheduled_at=float(data.get("scheduled_at", 0) or 0),
            )
        )
        return json_response(appt.to_dict(), status=201)
    except (ValidationError, NotFoundError) as exc:
        return error_response(str(exc), status=400 if isinstance(exc, ValidationError) else 404)


async def gate_checkin_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        visit = await port_erp.terminal.gate.check_in(
            gate_id=data.get("gate_id", ""),
            plate_number=data.get("plate_number", ""),
            driver_name=data.get("driver_name", ""),
            driver_id=data.get("driver_id", ""),
            appointment_id=data.get("appointment_id", ""),
            container_id=data.get("container_id", ""),
            ocr_image_ref=data.get("ocr_image_ref", ""),
            qr_payload=data.get("qr_payload", ""),
            access_list=data.get("access_list"),
        )
        return json_response(visit.to_dict(), status=201)
    except (ValidationError, NotFoundError) as exc:
        return error_response(str(exc), status=400 if isinstance(exc, ValidationError) else 404)


async def gate_approve_handler(request: web.Request) -> web.Response:
    try:
        visit = await port_erp.terminal.gate.approve(request.match_info["visit_id"])
        return json_response(visit.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def gate_reject_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
    except Exception:
        data = {}
    try:
        visit = await port_erp.terminal.gate.reject(
            request.match_info["visit_id"],
            reason=(data or {}).get("reason", "access_denied"),
        )
        return json_response(visit.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def gate_checkout_handler(request: web.Request) -> web.Response:
    try:
        visit = await port_erp.terminal.gate.check_out(request.match_info["visit_id"])
        return json_response(visit.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def gate_queue_handler(request: web.Request) -> web.Response:
    gate_id = request.match_info["gate_id"]
    return json_response({"items": [v.to_dict() for v in port_erp.terminal.gate.queue(gate_id)]})


async def equipment_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        eq = port_erp.terminal.equipment.register(
            Equipment(
                terminal_id=data.get("terminal_id", ""),
                name=data.get("name", ""),
                equipment_type=EquipmentType(data.get("equipment_type", "forklift")),
            )
        )
        return json_response(eq.to_dict(), status=201)
    except (ValidationError, ValueError) as exc:
        return error_response(str(exc), status=400)


async def equipment_list_handler(request: web.Request) -> web.Response:
    eq_type = request.query.get("equipment_type")
    items = port_erp.terminal.equipment.list_equipment(
        terminal_id=request.query.get("terminal_id") or None,
        equipment_type=EquipmentType(eq_type) if eq_type else None,
    )
    return json_response({"items": [e.to_dict() for e in items]})


async def equipment_maintenance_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
    except Exception:
        data = {}
    try:
        eq = port_erp.terminal.equipment.schedule_maintenance(
            request.match_info["equipment_id"],
            at=float(data["at"]) if data.get("at") else None,
        )
        return json_response(eq.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def crane_assign_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        assignment = await port_erp.terminal.cranes.assign(
            crane_id=data.get("crane_id", ""),
            vessel_id=data.get("vessel_id", ""),
            berth_id=data.get("berth_id", ""),
            voyage_id=data.get("voyage_id", ""),
            terminal_id=data.get("terminal_id", ""),
            prefer_type=EquipmentType(data.get("prefer_type", "sts_crane")),
        )
        return json_response(assignment.to_dict(), status=201)
    except (ValidationError, NotFoundError, ValueError) as exc:
        return error_response(str(exc), status=400 if not isinstance(exc, NotFoundError) else 404)


async def crane_finish_handler(request: web.Request) -> web.Response:
    try:
        assignment = await port_erp.terminal.cranes.finish(request.match_info["assignment_id"])
        return json_response(assignment.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def dispatch_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        job = port_erp.terminal.dispatch.create_job(
            DispatchJob(
                terminal_id=data.get("terminal_id", ""),
                job_type=data.get("job_type", "move"),
                container_id=data.get("container_id", ""),
                from_location=data.get("from_location", ""),
                to_location=data.get("to_location", ""),
            )
        )
        return json_response(job.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def dispatch_assign_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
    except Exception:
        data = {}
    try:
        job = port_erp.terminal.dispatch.assign_equipment(
            request.match_info["job_id"],
            equipment_id=(data or {}).get("equipment_id", ""),
        )
        return json_response(job.to_dict())
    except (ValidationError, NotFoundError) as exc:
        return error_response(str(exc), status=400 if isinstance(exc, ValidationError) else 404)


async def planning_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        plan = port_erp.terminal.planning.create_plan(
            TerminalPlan(
                terminal_id=data.get("terminal_id", ""),
                plan_type=PlanType(data.get("plan_type", "yard")),
                title=data.get("title", ""),
                resources=list(data.get("resources") or []),
                start_at=float(data.get("start_at", 0) or 0),
                end_at=float(data.get("end_at", 0) or 0),
                notes=data.get("notes", ""),
            )
        )
        return json_response(plan.to_dict(), status=201)
    except (ValidationError, ValueError) as exc:
        return error_response(str(exc), status=400)


async def planning_list_handler(request: web.Request) -> web.Response:
    plan_type = request.query.get("plan_type")
    items = port_erp.terminal.planning.list_plans(
        terminal_id=request.query.get("terminal_id") or None,
        plan_type=PlanType(plan_type) if plan_type else None,
    )
    return json_response(
        {
            "items": [p.to_dict() for p in items],
            "plan_types": port_erp.terminal.planning.plan_types(),
        }
    )


async def planning_activate_handler(request: web.Request) -> web.Response:
    try:
        plan = port_erp.terminal.planning.activate(request.match_info["plan_id"])
        return json_response(plan.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def storage_optimize_handler(request: web.Request) -> web.Response:
    return json_response(
        port_erp.terminal.storage.optimize(
            terminal_id=request.query.get("terminal_id", ""),
            warehouse_id=request.query.get("warehouse_id", ""),
        )
    )
