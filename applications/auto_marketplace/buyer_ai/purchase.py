"""Purchase intelligence & buying protection — Sprint 13.4."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.auto_marketplace.shared.exceptions import ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class PurchaseIntelligence:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store

    def analyze(
        self,
        *,
        price: float,
        mileage: int = 50000,
        fuel: str = "gasoline",
        years: int = 5,
        loan_rate: float = 0.06,
        down_payment: float = 0.0,
    ) -> dict[str, Any]:
        price = float(price)
        annual_fuel = 1400.0 if fuel == "electric" else 2200.0
        annual_maint = 600.0 + mileage / 100.0
        insurance = round(price * 0.035 + 400, 2)
        depreciation = round(price * (1 - 0.82**years), 2)
        residual = round(price - depreciation, 2)
        principal = max(0.0, price - float(down_payment))
        monthly_rate = float(loan_rate) / 12
        months = years * 12
        if monthly_rate > 0 and principal > 0:
            loan_payment = principal * (monthly_rate * (1 + monthly_rate) ** months) / ((1 + monthly_rate) ** months - 1)
        else:
            loan_payment = principal / max(1, months)
        lease_monthly = round(price * 0.018, 2)
        tco = round(price + annual_fuel * years + annual_maint * years + insurance * years, 2)
        rid = _id("bai_pi")
        result = {
            "analysis_id": rid,
            "price": price,
            "total_ownership_cost": tco,
            "insurance_prediction_annual": insurance,
            "fuel_cost_annual": annual_fuel,
            "maintenance_forecast_annual": round(annual_maint, 2),
            "depreciation_forecast": depreciation,
            "residual_value": residual,
            "loan": {
                "principal": round(principal, 2),
                "monthly_payment": round(loan_payment, 2),
                "rate": loan_rate,
                "term_months": months,
            },
            "leasing_comparison": {
                "estimated_monthly": lease_monthly,
                "better": "lease" if lease_monthly * months < tco * 0.55 else "buy",
            },
            "years": years,
            "at": _now(),
        }
        return self.store.ba_purchase_intel.save(rid, result)

    def status(self) -> dict[str, Any]:
        return {"analyses": self.store.ba_purchase_intel.count()}


class BuyingProtection:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store

    def assess(
        self,
        *,
        vin: str,
        listing_id: str = "",
        listing_price: float = 0.0,
        inspection_ref: str = "",
        fraud_flags: list[str] | None = None,
    ) -> dict[str, Any]:
        vin = (vin or "").strip().upper()
        if len(vin) < 11:
            raise ValidationError("vin required")
        flags = list(fraud_flags or [])
        if len(vin) != 17:
            flags.append("vin_length")
        if listing_price and listing_price < 1000:
            flags.append("suspicious_price")
        dupes = [l for l in self.store.ba_listings.list_all() if l.get("vin") == vin]
        if len(dupes) > 1:
            flags.append("duplicate_listing")
        scam = any(f in flags for f in ("suspicious_price", "duplicate_listing"))
        risk = min(100.0, 15.0 * len(flags) + (25 if scam else 0))
        rid = _id("bai_prot")
        result = {
            "protection_id": rid,
            "vin": vin,
            "listing_id": listing_id,
            "vin_verified": len(vin) == 17 and "IOQ" not in vin,
            "inspection_ref": inspection_ref,
            "fraud_detected": bool(flags),
            "scam_detected": scam,
            "duplicate_listing": "duplicate_listing" in flags,
            "risk_score": risk,
            "flags": flags,
            "legal_checklist": [
                "verify_title",
                "confirm_seller_identity",
                "review_contract",
                "confirm_payment_escrow",
            ],
            "at": _now(),
        }
        return self.store.ba_protection.save(rid, result)

    def status(self) -> dict[str, Any]:
        return {"assessments": self.store.ba_protection.count()}
