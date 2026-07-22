"""Photo / media inspection analysis — Sprint 13.2."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.auto_marketplace.shared.exceptions import ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store

PHOTO_ZONES = [
    "exterior",
    "interior",
    "engine_bay",
    "undercarriage",
    "wheel",
    "glass",
    "lighting",
    "paint",
    "vin_plate",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class PhotoInspection:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store
        self.zones = list(PHOTO_ZONES)

    def analyze(
        self,
        *,
        vin: str = "",
        zone: str,
        media_uri: str = "",
        media_type: str = "photo",
        signals: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if zone not in self.zones:
            raise ValidationError(f"zone must be one of {self.zones}")
        if media_type not in ("photo", "video"):
            raise ValidationError("media_type must be photo or video")
        signals = signals or {}
        quality = float(signals.get("quality", 0.85))
        findings: list[str] = []
        if zone == "vin_plate":
            findings.append("vin_characters_readable" if quality > 0.5 else "vin_plate_unclear")
        elif zone == "paint":
            findings.append("paint_uniform" if quality > 0.7 else "paint_irregularities")
        elif zone == "engine_bay":
            findings.append("bay_clean" if quality > 0.6 else "bay_contamination")
        else:
            findings.append(f"{zone}_captured")
        rid = _id("iaimg")
        result = {
            "analysis_id": rid,
            "vin": (vin or "").strip().upper(),
            "zone": zone,
            "media_uri": media_uri,
            "media_type": media_type,
            "quality": quality,
            "findings": findings,
            "analyzed_at": _now(),
        }
        return self.store.ia_photo_analyses.save(rid, result)

    def status(self) -> dict[str, Any]:
        return {"analyses": self.store.ia_photo_analyses.count(), "zones": self.zones}
