"""Shared store — Agro Enterprise (Sprint 14.0)."""

from __future__ import annotations

from typing import Generic, TypeVar

T = TypeVar("T")


class EntityStore(Generic[T]):
    def __init__(self) -> None:
        self._items: dict[str, T] = {}

    def save(self, key: str, item: T) -> T:
        self._items[key] = item
        return item

    def get(self, key: str) -> T | None:
        return self._items.get(key)

    def delete(self, key: str) -> None:
        self._items.pop(key, None)

    def list_all(self) -> list[T]:
        return list(self._items.values())

    def count(self) -> int:
        return len(self._items)

    def reset(self) -> None:
        self._items.clear()


class AgroEnterpriseStore:
    def __init__(self) -> None:
        # Marketplace
        self.listings: EntityStore = EntityStore()
        self.orders: EntityStore = EntityStore()
        self.suppliers: EntityStore = EntityStore()
        self.buyers: EntityStore = EntityStore()
        # Farm registry
        self.farms: EntityStore = EntityStore()
        self.companies: EntityStore = EntityStore()
        self.farmland: EntityStore = EntityStore()
        self.storage: EntityStore = EntityStore()
        self.equipment: EntityStore = EntityStore()
        self.livestock: EntityStore = EntityStore()
        self.certifications: EntityStore = EntityStore()
        # Crops
        self.crops: EntityStore = EntityStore()
        self.seasons: EntityStore = EntityStore()
        self.rotations: EntityStore = EntityStore()
        self.field_assignments: EntityStore = EntityStore()
        self.yield_plans: EntityStore = EntityStore()
        self.harvest_plans: EntityStore = EntityStore()
        self.production_calendar: EntityStore = EntityStore()
        # CRM
        self.crm_contacts: EntityStore = EntityStore()
        self.contracts: EntityStore = EntityStore()
        self.leads: EntityStore = EntityStore()
        self.tasks: EntityStore = EntityStore()
        self.calendar_events: EntityStore = EntityStore()
        # Knowledge & dashboards
        self.knowledge: EntityStore = EntityStore()
        self.dashboards: EntityStore = EntityStore()
        # Sprint 14.1 — Precision Agriculture
        self.pa_fields: EntityStore = EntityStore()
        self.pa_maps: EntityStore = EntityStore()
        self.pa_gis_layers: EntityStore = EntityStore()
        self.pa_drone_missions: EntityStore = EntityStore()
        self.pa_flight_archive: EntityStore = EntityStore()
        self.pa_satellite: EntityStore = EntityStore()
        self.pa_sat_analysis: EntityStore = EntityStore()
        self.pa_sensors: EntityStore = EntityStore()
        self.pa_sensor_readings: EntityStore = EntityStore()
        self.pa_irrigation: EntityStore = EntityStore()
        self.pa_ai_monitoring: EntityStore = EntityStore()
        self.pa_dashboards: EntityStore = EntityStore()
        self.pa_registries: EntityStore = EntityStore()
        # Sprint 14.2 — Smart Irrigation / Soil / Water
        self.si_soils: EntityStore = EntityStore()
        self.si_nutrient_analyses: EntityStore = EntityStore()
        self.si_water_sources: EntityStore = EntityStore()
        self.si_consumption: EntityStore = EntityStore()
        self.si_water_balance: EntityStore = EntityStore()
        self.si_water_quality: EntityStore = EntityStore()
        self.si_zones: EntityStore = EntityStore()
        self.si_schedules: EntityStore = EntityStore()
        self.si_valves: EntityStore = EntityStore()
        self.si_pumps: EntityStore = EntityStore()
        self.si_flow: EntityStore = EntityStore()
        self.si_remote_commands: EntityStore = EntityStore()
        self.si_gateways: EntityStore = EntityStore()
        self.si_iot_sensors: EntityStore = EntityStore()
        self.si_iot_readings: EntityStore = EntityStore()
        self.si_ai_predictions: EntityStore = EntityStore()
        self.si_weather: EntityStore = EntityStore()
        self.si_env_risks: EntityStore = EntityStore()
        self.si_dashboards: EntityStore = EntityStore()
        self.si_registries: EntityStore = EntityStore()

    def reset(self) -> None:
        for attr in vars(self).values():
            if isinstance(attr, EntityStore):
                attr.reset()


agro_enterprise_store = AgroEnterpriseStore()
