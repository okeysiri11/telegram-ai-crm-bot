from __future__ import annotations

from aiohttp import web

from applications.drone_platform.api.middleware import error_response, json_response
from applications.drone_platform.application import drone_platform
from applications.drone_platform.shared.exceptions import DronePlatformError, NotFoundError, ValidationError


def _body(request: web.Request) -> dict:
    return request.get("json_body") or {}


async def _read_json(request: web.Request) -> dict:
    if request.can_read_body:
        try:
            data = await request.json()
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}
    return {}


def _handle_error(exc: Exception) -> web.Response:
    if isinstance(exc, NotFoundError):
        return error_response(str(exc), status=404)
    if isinstance(exc, ValidationError):
        return error_response(str(exc), status=400)
    if isinstance(exc, DronePlatformError):
        return error_response(str(exc), status=400)
    return error_response(str(exc), status=500)


async def health_handler(request: web.Request) -> web.Response:
    return json_response(drone_platform.health())


# ---- registry ----
async def registry_types_handler(request: web.Request) -> web.Response:
    return json_response({"component_types": drone_platform.registry.list_component_types()})


async def registry_catalog_handler(request: web.Request) -> web.Response:
    return json_response(drone_platform.registry.catalog_summary())


async def registry_components_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            ctype = request.rel_url.query.get("type")
            items = drone_platform.registry.list_components(ctype)
            return json_response({"components": [c.to_dict() for c in items]})
        body = await _read_json(request)
        record = drone_platform.registry.register_component(
            component_type=body.get("component_type", ""),
            name=body.get("name", ""),
            manufacturer=body.get("manufacturer", ""),
            model=body.get("model", ""),
            specifications=body.get("specifications"),
            metadata=body.get("metadata"),
            component_id=body.get("component_id"),
        )
        return json_response(record.to_dict(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def registry_uavs_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            return json_response({"uavs": [u.to_dict() for u in drone_platform.registry.list_uavs()]})
        body = await _read_json(request)
        record = drone_platform.registry.register_uav(
            name=body.get("name", ""),
            airframe_type=body.get("airframe_type", "multirotor"),
            serial_number=body.get("serial_number", ""),
            frame_id=body.get("frame_id", ""),
            flight_controller_id=body.get("flight_controller_id", ""),
            component_ids=body.get("component_ids"),
            status=body.get("status", "design"),
            metadata=body.get("metadata"),
            uav_id=body.get("uav_id"),
        )
        return json_response(record.to_dict(), status=201)
    except Exception as exc:
        return _handle_error(exc)


# ---- projects / engineering ----
async def projects_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            return json_response({"projects": [p.to_dict() for p in drone_platform.projects.list_projects()]})
        body = await _read_json(request)
        project = drone_platform.projects.create_project(
            name=body.get("name", ""),
            description=body.get("description", ""),
            owner=body.get("owner", ""),
            tags=body.get("tags"),
            metadata=body.get("metadata"),
            project_id=body.get("project_id"),
        )
        return json_response(project.to_dict(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def project_versions_handler(request: web.Request) -> web.Response:
    try:
        project_id = request.match_info["project_id"]
        if request.method == "GET":
            versions = drone_platform.projects.list_versions(project_id)
            return json_response({"versions": [v.to_dict() for v in versions]})
        body = await _read_json(request)
        version = drone_platform.projects.create_version(
            project_id=project_id,
            version=body.get("version", "0.1.0"),
            bom=body.get("bom"),
            cad_references=body.get("cad_references"),
            pcb_references=body.get("pcb_references"),
            wiring_diagrams=body.get("wiring_diagrams"),
            assembly_instructions=body.get("assembly_instructions"),
            engineering_docs=body.get("engineering_docs"),
            engineering_notes=body.get("engineering_notes"),
            version_id=body.get("version_id"),
        )
        return json_response(version.to_dict(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def engineering_workspace_handler(request: web.Request) -> web.Response:
    try:
        project_id = request.match_info["project_id"]
        return json_response(drone_platform.engineering.workspace_summary(project_id))
    except Exception as exc:
        return _handle_error(exc)


# ---- firmware ----
async def firmware_catalog_handler(request: web.Request) -> web.Response:
    return json_response(drone_platform.firmware.catalog())


async def firmware_projects_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            stack = request.rel_url.query.get("stack")
            items = drone_platform.firmware.list_projects(stack)
            return json_response({"projects": [p.to_dict() for p in items]})
        body = await _read_json(request)
        project = drone_platform.firmware.create_project(
            name=body.get("name", ""),
            stack=body.get("stack", ""),
            version=body.get("version", ""),
            documentation=body.get("documentation", ""),
            metadata=body.get("metadata"),
            firmware_project_id=body.get("firmware_project_id"),
        )
        return json_response(project.to_dict(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def firmware_parameters_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        record = drone_platform.firmware.save_parameters(
            firmware_project_id=body.get("firmware_project_id", ""),
            name=body.get("name", "params"),
            parameters=body.get("parameters", {}),
            parameter_set_id=body.get("parameter_set_id"),
        )
        return json_response(record.to_dict(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def firmware_compare_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        result = drone_platform.firmware.compare_parameters(body.get("left_id", ""), body.get("right_id", ""))
        return json_response(result)
    except Exception as exc:
        return _handle_error(exc)


async def firmware_templates_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            stack = request.rel_url.query.get("stack")
            return json_response({"templates": [t.to_dict() for t in drone_platform.firmware.list_templates(stack)]})
        body = await _read_json(request)
        template = drone_platform.firmware.create_template(
            name=body.get("name", ""),
            stack=body.get("stack", ""),
            parameters=body.get("parameters", {}),
            description=body.get("description", ""),
            template_id=body.get("template_id"),
        )
        return json_response(template.to_dict(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def firmware_export_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        payload = drone_platform.firmware.export_configuration(body.get("parameter_set_id", ""))
        return json_response({"export": payload})
    except Exception as exc:
        return _handle_error(exc)


async def firmware_import_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        record = drone_platform.firmware.import_configuration(
            firmware_project_id=body.get("firmware_project_id", ""),
            name=body.get("name", "imported"),
            payload=body.get("payload", {}),
        )
        return json_response(record.to_dict(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def firmware_backup_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        backup = drone_platform.firmware.backup_firmware(
            firmware_project_id=body.get("firmware_project_id", ""),
            label=body.get("label", "firmware-backup"),
            payload=body.get("payload"),
        )
        return json_response(backup.to_dict(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def firmware_restore_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        project = drone_platform.firmware.restore_firmware(body.get("backup_id", ""))
        return json_response(project.to_dict())
    except Exception as exc:
        return _handle_error(exc)


# ---- missions ----
async def missions_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            templates = request.rel_url.query.get("templates") == "1"
            items = drone_platform.missions.list_missions(templates_only=templates)
            return json_response({"missions": [m.to_dict() for m in items]})
        body = await _read_json(request)
        mission = drone_platform.missions.create_mission(
            name=body.get("name", ""),
            uav_id=body.get("uav_id", ""),
            waypoints=body.get("waypoints"),
            rally_points=body.get("rally_points"),
            geofences=body.get("geofences"),
            payload_configuration=body.get("payload_configuration"),
            flight_profile=body.get("flight_profile"),
            is_template=bool(body.get("is_template", False)),
            mission_id=body.get("mission_id"),
        )
        return json_response(mission.to_dict(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def mission_waypoints_handler(request: web.Request) -> web.Response:
    try:
        mission_id = request.match_info["mission_id"]
        body = await _read_json(request)
        mission = drone_platform.missions.add_waypoint(mission_id, body)
        return json_response(mission.to_dict())
    except Exception as exc:
        return _handle_error(exc)


# ---- telemetry ----
async def telemetry_sessions_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            return json_response({"sessions": drone_platform.telemetry.list_sessions()})
        body = await _read_json(request)
        session = drone_platform.telemetry.start_session(
            uav_id=body.get("uav_id", ""),
            mission_id=body.get("mission_id", ""),
            metadata=body.get("metadata"),
        )
        return json_response(session, status=201)
    except Exception as exc:
        return _handle_error(exc)


async def telemetry_sample_handler(request: web.Request) -> web.Response:
    try:
        session_id = request.match_info["session_id"]
        body = await _read_json(request)
        session = drone_platform.telemetry.record_sample(session_id, body)
        return json_response(session)
    except Exception as exc:
        return _handle_error(exc)


# ---- inventory ----
async def inventory_warehouses_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            return json_response({"warehouses": [w.to_dict() for w in drone_platform.inventory.list_warehouses()]})
        body = await _read_json(request)
        warehouse = drone_platform.inventory.create_warehouse(
            name=body.get("name", ""),
            location=body.get("location", ""),
            warehouse_id=body.get("warehouse_id"),
        )
        return json_response(warehouse.to_dict(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def inventory_suppliers_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            return json_response({"suppliers": [s.to_dict() for s in drone_platform.inventory.list_suppliers()]})
        body = await _read_json(request)
        supplier = drone_platform.inventory.create_supplier(
            name=body.get("name", ""),
            contact=body.get("contact", ""),
            supplier_id=body.get("supplier_id"),
        )
        return json_response(supplier.to_dict(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def inventory_stock_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            wid = request.rel_url.query.get("warehouse_id")
            return json_response({"stock": [s.to_dict() for s in drone_platform.inventory.list_stock(wid)]})
        body = await _read_json(request)
        stock = drone_platform.inventory.add_stock(
            warehouse_id=body.get("warehouse_id", ""),
            component_type=body.get("component_type", ""),
            sku=body.get("sku", ""),
            quantity=int(body.get("quantity", 0)),
            serial_numbers=body.get("serial_numbers"),
            batch_id=body.get("batch_id", ""),
            lifecycle_stage=body.get("lifecycle_stage", "in_stock"),
            stock_id=body.get("stock_id"),
        )
        return json_response(stock.to_dict(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def inventory_reserve_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        reservation = drone_platform.inventory.reserve_stock(
            stock_id=body.get("stock_id", ""),
            quantity=int(body.get("quantity", 0)),
            project_id=body.get("project_id", ""),
            reservation_id=body.get("reservation_id"),
        )
        return json_response(reservation.to_dict(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def inventory_purchase_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            return json_response({"purchase_orders": [p.to_dict() for p in drone_platform.inventory.list_purchase_orders()]})
        body = await _read_json(request)
        order = drone_platform.inventory.create_purchase_order(
            supplier_id=body.get("supplier_id", ""),
            warehouse_id=body.get("warehouse_id", ""),
            lines=body.get("lines", []),
            purchase_order_id=body.get("purchase_order_id"),
        )
        return json_response(order.to_dict(), status=201)
    except Exception as exc:
        return _handle_error(exc)


# ---- documentation ----
async def documentation_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            doc_type = request.rel_url.query.get("type")
            project_id = request.rel_url.query.get("project_id")
            items = drone_platform.documentation.list(doc_type=doc_type, project_id=project_id)
            return json_response(
                {
                    "documents": [d.to_dict() for d in items],
                    "supported_types": drone_platform.documentation.supported_types(),
                }
            )
        body = await _read_json(request)
        doc = drone_platform.documentation.create(
            title=body.get("title", ""),
            doc_type=body.get("doc_type", ""),
            content=body.get("content", ""),
            project_id=body.get("project_id", ""),
            tags=body.get("tags"),
            metadata=body.get("metadata"),
            document_id=body.get("document_id"),
        )
        return json_response(doc.to_dict(), status=201)
    except Exception as exc:
        return _handle_error(exc)


# ---- ai ----
async def ai_capabilities_handler(request: web.Request) -> web.Response:
    return json_response({"capabilities": drone_platform.ai.capabilities(), "policy": "engineering_assistance_only"})


async def ai_assist_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        result = drone_platform.ai.assist(
            agent=body.get("agent", ""),
            query=body.get("query", ""),
            context=body.get("context"),
        )
        return json_response(result)
    except Exception as exc:
        return _handle_error(exc)
