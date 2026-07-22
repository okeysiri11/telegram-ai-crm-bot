"""Field management and GIS platform."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.agro_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.agro_enterprise.shared.store import AgroEnterpriseStore, agro_enterprise_store

GIS_LAYERS = ["satellite", "topo", "ndvi", "moisture", "elevation", "historical"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class FieldManagement:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store

    def register_field(
        self,
        *,
        name: str,
        farm_id: str = "",
        hectares: float = 0.0,
        soil_type: str = "loam",
        owner: str = "",
    ) -> dict[str, Any]:
        if not name:
            raise ValidationError("field name required")
        fid = _id("pa_field")
        field = {
            "field_id": fid,
            "name": name,
            "farm_id": farm_id,
            "hectares": float(hectares),
            "soil_type": soil_type,
            "owner": owner,
            "crop_id": "",
            "boundary": [],
            "history": [],
            "created_at": _now(),
        }
        return self.store.pa_fields.save(fid, field)

    def set_boundary(self, field_id: str, *, coordinates: list[dict[str, float]]) -> dict[str, Any]:
        field = self.store.pa_fields.get(field_id)
        if field is None:
            raise NotFoundError("field", field_id)
        if len(coordinates) < 3:
            raise ValidationError("boundary requires at least 3 GPS points")
        field["boundary"] = coordinates
        field["centroid"] = {
            "lat": round(sum(p["lat"] for p in coordinates) / len(coordinates), 6),
            "lon": round(sum(p["lon"] for p in coordinates) / len(coordinates), 6),
        }
        field["updated_at"] = _now()
        return self.store.pa_fields.save(field_id, field)

    def assign_crop(self, field_id: str, *, crop_id: str) -> dict[str, Any]:
        field = self.store.pa_fields.get(field_id)
        if field is None:
            raise NotFoundError("field", field_id)
        field["crop_id"] = crop_id
        field.setdefault("history", []).append({"event": "crop_assigned", "crop_id": crop_id, "at": _now()})
        return self.store.pa_fields.save(field_id, field)

    def record_history(self, field_id: str, *, event: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
        field = self.store.pa_fields.get(field_id)
        if field is None:
            raise NotFoundError("field", field_id)
        entry = {"event": event, "details": details or {}, "at": _now()}
        field.setdefault("history", []).append(entry)
        self.store.pa_fields.save(field_id, field)
        return entry

    def analytics(self, field_id: str) -> dict[str, Any]:
        field = self.store.pa_fields.get(field_id)
        if field is None:
            raise NotFoundError("field", field_id)
        return {
            "field_id": field_id,
            "hectares": field.get("hectares"),
            "soil_type": field.get("soil_type"),
            "boundary_points": len(field.get("boundary") or []),
            "history_events": len(field.get("history") or []),
            "crop_id": field.get("crop_id"),
            "at": _now(),
        }

    def status(self) -> dict[str, Any]:
        return {"fields": self.store.pa_fields.count()}


class GISPlatform:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store
        self.layers = list(GIS_LAYERS)

    def create_map(self, *, name: str, field_id: str = "", basemap: str = "satellite") -> dict[str, Any]:
        if basemap not in self.layers:
            raise ValidationError(f"basemap must be one of {self.layers}")
        mid = _id("pa_map")
        return self.store.pa_maps.save(
            mid,
            {
                "map_id": mid,
                "name": name,
                "field_id": field_id,
                "basemap": basemap,
                "layers": [basemap],
                "created_at": _now(),
            },
        )

    def add_layer(self, map_id: str, *, layer: str, opacity: float = 0.7) -> dict[str, Any]:
        m = self.store.pa_maps.get(map_id)
        if m is None:
            raise NotFoundError("map", map_id)
        if layer not in self.layers:
            raise ValidationError(f"layer must be one of {self.layers}")
        if layer not in m["layers"]:
            m["layers"].append(layer)
        lid = _id("pa_layer")
        record = {
            "layer_id": lid,
            "map_id": map_id,
            "layer": layer,
            "opacity": float(opacity),
            "at": _now(),
        }
        self.store.pa_gis_layers.save(lid, record)
        self.store.pa_maps.save(map_id, m)
        return record

    def status(self) -> dict[str, Any]:
        return {"maps": self.store.pa_maps.count(), "layers": self.store.pa_gis_layers.count(), "types": self.layers}
