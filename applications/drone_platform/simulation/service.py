"""Simulation — SITL-ready scenarios, replays, virtual sensors (Sprint 11.4)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.drone_platform.shared.exceptions import NotFoundError, ValidationError
from applications.drone_platform.shared.store import DroneStore, drone_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SimulationService:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def create_run(
        self,
        *,
        name: str,
        firmware_project_id: str = "",
        mission_id: str = "",
        parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        sid = f"sim_{uuid.uuid4().hex[:12]}"
        run = {
            "simulation_id": sid,
            "name": name,
            "firmware_project_id": firmware_project_id,
            "mission_id": mission_id,
            "parameters": dict(parameters or {}),
            "status": "queued",
            "sitl_ready": True,
            "created_at": _now(),
        }
        self.store.simulations.save(sid, run)
        return run

    def list_runs(self) -> list[dict[str, Any]]:
        return self.store.simulations.list_all()

    def get_run(self, simulation_id: str) -> dict[str, Any]:
        item = self.store.simulations.get(simulation_id)
        if item is None:
            raise NotFoundError("simulation", simulation_id)
        return item

    def mark_sitl_ready(self, simulation_id: str) -> dict[str, Any]:
        run = self.get_run(simulation_id)
        run["sitl_ready"] = True
        run["status"] = "sitl_ready"
        run["updated_at"] = _now()
        self.store.simulations.save(simulation_id, run)
        return run

    def build_scenario(
        self,
        *,
        name: str,
        environment: dict[str, Any] | None = None,
        vehicles: list[dict[str, Any]] | None = None,
        events: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        sid = f"scn_{uuid.uuid4().hex[:12]}"
        scenario = {
            "scenario_id": sid,
            "name": name,
            "environment": dict(environment or {"wind_mps": 2, "visibility": "good"}),
            "vehicles": list(vehicles or [{"vehicle_id": "sim_uav_1", "type": "copter"}]),
            "events": list(events or []),
            "created_at": _now(),
        }
        self.store.sim_scenarios.save(sid, scenario)
        return scenario

    def virtual_sensors(self, *, scenario_id: str, readings: dict[str, Any] | None = None) -> dict[str, Any]:
        scenario = self.store.sim_scenarios.get(scenario_id)
        if scenario is None:
            raise NotFoundError("sim_scenario", scenario_id)
        sensors = dict(
            readings
            or {
                "gps": {"fix_type": 3, "sats": 12},
                "imu": {"ok": True},
                "baro": {"alt_m": 40},
                "mag": {"ok": True},
                "camera": {"frames": 1},
                "lidar": {"range_m": 12},
            }
        )
        scenario["virtual_sensors"] = sensors
        scenario["updated_at"] = _now()
        self.store.sim_scenarios.save(scenario_id, scenario)
        return {"scenario_id": scenario_id, "sensors": sensors}

    def mission_replay(self, *, mission_id: str, waypoints: list[dict[str, Any]]) -> dict[str, Any]:
        rid = f"srpl_{uuid.uuid4().hex[:12]}"
        replay = {
            "replay_id": rid,
            "replay_type": "mission",
            "mission_id": mission_id,
            "steps": [{"i": i, "waypoint": wp} for i, wp in enumerate(waypoints)],
            "cursor": 0,
            "created_at": _now(),
        }
        self.store.sim_replays.save(rid, replay)
        return replay

    def visual_replay(self, *, frame_ids: list[str], detections: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        rid = f"srpl_{uuid.uuid4().hex[:12]}"
        replay = {
            "replay_id": rid,
            "replay_type": "visual",
            "frame_ids": list(frame_ids),
            "detections": list(detections or []),
            "cursor": 0,
            "created_at": _now(),
        }
        self.store.sim_replays.save(rid, replay)
        return replay

    def simulation_timeline(self, *, simulation_id: str, events: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        run = self.get_run(simulation_id)
        timeline = {
            "simulation_id": simulation_id,
            "events": list(events or [{"t": 0, "event": "start"}, {"t": 1, "event": "takeoff"}]),
            "status": run.get("status"),
            "built_at": _now(),
        }
        run["timeline"] = timeline
        self.store.simulations.save(simulation_id, run)
        return timeline

    def status(self) -> dict[str, Any]:
        return {
            "simulation": "1.1",
            "sitl_ready": True,
            "run_count": self.store.simulations.count(),
            "scenario_count": self.store.sim_scenarios.count(),
            "replay_count": self.store.sim_replays.count(),
            "capabilities": [
                "sitl_ready",
                "mission_replay",
                "visual_replay",
                "simulation_timeline",
                "scenario_builder",
                "virtual_sensors",
            ],
        }


simulation_service = SimulationService()
