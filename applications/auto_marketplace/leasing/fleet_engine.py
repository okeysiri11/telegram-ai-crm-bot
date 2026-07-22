# Fleet Leasing — operational/financial leases (alongside purchase LeasingEngine).

from __future__ import annotations

from applications.auto_marketplace.fleet.models import FleetLeaseContract, FleetLeaseKind
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class FleetLeasingEngine:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def quote(
        self,
        *,
        fleet_vehicle_id: str,
        customer_id: str,
        vehicle_price: float,
        kind: FleetLeaseKind = FleetLeaseKind.OPERATIONAL,
        term_months: int = 36,
        residual_pct: float = 0.4,
        insurance_policy: str = "",
        currency: str = "USD",
    ) -> FleetLeaseContract:
        if vehicle_price <= 0 or term_months <= 0:
            raise ValidationError("vehicle_price and term_months must be positive")
        residual = round(vehicle_price * residual_pct, 2)
        factor = 0.0022 if kind == FleetLeaseKind.OPERATIONAL else 0.0028
        monthly = round((vehicle_price - residual) / term_months + vehicle_price * factor, 2)
        schedule = [{"month": i, "amount": monthly, "status": "scheduled"} for i in range(1, term_months + 1)]
        contract = FleetLeaseContract(
            fleet_vehicle_id=fleet_vehicle_id,
            customer_id=customer_id,
            kind=kind,
            vehicle_price=vehicle_price,
            residual_value=residual,
            term_months=term_months,
            monthly_payment=monthly,
            schedule=schedule,
            insurance_policy=insurance_policy or "fleet-default",
            buyout_price=residual,
            currency=currency,
            status="quoted",
        )
        return self._store.fleet_lease_contracts.save(contract.lease_id, contract)

    def approve(self, lease_id: str) -> FleetLeaseContract:
        contract = self._get(lease_id)
        contract.status = "approved"
        return self._store.fleet_lease_contracts.save(lease_id, contract)

    def buyout(self, lease_id: str) -> FleetLeaseContract:
        contract = self._get(lease_id)
        contract.status = "bought_out"
        return self._store.fleet_lease_contracts.save(lease_id, contract)

    def _get(self, lease_id: str) -> FleetLeaseContract:
        item = self._store.fleet_lease_contracts.get(lease_id)
        if item is None:
            raise NotFoundError("FleetLeaseContract", lease_id)
        return item

    def list_leases(self, *, customer_id: str = "") -> list[FleetLeaseContract]:
        items = self._store.fleet_lease_contracts.list_all()
        if customer_id:
            items = [c for c in items if c.customer_id == customer_id]
        return items

    def metrics(self) -> dict:
        return {"fleet_leases": self._store.fleet_lease_contracts.count()}


fleet_leasing_engine = FleetLeasingEngine()
