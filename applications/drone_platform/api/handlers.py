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


# ---- engineering suite (11.5) ----
async def engineering_suite_status_handler(request: web.Request) -> web.Response:
    return json_response(drone_platform.engineering_suite.status())


async def engineering_airframe_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            return json_response(
                {
                    "airframes": drone_platform.engineering_suite.airframe.list(),
                    "catalog": drone_platform.engineering_suite.airframe.frame_database(),
                }
            )
        body = await _read_json(request)
        action = body.get("action", "create")
        af = drone_platform.engineering_suite.airframe
        if action == "wing":
            return json_response(af.wing_calculator(span_m=float(body["span_m"]), chord_m=float(body["chord_m"])))
        if action == "flying_wing":
            return json_response(
                af.flying_wing_designer(
                    span_m=float(body["span_m"]),
                    root_chord_m=float(body["root_chord_m"]),
                    tip_chord_m=float(body["tip_chord_m"]),
                    sweep_deg=float(body.get("sweep_deg", 30)),
                ),
                status=201,
            )
        if action == "multirotor":
            return json_response(
                af.multirotor_designer(
                    arms=int(body.get("arms", 4)),
                    wheelbase_mm=float(body.get("wheelbase_mm", 450)),
                    auw_kg=float(body.get("auw_kg", 1.5)),
                ),
                status=201,
            )
        if action == "vtol":
            return json_response(
                af.vtol_designer(
                    span_m=float(body.get("span_m", 2.0)),
                    lift_motors=int(body.get("lift_motors", 4)),
                    auw_kg=float(body.get("auw_kg", 5.0)),
                ),
                status=201,
            )
        if action == "cg":
            return json_response(af.cg_calculator(stations=body.get("stations", [])))
        if action == "payload":
            return json_response(
                af.payload_calculator(
                    empty_kg=float(body["empty_kg"]),
                    max_takeoff_kg=float(body["max_takeoff_kg"]),
                    reserve_kg=float(body.get("reserve_kg", 0.1)),
                )
            )
        if action == "structural":
            return json_response(af.structural_validator(auw_kg=float(body.get("auw_kg", 1.5))))
        item = af.create(name=body.get("name", ""), frame_type=body.get("frame_type", "multirotor"), specs=body.get("specs"), masses=body.get("masses"))
        return json_response(item, status=201)
    except Exception as exc:
        return _handle_error(exc)


async def engineering_propulsion_handler(request: web.Request) -> web.Response:
    try:
        prop = drone_platform.engineering_suite.propulsion
        if request.method == "GET":
            return json_response(
                {
                    "motors": prop.motor_database(),
                    "propellers": prop.propeller_database(),
                    "escs": prop.esc_database(),
                }
            )
        body = await _read_json(request)
        action = body.get("action", "thrust")
        if action == "hover":
            return json_response(
                prop.hover_calculator(
                    auw_kg=float(body["auw_kg"]),
                    motors=int(body.get("motors", 4)),
                    thrust_per_motor_kgf=float(body["thrust_per_motor_kgf"]),
                )
            )
        if action == "efficiency":
            return json_response(prop.efficiency_optimizer(candidates=body.get("candidates", [])))
        if action == "power":
            return json_response(
                prop.power_consumption(
                    voltage=float(body["voltage"]),
                    current_a=float(body["current_a"]),
                    motors=int(body.get("motors", 1)),
                    duty=float(body.get("duty", 1.0)),
                )
            )
        return json_response(
            prop.thrust_calculator(
                diameter_in=float(body.get("diameter_in", 10)),
                pitch_in=float(body.get("pitch_in", 4.7)),
                rpm=float(body.get("rpm", 8000)),
            )
        )
    except Exception as exc:
        return _handle_error(exc)


async def engineering_battery_handler(request: web.Request) -> web.Response:
    try:
        batt = drone_platform.engineering_suite.battery
        if request.method == "GET":
            return json_response({"packs": batt.list(), **batt.status()})
        body = await _read_json(request)
        action = body.get("action", "build")
        if action == "flight_time":
            return json_response(
                batt.flight_time_estimator(
                    capacity_mah=float(body["capacity_mah"]),
                    average_current_a=float(body["average_current_a"]),
                )
            )
        if action == "health":
            return json_response(
                batt.battery_health(
                    cycles=int(body.get("cycles", 0)),
                    measured_capacity_mah=float(body["measured_capacity_mah"]),
                    rated_capacity_mah=float(body["rated_capacity_mah"]),
                    ir_increase_pct=float(body.get("ir_increase_pct", 0)),
                )
            )
        if action == "lipo":
            return json_response(
                batt.lipo_calculator(
                    series=int(body.get("series", 4)),
                    capacity_mah=float(body.get("capacity_mah", 5000)),
                    c_rating=float(body.get("c_rating", 25)),
                ),
                status=201,
            )
        pack = batt.build_pack(
            name=body.get("name", "Pack"),
            cell_type=body.get("cell_type", "18650"),
            series=int(body.get("series", 4)),
            parallel=int(body.get("parallel", 2)),
            cell_capacity_mah=body.get("cell_capacity_mah"),
        )
        return json_response(pack, status=201)
    except Exception as exc:
        return _handle_error(exc)


async def engineering_electronics_handler(request: web.Request) -> web.Response:
    try:
        elec = drone_platform.engineering_suite.electronics
        if request.method == "GET":
            category = request.rel_url.query.get("category")
            return json_response({"parts": elec.registry(category), **elec.status()})
        body = await _read_json(request)
        action = body.get("action", "pdb")
        if action == "bec":
            return json_response(
                elec.bec_calculator(
                    input_v=float(body["input_v"]),
                    output_v=float(body["output_v"]),
                    load_a=float(body["load_a"]),
                    efficiency=float(body.get("efficiency", 0.85)),
                )
            )
        if action == "wiring":
            return json_response(elec.wiring_planner(harness=body.get("harness", [])))
        return json_response(elec.power_distribution(battery_v=float(body.get("battery_v", 16)), loads=body.get("loads", [])))
    except Exception as exc:
        return _handle_error(exc)


async def engineering_pcb_handler(request: web.Request) -> web.Response:
    try:
        pcb = drone_platform.engineering_suite.pcb
        if request.method == "GET":
            return json_response({"projects": pcb.pcb_registry(), "components": pcb.component_library()})
        body = await _read_json(request)
        action = body.get("action", "create")
        if action == "bom":
            return json_response(pcb.bom_generator(body.get("pcb_project_id", "")))
        if action == "validate":
            return json_response(pcb.schematic_validator(body.get("pcb_project_id", "")))
        if action == "gerber":
            return json_response(pcb.gerber_export(body.get("pcb_project_id", "")))
        if action == "mfg":
            return json_response(pcb.manufacturing_package(body.get("pcb_project_id", "")))
        project = pcb.create_project(
            name=body.get("name", ""),
            tool=body.get("tool", "kicad"),
            revision=body.get("revision", "A"),
            components=body.get("components"),
            layers=int(body.get("layers", 4)),
        )
        return json_response(project, status=201)
    except Exception as exc:
        return _handle_error(exc)


async def engineering_cad_handler(request: web.Request) -> web.Response:
    try:
        cad = drone_platform.engineering_suite.cad
        if request.method == "GET":
            return json_response({"library": cad.part_library(), **cad.status()})
        body = await _read_json(request)
        action = body.get("action", "register")
        if action == "assembly":
            return json_response(cad.create_assembly(name=body.get("name", ""), part_ids=body.get("part_ids", [])), status=201)
        if action == "preview":
            return json_response(cad.preview_3d(body.get("part_id", "")))
        if action == "export":
            return json_response(cad.export(body.get("part_id", ""), target_format=body.get("target_format", "stl")))
        part = cad.register_part(name=body.get("name", ""), format=body.get("format", "step"), path=body.get("path", ""), metadata=body.get("metadata"))
        return json_response(part, status=201)
    except Exception as exc:
        return _handle_error(exc)


