"""Soil intelligence and water management."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.agro_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.agro_enterprise.shared.store import AgroEnterpriseStore, agro_enterprise_store

WATER_SOURCE_TYPES = ["reservoir", "canal", "groundwater", "river", "municipal"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class SoilIntelligence:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store

    def register_soil(
        self,
        *,
        field_id: str,
        composition: dict[str, float] | None = None,
        organic_matter_pct: float = 2.5,
        ph: float = 6.5,
        salinity_ds_m: float = 0.8,
        compaction_mpa: float = 1.2,
    ) -> dict[str, Any]:
        if not field_id:
            raise ValidationError("field_id required")
        sid = _id("si_soil")
        composition = composition or {"sand": 40.0, "silt": 40.0, "clay": 20.0}
        fertility = round(
            max(0.0, min(100.0, organic_matter_pct * 12 + (7 - abs(ph - 6.5)) * 8 - salinity_ds_m * 10)),
            1,
        )
        record = {
            "soil_id": sid,
            "field_id": field_id,
            "composition": composition,
            "organic_matter_pct": float(organic_matter_pct),
            "ph": float(ph),
            "salinity_ds_m": float(salinity_ds_m),
            "compaction_mpa": float(compaction_mpa),
            "fertility_score": fertility,
            "nutrients": {"n": 45.0, "p": 22.0, "k": 180.0},
            "created_at": _now(),
        }
        return self.store.si_soils.save(sid, record)

    def nutrient_analysis(self, soil_id: str, *, n: float, p: float, k: float) -> dict[str, Any]:
        soil = self.store.si_soils.get(soil_id)
        if soil is None:
            raise NotFoundError("soil", soil_id)
        soil["nutrients"] = {"n": float(n), "p": float(p), "k": float(k)}
        soil["updated_at"] = _now()
        self.store.si_soils.save(soil_id, soil)
        aid = _id("si_nut")
        return self.store.si_nutrient_analyses.save(
            aid,
            {
                "analysis_id": aid,
                "soil_id": soil_id,
                "nutrients": soil["nutrients"],
                "status": "balanced" if n > 30 and p > 15 and k > 100 else "deficient",
                "at": _now(),
            },
        )

    def history(self, field_id: str) -> list[dict[str, Any]]:
        return [s for s in self.store.si_soils.list_all() if s.get("field_id") == field_id]

    def status(self) -> dict[str, Any]:
        return {"soils": self.store.si_soils.count(), "nutrient_analyses": self.store.si_nutrient_analyses.count()}


class WaterManagement:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store
        self.source_types = list(WATER_SOURCE_TYPES)

    def register_source(self, *, name: str, source_type: str, capacity_m3: float = 0.0) -> dict[str, Any]:
        if source_type not in self.source_types:
            raise ValidationError(f"source_type must be one of {self.source_types}")
        if not name:
            raise ValidationError("name required")
        sid = _id("si_src")
        return self.store.si_water_sources.save(
            sid,
            {
                "source_id": sid,
                "name": name,
                "source_type": source_type,
                "capacity_m3": float(capacity_m3),
                "level_m3": float(capacity_m3) * 0.7,
                "quality_index": 0.85,
                "created_at": _now(),
            },
        )

    def update_level(self, source_id: str, *, level_m3: float) -> dict[str, Any]:
        src = self.store.si_water_sources.get(source_id)
        if src is None:
            raise NotFoundError("water_source", source_id)
        src["level_m3"] = float(level_m3)
        src["updated_at"] = _now()
        return self.store.si_water_sources.save(source_id, src)

    def log_consumption(self, *, source_id: str, volume_m3: float, zone_id: str = "") -> dict[str, Any]:
        if self.store.si_water_sources.get(source_id) is None:
            raise NotFoundError("water_source", source_id)
        cid = _id("si_cons")
        return self.store.si_consumption.save(
            cid,
            {
                "consumption_id": cid,
                "source_id": source_id,
                "zone_id": zone_id,
                "volume_m3": float(volume_m3),
                "at": _now(),
            },
        )

    def water_balance(self, source_id: str) -> dict[str, Any]:
        src = self.store.si_water_sources.get(source_id)
        if src is None:
            raise NotFoundError("water_source", source_id)
        used = sum(
            float(c.get("volume_m3") or 0)
            for c in self.store.si_consumption.list_all()
            if c.get("source_id") == source_id
        )
        bid = _id("si_bal")
        return self.store.si_water_balance.save(
            bid,
            {
                "balance_id": bid,
                "source_id": source_id,
                "capacity_m3": src.get("capacity_m3"),
                "level_m3": src.get("level_m3"),
                "consumed_m3": round(used, 2),
                "available_m3": round(float(src.get("level_m3") or 0), 2),
                "at": _now(),
            },
        )

    def quality_check(self, source_id: str, *, turbidity: float = 2.0, ph: float = 7.0) -> dict[str, Any]:
        if self.store.si_water_sources.get(source_id) is None:
            raise NotFoundError("water_source", source_id)
        qid = _id("si_qual")
        index = round(max(0.0, 1.0 - turbidity / 20 - abs(ph - 7) / 10), 3)
        return self.store.si_water_quality.save(
            qid,
            {
                "quality_id": qid,
                "source_id": source_id,
                "turbidity": float(turbidity),
                "ph": float(ph),
                "quality_index": index,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "sources": self.store.si_water_sources.count(),
            "consumption_events": self.store.si_consumption.count(),
            "types": self.source_types,
        }
