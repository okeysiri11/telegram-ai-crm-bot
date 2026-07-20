# Receipt service.

from __future__ import annotations

from applications.auto_marketplace.finance.models import Receipt
from applications.auto_marketplace.shared.exceptions import NotFoundError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class ReceiptService:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def generate(self, *, payment_id: str, invoice_id: str, customer_id: str, amount: float, currency: str = "USD") -> Receipt:
        receipt = Receipt(
            payment_id=payment_id,
            invoice_id=invoice_id,
            customer_id=customer_id,
            amount=amount,
            currency=currency,
            pdf_url=f"/receipts/{payment_id}.pdf",
        )
        return self._store.receipts.save(receipt.receipt_id, receipt)

    def get(self, receipt_id: str) -> Receipt:
        receipt = self._store.receipts.get(receipt_id)
        if receipt is None:
            raise NotFoundError("Receipt", receipt_id)
        return receipt

    def list_receipts(self, *, customer_id: str = "") -> list[Receipt]:
        items = self._store.receipts.list_all()
        if customer_id:
            items = [r for r in items if r.customer_id == customer_id]
        return items


receipt_service = ReceiptService()