async def engineering_sim_handler(request: web.Request) -> web.Response:
    try:
        sim = drone_platform.engineering_suite.simulation
        body = await _read_json(request)
        kind = body.get("kind", "flight_performance")
        if kind == "power":
            return json_response(
                sim.power_simulator(
                    voltage=float(body["voltage"]),
                    hover_a=float(body["hover_a"]),
                    cruise_a=float(body["cruise_a"]),
                    hover_min=float(body.get("hover_min", 1)),
                    cruise_min=float(body.get("cruise_min", 10)),
                ),
                status=201,
            )
        if kind == "range":
            return json_response(
                sim.range_simulator(
                    cruise_speed_mps=float(body.get("cruise_speed_mps", 12)),
                    cruise_min=float(body.get("cruise_min", 15)),
                ),
                status=201,
            )
        if kind == "weather":
            return json_response(
                sim.weather_impact(
                    base_range_km=float(body.get("base_range_km", 5)),
                    wind_mps=float(body.get("wind_mps", 5)),
                    rain=bool(body.get("rain", False)),
                ),
                status=201,
            )
        return json_response(
            sim.flight_performance(
                auw_kg=float(body.get("auw_kg", 1.5)),
                thrust_kgf=float(body.get("thrust_kgf", 4.0)),
                drag_n=float(body.get("drag_n", 5)),
            ),
            status=201,
        )
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


# ---- firmware intelligence (11.2) ----
async def firmware_intel_status_handler(request: web.Request) -> web.Response:
    return json_response(drone_platform.firmware_intel.status())


async def firmware_artifacts_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            t = request.rel_url.query.get("type")
            return json_response({"artifacts": drone_platform.firmware_intel.repository.list(t)})
        body = await _read_json(request)
        art = drone_platform.firmware_intel.repository.add_artifact(
            name=body.get("name", ""),
            artifact_type=body.get("artifact_type", ".param"),
            content=body.get("content", ""),
            firmware_project_id=body.get("firmware_project_id", ""),
            version=body.get("version", ""),
            metadata=body.get("metadata"),
            artifact_id=body.get("artifact_id"),
        )
        return json_response(art, status=201)
    except Exception as exc:
        return _handle_error(exc)


async def firmware_analyze_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(drone_platform.firmware_intel.analyzer.analyze_artifact(body.get("artifact_id", "")))
    except Exception as exc:
        return _handle_error(exc)


async def firmware_build_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        build = drone_platform.firmware_intel.builder.build(
            firmware_project_id=body.get("firmware_project_id", ""),
            profile=body.get("profile", "release"),
            custom_modules=body.get("custom_modules"),
            custom_drivers=body.get("custom_drivers"),
            custom_sensors=body.get("custom_sensors"),
            custom_mavlink=body.get("custom_mavlink"),
            validate_dependencies=bool(body.get("validate_dependencies", True)),
        )
        return json_response(build, status=201)
    except Exception as exc:
        return _handle_error(exc)


async def firmware_compare_artifacts_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            drone_platform.firmware_intel.comparator.compare_artifacts(
                body.get("left_id", ""), body.get("right_id", "")
            )
        )
    except Exception as exc:
        return _handle_error(exc)


async def firmware_patch_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        patch = drone_platform.firmware_intel.patches.create_patch(
            firmware_project_id=body.get("firmware_project_id", ""),
            title=body.get("title", ""),
            diff=body.get("diff", ""),
            description=body.get("description", ""),
            metadata=body.get("metadata"),
        )
        return json_response(patch, status=201)
    except Exception as exc:
        return _handle_error(exc)


