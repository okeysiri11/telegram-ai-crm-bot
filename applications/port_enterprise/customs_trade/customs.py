"""Customs management — declarations, HS codes, tariffs, clearance."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.port_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.port_enterprise.shared.store import PortEnterpriseStore, port_enterprise_store

DECLARATION_TYPES = ["import", "export", "transit"]
CLEARANCE_STATUSES = ["submitted", "under_review", "cleared", "held", "rejected"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class CustomsManagement:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store

    def register_office(self, *, name: str, code: str = "", country: str = "") -> dict[str, Any]:
        if not name:
            raise ValidationError("customs office name required")
        oid = _id("ct_off")
        return self.store.ct_offices.save(
            oid,
            {
                "office_id": oid,
                "name": name,
                "code": code,
                "country": country,
                "created_at": _now(),
            },
        )

    def declare(
        self,
        *,
        declaration_type: str,
        reference: str,
        office_id: str = "",
        hs_code: str = "",
        value: float = 0.0,
    ) -> dict[str, Any]:
        if declaration_type not in DECLARATION_TYPES:
            raise ValidationError(f"declaration_type must be one of {DECLARATION_TYPES}")
        if not reference:
            raise ValidationError("declaration reference required")
        did = _id("ct_dec")
        return self.store.ct_declarations.save(
            did,
            {
                "declaration_id": did,
                "declaration_type": declaration_type,
                "reference": reference,
                "office_id": office_id,
                "hs_code": hs_code,
                "value": float(value),
                "status": "submitted",
                "created_at": _now(),
            },
        )

    def register_hs_code(self, *, code: str, description: str = "", duty_rate: float = 0.0) -> dict[str, Any]:
        if not code:
            raise ValidationError("HS code required")
        hid = _id("ct_hs")
        return self.store.ct_hs_codes.save(
            hid,
            {
                "hs_id": hid,
                "code": code,
                "description": description,
                "duty_rate": float(duty_rate),
                "created_at": _now(),
            },
        )

    def set_tariff(self, *, hs_code: str, country: str, rate: float) -> dict[str, Any]:
        if not hs_code or not country:
            raise ValidationError("hs_code and country required")
        tid = _id("ct_tar")
        return self.store.ct_tariffs.save(
            tid,
            {
                "tariff_id": tid,
                "hs_code": hs_code,
                "country": country,
                "rate": float(rate),
                "at": _now(),
            },
        )

    def calculate_duty(self, *, declaration_id: str, duty_rate: float = 0.0, tax_rate: float = 0.2) -> dict[str, Any]:
        decl = self.store.ct_declarations.get(declaration_id)
        if decl is None:
            raise NotFoundError("declaration", declaration_id)
        value = float(decl.get("value", 0))
        duty = round(value * float(duty_rate), 2)
        tax = round((value + duty) * float(tax_rate), 2)
        cid = _id("ct_duty")
        return self.store.ct_duties.save(
            cid,
            {
                "calculation_id": cid,
                "declaration_id": declaration_id,
                "value": value,
                "duty": duty,
                "tax": tax,
                "total": round(duty + tax, 2),
                "at": _now(),
            },
        )

    def clear(self, declaration_id: str, *, status: str = "cleared") -> dict[str, Any]:
        decl = self.store.ct_declarations.get(declaration_id)
        if decl is None:
            raise NotFoundError("declaration", declaration_id)
        if status not in CLEARANCE_STATUSES:
            raise ValidationError(f"status must be one of {CLEARANCE_STATUSES}")
        decl["status"] = status
        decl["cleared_at"] = _now() if status == "cleared" else None
        self.store.ct_declarations.save(declaration_id, decl)
        wid = _id("ct_clr")
        return self.store.ct_clearances.save(
            wid,
            {
                "clearance_id": wid,
                "declaration_id": declaration_id,
                "status": status,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "offices": self.store.ct_offices.count(),
            "declarations": self.store.ct_declarations.count(),
            "hs_codes": self.store.ct_hs_codes.count(),
            "clearances": self.store.ct_clearances.count(),
        }


class BorderControl:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store

    def register_checkpoint(self, *, name: str, border: str = "") -> dict[str, Any]:
        if not name:
            raise ValidationError("checkpoint name required")
        cid = _id("ct_cp")
        return self.store.ct_checkpoints.save(
            cid, {"checkpoint_id": cid, "name": name, "border": border, "created_at": _now()}
        )

    def inspect_cargo(self, *, checkpoint_id: str, cargo_ref: str, result: str = "pass") -> dict[str, Any]:
        if self.store.ct_checkpoints.get(checkpoint_id) is None:
            raise NotFoundError("checkpoint", checkpoint_id)
        iid = _id("ct_icin")
        return self.store.ct_cargo_insp.save(
            iid,
            {
                "inspection_id": iid,
                "checkpoint_id": checkpoint_id,
                "cargo_ref": cargo_ref,
                "result": result,
                "at": _now(),
            },
        )

    def inspect_vehicle(self, *, checkpoint_id: str, plate: str, result: str = "pass") -> dict[str, Any]:
        if self.store.ct_checkpoints.get(checkpoint_id) is None:
            raise NotFoundError("checkpoint", checkpoint_id)
        iid = _id("ct_ivin")
        return self.store.ct_vehicle_insp.save(
            iid,
            {
                "inspection_id": iid,
                "checkpoint_id": checkpoint_id,
                "plate": plate,
                "result": result,
                "at": _now(),
            },
        )

    def inspect_container(self, *, checkpoint_id: str, container_ref: str, result: str = "pass") -> dict[str, Any]:
        if self.store.ct_checkpoints.get(checkpoint_id) is None:
            raise NotFoundError("checkpoint", checkpoint_id)
        iid = _id("ct_ictn")
        return self.store.ct_container_insp.save(
            iid,
            {
                "inspection_id": iid,
                "checkpoint_id": checkpoint_id,
                "container_ref": container_ref,
                "result": result,
                "at": _now(),
            },
        )

    def verify_seal(self, *, container_ref: str, seal_no: str, intact: bool = True) -> dict[str, Any]:
        if not seal_no:
            raise ValidationError("seal_no required")
        sid = _id("ct_seal")
        return self.store.ct_seals.save(
            sid,
            {
                "seal_id": sid,
                "container_ref": container_ref,
                "seal_no": seal_no,
                "intact": bool(intact),
                "at": _now(),
            },
        )

    def risk_inspect(self, *, checkpoint_id: str, subject_ref: str, risk_score: float) -> dict[str, Any]:
        if self.store.ct_checkpoints.get(checkpoint_id) is None:
            raise NotFoundError("checkpoint", checkpoint_id)
        risk = float(risk_score)
        if risk < 0 or risk > 1:
            raise ValidationError("risk_score must be 0..1")
        rid = _id("ct_risk")
        return self.store.ct_risk_insp.save(
            rid,
            {
                "inspection_id": rid,
                "checkpoint_id": checkpoint_id,
                "subject_ref": subject_ref,
                "risk_score": risk,
                "action": "inspect" if risk >= 0.5 else "release",
                "at": _now(),
            },
        )

    def crossing(self, *, checkpoint_id: str, direction: str, subject_ref: str) -> dict[str, Any]:
        if self.store.ct_checkpoints.get(checkpoint_id) is None:
            raise NotFoundError("checkpoint", checkpoint_id)
        if direction not in ("in", "out"):
            raise ValidationError("direction must be in or out")
        xid = _id("ct_xng")
        return self.store.ct_crossings.save(
            xid,
            {
                "crossing_id": xid,
                "checkpoint_id": checkpoint_id,
                "direction": direction,
                "subject_ref": subject_ref,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "checkpoints": self.store.ct_checkpoints.count(),
            "cargo_inspections": self.store.ct_cargo_insp.count(),
            "crossings": self.store.ct_crossings.count(),
        }
