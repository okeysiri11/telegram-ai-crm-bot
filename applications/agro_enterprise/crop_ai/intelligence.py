"""Crop intelligence, disease detection, pest intelligence."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.agro_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.agro_enterprise.shared.store import AgroEnterpriseStore, agro_enterprise_store

GROWTH_STAGES = ["emergence", "vegetative", "reproductive", "maturity", "senescence"]
DISEASE_PARTS = ["leaf", "stem", "root", "fruit"]
DISEASE_TYPES = ["fungal", "bacterial", "viral"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class CropIntelligence:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store
        self.stages = list(GROWTH_STAGES)

    def register_crop(self, *, name: str, variety: str = "", field_id: str = "") -> dict[str, Any]:
        if not name:
            raise ValidationError("crop name required")
        cid = _id("ca_crop")
        return self.store.ca_crops.save(
            cid,
            {
                "crop_id": cid,
                "name": name,
                "variety": variety,
                "field_id": field_id,
                "growth_stage": "emergence",
                "health_score": 90.0,
                "phenology_day": 0,
                "created_at": _now(),
            },
        )

    def track_stage(self, crop_id: str, *, stage: str, phenology_day: int = 0) -> dict[str, Any]:
        crop = self.store.ca_crops.get(crop_id)
        if crop is None:
            raise NotFoundError("crop", crop_id)
        if stage not in self.stages:
            raise ValidationError(f"stage must be one of {self.stages}")
        crop["growth_stage"] = stage
        crop["phenology_day"] = int(phenology_day)
        crop["updated_at"] = _now()
        self.store.ca_crops.save(crop_id, crop)
        tid = _id("ca_stage")
        return self.store.ca_stage_events.save(
            tid,
            {"event_id": tid, "crop_id": crop_id, "stage": stage, "phenology_day": phenology_day, "at": _now()},
        )

    def health(self, crop_id: str, *, health_score: float) -> dict[str, Any]:
        crop = self.store.ca_crops.get(crop_id)
        if crop is None:
            raise NotFoundError("crop", crop_id)
        crop["health_score"] = float(health_score)
        crop["updated_at"] = _now()
        return self.store.ca_crops.save(crop_id, crop)

    def harvest_readiness(self, crop_id: str) -> dict[str, Any]:
        crop = self.store.ca_crops.get(crop_id)
        if crop is None:
            raise NotFoundError("crop", crop_id)
        ready = crop.get("growth_stage") in ("maturity", "senescence") and float(crop.get("health_score") or 0) >= 60
        rid = _id("ca_ready")
        return self.store.ca_harvest_readiness.save(
            rid,
            {
                "readiness_id": rid,
                "crop_id": crop_id,
                "ready": ready,
                "stage": crop.get("growth_stage"),
                "health_score": crop.get("health_score"),
                "at": _now(),
            },
        )

    def analytics(self, crop_id: str) -> dict[str, Any]:
        crop = self.store.ca_crops.get(crop_id)
        if crop is None:
            raise NotFoundError("crop", crop_id)
        events = [e for e in self.store.ca_stage_events.list_all() if e.get("crop_id") == crop_id]
        return {
            "crop_id": crop_id,
            "name": crop.get("name"),
            "stage": crop.get("growth_stage"),
            "phenology_day": crop.get("phenology_day"),
            "health_score": crop.get("health_score"),
            "timeline_events": len(events),
            "at": _now(),
        }

    def status(self) -> dict[str, Any]:
        return {"crops": self.store.ca_crops.count(), "stage_events": self.store.ca_stage_events.count()}


class DiseaseDetectionAI:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store

    def detect(
        self,
        *,
        crop_id: str,
        part: str = "leaf",
        disease_type: str = "fungal",
        confidence: float = 0.8,
        severity: float = 0.3,
    ) -> dict[str, Any]:
        if self.store.ca_crops.get(crop_id) is None:
            raise NotFoundError("crop", crop_id)
        if part not in DISEASE_PARTS:
            raise ValidationError(f"part must be one of {DISEASE_PARTS}")
        if disease_type not in DISEASE_TYPES:
            raise ValidationError(f"disease_type must be one of {DISEASE_TYPES}")
        did = _id("ca_dis")
        treatments = {
            "fungal": ["fungicide_spray", "improve_airflow"],
            "bacterial": ["copper_treatment", "remove_infected"],
            "viral": ["vector_control", "resistant_varieties"],
        }
        result = {
            "detection_id": did,
            "crop_id": crop_id,
            "part": part,
            "disease_type": disease_type,
            "confidence": float(confidence),
            "severity_score": float(severity),
            "treatment_recommendation": treatments[disease_type],
            "at": _now(),
        }
        return self.store.ca_diseases.save(did, result)

    def status(self) -> dict[str, Any]:
        return {"detections": self.store.ca_diseases.count()}


class PestIntelligence:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store

    def identify(self, *, crop_id: str, pest_name: str, population_index: float = 0.4) -> dict[str, Any]:
        if self.store.ca_crops.get(crop_id) is None:
            raise NotFoundError("crop", crop_id)
        if not pest_name:
            raise ValidationError("pest_name required")
        pid = _id("ca_pest")
        infestation = min(0.95, population_index * 1.2)
        return self.store.ca_pests.save(
            pid,
            {
                "pest_id": pid,
                "crop_id": crop_id,
                "pest_name": pest_name,
                "population_index": float(population_index),
                "infestation_probability": round(infestation, 3),
                "risk_level": "high" if infestation > 0.6 else "medium" if infestation > 0.3 else "low",
                "treatment_plan": ["targeted_spray", "scout_edges"],
                "biological_control": ["beneficial_insects"] if infestation < 0.7 else ["integrated_pest_mgmt"],
                "at": _now(),
            },
        )

    def risk_map(self, *, region: str) -> dict[str, Any]:
        pests = self.store.ca_pests.list_all()
        rid = _id("ca_prisk")
        return self.store.ca_pest_risks.save(
            rid,
            {
                "map_id": rid,
                "region": region,
                "hotspots": len([p for p in pests if p.get("risk_level") == "high"]),
                "pests_tracked": len(pests),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"pests": self.store.ca_pests.count(), "risk_maps": self.store.ca_pest_risks.count()}
