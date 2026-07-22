# Leasing Engine — personal/business/fleet leases and contracts.

from __future__ import annotations

from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store
from applications.auto_marketplace.transactions.models import LeaseOffer, LeaseType


class LeasingEngine:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def quote(
        self,
        *,
        buyer_id: str,
        vehicle_price: float,
        lease_type: LeaseType = LeaseType.PERSONAL,
        term_months: int = 36,
        residual_pct: float = 0.45,
        vehicle_id: str = "",
        mileage_limit_km: int = 15000,
        currency: str = "USD",
    ) -> LeaseOffer:
        if vehicle_price <= 0 or term_months <= 0:
            raise ValidationError("vehicle_price and term_months must be positive")
        residual = round(vehicle_price * residual_pct, 2)
        depreciable = vehicle_price - residual
        money_factor = 0.0025 if lease_type == LeaseType.PERSONAL else 0.0022
        monthly = round(depreciable / term_months + vehicle_price * money_factor, 2)
        contract = (
            f"Lease ({lease_type.value}) for vehicle {vehicle_id or 'N/A'}: "
            f"{term_months} months @ {monthly} {currency}/mo, residual {residual}."
        )
        offer = LeaseOffer(
            buyer_id=buyer_id,
            vehicle_id=vehicle_id,
            lease_type=lease_type,
            vehicle_price=vehicle_price,
            residual_value=residual,
            term_months=term_months,
            monthly_payment=monthly,
            mileage_limit_km=mileage_limit_km,
            currency=currency,
            contract_text=contract,
        )
        return self._store.lease_offers.save(offer.lease_id, offer)

    def compare(self, vehicle_price: float, term_months: int = 36) -> list[dict]:
        out = []
        for lt in LeaseType:
            offer = self.quote(buyer_id="compare", vehicle_price=vehicle_price, lease_type=lt, term_months=term_months)
            out.append(offer.to_dict())
        return out

    def generate_contract(self, lease_id: str) -> LeaseOffer:
        offer = self._store.lease_offers.get(lease_id)
        if offer is None:
            raise NotFoundError("LeaseOffer", lease_id)
        offer.status = "contract_ready"
        offer.contract_text = offer.contract_text or f"Lease contract {lease_id}"
        return self._store.lease_offers.save(lease_id, offer)

    def list_offers(self, *, buyer_id: str = "") -> list[LeaseOffer]:
        items = self._store.lease_offers.list_all()
        if buyer_id:
            items = [o for o in items if o.buyer_id == buyer_id]
        return items

    def metrics(self) -> dict:
        return {"lease_offers": self._store.lease_offers.count()}


leasing_engine = LeasingEngine()
