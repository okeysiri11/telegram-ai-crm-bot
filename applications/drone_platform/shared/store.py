# In-memory entity store for Drone Platform.

from __future__ import annotations

from typing import Generic, TypeVar

T = TypeVar("T")


class EntityStore(Generic[T]):
    def __init__(self) -> None:
        self._items: dict[str, T] = {}

    def reset(self) -> None:
        self._items.clear()

    def save(self, entity_id: str, entity: T) -> T:
        self._items[entity_id] = entity
        return entity

    def get(self, entity_id: str) -> T | None:
        return self._items.get(entity_id)

    def delete(self, entity_id: str) -> bool:
        return self._items.pop(entity_id, None) is not None

    def list_all(self) -> list[T]:
        return list(self._items.values())

    def count(self) -> int:
        return len(self._items)


class DroneStore:
    def __init__(self) -> None:
        self.components: EntityStore = EntityStore()
        self.uavs: EntityStore = EntityStore()
        self.projects: EntityStore = EntityStore()
        self.project_versions: EntityStore = EntityStore()
        self.firmware_projects: EntityStore = EntityStore()
        self.parameter_sets: EntityStore = EntityStore()
        self.parameter_templates: EntityStore = EntityStore()
        self.firmware_backups: EntityStore = EntityStore()
        self.missions: EntityStore = EntityStore()
        self.telemetry_sessions: EntityStore = EntityStore()
        self.warehouses: EntityStore = EntityStore()
        self.suppliers: EntityStore = EntityStore()
        self.stock_items: EntityStore = EntityStore()
        self.purchase_orders: EntityStore = EntityStore()
        self.reservations: EntityStore = EntityStore()
        self.documents: EntityStore = EntityStore()
        self.ai_sessions: EntityStore = EntityStore()
        self.manufacturing_builds: EntityStore = EntityStore()
        self.simulations: EntityStore = EntityStore()
        # Sprint 11.2 — firmware intelligence
        self.firmware_artifacts: EntityStore = EntityStore()
        self.firmware_builds: EntityStore = EntityStore()
        self.firmware_patches: EntityStore = EntityStore()
        self.firmware_releases: EntityStore = EntityStore()
        self.firmware_signatures: EntityStore = EntityStore()
        self.firmware_configs: EntityStore = EntityStore()
        self.ardupilot_projects: EntityStore = EntityStore()
        self.parameter_definitions: EntityStore = EntityStore()
        self.vehicle_profiles: EntityStore = EntityStore()
        self.flight_modes: EntityStore = EntityStore()
        self.mission_library: EntityStore = EntityStore()
        self.firmware_branches: EntityStore = EntityStore()
        self.mp_profiles: EntityStore = EntityStore()
        # Sprint 11.3 — MAVLink / telemetry / flight logs / GCS
        self.mavlink_connections: EntityStore = EntityStore()
        self.mavlink_routes: EntityStore = EntityStore()
        self.mavlink_vehicles: EntityStore = EntityStore()
        self.mavlink_streams: EntityStore = EntityStore()
        self.mavlink_heartbeats: EntityStore = EntityStore()
        self.telemetry_recordings: EntityStore = EntityStore()
        self.telemetry_replays: EntityStore = EntityStore()
        self.flight_logs: EntityStore = EntityStore()
        self.diagnostic_reports: EntityStore = EntityStore()
        self.mission_analyses: EntityStore = EntityStore()
        self.gcs_bridges: EntityStore = EntityStore()
        self.visualization_charts: EntityStore = EntityStore()
        # Sprint 11.4 — vision / navigation / mapping / autonomy
        self.cameras: EntityStore = EntityStore()
        self.video_streams: EntityStore = EntityStore()
        self.vision_frames: EntityStore = EntityStore()
        self.detections: EntityStore = EntityStore()
        self.tracks: EntityStore = EntityStore()
        self.navigation_plans: EntityStore = EntityStore()
        self.maps: EntityStore = EntityStore()
        self.point_clouds: EntityStore = EntityStore()
        self.autonomy_missions: EntityStore = EntityStore()
        self.sim_scenarios: EntityStore = EntityStore()
        self.sim_replays: EntityStore = EntityStore()
        # Sprint 11.5 — engineering suite
        self.airframes: EntityStore = EntityStore()
        self.motors: EntityStore = EntityStore()
        self.propellers: EntityStore = EntityStore()
        self.escs: EntityStore = EntityStore()
        self.battery_packs: EntityStore = EntityStore()
        self.electronics_parts: EntityStore = EntityStore()
        self.pcb_projects: EntityStore = EntityStore()
        self.cad_parts: EntityStore = EntityStore()
        self.cad_assemblies: EntityStore = EntityStore()
        self.eng_simulations: EntityStore = EntityStore()
        self.eng_calculations: EntityStore = EntityStore()
        # Sprint 11.6 — manufacturing / production
        self.production_orders: EntityStore = EntityStore()
        self.work_centers: EntityStore = EntityStore()
        self.assembly_templates: EntityStore = EntityStore()
        self.assemblies: EntityStore = EntityStore()
        self.work_instructions: EntityStore = EntityStore()
        self.boms: EntityStore = EntityStore()
        self.workflow_jobs: EntityStore = EntityStore()
        self.programming_sessions: EntityStore = EntityStore()
        self.calibration_reports: EntityStore = EntityStore()
        self.qa_checks: EntityStore = EntityStore()
        self.flight_tests: EntityStore = EntityStore()
        self.aircraft_lifecycle: EntityStore = EntityStore()
        self.production_calendar: EntityStore = EntityStore()

    def reset(self) -> None:
        for attr in vars(self).values():
            if isinstance(attr, EntityStore):
                attr.reset()


drone_store = DroneStore()
