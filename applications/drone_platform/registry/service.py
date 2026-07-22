from __future__ import annotations

import uuid
from typing import Any

from applications.drone_platform.models.components import COMPONENT_TYPES, ComponentRecord, UAVRecord
from applications.drone_platform.shared.exceptions import NotFoundError, ValidationError
from applications.drone_platform.shared.store import DroneStore, drone_store


class RegistryService:
    def __init__(self, store: DroneStore | None = None) -> None:
        self.store = store or drone_store

    def list_component_types(self) -> list[str]:
        return list(COMPONENT_TYPES)

    def register_component(
        self,
        *,
        component_type: str,
        name: str,
        manufacturer: str = "",
        model: str = "",
        specifications: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        component_id: str | None = None,
    ) -> ComponentRecord:
        if component_type not in COMPONENT_TYPES:
            raise ValidationError(f"Unsupported component type: {component_type}")
        if component_type == "uav":
            raise ValidationError("Use register_uav for UAV records")
        cid = component_id or f"cmp_{uuid.uuid4().hex[:12]}"
        record = ComponentRecord(
            component_id=cid,
            component_type=component_type,
            name=name,
            manufacturer=manufacturer,
            model=model,
            specifications=dict(specifications or {}),
            metadata=dict(metadata or {}),
        )
        self.store.components.save(cid, record)
        return record

    def get_component(self, component_id: str) -> ComponentRecord:
        item = self.store.components.get(component_id)
        if item is None:
            raise NotFoundError("component", component_id)
        return item

    def list_components(self, component_type: str | None = None) -> list[ComponentRecord]:
        items = self.store.components.list_all()
        if component_type:
            return [c for c in items if c.component_type == component_type]
        return items

    def register_uav(
        self,
        *,
        name: str,
        airframe_type: str = "multirotor",
        serial_number: str = "",
        frame_id: str = "",
        flight_controller_id: str = "",
        component_ids: list[str] | None = None,
        status: str = "design",
        metadata: dict[str, Any] | None = None,
        uav_id: str | None = None,
    ) -> UAVRecord:
        uid = uav_id or f"uav_{uuid.uuid4().hex[:12]}"
        record = UAVRecord(
            uav_id=uid,
            name=name,
            airframe_type=airframe_type,
            serial_number=serial_number,
            frame_id=frame_id,
            flight_controller_id=flight_controller_id,
            component_ids=list(component_ids or []),
            status=status,
            metadata=dict(metadata or {}),
        )
        self.store.uavs.save(uid, record)
        return record

    def get_uav(self, uav_id: str) -> UAVRecord:
        item = self.store.uavs.get(uav_id)
        if item is None:
            raise NotFoundError("uav", uav_id)
        return item

    def list_uavs(self) -> list[UAVRecord]:
        return self.store.uavs.list_all()

    def catalog_summary(self) -> dict[str, Any]:
        by_type: dict[str, int] = {t: 0 for t in COMPONENT_TYPES if t != "uav"}
        for c in self.store.components.list_all():
            by_type[c.component_type] = by_type.get(c.component_type, 0) + 1
        return {
            "component_types": list(COMPONENT_TYPES),
            "counts_by_type": by_type,
            "uav_count": self.store.uavs.count(),
            "component_count": self.store.components.count(),
        }


registry_service = RegistryService()
