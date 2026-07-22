# Digital contracts for vehicle transactions.

from __future__ import annotations

import time

from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store
from applications.auto_marketplace.transactions.models import TransactionContract


class TransactionContractEngine:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def create(
        self,
        *,
        transaction_id: str,
        title: str = "Vehicle Purchase Agreement",
        body: str = "",
        price: float = 0.0,
        vehicle_id: str = "",
        buyer_id: str = "",
        seller_id: str = "",
    ) -> TransactionContract:
        if not transaction_id:
            raise ValidationError("transaction_id is required")
        body = body or (
            f"Agreement for vehicle {vehicle_id} between buyer {buyer_id} and seller {seller_id} "
            f"at price {price}."
        )
        contract = TransactionContract(transaction_id=transaction_id, title=title, body=body)
        return self._store.transaction_contracts.save(contract.contract_id, contract)

    def get(self, contract_id: str) -> TransactionContract:
        contract = self._store.transaction_contracts.get(contract_id)
        if contract is None:
            raise NotFoundError("TransactionContract", contract_id)
        return contract

    def sign(self, contract_id: str, signed_by: str) -> TransactionContract:
        contract = self.get(contract_id)
        if not signed_by:
            raise ValidationError("signed_by is required")
        contract.signed = True
        contract.signed_by = signed_by
        contract.signed_at = time.time()
        return self._store.transaction_contracts.save(contract_id, contract)

    def metrics(self) -> dict:
        items = self._store.transaction_contracts.list_all()
        return {"transaction_contracts": len(items), "signed": len([c for c in items if c.signed])}


transaction_contract_engine = TransactionContractEngine()
