# Transaction document packing — bill of sale, delivery receipt, title packet.

from __future__ import annotations

import time
import uuid

from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class TransactionDocumentEngine:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def generate_packet(self, *, transaction_id: str, kinds: list[str] | None = None) -> list[dict]:
        kinds = kinds or ["bill_of_sale", "delivery_receipt", "title_transfer"]
        docs = []
        for kind in kinds:
            doc = {
                "document_id": str(uuid.uuid4()),
                "transaction_id": transaction_id,
                "kind": kind,
                "status": "generated",
                "created_at": time.time(),
            }
            self._store.transaction_documents.save(doc["document_id"], doc)
            docs.append(doc)
        return docs

    def list_for_transaction(self, transaction_id: str) -> list[dict]:
        return [d for d in self._store.transaction_documents.list_all() if d["transaction_id"] == transaction_id]

    def metrics(self) -> dict:
        return {"transaction_documents": self._store.transaction_documents.count()}


transaction_document_engine = TransactionDocumentEngine()
