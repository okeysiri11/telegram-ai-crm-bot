# Freight finance — export shipment cost tracking.

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from applications.agro_marketplace.shared.store import AgroStore, agro_store


@dataclass
class FreightFinanceRecord:
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    shipment_id: str = ""
    freight_cost: float = 0.0
    insurance_premium: float = 0.0
    duties_estimate: float = 0.0
    currency: str = "USD"
    status: str = "open"
    created_at: float = field(default_factory=time.time)

    @property
    def total(self) -> float:
        return self.freight_cost + self.insurance_premium + self.duties_estimate

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "shipment_id": self.shipment_id,
            "freight_cost": self.freight_cost,
            "insurance_premium": self.insurance_premium,
            "duties_estimate": self.duties_estimate,
            "currency": self.currency,
            "total": self.total,
            "status": self.status,
            "created_at": self.created_at,
        }


class FreightFinanceService:
    def __init__(self, store: AgroStore | None = None) -> None:
        self._store = store or agro_store

    def create(self, record: FreightFinanceRecord) -> FreightFinanceRecord:
        return self._store.freight_finance.save(record.record_id, record)

    def list_records(self, *, shipment_id: str | None = None) -> list[FreightFinanceRecord]:
        items = self._store.freight_finance.list_all()
        if shipment_id:
            items = [r for r in items if r.shipment_id == shipment_id]
        return items

    def estimate(
        self,
        *,
        shipment_id: str,
        freight_cost: float,
        coverage_amount: float = 0.0,
        duties_rate: float = 0.05,
        cargo_value: float = 0.0,
    ) -> FreightFinanceRecord:
        premium = round(coverage_amount * 0.012, 2) if coverage_amount else 0.0
        duties = round(cargo_value * duties_rate, 2)
        return self.create(
            FreightFinanceRecord(
                shipment_id=shipment_id,
                freight_cost=freight_cost,
                insurance_premium=premium,
                duties_estimate=duties,
            )
        )


freight_finance_service = FreightFinanceService()
