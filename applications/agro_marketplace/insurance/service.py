# Insurance policies for export shipments.

from __future__ import annotations

from applications.agro_marketplace.export.models import InsurancePolicy
from applications.agro_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.agro_marketplace.shared.store import AgroStore, agro_store


class InsuranceService:
    def __init__(self, store: AgroStore | None = None) -> None:
        self._store = store or agro_store

    def create_policy(self, policy: InsurancePolicy) -> InsurancePolicy:
        if policy.coverage_amount <= 0:
            raise ValidationError("coverage_amount must be positive")
        if not policy.premium:
            policy.premium = round(policy.coverage_amount * 0.012, 2)
        return self._store.insurance_policies.save(policy.policy_id, policy)

    def get(self, policy_id: str) -> InsurancePolicy:
        policy = self._store.insurance_policies.get(policy_id)
        if policy is None:
            raise NotFoundError("InsurancePolicy", policy_id)
        return policy

    def list_policies(self, *, shipment_id: str | None = None) -> list[InsurancePolicy]:
        items = self._store.insurance_policies.list_all()
        if shipment_id:
            items = [p for p in items if p.shipment_id == shipment_id]
        return items


insurance_service = InsuranceService()
