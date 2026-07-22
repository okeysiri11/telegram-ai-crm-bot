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
