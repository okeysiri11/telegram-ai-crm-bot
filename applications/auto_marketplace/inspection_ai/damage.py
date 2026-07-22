"""Damage detection models — Sprint 13.2."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.auto_marketplace.shared.exceptions import ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store

DAMAGE_TYPES = [
    "dent",
    "scratch",
    "paint_thickness",
    "rust",
    "corrosion",
    "crack",
    "frame",
    "flood",
    "fire",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class DamageDetection:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store
        self.damage_types = list(DAMAGE_TYPES)

    def detect(
        self,
        *,
        vin: str = "",
        damage_type: str,
        location: str = "body",
        severity: float = 0.3,
        evidence: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if damage_type not in self.damage_types:
            raise ValidationError(f"damage_type must be one of {self.damage_types}")
        severity = max(0.0, min(1.0, float(severity)))
        evidence = evidence or {}
        detected = severity >= 0.2 or bool(evidence.get("force"))
        level = "high" if severity >= 0.7 else "medium" if severity >= 0.4 else "low"
        rid = _id("iadmg")
        result = {
            "detection_id": rid,
            "vin": (vin or "").strip().upper(),
            "damage_type": damage_type,
            "location": location,
            "severity": severity,
            "level": level,
            "detected": detected,
            "evidence": evidence,
            "detected_at": _now(),
        }
        return self.store.ia_damages.save(rid, result)

    def scan_all(self, *, vin: str, signals: dict[str, float] | None = None) -> list[dict[str, Any]]:
        signals = signals or {}
        results = []
        for dtype in self.damage_types:
            sev = float(signals.get(dtype, 0.15 if dtype in ("dent", "scratch") else 0.05))
            results.append(self.detect(vin=vin, damage_type=dtype, severity=sev, location="multi"))
        return results

    def list_for_vin(self, vin: str) -> list[dict[str, Any]]:
        vin = (vin or "").strip().upper()
        return [d for d in self.store.ia_damages.list_all() if d.get("vin") == vin]

    def status(self) -> dict[str, Any]:
        return {"detections": self.store.ia_damages.count(), "damage_types": self.damage_types}
