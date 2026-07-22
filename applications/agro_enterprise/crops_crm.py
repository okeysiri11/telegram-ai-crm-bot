"""Crop management and Agro CRM."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.agro_enterprise.config import DEFAULT_CONFIG
from applications.agro_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.agro_enterprise.shared.store import AgroEnterpriseStore, agro_enterprise_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class CropManagement:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store

    def add_crop(self, *, name: str, variety: str = "", season: str = "summer") -> dict[str, Any]:
        if not name:
            raise ValidationError("crop name required")
        cid = _id("ae_crop")
        return self.store.crops.save(
            cid, {"crop_id": cid, "name": name, "variety": variety, "season": season, "created_at": _now()}
        )

    def plan_season(self, *, farm_id: str, year: int, crops: list[str] | None = None) -> dict[str, Any]:
        sid = _id("ae_season")
        return self.store.seasons.save(
            sid,
            {
                "season_id": sid,
                "farm_id": farm_id,
                "year": int(year),
                "crops": crops or [],
                "status": "planned",
                "created_at": _now(),
            },
        )

    def crop_rotation(self, *, farm_id: str, sequence: list[str]) -> dict[str, Any]:
        if not sequence:
            raise ValidationError("rotation sequence required")
        rid = _id("ae_rot")
        return self.store.rotations.save(
            rid, {"rotation_id": rid, "farm_id": farm_id, "sequence": sequence, "created_at": _now()}
        )

    def assign_field(self, *, farm_id: str, land_id: str, crop_id: str) -> dict[str, Any]:
        if self.store.crops.get(crop_id) is None:
            raise NotFoundError("crop", crop_id)
        aid = _id("ae_field")
        return self.store.field_assignments.save(
            aid,
            {
                "assignment_id": aid,
                "farm_id": farm_id,
                "land_id": land_id,
                "crop_id": crop_id,
                "created_at": _now(),
            },
        )

    def yield_plan(self, *, crop_id: str, hectares: float, expected_t_per_ha: float) -> dict[str, Any]:
        if self.store.crops.get(crop_id) is None:
            raise NotFoundError("crop", crop_id)
        yid = _id("ae_yield")
        expected = round(hectares * expected_t_per_ha, 2)
        return self.store.yield_plans.save(
            yid,
            {
                "yield_plan_id": yid,
                "crop_id": crop_id,
                "hectares": float(hectares),
                "expected_t_per_ha": float(expected_t_per_ha),
                "expected_total_t": expected,
                "created_at": _now(),
            },
        )

    def harvest_plan(self, *, crop_id: str, window_start: str, window_end: str) -> dict[str, Any]:
        if self.store.crops.get(crop_id) is None:
            raise NotFoundError("crop", crop_id)
        hid = _id("ae_harv")
        return self.store.harvest_plans.save(
            hid,
            {
                "harvest_plan_id": hid,
                "crop_id": crop_id,
                "window_start": window_start,
                "window_end": window_end,
                "status": "scheduled",
                "created_at": _now(),
            },
        )

    def calendar_entry(self, *, farm_id: str, title: str, date: str, kind: str = "production") -> dict[str, Any]:
        eid = _id("ae_calp")
        return self.store.production_calendar.save(
            eid,
            {
                "entry_id": eid,
                "farm_id": farm_id,
                "title": title,
                "date": date,
                "kind": kind,
                "created_at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "crops": self.store.crops.count(),
            "seasons": self.store.seasons.count(),
            "yield_plans": self.store.yield_plans.count(),
            "harvest_plans": self.store.harvest_plans.count(),
        }


class AgroCRM:
    def __init__(self, store: AgroEnterpriseStore | None = None) -> None:
        self.store = store or agro_enterprise_store
        self.types = list(DEFAULT_CONFIG.crm_types)

    def create_contact(self, *, name: str, crm_type: str, company: str = "") -> dict[str, Any]:
        if crm_type not in self.types:
            raise ValidationError(f"crm_type must be one of {self.types}")
        if not name:
            raise ValidationError("name required")
        cid = _id("ae_crm")
        return self.store.crm_contacts.save(
            cid,
            {
                "contact_id": cid,
                "name": name,
                "crm_type": crm_type,
                "company": company,
                "created_at": _now(),
            },
        )

    def create_contract(self, *, party_id: str, title: str, value: float = 0.0) -> dict[str, Any]:
        cid = _id("ae_con")
        return self.store.contracts.save(
            cid,
            {
                "contract_id": cid,
                "party_id": party_id,
                "title": title,
                "value": float(value),
                "status": "active",
                "created_at": _now(),
            },
        )

    def create_lead(self, *, name: str, source: str = "marketplace", score: float = 0.5) -> dict[str, Any]:
        lid = _id("ae_lead")
        return self.store.leads.save(
            lid,
            {
                "lead_id": lid,
                "name": name,
                "source": source,
                "score": float(score),
                "status": "open",
                "created_at": _now(),
            },
        )

    def create_task(self, *, title: str, assignee: str = "", due_at: str = "") -> dict[str, Any]:
        if not title:
            raise ValidationError("title required")
        tid = _id("ae_task")
        return self.store.tasks.save(
            tid,
            {
                "task_id": tid,
                "title": title,
                "assignee": assignee,
                "due_at": due_at,
                "status": "open",
                "created_at": _now(),
            },
        )

    def calendar_event(self, *, title: str, starts_at: str, kind: str = "meeting") -> dict[str, Any]:
        eid = _id("ae_cale")
        return self.store.calendar_events.save(
            eid,
            {"event_id": eid, "title": title, "starts_at": starts_at, "kind": kind, "created_at": _now()},
        )

    def status(self) -> dict[str, Any]:
        return {
            "contacts": self.store.crm_contacts.count(),
            "contracts": self.store.contracts.count(),
            "leads": self.store.leads.count(),
            "tasks": self.store.tasks.count(),
        }
