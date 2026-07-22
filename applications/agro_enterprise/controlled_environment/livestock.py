"""Livestock, poultry, aquaculture, feed, biosecurity."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.agro_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.agro_enterprise.shared.store import AgroEnterpriseStore, agro_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class LivestockManagement:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store

    def register_breed(self, *, name: str, species: str = "cattle") -> dict[str, Any]:
        if not name:
            raise ValidationError("breed name required")
        bid = _id("ce_breed")
        return self.store.ce_breeds.save(
            bid, {"breed_id": bid, "name": name, "species": species, "created_at": _now()}
        )

    def register_animal(self, *, tag: str, breed_id: str, sex: str = "F") -> dict[str, Any]:
        if self.store.ce_breeds.get(breed_id) is None:
            raise NotFoundError("breed", breed_id)
        aid = _id("ce_an")
        return self.store.ce_animals.save(
            aid,
            {
                "animal_id": aid,
                "tag": tag,
                "breed_id": breed_id,
                "sex": sex,
                "weight_kg": 0.0,
                "health_score": 90.0,
                "created_at": _now(),
            },
        )

    def health(self, animal_id: str, *, health_score: float, note: str = "") -> dict[str, Any]:
        animal = self.store.ce_animals.get(animal_id)
        if animal is None:
            raise NotFoundError("animal", animal_id)
        animal["health_score"] = float(health_score)
        self.store.ce_animals.save(animal_id, animal)
        hid = _id("ce_ah")
        return self.store.ce_animal_health.save(
            hid, {"record_id": hid, "animal_id": animal_id, "health_score": health_score, "note": note, "at": _now()}
        )

    def vaccinate(self, animal_id: str, *, vaccine: str) -> dict[str, Any]:
        if self.store.ce_animals.get(animal_id) is None:
            raise NotFoundError("animal", animal_id)
        vid = _id("ce_vac")
        return self.store.ce_vaccinations.save(
            vid, {"vaccination_id": vid, "animal_id": animal_id, "vaccine": vaccine, "at": _now()}
        )

    def feed(self, animal_id: str, *, ration_kg: float) -> dict[str, Any]:
        if self.store.ce_animals.get(animal_id) is None:
            raise NotFoundError("animal", animal_id)
        fid = _id("ce_feedevt")
        return self.store.ce_feeding.save(
            fid, {"feeding_id": fid, "animal_id": animal_id, "ration_kg": float(ration_kg), "at": _now()}
        )

    def weigh(self, animal_id: str, *, weight_kg: float) -> dict[str, Any]:
        animal = self.store.ce_animals.get(animal_id)
        if animal is None:
            raise NotFoundError("animal", animal_id)
        animal["weight_kg"] = float(weight_kg)
        return self.store.ce_animals.save(animal_id, animal)

    def milk(self, animal_id: str, *, liters: float) -> dict[str, Any]:
        if self.store.ce_animals.get(animal_id) is None:
            raise NotFoundError("animal", animal_id)
        mid = _id("ce_milk")
        return self.store.ce_milk.save(
            mid, {"milk_id": mid, "animal_id": animal_id, "liters": float(liters), "at": _now()}
        )

    def reproduction(self, animal_id: str, *, status: str = "pregnant") -> dict[str, Any]:
        if self.store.ce_animals.get(animal_id) is None:
            raise NotFoundError("animal", animal_id)
        rid = _id("ce_repro")
        return self.store.ce_reproduction.save(
            rid, {"record_id": rid, "animal_id": animal_id, "status": status, "at": _now()}
        )

    def status(self) -> dict[str, Any]:
        return {
            "animals": self.store.ce_animals.count(),
            "breeds": self.store.ce_breeds.count(),
            "milk_records": self.store.ce_milk.count(),
        }


class PoultryManagement:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store

    def register_flock(self, *, name: str, birds: int = 1000) -> dict[str, Any]:
        if not name:
            raise ValidationError("flock name required")
        fid = _id("ce_flock")
        return self.store.ce_flocks.save(
            fid,
            {
                "flock_id": fid,
                "name": name,
                "birds": int(birds),
                "mortality": 0,
                "eggs": 0,
                "created_at": _now(),
            },
        )

    def record_eggs(self, flock_id: str, *, count: int) -> dict[str, Any]:
        flock = self.store.ce_flocks.get(flock_id)
        if flock is None:
            raise NotFoundError("flock", flock_id)
        flock["eggs"] = int(flock.get("eggs") or 0) + int(count)
        self.store.ce_flocks.save(flock_id, flock)
        eid = _id("ce_egg")
        return self.store.ce_eggs.save(
            eid, {"record_id": eid, "flock_id": flock_id, "count": int(count), "at": _now()}
        )

    def mortality(self, flock_id: str, *, count: int, reason: str = "") -> dict[str, Any]:
        flock = self.store.ce_flocks.get(flock_id)
        if flock is None:
            raise NotFoundError("flock", flock_id)
        flock["mortality"] = int(flock.get("mortality") or 0) + int(count)
        flock["birds"] = max(0, int(flock.get("birds") or 0) - int(count))
        self.store.ce_flocks.save(flock_id, flock)
        mid = _id("ce_mort")
        return self.store.ce_poultry_mortality.save(
            mid, {"record_id": mid, "flock_id": flock_id, "count": int(count), "reason": reason, "at": _now()}
        )

    def status(self) -> dict[str, Any]:
        return {"flocks": self.store.ce_flocks.count(), "egg_records": self.store.ce_eggs.count()}


class Aquaculture:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store

    def register_farm(self, *, name: str, species: str = "tilapia") -> dict[str, Any]:
        if not name:
            raise ValidationError("farm name required")
        fid = _id("ce_aq")
        return self.store.ce_fish_farms.save(
            fid, {"farm_id": fid, "name": name, "species": species, "created_at": _now()}
        )

    def water_quality(self, farm_id: str, *, oxygen_mg_l: float, temp_c: float, ph: float = 7.0) -> dict[str, Any]:
        if self.store.ce_fish_farms.get(farm_id) is None:
            raise NotFoundError("fish_farm", farm_id)
        wid = _id("ce_aqw")
        return self.store.ce_aqua_water.save(
            wid,
            {
                "reading_id": wid,
                "farm_id": farm_id,
                "oxygen_mg_l": float(oxygen_mg_l),
                "temp_c": float(temp_c),
                "ph": float(ph),
                "status": "ok" if oxygen_mg_l >= 5 else "low_oxygen",
                "at": _now(),
            },
        )

    def feed(self, farm_id: str, *, kg: float) -> dict[str, Any]:
        if self.store.ce_fish_farms.get(farm_id) is None:
            raise NotFoundError("fish_farm", farm_id)
        fid = _id("ce_aqf")
        return self.store.ce_aqua_feed.save(
            fid, {"feeding_id": fid, "farm_id": farm_id, "kg": float(kg), "automated": True, "at": _now()}
        )

    def growth_prediction(self, farm_id: str, *, biomass_kg: float, days: int = 30) -> dict[str, Any]:
        if self.store.ce_fish_farms.get(farm_id) is None:
            raise NotFoundError("fish_farm", farm_id)
        pid = _id("ce_aqg")
        return self.store.ce_aqua_growth.save(
            pid,
            {
                "prediction_id": pid,
                "farm_id": farm_id,
                "biomass_kg": float(biomass_kg),
                "forecast_kg": round(biomass_kg * (1 + days * 0.012), 2),
                "harvest_ready_days": max(7, 90 - days),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"farms": self.store.ce_fish_farms.count(), "water_readings": self.store.ce_aqua_water.count()}


class FeedNutrition:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store

    def add_inventory(self, *, sku: str, kg: float, cost_per_kg: float = 0.0) -> dict[str, Any]:
        if not sku:
            raise ValidationError("sku required")
        iid = _id("ce_fi")
        return self.store.ce_feed_inventory.save(
            iid,
            {"item_id": iid, "sku": sku, "kg": float(kg), "cost_per_kg": float(cost_per_kg), "created_at": _now()},
        )

    def formulate(self, *, name: str, ingredients: dict[str, float]) -> dict[str, Any]:
        if not name or not ingredients:
            raise ValidationError("name and ingredients required")
        fid = _id("ce_ff")
        return self.store.ce_feed_formulas.save(
            fid, {"formula_id": fid, "name": name, "ingredients": ingredients, "created_at": _now()}
        )

    def status(self) -> dict[str, Any]:
        return {
            "inventory": self.store.ce_feed_inventory.count(),
            "formulas": self.store.ce_feed_formulas.count(),
        }


class Biosecurity:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store

    def access(self, *, site: str, principal: str, granted: bool = True) -> dict[str, Any]:
        aid = _id("ce_acc")
        return self.store.ce_access.save(
            aid,
            {
                "access_id": aid,
                "site": site,
                "principal": principal,
                "granted": bool(granted),
                "at": _now(),
            },
        )

    def quarantine(self, *, subject: str, reason: str) -> dict[str, Any]:
        qid = _id("ce_quar")
        return self.store.ce_quarantine.save(
            qid, {"quarantine_id": qid, "subject": subject, "reason": reason, "status": "active", "at": _now()}
        )

    def incident(self, *, title: str, severity: str = "medium") -> dict[str, Any]:
        iid = _id("ce_inc")
        return self.store.ce_incidents.save(
            iid, {"incident_id": iid, "title": title, "severity": severity, "status": "open", "at": _now()}
        )

    def sanitation(self, *, area: str, status: str = "completed") -> dict[str, Any]:
        sid = _id("ce_san")
        return self.store.ce_sanitation.save(
            sid, {"record_id": sid, "area": area, "status": status, "at": _now()}
        )

    def compliance(self, *, framework: str, status: str = "compliant") -> dict[str, Any]:
        cid = _id("ce_comp")
        return self.store.ce_compliance.save(
            cid, {"compliance_id": cid, "framework": framework, "status": status, "at": _now()}
        )

    def status(self) -> dict[str, Any]:
        return {
            "access_events": self.store.ce_access.count(),
            "quarantine": self.store.ce_quarantine.count(),
            "incidents": self.store.ce_incidents.count(),
        }
