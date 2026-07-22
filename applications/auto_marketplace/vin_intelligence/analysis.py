"""AI VIN analysis — fraud, value, risk — Sprint 13.1."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.auto_marketplace.shared.exceptions import ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store
from applications.auto_marketplace.vin_intelligence.decoder import VINDecoder


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class AIAnalysis:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store
        self.decoder = VINDecoder(self.store)

    def _save(self, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
        rid = _id("vianal")
        result = {"analysis_id": rid, "kind": kind, **payload, "at": _now()}
        return self.store.vi_analyses.save(rid, result)

    def validate_vin(self, vin: str) -> dict[str, Any]:
        fmt = self.decoder.validate_format(vin)
        return self._save("vin_validation", {**fmt, "validated": fmt["valid_format"]})

    def detect_fake_vin(self, vin: str) -> dict[str, Any]:
        fmt = self.decoder.validate_format(vin)
        flags = list(fmt["issues"])
        vin_n = fmt["vin"]
        if vin_n and vin_n == vin_n[0] * len(vin_n):
            flags.append("repeated_chars")
        if "000000" in vin_n:
            flags.append("suspicious_zeros")
        return self._save(
            "fake_vin",
            {"vin": vin_n, "fake": bool(flags) or not fmt["valid_format"], "flags": flags},
        )

    def detect_clone(self, vin: str) -> dict[str, Any]:
        vin_n = (vin or "").strip().upper()
        matches = [p for p in self.store.vi_passports.list_all() if p.get("vin") == vin_n]
        histories = [h for h in self.store.vi_history.list_all() if h.get("vin") == vin_n]
        clone_risk = len(matches) > 1 or len(histories) > 5
        return self._save(
            "clone_detection",
            {
                "vin": vin_n,
                "clone_suspected": clone_risk,
                "passport_count": len(matches),
                "history_records": len(histories),
            },
        )

    def detect_fraud(self, *, vin: str, listing_price: float = 0.0, claimed_mileage: int = 0) -> dict[str, Any]:
        fake = self.detect_fake_vin(vin)
        clone = self.detect_clone(vin)
        flags: list[str] = []
        if fake.get("fake"):
            flags.append("fake_vin")
        if clone.get("clone_suspected"):
            flags.append("possible_clone")
        if listing_price and listing_price < 1000:
            flags.append("suspicious_price")
        if claimed_mileage and claimed_mileage < 100 and listing_price > 5000:
            flags.append("mileage_price_mismatch")
        score = min(1.0, 0.25 * len(flags))
        return self._save(
            "fraud_detection",
            {
                "vin": (vin or "").strip().upper(),
                "listing_price": listing_price,
                "claimed_mileage": claimed_mileage,
                "fraudulent": bool(flags),
                "fraud_score": score,
                "flags": flags,
            },
        )

    def predict_odometer_fraud(self, *, vin: str, mileage: int, year: int | None = None) -> dict[str, Any]:
        expected_min = max(0, ((year or 2018) - 2000) * 8000) if year else 40000
        roll_back = mileage < expected_min * 0.35
        return self._save(
            "odometer_fraud",
            {
                "vin": (vin or "").strip().upper(),
                "mileage": mileage,
                "expected_min": expected_min,
                "rollback_suspected": roll_back,
                "risk": "high" if roll_back else "low",
            },
        )

    def accident_probability(self, *, vin: str, age_years: int = 5, prior_accidents: int = 0) -> dict[str, Any]:
        base = min(0.85, 0.08 * age_years + 0.2 * prior_accidents)
        return self._save(
            "accident_probability",
            {"vin": (vin or "").strip().upper(), "probability": round(base, 3), "age_years": age_years, "prior_accidents": prior_accidents},
        )

    def market_value(self, *, vin: str, mileage: int = 50000, base_price: float = 20000.0) -> dict[str, Any]:
        adj = max(0.35, 1.0 - mileage / 280000.0)
        value = round(base_price * adj, 2)
        return self._save(
            "market_value",
            {"vin": (vin or "").strip().upper(), "mileage": mileage, "estimate": value, "currency": "USD"},
        )

    def future_repairs(self, *, vin: str, mileage: int = 0) -> dict[str, Any]:
        repairs = []
        if mileage >= 40000:
            repairs.append({"item": "brake_service", "eta_miles": mileage + 5000, "est_cost": 450})
        if mileage >= 80000:
            repairs.append({"item": "timing_components", "eta_miles": mileage + 10000, "est_cost": 1200})
        if not repairs:
            repairs.append({"item": "routine_inspection", "eta_miles": mileage + 10000, "est_cost": 150})
        return self._save("future_repairs", {"vin": (vin or "").strip().upper(), "mileage": mileage, "repairs": repairs})

    def residual_value(self, *, vin: str, current_value: float = 20000.0, years: int = 3) -> dict[str, Any]:
        residual = round(current_value * (0.82**years), 2)
        return self._save(
            "residual_value",
            {"vin": (vin or "").strip().upper(), "current_value": current_value, "years": years, "forecast": residual},
        )

    def run(self, *, kind: str, **kwargs: Any) -> dict[str, Any]:
        mapping = {
            "vin_validation": lambda: self.validate_vin(kwargs.get("vin", "")),
            "fake_vin": lambda: self.detect_fake_vin(kwargs.get("vin", "")),
            "clone_detection": lambda: self.detect_clone(kwargs.get("vin", "")),
            "fraud_detection": lambda: self.detect_fraud(
                vin=kwargs.get("vin", ""),
                listing_price=float(kwargs.get("listing_price", 0) or 0),
                claimed_mileage=int(kwargs.get("claimed_mileage", 0) or 0),
            ),
            "odometer_fraud": lambda: self.predict_odometer_fraud(
                vin=kwargs.get("vin", ""),
                mileage=int(kwargs.get("mileage", 0) or 0),
                year=kwargs.get("year"),
            ),
            "accident_probability": lambda: self.accident_probability(
                vin=kwargs.get("vin", ""),
                age_years=int(kwargs.get("age_years", 5) or 5),
                prior_accidents=int(kwargs.get("prior_accidents", 0) or 0),
            ),
            "market_value": lambda: self.market_value(
                vin=kwargs.get("vin", ""),
                mileage=int(kwargs.get("mileage", 50000) or 50000),
                base_price=float(kwargs.get("base_price", 20000) or 20000),
            ),
            "future_repairs": lambda: self.future_repairs(
                vin=kwargs.get("vin", ""),
                mileage=int(kwargs.get("mileage", 0) or 0),
            ),
            "residual_value": lambda: self.residual_value(
                vin=kwargs.get("vin", ""),
                current_value=float(kwargs.get("current_value", 20000) or 20000),
                years=int(kwargs.get("years", 3) or 3),
            ),
        }
        if kind not in mapping:
            raise ValidationError(f"kind must be one of {list(mapping)}")
        return mapping[kind]()

    def status(self) -> dict[str, Any]:
        return {"analyses": self.store.vi_analyses.count()}
