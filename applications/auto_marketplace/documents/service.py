# DocumentService — contracts, invoices, inspection reports.

from __future__ import annotations

import time
from typing import Any

from applications.auto_marketplace.shared.exceptions import NotFoundError
from applications.auto_marketplace.shared.models import Invoice
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class DocumentService:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def store_document(self, doc_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        doc = {"document_id": doc_id, "created_at": time.time(), **payload}
        self._store.documents.save(doc_id, doc)
        return doc

    def get_document(self, doc_id: str) -> dict[str, Any]:
        doc = self._store.documents.get(doc_id)
        if doc is None:
            raise NotFoundError("Document", doc_id)
        return doc

    def generate_invoice(self, invoice: Invoice) -> Invoice:
        invoice.pdf_url = f"/documents/invoices/{invoice.invoice_id}.pdf"
        self._store.invoices.save(invoice.invoice_id, invoice)
        self.store_document(
            invoice.invoice_id,
            {"type": "invoice", "deal_id": invoice.deal_id, "pdf_url": invoice.pdf_url},
        )
        return invoice


document_service = DocumentService()