async def firmware_sign_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            drone_platform.firmware_intel.signing.sign_artifact(
                body.get("artifact_id", ""), signer=body.get("signer", "drone-engineering")
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def firmware_release_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            return json_response({"releases": drone_platform.firmware_intel.releases.list()})
        body = await _read_json(request)
        release = drone_platform.firmware_intel.releases.create_release(
            firmware_project_id=body.get("firmware_project_id", ""),
            version=body.get("version", ""),
            notes=body.get("notes", ""),
            artifact_ids=body.get("artifact_ids"),
            channel=body.get("channel", "stable"),
            metadata=body.get("metadata"),
        )
        return json_response(release, status=201)
    except Exception as exc:
        return _handle_error(exc)


async def firmware_rollback_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        if body.get("backup_id"):
            return json_response(drone_platform.firmware_intel.rollback.rollback_firmware(body["backup_id"]))
        return json_response(
            drone_platform.firmware_intel.rollback.rollback_parameters(
                body.get("parameter_set_id", ""),
                target_name=body.get("target_name", "rollback"),
            )
        )
    except Exception as exc:
        return _handle_error(exc)


async def ardupilot_projects_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            return json_response({"projects": drone_platform.ardupilot.list_projects()})
        body = await _read_json(request)
        project = drone_platform.ardupilot.create_project(
            name=body.get("name", ""),
            vehicle_type=body.get("vehicle_type", "copter"),
            branch=body.get("branch", "master"),
            version=body.get("version", ""),
            metadata=body.get("metadata"),
        )
        return json_response(project, status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ardupilot_params_handler(request: web.Request) -> web.Response:
    vehicle = request.rel_url.query.get("vehicle")
    return json_response({"parameters": drone_platform.ardupilot.parameter_database(vehicle)})


async def ardupilot_modes_handler(request: web.Request) -> web.Response:
    vehicle = request.rel_url.query.get("vehicle")
    return json_response({"modes": drone_platform.ardupilot.modes(vehicle)})


async def ardupilot_vehicles_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            return json_response(
                {
                    "supported": drone_platform.ardupilot.supported_vehicles(),
                    "profiles": drone_platform.ardupilot.list_vehicle_profiles(),
                }
            )
        body = await _read_json(request)
        profile = drone_platform.ardupilot.create_vehicle_profile(
            name=body.get("name", ""),
            vehicle_type=body.get("vehicle_type", "copter"),
            parameters=body.get("parameters"),
            metadata=body.get("metadata"),
        )
        return json_response(profile, status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ardupilot_branches_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            return json_response({"branches": drone_platform.ardupilot.list_branches()})
        body = await _read_json(request)
        branch = drone_platform.ardupilot.create_branch(
            name=body.get("name", ""),
            base=body.get("base", "master"),
            ardupilot_project_id=body.get("ardupilot_project_id", ""),
            notes=body.get("notes", ""),
        )
        return json_response(branch, status=201)
    except Exception as exc:
        return _handle_error(exc)


async def mission_planner_import_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(drone_platform.mission_planner.import_mission(body), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def mission_planner_export_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response({"export": drone_platform.mission_planner.export_mission(body.get("mission_id", ""))})
    except Exception as exc:
        return _handle_error(exc)


async def mission_planner_waypoints_handler(request: web.Request) -> web.Response:
    try:
        mission_id = request.match_info["mission_id"]
        body = await _read_json(request)
        return json_response(drone_platform.mission_planner.edit_waypoints(mission_id, body.get("waypoints", [])))
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


async def telemetry_ai_status_handler(request: web.Request) -> web.Response:
    return json_response(drone_platform.telemetry_ai.status())


async def telemetry_analyze_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        result = drone_platform.telemetry_ai.analyze_session(body.get("session_id", ""))
        return json_response(result)
    except Exception as exc:
        return _handle_error(exc)


async def telemetry_record_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        action = body.get("action", "start")
        if action == "stop":
            return json_response(drone_platform.telemetry_ai.recorder.stop(body.get("recording_id", "")))
        recording = drone_platform.telemetry_ai.recorder.start(
            body.get("session_id", ""),
            label=body.get("label", ""),
        )
        return json_response(recording, status=201)
    except Exception as exc:
        return _handle_error(exc)


async def telemetry_replay_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        if body.get("action") == "step":
            return json_response(drone_platform.telemetry_ai.replay.step(body.get("replay_id", "")))
        replay = drone_platform.telemetry_ai.replay.create(
            body.get("session_id", ""),
            speed=float(body.get("speed", 1.0)),
        )
        return json_response(replay, status=201)
    except Exception as exc:
        return _handle_error(exc)


# ---- mavlink ----
async def mavlink_status_handler(request: web.Request) -> web.Response:
    return json_response(drone_platform.mavlink.status())


async def mavlink_messages_handler(request: web.Request) -> web.Response:
    category = request.rel_url.query.get("category")
    return json_response({"messages": drone_platform.mavlink.messages.list_messages(category=category)})


async def mavlink_commands_handler(request: web.Request) -> web.Response:
    category = request.rel_url.query.get("category")
    return json_response({"commands": drone_platform.mavlink.commands.list_commands(category=category)})


async def mavlink_parse_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        if body.get("content"):
            return json_response({"messages": drone_platform.mavlink.parser.parse_many(body["content"])})
        return json_response(drone_platform.mavlink.parser.parse(body.get("payload", body)))
    except Exception as exc:
        return _handle_error(exc)


async def mavlink_connections_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            return json_response({"connections": drone_platform.mavlink.connections.list()})
        body = await _read_json(request)
        profile = drone_platform.mavlink.connections.create(
            name=body.get("name", ""),
            transport=body.get("transport", "udp"),
            endpoint=body.get("endpoint", "udpin:0.0.0.0:14550"),
            dialect=body.get("dialect", "ardupilotmega"),
            baud=int(body.get("baud", 57600)),
            metadata=body.get("metadata"),
        )
        return json_response(profile, status=201)
    except Exception as exc:
        return _handle_error(exc)


async def mavlink_heartbeat_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        beat = drone_platform.mavlink.heartbeat.record(
            system_id=int(body.get("system_id", 1)),
            autopilot=body.get("autopilot", "ardupilot"),
            vehicle_type=body.get("vehicle_type", "quadrotor"),
            base_mode=int(body.get("base_mode", 0)),
        )
        vehicle = drone_platform.mavlink.discovery.discover_from_heartbeat(beat)
        return json_response({"heartbeat": beat, "vehicle": vehicle}, status=201)
    except Exception as exc:
        return _handle_error(exc)


async def mavlink_stream_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            return json_response({"streams": drone_platform.mavlink.streams.list()})
        body = await _read_json(request)
        if body.get("action") == "ingest":
            msg = drone_platform.mavlink.streams.ingest(body.get("stream_id", ""), body.get("payload", {}))
            return json_response(msg)
        stream = drone_platform.mavlink.streams.open_stream(
            connection_id=body.get("connection_id", ""),
            name=body.get("name", "primary"),
        )
        return json_response(stream, status=201)
    except Exception as exc:
        return _handle_error(exc)


# ---- flight logs ----
async def flight_logs_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            return json_response(
                {
                    "logs": drone_platform.flight_logs.list(),
                    "supported_types": drone_platform.flight_logs.supported_types(),
                }
            )
        body = await _read_json(request)
        log = drone_platform.flight_logs.ingest(
            name=body.get("name", "flight.log"),
            content=body.get("content", ""),
            filename=body.get("filename", ""),
            log_type=body.get("log_type", ""),
            uav_id=body.get("uav_id", ""),
            mission_id=body.get("mission_id", ""),
        )
        return json_response(log, status=201)
    except Exception as exc:
        return _handle_error(exc)


# ---- diagnostics ----
async def diagnostics_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            return json_response({"reports": drone_platform.diagnostics.list(), **drone_platform.diagnostics.status()})
        body = await _read_json(request)
        samples = body.get("samples")
        if not samples and body.get("session_id"):
            session = drone_platform.telemetry.get_session(body["session_id"])
            samples = session.get("samples", [])
        report = drone_platform.diagnostics.detect(samples or [], source=body.get("source", "telemetry"))
        return json_response(report, status=201)
    except Exception as exc:
        return _handle_error(exc)


# ---- mission intelligence ----
async def mission_intel_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        result = drone_platform.mission_intel.analyze_mission(
            body.get("mission_id", ""),
            battery_pct=float(body.get("battery_pct", 100)),
            wind_mps=float(body.get("wind_mps", 0)),
            cruise_speed_mps=float(body.get("cruise_speed_mps", 12)),
        )
        return json_response(result)
    except Exception as exc:
        return _handle_error(exc)


async def mission_intel_compare_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            drone_platform.mission_intel.compare_missions(body.get("left_id", ""), body.get("right_id", ""))
        )
    except Exception as exc:
        return _handle_error(exc)


async def mission_intel_rth_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            drone_platform.mission_intel.simulate_rth(
                home=body.get("home", {}),
                current=body.get("current", {}),
                battery_pct=float(body.get("battery_pct", 100)),
            )
        )
    except Exception as exc:
        return _handle_error(exc)


# ---- gcs ----
async def gcs_bridges_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            return json_response({"bridges": drone_platform.gcs.list(), **drone_platform.gcs.status()})
        body = await _read_json(request)
        bridge = drone_platform.gcs.create_bridge(
            name=body.get("name", ""),
            gcs_type=body.get("gcs_type", "custom"),
            endpoint=body.get("endpoint", ""),
            metadata=body.get("metadata"),
        )
        return json_response(bridge, status=201)
    except Exception as exc:
        return _handle_error(exc)


# ---- visualization ----
async def visualization_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        samples = body.get("samples")
        if not samples and body.get("session_id"):
            session = drone_platform.telemetry.get_session(body["session_id"])
            samples = session.get("samples", [])
        bundle = drone_platform.visualization.build_bundle(
            samples or [],
            waypoints=body.get("waypoints"),
            events=body.get("events"),
        )
        return json_response(bundle)
    except Exception as exc:
        return _handle_error(exc)


# ---- vision / detection (11.4) ----
async def vision_status_handler(request: web.Request) -> web.Response:
    return json_response({**drone_platform.vision.status(), "detection": drone_platform.detection.status()})


async def vision_cameras_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            ctype = request.rel_url.query.get("type")
            return json_response({"cameras": drone_platform.vision.cameras.list(camera_type=ctype)})
        body = await _read_json(request)
        if body.get("multi"):
            cams = drone_platform.vision.register_multi_camera(uav_id=body.get("uav_id", ""), cameras=body.get("cameras", []))
            return json_response({"cameras": cams}, status=201)
        camera = drone_platform.vision.cameras.register(
            name=body.get("name", ""),
            camera_type=body.get("camera_type", "rgb"),
            resolution=body.get("resolution", "1920x1080"),
            fps=int(body.get("fps", 30)),
            uav_id=body.get("uav_id", ""),
            metadata=body.get("metadata"),
        )
        return json_response(camera, status=201)
    except Exception as exc:
        return _handle_error(exc)


async def vision_streams_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            return json_response({"streams": drone_platform.vision.streams.list()})
        body = await _read_json(request)
        stream = drone_platform.vision.streams.open(
            camera_id=body.get("camera_id", ""),
            name=body.get("name", "primary"),
        )
        return json_response(stream, status=201)
    except Exception as exc:
        return _handle_error(exc)


async def vision_frames_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        frame = drone_platform.vision.frames.process(
            stream_id=body.get("stream_id", ""),
            width=int(body.get("width", 1920)),
            height=int(body.get("height", 1080)),
            timestamp_ms=body.get("timestamp_ms"),
            metadata=body.get("metadata"),
        )
        pipeline = drone_platform.vision.pipeline.run(frame, stages=body.get("stages"))
        return json_response({"frame": frame, "pipeline": pipeline}, status=201)
    except Exception as exc:
        return _handle_error(exc)


async def vision_detect_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        result = drone_platform.detection.detector.detect(
            frame_id=body.get("frame_id", ""),
            annotations=body.get("annotations"),
            model=body.get("model", "drone_cv_v1"),
        )
        return json_response(result, status=201)
    except Exception as exc:
        return _handle_error(exc)


async def vision_track_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        if body.get("detection_ids"):
            tracks = drone_platform.detection.tracker.multi_object_track(body["detection_ids"])
            return json_response({"tracks": tracks}, status=201)
        track = drone_platform.detection.tracker.start_track(
            detection_id=body.get("detection_id", ""),
            label=body.get("label", ""),
        )
        return json_response(track, status=201)
    except Exception as exc:
        return _handle_error(exc)


# ---- navigation ----
async def navigation_status_handler(request: web.Request) -> web.Response:
    return json_response(drone_platform.navigation.status())


async def navigation_plan_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        mode = body.get("mode", "dynamic_path")
        nav = drone_platform.navigation
        if mode == "visual":
            result = nav.visual_navigation(landmarks=body.get("landmarks", []), current=body.get("current", {}))
        elif mode == "gps_assisted":
            result = nav.gps_assisted(waypoints=body.get("waypoints", []), gps_ok=bool(body.get("gps_ok", True)))
        elif mode == "gps_denied":
            result = nav.gps_denied(visual_fix=bool(body.get("visual_fix", True)), imu_ok=bool(body.get("imu_ok", True)))
        elif mode == "terrain_following":
            result = nav.terrain_following(clearance_m=float(body.get("clearance_m", 30)), terrain_profile=body.get("terrain_profile"))
        elif mode == "terrain_avoidance":
            result = nav.terrain_avoidance(obstacles=body.get("obstacles", []), altitude_m=float(body.get("altitude_m", 40)))
        elif mode == "obstacle_avoidance":
            result = nav.obstacle_avoidance(obstacles=body.get("obstacles", []), heading_deg=float(body.get("heading_deg", 0)))
        elif mode == "safe_landing":
            result = nav.safe_landing_finder(candidates=body.get("candidates", []))
        elif mode == "route_optimizer":
            result = nav.route_optimizer(waypoints=body.get("waypoints", []))
        elif mode == "emergency_route":
            result = nav.emergency_route(
                current=body.get("current", {}),
                home=body.get("home", {}),
                battery_pct=float(body.get("battery_pct", 50)),
            )
        else:
            result = nav.dynamic_path_planning(
                start=body.get("start", {}),
                goal=body.get("goal", {}),
                obstacles=body.get("obstacles"),
            )
        return json_response(result, status=201)
    except Exception as exc:
        return _handle_error(exc)


# ---- mapping / slam ----
async def mapping_status_handler(request: web.Request) -> web.Response:
    return json_response(drone_platform.mapping.status())


async def mapping_slam_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        slam = drone_platform.mapping.visual_slam(
            frame_ids=body.get("frame_ids", []),
            seed_pose=body.get("seed_pose"),
        )
        if body.get("features"):
            slam = drone_platform.mapping.feature_mapping(map_id=slam["map_id"], features=body["features"])
        cloud = None
        if body.get("generate_point_cloud", True):
            cloud = drone_platform.mapping.point_cloud(map_id=slam["map_id"], points=body.get("points"))
            slam = drone_platform.mapping.reconstruct_3d(map_id=slam["map_id"], point_cloud_id=cloud["point_cloud_id"])
        return json_response({"map": slam, "point_cloud": cloud}, status=201)
    except Exception as exc:
        return _handle_error(exc)


async def mapping_mission_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        result = drone_platform.mapping.mission_map_builder(
            mission_id=body.get("mission_id", ""),
            waypoints=body.get("waypoints", []),
        )
        return json_response(result, status=201)
    except Exception as exc:
        return _handle_error(exc)


# ---- autonomy ----
async def autonomy_status_handler(request: web.Request) -> web.Response:
    return json_response(drone_platform.autonomy.status())


async def autonomy_action_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        mode = body.get("mode", "decision")
        auto = drone_platform.autonomy
        if mode == "takeoff":
            result = auto.takeoff_assistant(target_alt_m=float(body.get("target_alt_m", 10)), clear=bool(body.get("clear", True)))
        elif mode == "landing":
            result = auto.landing_assistant(zone=body.get("zone", {}), battery_pct=float(body.get("battery_pct", 50)))
        elif mode == "patrol":
            result = auto.autonomous_patrol(waypoints=body.get("waypoints", []), loops=int(body.get("loops", 1)))
        elif mode == "waypoint_ai":
            result = auto.waypoint_ai(waypoints=body.get("waypoints", []), adapt=bool(body.get("adapt", True)))
        elif mode == "target_following":
            result = auto.target_following(track_id=body.get("track_id", ""), standoff_m=float(body.get("standoff_m", 15)))
        elif mode == "orbit":
            result = auto.orbit_mode(
                center=body.get("center", {}),
                radius_m=float(body.get("radius_m", 50)),
                speed_mps=float(body.get("speed_mps", 5)),
            )
        elif mode == "search":
            result = auto.search_pattern(bounds=body.get("bounds", {}), pattern=body.get("pattern", "lawnmower"), spacing_m=float(body.get("spacing_m", 40)))
        elif mode == "coverage":
            result = auto.area_coverage(bounds=body.get("bounds", {}), altitude_m=float(body.get("altitude_m", 60)), overlap=float(body.get("overlap", 0.3)))
        elif mode == "swarm":
            result = auto.swarm_ready(vehicle_ids=body.get("vehicle_ids", []), formation=body.get("formation", "line"))
        else:
            result = auto.decision_engine(
                observations=body.get("observations", {}),
                battery_pct=float(body.get("battery_pct", 100)),
                link_ok=bool(body.get("link_ok", True)),
            )
        return json_response(result, status=201)
    except Exception as exc:
        return _handle_error(exc)


# ---- simulation (11.4) ----
async def simulation_status_handler(request: web.Request) -> web.Response:
    return json_response(drone_platform.simulation.status())


async def simulation_runs_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            return json_response({"runs": drone_platform.simulation.list_runs()})
        body = await _read_json(request)
        run = drone_platform.simulation.create_run(
            name=body.get("name", ""),
            firmware_project_id=body.get("firmware_project_id", ""),
            mission_id=body.get("mission_id", ""),
            parameters=body.get("parameters"),
        )
        return json_response(run, status=201)
    except Exception as exc:
        return _handle_error(exc)


async def simulation_scenario_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        scenario = drone_platform.simulation.build_scenario(
            name=body.get("name", ""),
            environment=body.get("environment"),
            vehicles=body.get("vehicles"),
            events=body.get("events"),
        )
        sensors = None
        if body.get("virtual_sensors") is not False:
            sensors = drone_platform.simulation.virtual_sensors(scenario_id=scenario["scenario_id"], readings=body.get("readings"))
        return json_response({"scenario": scenario, "virtual_sensors": sensors}, status=201)
    except Exception as exc:
        return _handle_error(exc)


# ---- mission operations (11.7) ----
async def ops_status_handler(request: web.Request) -> web.Response:
    return json_response(drone_platform.mission_ops.status())


async def ops_missions_handler(request: web.Request) -> web.Response:
    try:
        center = drone_platform.mission_ops.center
        if request.method == "GET":
            return json_response({"missions": center.list(), "templates": center.list_templates()})
        body = await _read_json(request)
        action = body.get("action", "create")
        if action == "template":
            return json_response(center.create_template(name=body.get("name", ""), waypoints=body.get("waypoints")), status=201)
        if action == "schedule":
            return json_response(center.schedule(body.get("ops_mission_id", ""), scheduled_at=body.get("scheduled_at", ""), window_min=int(body.get("window_min", 60))))
        if action == "validate":
            return json_response(center.validate(body.get("ops_mission_id", "")))
        if action == "simulate":
            return json_response(center.simulate(body.get("ops_mission_id", ""), speed_mps=float(body.get("speed_mps", 12))))
        if action == "replay":
            return json_response(center.replay(body.get("ops_mission_id", "")))
        if action == "archive":
            return json_response(center.archive(body.get("ops_mission_id", ""), reason=body.get("reason", "completed")))
        if action == "report":
            return json_response(center.report(body.get("ops_mission_id", ""), success=bool(body.get("success", True)), notes=body.get("notes", "")), status=201)
        if action == "timeline":
            return json_response(center.timeline(body.get("ops_mission_id", "")))
        mission = center.create_ops_mission(
            name=body.get("name", ""),
            waypoints=body.get("waypoints"),
            template_id=body.get("template_id", ""),
            scheduled_at=body.get("scheduled_at", ""),
            priority=body.get("priority", "normal"),
            metadata=body.get("metadata"),
        )
        return json_response(mission, status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ops_fleet_handler(request: web.Request) -> web.Response:
    try:
        fleet = drone_platform.mission_ops.fleet
        if request.method == "GET":
            return json_response({"aircraft": fleet.list(), "available": fleet.available_aircraft()})
        body = await _read_json(request)
        action = body.get("action", "register")
        if action == "assign":
            return json_response(
                fleet.assign(
                    body.get("fleet_id", ""),
                    pilot_id=body.get("pilot_id", ""),
                    payload_id=body.get("payload_id", ""),
                    battery_id=body.get("battery_id", ""),
                    equipment=body.get("equipment"),
                    ops_mission_id=body.get("ops_mission_id", ""),
                ),
                status=201,
            )
        if action == "readiness":
            return json_response(fleet.readiness(body.get("fleet_id", "")))
        if action == "availability":
            return json_response(fleet.set_availability(body.get("fleet_id", ""), available=bool(body.get("available", True))))
        if action == "maintenance":
            return json_response(fleet.set_maintenance(body.get("fleet_id", ""), maintenance_status=body.get("maintenance_status", "ok")))
        return json_response(
            fleet.register_aircraft(
                name=body.get("name", ""),
                serial_number=body.get("serial_number", ""),
                model=body.get("model", ""),
                status=body.get("status", "available"),
                maintenance_status=body.get("maintenance_status", "ok"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ops_ground_handler(request: web.Request) -> web.Response:
    try:
        gnd = drone_platform.mission_ops.ground
        if request.method == "GET":
            return json_response({"alerts": gnd.list_alerts(), **gnd.status()})
        body = await _read_json(request)
        action = body.get("action", "session")
        if action == "alert":
            return json_response(gnd.raise_alert(severity=body.get("severity", "info"), message=body.get("message", ""), source=body.get("source", "system"), ops_mission_id=body.get("ops_mission_id", "")), status=201)
        if action == "dashboard":
            return json_response(gnd.mission_dashboard(ops_mission_id=body.get("ops_mission_id", ""), fleet_ids=body.get("fleet_ids")))
        if action == "operator":
            return json_response(gnd.operator_console(body.get("session_id", "")))
        if action == "emergency_console":
            return json_response(gnd.emergency_console(body.get("session_id", "")))
        return json_response(gnd.open_session(operator_id=body.get("operator_id", ""), role=body.get("role", "operator")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ops_swarm_handler(request: web.Request) -> web.Response:
    try:
        swarm = drone_platform.mission_ops.swarm
        if request.method == "GET":
            return json_response({"swarms": swarm.list(), **swarm.status()})
        body = await _read_json(request)
        action = body.get("action", "create")
        if action == "formation":
            return json_response(swarm.formation_flight(body.get("swarm_id", ""), formation=body.get("formation", "line")))
        if action == "tasks":
            return json_response(swarm.distribute_tasks(body.get("swarm_id", ""), tasks=body.get("tasks", [])))
        if action == "coverage":
            return json_response(swarm.area_coverage(body.get("swarm_id", ""), bounds=body.get("bounds", {}), spacing_m=float(body.get("spacing_m", 50))))
        if action == "recover":
            return json_response(swarm.automatic_recovery(body.get("swarm_id", ""), failed_fleet_id=body.get("failed_fleet_id", "")))
        if action == "health":
            return json_response(swarm.swarm_health(body.get("swarm_id", ""), vehicle_health=body.get("vehicle_health")))
        if action == "decide":
            return json_response(swarm.decision_engine(body.get("swarm_id", ""), observations=body.get("observations")))
        return json_response(
            swarm.create_swarm_mission(
                name=body.get("name", ""),
                fleet_ids=body.get("fleet_ids", []),
                formation=body.get("formation", "line"),
                leader_id=body.get("leader_id", ""),
                tasks=body.get("tasks"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ops_emergency_handler(request: web.Request) -> web.Response:
    try:
        emg = drone_platform.mission_ops.emergency
        body = await _read_json(request)
        action = body.get("action", "trigger")
        if action == "recover":
            return json_response(emg.automatic_recovery(body.get("emergency_id", "")))
        if action == "rth":
            return json_response(
                emg.return_to_home(
                    fleet_id=body.get("fleet_id", ""),
                    home=body.get("home", {}),
                    current=body.get("current", {}),
                    battery_pct=float(body.get("battery_pct", 50)),
                )
            )
        return json_response(
            emg.trigger(
                emergency_type=body.get("emergency_type", "mission_abort"),
                fleet_id=body.get("fleet_id", ""),
                ops_mission_id=body.get("ops_mission_id", ""),
                details=body.get("details"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ops_analytics_handler(request: web.Request) -> web.Response:
    try:
        anx = drone_platform.mission_ops.analytics
        body = await _read_json(request)
        kind = body.get("kind", "success_rate")
        if kind == "coverage":
            return json_response(anx.coverage_analysis(planned_area_km2=float(body.get("planned_area_km2", 1)), covered_area_km2=float(body.get("covered_area_km2", 0.8))))
        if kind == "battery":
            return json_response(anx.battery_consumption(start_pct=float(body.get("start_pct", 100)), end_pct=float(body.get("end_pct", 60)), duration_min=float(body.get("duration_min", 20))))
        if kind == "efficiency":
            return json_response(anx.flight_efficiency(distance_m=float(body.get("distance_m", 5000)), energy_wh=float(body.get("energy_wh", 100))))
        return json_response(anx.mission_success_rate(reports=body.get("reports", [])), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ops_collaboration_handler(request: web.Request) -> web.Response:
    try:
        collab = drone_platform.mission_ops.collaboration
        body = await _read_json(request)
        action = body.get("action", "register")
        if action == "comment":
            return json_response(collab.add_comment(ops_mission_id=body.get("ops_mission_id", ""), operator_id=body.get("operator_id", ""), text=body.get("text", "")), status=201)
        if action == "approve_request":
            return json_response(collab.request_approval(ops_mission_id=body.get("ops_mission_id", ""), requester_id=body.get("requester_id", "")), status=201)
        if action == "approve_decide":
            return json_response(collab.decide_approval(body.get("approval_id", ""), approver_id=body.get("approver_id", ""), approved=bool(body.get("approved", True)), notes=body.get("notes", "")))
        return json_response(collab.register_operator(name=body.get("name", ""), role=body.get("role", "operator")), status=201)
    except Exception as exc:
        return _handle_error(exc)


# ---- drone cloud (11.8) ----
async def cloud_status_handler(request: web.Request) -> web.Response:
    return json_response(drone_platform.cloud.status())


async def cloud_nodes_handler(request: web.Request) -> web.Response:
    try:
        mgr = drone_platform.cloud.manager
        if request.method == "GET":
            return json_response({"nodes": mgr.list_nodes(), "api": mgr.cloud_api_info()})
        body = await _read_json(request)
        action = body.get("action", "register")
        if action == "backup":
            return json_response(mgr.backup(cloud_id=body.get("cloud_id", ""), label=body.get("label", "scheduled")), status=201)
        if action == "store":
            return json_response(mgr.store_object(key=body.get("key", ""), content=body.get("content", ""), content_type=body.get("content_type", "application/json"), cloud_id=body.get("cloud_id", "")), status=201)
        if action == "auth":
            return json_response(mgr.authenticate(principal=body.get("principal", ""), token=body.get("token", ""), role=body.get("role", "operator")), status=201)
        if action == "audit":
            return json_response(mgr.audit(actor=body.get("actor", ""), action=body.get("audit_action", body.get("event", "")), resource=body.get("resource", ""), details=body.get("details")), status=201)
        if action == "gateway":
            return json_response(mgr.gateway_route(path=body.get("path", "/"), method=body.get("method", "GET"), target=body.get("target", "mission_ops")))
        return json_response(
            mgr.register_node(
                name=body.get("name", ""),
                region=body.get("region", "eu-central"),
                node_type=body.get("node_type", "edge"),
                company_id=body.get("company_id", ""),
                metadata=body.get("metadata"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def cloud_sync_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            drone_platform.cloud.manager.sync(
                source_id=body.get("source_id", ""),
                target_id=body.get("target_id", ""),
                entities=body.get("entities"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def cloud_remote_handler(request: web.Request) -> web.Response:
    try:
        remote = drone_platform.cloud.remote
        if request.method == "GET":
            return json_response(remote.status())
        body = await _read_json(request)
        action = body.get("action", "open")
        sid = body.get("remote_session_id", "")
        if action == "command":
            return json_response(remote.remote_mission_control(sid, command=body.get("command", ""), params=body.get("params")))
        if action == "gcs":
            return json_response(remote.remote_ground_station(sid))
        if action == "firmware":
            return json_response(remote.remote_firmware_upload(sid, firmware_id=body.get("firmware_id", ""), version=body.get("version", "")), status=201)
        if action == "parameters":
            return json_response(remote.remote_parameter_edit(sid, parameters=body.get("parameters") or {}))
        if action == "mission_upload":
            return json_response(remote.remote_mission_upload(sid, waypoints=body.get("waypoints") or [], mission_name=body.get("mission_name", "")), status=201)
        if action == "log_download":
            return json_response(remote.remote_log_download(sid, log_id=body.get("log_id", "")))
        if action == "diagnostics":
            return json_response(remote.remote_diagnostics(sid))
        if action == "camera":
            return json_response(remote.remote_camera_stream(sid, enable=bool(body.get("enable", True))))
        if action == "telemetry":
            return json_response(remote.remote_telemetry(sid, enable=bool(body.get("enable", True))))
        if action == "shell":
            return json_response(remote.remote_shell(sid, command=body.get("command", "")))
        return json_response(
            remote.open_session(
                operator_id=body.get("operator_id", ""),
                aircraft_id=body.get("aircraft_id", ""),
                mode=body.get("mode", "mission_control"),
                location=body.get("location", "remote"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def cloud_fleet_handler(request: web.Request) -> web.Response:
    try:
        fleet = drone_platform.cloud.fleet
        if request.method == "GET":
            return json_response({"fleets": fleet.list_fleets(), "dashboard": fleet.global_dashboard(), "availability": fleet.global_availability()})
        body = await _read_json(request)
        action = body.get("action", "register")
        if action == "share":
            return json_response(fleet.share_fleet(body.get("cloud_fleet_id", ""), with_company_id=body.get("with_company_id", "")))
        if action == "federate":
            return json_response(fleet.federate(body.get("cloud_fleet_id", ""), peer_fleet_id=body.get("peer_fleet_id", "")))
        if action == "assign":
            return json_response(
                fleet.remote_assignment(
                    body.get("cloud_fleet_id", ""),
                    operator_id=body.get("operator_id", ""),
                    mission_id=body.get("mission_id", ""),
                ),
                status=201,
            )
        if action == "maintenance":
            return json_response(fleet.remote_maintenance(body.get("cloud_fleet_id", ""), notes=body.get("notes", ""), enable=bool(body.get("enable", True))))
        return json_response(
            fleet.register_org_fleet(
                name=body.get("name", ""),
                company_id=body.get("company_id", ""),
                country=body.get("country", "UA"),
                aircraft_ids=body.get("aircraft_ids"),
                metadata=body.get("metadata"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def cloud_command_handler(request: web.Request) -> web.Response:
    try:
        cmd = drone_platform.cloud.command
        if request.method == "GET":
            return json_response({
                "operations_center": cmd.operations_center(),
                "dashboard": cmd.global_dashboard(),
                "tracking": cmd.live_aircraft_tracking(),
                "incidents": cmd.incident_dashboard(),
            })
        body = await _read_json(request)
        action = body.get("action", "track")
        if action == "incident":
            return json_response(
                cmd.raise_incident(
                    title=body.get("title", ""),
                    severity=body.get("severity", "medium"),
                    aircraft_id=body.get("aircraft_id", ""),
                    mission_id=body.get("mission_id", ""),
                    details=body.get("details"),
                ),
                status=201,
            )
        if action == "fleet_map":
            return json_response(cmd.fleet_map(body.get("fleets")))
        if action == "mission_map":
            return json_response(cmd.mission_map(body.get("missions")))
        if action == "operator_dashboard":
            return json_response(cmd.operator_dashboard(operator_id=body.get("operator_id", "")))
        if action == "timeline":
            return json_response(cmd.mission_timeline(mission_id=body.get("mission_id", ""), events=body.get("events")))
        return json_response(
            cmd.live_track(
                aircraft_id=body.get("aircraft_id", ""),
                lat=float(body.get("lat", 0)),
                lon=float(body.get("lon", 0)),
                alt=float(body.get("alt", 0)),
                heading=float(body.get("heading", 0)),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def cloud_twins_handler(request: web.Request) -> web.Response:
    try:
        twins = drone_platform.cloud.twins
        if request.method == "GET":
            twin_type = request.rel_url.query.get("type")
            return json_response({"twins": twins.list_twins(twin_type=twin_type)})
        body = await _read_json(request)
        action = body.get("action", "create")
        if action == "sync":
            return json_response(twins.live_sync(body.get("twin_id", ""), state=body.get("state") or {}))
        twin_type = body.get("twin_type", "aircraft")
        factories = {
            "aircraft": twins.aircraft_twin,
            "battery": twins.battery_twin,
            "mission": twins.mission_twin,
            "maintenance": twins.maintenance_twin,
            "engineering": twins.engineering_twin,
        }
        if twin_type in factories and twin_type == "aircraft":
            return json_response(factories[twin_type](name=body.get("name", ""), aircraft_id=body.get("source_id", ""), state=body.get("state")), status=201)
        if twin_type == "battery":
            return json_response(twins.battery_twin(name=body.get("name", ""), battery_id=body.get("source_id", ""), state=body.get("state")), status=201)
        if twin_type == "mission":
            return json_response(twins.mission_twin(name=body.get("name", ""), mission_id=body.get("source_id", ""), state=body.get("state")), status=201)
        if twin_type == "maintenance":
            return json_response(twins.maintenance_twin(name=body.get("name", ""), asset_id=body.get("source_id", ""), state=body.get("state")), status=201)
        if twin_type == "engineering":
            return json_response(twins.engineering_twin(name=body.get("name", ""), project_id=body.get("source_id", ""), state=body.get("state")), status=201)
        return json_response(
            twins.create_twin(
                twin_type=twin_type,
                name=body.get("name", ""),
                source_id=body.get("source_id", ""),
                state=body.get("state"),
                metadata=body.get("metadata"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def cloud_security_handler(request: web.Request) -> web.Response:
    try:
        sec = drone_platform.cloud.security
        body = await _read_json(request)
        action = body.get("action", "encrypt_telemetry")
        if action == "encrypt_command":
            return json_response(sec.encrypt_command(command=body.get("command", ""), key_id=body.get("key_id", "default")))
        if action == "certificate":
            return json_response(sec.issue_certificate(subject=body.get("subject", ""), purpose=body.get("purpose", "operator")), status=201)
        if action == "rbac":
            return json_response(sec.grant_role(principal=body.get("principal", ""), role=body.get("role", "operator")), status=201)
        if action == "operator_permissions":
            return json_response(sec.operator_permissions(operator_id=body.get("operator_id", ""), permissions=body.get("permissions")), status=201)
        if action == "mission_permissions":
            return json_response(sec.mission_permissions(mission_id=body.get("mission_id", ""), principal=body.get("principal", ""), permissions=body.get("permissions")), status=201)
        if action == "audit":
            return json_response(sec.audit_log(actor=body.get("actor", ""), action=body.get("audit_action", body.get("event", "")), resource=body.get("resource", "")), status=201)
        return json_response(sec.encrypt_telemetry(payload=body.get("payload", ""), key_id=body.get("key_id", "default")))
    except Exception as exc:
        return _handle_error(exc)


async def cloud_enterprise_handler(request: web.Request) -> web.Response:
    try:
        ent = drone_platform.cloud.enterprise
        if request.method == "GET":
            return json_response({
                "supported": ent.supported(),
                "rest": ent.rest_info(),
                "graphql": ent.graphql_schema(),
                "websocket": ent.websocket_channels(),
                "mqtt": ent.mqtt_topics(),
                "mavlink": ent.mavlink_bridge(),
                "ros2": ent.ros2_bridge(),
                "gcs": ent.gcs_bridges(),
            })
        body = await _read_json(request)
        return json_response(ent.connect(protocol=body.get("protocol", "rest"), endpoint=body.get("endpoint", "")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def cloud_engineering_handler(request: web.Request) -> web.Response:
    try:
        eng = drone_platform.cloud.remote_eng
        body = await _read_json(request)
        action = body.get("action", "firmware_build")
        if action == "simulation":
            return json_response(eng.remote_simulation(scenario=body.get("scenario", "hover"), duration_s=int(body.get("duration_s", 60))), status=201)
        if action == "pcb_review":
            return json_response(eng.remote_pcb_review(project_id=body.get("project_id", ""), notes=body.get("notes", "")), status=201)
        if action == "cad_review":
            return json_response(eng.remote_cad_review(assembly_id=body.get("assembly_id", ""), notes=body.get("notes", "")), status=201)
        if action == "ai_assist":
            return json_response(eng.remote_ai_engineering_assistant(query=body.get("query", ""), context=body.get("context")), status=201)
        if action == "mission_planning":
            return json_response(eng.remote_mission_planning(waypoints=body.get("waypoints") or [], name=body.get("name", "remote_plan")), status=201)
        return json_response(
            eng.remote_firmware_build(target=body.get("target", "ardupilot"), board=body.get("board", "Pixhawk"), branch=body.get("branch", "main")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


# ---- resilience (11.9) ----
async def resilience_status_handler(request: web.Request) -> web.Response:
    return json_response(drone_platform.resilience.status())


async def resilience_navigation_handler(request: web.Request) -> web.Response:
    try:
        nav = drone_platform.resilience.navigation
        if request.method == "GET":
            return json_response(nav.status())
        body = await _read_json(request)
        action = body.get("action", "create")
        sid = body.get("nav_session_id", "")
        if action == "health":
            return json_response(nav.navigation_health(sid))
        if action == "gps":
            return json_response(nav.update_gps(sid, fix_ok=bool(body.get("fix_ok", True)), sat_count=int(body.get("sat_count", 12)), hdop=float(body.get("hdop", 1.0)), lat=float(body.get("lat", 0)), lon=float(body.get("lon", 0)), alt=float(body.get("alt", 0))))
        if action == "rtk":
            return json_response(nav.update_rtk(sid, fixed=bool(body.get("fixed", True)), age_s=body.get("age_s", 0.5)))
        if action == "visual":
            return json_response(nav.visual_navigation_interface(sid, enabled=bool(body.get("enabled", True)), quality=float(body.get("quality", 0.8))))
        if action == "dead_reckoning":
            return json_response(nav.dead_reckoning(sid, dt_s=float(body.get("dt_s", 1.0)), vx=float(body.get("vx", 0)), vy=float(body.get("vy", 0)), vz=float(body.get("vz", 0))))
        if action == "estimate":
            return json_response(nav.multi_source_estimate(sid))
        if action == "confidence":
            return json_response(nav.position_confidence(sid))
        return json_response(nav.create_session(aircraft_id=body.get("aircraft_id", ""), sources=body.get("sources"), metadata=body.get("metadata")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def resilience_communications_handler(request: web.Request) -> web.Response:
    try:
        comm = drone_platform.resilience.communications
        if request.method == "GET":
            return json_response(comm.status())
        body = await _read_json(request)
        action = body.get("action", "open")
        lid = body.get("link_id", "")
        if action == "quality":
            return json_response(comm.link_quality(lid))
        if action == "update_quality":
            return json_response(comm.update_quality(lid, channel=body.get("channel", "lte"), quality=float(body.get("quality", 0.5)), latency_ms=float(body.get("latency_ms", 50)), bandwidth_kbps=float(body.get("bandwidth_kbps", 500)), up=bool(body.get("up", True))))
        if action == "router":
            return json_response(comm.telemetry_router(lid, prefer=body.get("prefer")))
        if action == "switch":
            return json_response(comm.automatic_link_switching(lid, quality_threshold=float(body.get("quality_threshold", 0.5))))
        if action == "bandwidth":
            return json_response(comm.bandwidth_optimizer(lid))
        if action == "latency":
            return json_response(comm.latency_monitor(lid))
        if action == "recorder":
            return json_response(comm.recorder(lid, enable=bool(body.get("enable", True)), frames=int(body.get("frames", 0))))
        if action == "diagnostics":
            return json_response(comm.diagnostics(lid))
        return json_response(comm.open_link(aircraft_id=body.get("aircraft_id", ""), primary=body.get("primary", "lte"), secondary=body.get("secondary", "radio"), metadata=body.get("metadata")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def resilience_safety_handler(request: web.Request) -> web.Response:
    try:
        safety = drone_platform.resilience.safety
        if request.method == "GET":
            return json_response({"status": safety.status(), "nofly_zones": safety.list_nofly_zones()})
        body = await _read_json(request)
        action = body.get("action", "create")
        sid = body.get("safety_id", "")
        if action == "geofence":
            return json_response(safety.set_geofence(sid, south=float(body.get("south", 0)), north=float(body.get("north", 0)), west=float(body.get("west", 0)), east=float(body.get("east", 0))))
        if action == "nofly":
            return json_response(safety.add_nofly_zone(name=body.get("name", ""), south=float(body.get("south", 0)), north=float(body.get("north", 0)), west=float(body.get("west", 0)), east=float(body.get("east", 0))), status=201)
        if action == "check":
            return json_response(safety.check_position(sid, lat=float(body.get("lat", 0)), lon=float(body.get("lon", 0)), alt_m=float(body.get("alt_m", 0)), speed_mps=float(body.get("speed_mps", 0)), battery_pct=float(body.get("battery_pct", 100)), esc_temp_c=float(body.get("esc_temp_c", 40))))
        if action == "envelope":
            return json_response(safety.flight_envelope(sid))
        return json_response(
            safety.create_policy(
                aircraft_id=body.get("aircraft_id", ""),
                max_alt_m=float(body.get("max_alt_m", 120)),
                max_speed_mps=float(body.get("max_speed_mps", 20)),
                min_battery_pct=float(body.get("min_battery_pct", 25)),
                max_esc_temp_c=float(body.get("max_esc_temp_c", 90)),
                geofence=body.get("geofence"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def resilience_health_handler(request: web.Request) -> web.Response:
    try:
        health = drone_platform.resilience.health
        if request.method == "GET":
            return json_response(health.status())
        body = await _read_json(request)
        action = body.get("action", "open")
        hid = body.get("health_id", "")
        if action == "update":
            return json_response(health.update(hid, section=body.get("section", "sensors"), values=body.get("values") or {}))
        if action == "overview":
            return json_response(health.overview(hid))
        if action == "sensors":
            return json_response(health.sensor_health(hid))
        if action == "power":
            return json_response(health.power_health(hid))
        if action == "motors":
            return json_response(health.motor_health(hid))
        if action == "esc":
            return json_response(health.esc_health(hid))
        if action == "battery":
            return json_response(health.battery_health(hid))
        if action == "storage":
            return json_response(health.storage_health(hid))
        if action == "cpu_ram":
            return json_response(health.cpu_ram_monitor(hid))
        return json_response(health.open(aircraft_id=body.get("aircraft_id", "")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def resilience_recovery_handler(request: web.Request) -> web.Response:
    try:
        recovery = drone_platform.resilience.recovery
        if request.method == "GET":
            return json_response(recovery.status())
        body = await _read_json(request)
        action = body.get("action", "start")
        rid = body.get("recovery_id", "")
        if action == "rtl":
            return json_response(recovery.automatic_return(rid))
        if action == "land":
            return json_response(recovery.safe_landing(rid, site=body.get("site")))
        if action == "resume":
            return json_response(recovery.mission_resume(rid, waypoint_index=int(body.get("waypoint_index", 0))))
        if action == "connection":
            return json_response(recovery.connection_recovery(rid, link=body.get("link", "lte")))
        if action == "sensors":
            return json_response(recovery.sensor_reconfiguration(rid, disabled=body.get("disabled"), enabled=body.get("enabled")))
        if action == "mode":
            return json_response(recovery.emergency_flight_mode(rid, mode=body.get("mode", "rtl")))
        if action == "complete":
            return json_response(recovery.complete(rid, outcome=body.get("outcome", "safe")))
        if action == "report":
            return json_response(recovery.report(rid))
        return json_response(
            recovery.start(
                aircraft_id=body.get("aircraft_id", ""),
                reason=body.get("reason", ""),
                mode=body.get("mode", "rtl"),
                home=body.get("home"),
                metadata=body.get("metadata"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


# ---- manufacturing suite (11.6) ----
async def manufacturing_suite_status_handler(request: web.Request) -> web.Response:
    return json_response(drone_platform.manufacturing_suite.status())


async def manufacturing_orders_handler(request: web.Request) -> web.Response:
    try:
        prod = drone_platform.manufacturing_suite.production
        if request.method == "GET":
            return json_response({"orders": prod.list_orders(), "work_centers": prod.list_work_centers()})
        body = await _read_json(request)
        action = body.get("action", "create")
        if action == "work_center":
            return json_response(prod.create_work_center(name=body.get("name", ""), center_type=body.get("center_type", "assembly")), status=201)
        if action == "plan":
            return json_response(prod.plan(order_id=body.get("order_id", ""), work_center_id=body.get("work_center_id", ""), start=body.get("start", ""), end=body.get("end", "")))
        if action == "calendar":
            return json_response(prod.calendar_event(title=body.get("title", ""), date=body.get("date", ""), order_id=body.get("order_id", "")), status=201)
        order = prod.create_order(
            product_name=body.get("product_name", ""),
            quantity=int(body.get("quantity", 1)),
            project_id=body.get("project_id", ""),
            bom_id=body.get("bom_id", ""),
            revision=body.get("revision", "A"),
            due_date=body.get("due_date", ""),
        )
        return json_response(order, status=201)
    except Exception as exc:
        return _handle_error(exc)


async def manufacturing_assembly_handler(request: web.Request) -> web.Response:
    try:
        asm = drone_platform.manufacturing_suite.assembly
        if request.method == "GET":
            return json_response({"assemblies": asm.list(), "templates": asm.list_templates()})
        body = await _read_json(request)
        action = body.get("action", "start")
        if action == "template":
            return json_response(asm.create_template(name=body.get("name", ""), product=body.get("product", "multirotor"), steps=body.get("steps")), status=201)
        if action == "instruction":
            return json_response(asm.create_work_instruction(title=body.get("title", ""), steps=body.get("steps", []), template_id=body.get("template_id", "")), status=201)
        if action == "complete_step":
            return json_response(asm.complete_step(body.get("assembly_id", ""), notes=body.get("notes", "")))
        if action == "line":
            return json_response(asm.assembly_line_status(body.get("line_name", "Line-1")))
        started = asm.start_assembly(
            order_id=body.get("order_id", ""),
            template_id=body.get("template_id", ""),
            serial_number=body.get("serial_number", ""),
            line_name=body.get("line_name", "Line-1"),
        )
        return json_response(started, status=201)
    except Exception as exc:
        return _handle_error(exc)


async def manufacturing_bom_handler(request: web.Request) -> web.Response:
    try:
        bom = drone_platform.manufacturing_suite.bom
        if request.method == "GET":
            return json_response({"boms": bom.list(bom_type=request.rel_url.query.get("type"))})
        body = await _read_json(request)
        action = body.get("action", "create")
        if action == "cost":
            return json_response(bom.cost_calculator(body.get("bom_id", "")))
        if action == "availability":
            return json_response(bom.availability_checker(body.get("bom_id", ""), warehouse_id=body.get("warehouse_id")))
        if action == "procure":
            return json_response(bom.procurement_suggestions(body.get("bom_id", ""), warehouse_id=body.get("warehouse_id")))
        item = bom.create(
            name=body.get("name", ""),
            bom_type=body.get("bom_type", "manufacturing"),
            version=body.get("version", "1.0"),
            lines=body.get("lines"),
            alternatives=body.get("alternatives"),
        )
        return json_response(item, status=201)
    except Exception as exc:
        return _handle_error(exc)


async def manufacturing_warehouse_handler(request: web.Request) -> web.Response:
    try:
        wh = drone_platform.manufacturing_suite.warehouse
        if request.method == "GET":
            return json_response({"categories": wh.categories(), "levels": wh.stock_levels(), "suppliers": wh.supplier_registry()})
        body = await _read_json(request)
        if body.get("action") == "trace":
            return json_response(wh.traceability(serial_number=body.get("serial_number", "")))
        received = wh.receive_components(
            warehouse_id=body.get("warehouse_id", ""),
            component_type=body.get("component_type", "motors"),
            sku=body.get("sku", ""),
            quantity=int(body.get("quantity", 1)),
            serial_numbers=body.get("serial_numbers"),
            batch_id=body.get("batch_id", ""),
        )
        return json_response(received, status=201)
    except Exception as exc:
        return _handle_error(exc)


async def manufacturing_workflow_handler(request: web.Request) -> web.Response:
    try:
        wf = drone_platform.manufacturing_suite.workflow
        body = await _read_json(request)
        if body.get("action") == "advance":
            return json_response(wf.advance(body.get("job_id", ""), notes=body.get("notes", ""), result=body.get("result", "pass")))
        job = wf.start_job(order_id=body.get("order_id", ""), assembly_id=body.get("assembly_id", ""), serial_number=body.get("serial_number", ""))
        return json_response(job, status=201)
    except Exception as exc:
        return _handle_error(exc)


async def manufacturing_programming_handler(request: web.Request) -> web.Response:
    try:
        prg = drone_platform.manufacturing_suite.programming
        body = await _read_json(request)
        action = body.get("action", "flash")
        if action == "params":
            return json_response(prg.upload_parameters(serial_number=body.get("serial_number", ""), parameters=body.get("parameters", {}), profile=body.get("profile", "default")), status=201)
        if action == "serial":
            return json_response(prg.assign_serial_number(prefix=body.get("prefix", "UAV")))
        if action == "qr":
            return json_response(prg.qr_code_generator(serial_number=body.get("serial_number", "")))
        if action == "register":
            return json_response(prg.device_registration(serial_number=body.get("serial_number", ""), model=body.get("model", ""), order_id=body.get("order_id", "")), status=201)
        return json_response(
            prg.flash_firmware(
                serial_number=body.get("serial_number", ""),
                firmware_version=body.get("firmware_version", ""),
                stack=body.get("stack", "ardupilot"),
                artifact_id=body.get("artifact_id", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def manufacturing_calibration_handler(request: web.Request) -> web.Response:
    try:
        cal = drone_platform.manufacturing_suite.calibration
        body = await _read_json(request)
        if body.get("action") == "suite":
            return json_response(cal.run_suite(serial_number=body.get("serial_number", ""), types=body.get("types")), status=201)
        return json_response(
            cal.calibrate(
                serial_number=body.get("serial_number", ""),
                calibration_type=body.get("calibration_type", "accelerometer"),
                result=body.get("result", "pass"),
                details=body.get("details"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def manufacturing_qa_handler(request: web.Request) -> web.Response:
    try:
        qa = drone_platform.manufacturing_suite.qa
        body = await _read_json(request)
        action = body.get("action", "checklist")
        if action == "certify":
            return json_response(qa.final_certification(serial_number=body.get("serial_number", ""), inspector=body.get("inspector", "qa")))
        if action == "check":
            return json_response(
                qa.run_check(
                    serial_number=body.get("serial_number", ""),
                    check_type=body.get("check_type", "visual_inspection"),
                    passed=bool(body.get("passed", True)),
                    notes=body.get("notes", ""),
                    measurements=body.get("measurements"),
                ),
                status=201,
            )
        return json_response(qa.run_full_checklist(serial_number=body.get("serial_number", ""), results=body.get("results")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def manufacturing_flight_tests_handler(request: web.Request) -> web.Response:
    try:
        ft = drone_platform.manufacturing_suite.flight_tests
        body = await _read_json(request)
        action = body.get("action", "run")
        if action == "acceptance":
            return json_response(ft.acceptance_protocol(serial_number=body.get("serial_number", "")))
        if action == "report":
            return json_response(ft.flight_report(serial_number=body.get("serial_number", "")))
        return json_response(
            ft.run_test(
                serial_number=body.get("serial_number", ""),
                test_type=body.get("test_type", "bench"),
                result=body.get("result", "pass"),
                metrics=body.get("metrics"),
                notes=body.get("notes", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def manufacturing_lifecycle_handler(request: web.Request) -> web.Response:
    try:
        life = drone_platform.manufacturing_suite.lifecycle
        if request.method == "GET":
            return json_response({"aircraft": life.list(), **life.status()})
        body = await _read_json(request)
        action = body.get("action", "register")
        if action == "hours":
            return json_response(life.add_flight_hours(body.get("aircraft_id", ""), float(body.get("hours", 0))))
        if action == "cycles":
            return json_response(life.add_battery_cycles(body.get("aircraft_id", ""), int(body.get("cycles", 1))))
        if action == "eol":
            return json_response(life.end_of_life(body.get("aircraft_id", ""), reason=body.get("reason", "retired")))
        if action == "event":
            return json_response(life.add_event(body.get("aircraft_id", ""), bucket=body.get("bucket", "maintenance"), event=body.get("event", {})))
        return json_response(
            life.register_aircraft(
                serial_number=body.get("serial_number", ""),
                model=body.get("model", ""),
                order_id=body.get("order_id", ""),
            ),
            status=201,
        )
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
