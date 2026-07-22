# Vehicle Transaction Engine — purchase, reserve, offer, contract, delivery.

from __future__ import annotations

import time

from applications.auto_marketplace.contracts.transaction_engine import (
    TransactionContractEngine,
    transaction_contract_engine,
)
from applications.auto_marketplace.documents.transaction_engine import (
    TransactionDocumentEngine,
    transaction_document_engine,
)
from applications.auto_marketplace.escrow.engine import EscrowEngine, escrow_engine
from applications.auto_marketplace.ownership_transfer.engine import (
    OwnershipTransferEngine,
    ownership_transfer_engine,
)
from applications.auto_marketplace.payments.transaction_engine import (
    TransactionPaymentEngine,
    transaction_payment_engine,
)
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store
from applications.auto_marketplace.transactions.models import TransactionStatus, VehicleTransaction


class VehicleTransactionEngine:
    def __init__(
        self,
        store: MarketplaceStore | None = None,
        escrow: EscrowEngine | None = None,
        payments: TransactionPaymentEngine | None = None,
        contracts: TransactionContractEngine | None = None,
        ownership: OwnershipTransferEngine | None = None,
        documents: TransactionDocumentEngine | None = None,
    ) -> None:
        self._store = store or marketplace_store
        self.escrow = escrow or escrow_engine
        self.payments = payments or transaction_payment_engine
        self.contracts = contracts or transaction_contract_engine
        self.ownership = ownership or ownership_transfer_engine
        self.documents = documents or transaction_document_engine

    def create(self, tx: VehicleTransaction) -> VehicleTransaction:
        if not tx.vehicle_id or not tx.buyer_id:
            raise ValidationError("vehicle_id and buyer_id are required")
        if tx.price <= 0:
            raise ValidationError("price must be positive")
        tx.status = TransactionStatus.DRAFT
        tx.updated_at = time.time()
        return self._store.vehicle_transactions.save(tx.transaction_id, tx)

    def get(self, transaction_id: str) -> VehicleTransaction:
        tx = self._store.vehicle_transactions.get(transaction_id)
        if tx is None:
            raise NotFoundError("VehicleTransaction", transaction_id)
        return tx

    def reserve(self, transaction_id: str, deposit: float = 0.0) -> VehicleTransaction:
        tx = self.get(transaction_id)
        tx.status = TransactionStatus.RESERVED
        tx.updated_at = time.time()
        if deposit > 0:
            self.payments.create(transaction_id=transaction_id, amount=deposit, kind="deposit", currency=tx.currency)
        return self._store.vehicle_transactions.save(transaction_id, tx)

    def make_offer(self, transaction_id: str, amount: float, from_party: str = "buyer") -> VehicleTransaction:
        tx = self.get(transaction_id)
        tx.offers.append({"amount": amount, "from": from_party, "at": time.time(), "type": "offer"})
        tx.status = TransactionStatus.OFFERED
        tx.price = amount
        tx.updated_at = time.time()
        return self._store.vehicle_transactions.save(transaction_id, tx)

    def counter_offer(self, transaction_id: str, amount: float, from_party: str = "seller") -> VehicleTransaction:
        tx = self.get(transaction_id)
        tx.offers.append({"amount": amount, "from": from_party, "at": time.time(), "type": "counter"})
        tx.status = TransactionStatus.COUNTERED
        tx.price = amount
        tx.updated_at = time.time()
        return self._store.vehicle_transactions.save(transaction_id, tx)

    def create_contract(self, transaction_id: str) -> VehicleTransaction:
        tx = self.get(transaction_id)
        contract = self.contracts.create(
            transaction_id=transaction_id,
            price=tx.price,
            vehicle_id=tx.vehicle_id,
            buyer_id=tx.buyer_id,
            seller_id=tx.seller_id,
        )
        tx.contract_id = contract.contract_id
        tx.status = TransactionStatus.CONTRACTED
        tx.updated_at = time.time()
        return self._store.vehicle_transactions.save(transaction_id, tx)

    def sign(self, transaction_id: str, signed_by: str) -> VehicleTransaction:
        tx = self.get(transaction_id)
        if not tx.contract_id:
            self.create_contract(transaction_id)
            tx = self.get(transaction_id)
        self.contracts.sign(tx.contract_id, signed_by)
        tx.signature = signed_by
        tx.status = TransactionStatus.SIGNED
        tx.updated_at = time.time()
        return self._store.vehicle_transactions.save(transaction_id, tx)

    def fund_escrow(self, transaction_id: str) -> VehicleTransaction:
        tx = self.get(transaction_id)
        account = self.escrow.open(transaction_id=transaction_id, amount=tx.price, currency=tx.currency)
        self.escrow.hold(account.escrow_id)
        payment = self.payments.create(
            transaction_id=transaction_id, amount=tx.price, kind="invoice", currency=tx.currency
        )
        self.payments.capture(payment.payment_id)
        tx.escrow_id = account.escrow_id
        tx.status = TransactionStatus.PAID
        tx.updated_at = time.time()
        return self._store.vehicle_transactions.save(transaction_id, tx)

    def transfer_ownership(self, transaction_id: str) -> VehicleTransaction:
        tx = self.get(transaction_id)
        record = self.ownership.initiate(
            transaction_id=transaction_id,
            vehicle_id=tx.vehicle_id,
            from_owner=tx.seller_id or tx.dealer_id,
            to_owner=tx.buyer_id,
        )
        self.ownership.complete(record.transfer_id)
        if tx.escrow_id:
            self.escrow.release(
                tx.escrow_id,
                conditions_met=["payment_cleared", "contract_signed", "no_active_dispute"],
            )
        tx.status = TransactionStatus.TRANSFERRED
        tx.updated_at = time.time()
        self.documents.generate_packet(transaction_id=transaction_id)
        return self._store.vehicle_transactions.save(transaction_id, tx)

    def deliver(self, transaction_id: str, *, location: str = "", carrier: str = "") -> VehicleTransaction:
        tx = self.get(transaction_id)
        tx.delivery = {"location": location, "carrier": carrier, "delivered_at": time.time()}
        tx.status = TransactionStatus.DELIVERED
        tx.updated_at = time.time()
        return self._store.vehicle_transactions.save(transaction_id, tx)

    def complete(self, transaction_id: str) -> VehicleTransaction:
        tx = self.get(transaction_id)
        tx.status = TransactionStatus.COMPLETED
        tx.updated_at = time.time()
        return self._store.vehicle_transactions.save(transaction_id, tx)

    def list_transactions(self, *, buyer_id: str = "", status: str = "") -> list[VehicleTransaction]:
        items = self._store.vehicle_transactions.list_all()
        if buyer_id:
            items = [t for t in items if t.buyer_id == buyer_id]
        if status:
            items = [t for t in items if t.status.value == status]
        return items

    def metrics(self) -> dict:
        items = self._store.vehicle_transactions.list_all()
        return {
            "vehicle_transactions": len(items),
            "completed": len([t for t in items if t.status == TransactionStatus.COMPLETED]),
            "escrow": self.escrow.metrics(),
            "payments": self.payments.metrics(),
        }


vehicle_transaction_engine = VehicleTransactionEngine()
