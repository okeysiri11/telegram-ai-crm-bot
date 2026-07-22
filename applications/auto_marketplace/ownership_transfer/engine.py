# Ownership Transfer Engine — title transfer for vehicle transactions.

from __future__ import annotations

import time

from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store
from applications.auto_marketplace.transactions.models import OwnershipTransferRecord


class OwnershipTransferEngine:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def initiate(
        self,
        *,
        transaction_id: str,
        vehicle_id: str,
        from_owner: str,
        to_owner: str,
    ) -> OwnershipTransferRecord:
        if not vehicle_id or not to_owner:
            raise ValidationError("vehicle_id and to_owner are required")
        record = OwnershipTransferRecord(
            transaction_id=transaction_id,
            vehicle_id=vehicle_id,
            from_owner=from_owner,
            to_owner=to_owner,
            status="pending",
        )
        return self._store.ownership_transfer_records.save(record.transfer_id, record)

    def complete(self, transfer_id: str) -> OwnershipTransferRecord:
        record = self._store.ownership_transfer_records.get(transfer_id)
        if record is None:
            raise NotFoundError("OwnershipTransferRecord", transfer_id)
        record.status = "completed"
        record.completed_at = time.time()
        return self._store.ownership_transfer_records.save(transfer_id, record)

    def get(self, transfer_id: str) -> OwnershipTransferRecord:
        record = self._store.ownership_transfer_records.get(transfer_id)
        if record is None:
            raise NotFoundError("OwnershipTransferRecord", transfer_id)
        return record

    def metrics(self) -> dict:
        return {"ownership_transfer_records": self._store.ownership_transfer_records.count()}


ownership_transfer_engine = OwnershipTransferEngine()
