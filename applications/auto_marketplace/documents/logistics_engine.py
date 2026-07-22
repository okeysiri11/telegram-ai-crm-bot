# Logistics Documents — CMR, BoL, declarations, invoices, insurance, e-sign.

from __future__ import annotations

import time

from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store
from applications.auto_marketplace.transport.models import LogisticsDocument


class LogisticsDocumentEngine:
    DOC_TYPES = (
        "cmr",
        "bol",
        "export_declaration",
        "import_declaration",
        "invoice",
        "insurance",
        "delivery_receipt",
    )

    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def create(
        self,
        *,
        shipment_id: str,
        doc_type: str,
        title: str = "",
        body: str = "",
    ) -> LogisticsDocument:
        if doc_type not in self.DOC_TYPES:
            raise ValidationError(f"unsupported doc_type: {doc_type}")
        if not shipment_id:
            raise ValidationError("shipment_id is required")
        doc = LogisticsDocument(
            shipment_id=shipment_id,
            doc_type=doc_type,
            title=title or doc_type.replace("_", " ").title(),
            body=body or f"{doc_type} for shipment {shipment_id}",
        )
        return self._store.logistics_documents.save(doc.document_id, doc)

    def get(self, document_id: str) -> LogisticsDocument:
        item = self._store.logistics_documents.get(document_id)
        if item is None:
            raise NotFoundError("LogisticsDocument", document_id)
        return item

    def sign(self, document_id: str, signed_by: str) -> LogisticsDocument:
        doc = self.get(document_id)
        if not signed_by:
            raise ValidationError("signed_by is required")
        doc.signed = True
        doc.signed_by = signed_by
        doc.signed_at = time.time()
        return self._store.logistics_documents.save(document_id, doc)

    def packet(self, shipment_id: str, *, international: bool = False) -> list[LogisticsDocument]:
        types = ["cmr", "invoice", "insurance", "delivery_receipt"]
        if international:
            types.extend(["export_declaration", "import_declaration", "bol"])
        return [self.create(shipment_id=shipment_id, doc_type=t) for t in types]

    def metrics(self) -> dict:
        return {"logistics_documents": self._store.logistics_documents.count(), "types": list(self.DOC_TYPES)}


logistics_document_engine = LogisticsDocumentEngine()
