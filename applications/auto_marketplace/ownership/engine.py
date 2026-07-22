# Ownership Engine — ownership transfers linked to vehicle history.

from __future__ import annotations

from applications.auto_marketplace.history.engine import HistoryEngine, history_engine
from applications.auto_marketplace.marketplace.models import OwnershipTransfer
from applications.auto_marketplace.shared.exceptions import ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class OwnershipEngine:
    def __init__(
        self,
        store: MarketplaceStore | None = None,
        history: HistoryEngine | None = None,
    ) -> None:
        self._store = store or marketplace_store
        self._history = history or history_engine

    def transfer(self, transfer: OwnershipTransfer) -> OwnershipTransfer:
        if not transfer.vin or not transfer.to_owner:
            raise ValidationError("vin and to_owner are required")
        saved = self._store.ownership_transfers.save(transfer.transfer_id, transfer)
        self._history.add_ownership(
            transfer.vin,
            transfer.to_owner,
            from_date=transfer.from_owner,
            to_date="",
        )
        return saved

    def list_for_vin(self, vin: str) -> list[OwnershipTransfer]:
        vin = (vin or "").strip().upper()
        return [t for t in self._store.ownership_transfers.list_all() if t.vin.upper() == vin]

    def metrics(self) -> dict:
        return {"ownership_transfers": self._store.ownership_transfers.count()}


ownership_engine = OwnershipEngine()
