# Warranty Engine — validation, repairs, claims, history.

from __future__ import annotations

import time

from applications.auto_marketplace.service_centers.models import WarrantyClaim, WarrantyKind, WarrantyPolicy
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class WarrantyEngine:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def register(self, policy: WarrantyPolicy) -> WarrantyPolicy:
        if not policy.vehicle_id and not policy.vin:
            raise ValidationError("vehicle_id or vin is required")
        if not policy.ends_at:
            policy.ends_at = time.time() + 3 * 365 * 86400
        policy.history.append({"event": "registered", "at": time.time()})
        return self._store.warranty_policies.save(policy.warranty_id, policy)

    def get(self, warranty_id: str) -> WarrantyPolicy:
        item = self._store.warranty_policies.get(warranty_id)
        if item is None:
            raise NotFoundError("WarrantyPolicy", warranty_id)
        return item

    def validate(self, warranty_id: str, *, mileage_km: int = 0, now: float | None = None) -> dict:
        policy = self.get(warranty_id)
        now = now if now is not None else time.time()
        valid = policy.active and now <= policy.ends_at and mileage_km <= policy.mileage_limit_km
        return {
            "warranty_id": warranty_id,
            "valid": valid,
            "kind": policy.kind.value,
            "provider": policy.provider,
            "ends_at": policy.ends_at,
            "mileage_limit_km": policy.mileage_limit_km,
        }

    def open_claim(self, *, warranty_id: str, description: str, order_id: str = "", amount: float = 0.0) -> WarrantyClaim:
        self.get(warranty_id)
        claim = WarrantyClaim(
            warranty_id=warranty_id,
            order_id=order_id,
            description=description,
            amount=amount,
        )
        policy = self.get(warranty_id)
        policy.history.append({"event": "claim_opened", "claim_id": claim.claim_id, "at": time.time()})
        self._store.warranty_policies.save(warranty_id, policy)
        return self._store.warranty_claims.save(claim.claim_id, claim)

    def list_for_vehicle(self, vehicle_id: str = "", vin: str = "") -> list[WarrantyPolicy]:
        items = self._store.warranty_policies.list_all()
        if vehicle_id:
            items = [w for w in items if w.vehicle_id == vehicle_id]
        if vin:
            items = [w for w in items if w.vin.upper() == vin.upper()]
        return items

    def metrics(self) -> dict:
        return {
            "policies": self._store.warranty_policies.count(),
            "claims": self._store.warranty_claims.count(),
            "kinds": [k.value for k in WarrantyKind],
        }


warranty_engine = WarrantyEngine()
