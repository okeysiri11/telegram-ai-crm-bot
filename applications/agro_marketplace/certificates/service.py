# Export certificates — origin and phytosanitary.

from __future__ import annotations

from applications.agro_marketplace.export.models import DocumentType, TradeDocument
from applications.agro_marketplace.shared.store import AgroStore, agro_store


class ExportCertificatesService:
    def __init__(self, store: AgroStore | None = None) -> None:
        self._store = store or agro_store

    def issue_certificate_of_origin(
        self,
        *,
        shipment_id: str,
        country_of_origin: str,
        issuer: str = "Chamber of Commerce",
    ) -> TradeDocument:
        doc = TradeDocument(
            shipment_id=shipment_id,
            document_type=DocumentType.CERTIFICATE_OF_ORIGIN,
            title="Certificate of Origin",
            reference=f"COO-{shipment_id[:8].upper()}",
            issuer=issuer,
            payload={"country_of_origin": country_of_origin},
        )
        return self._store.trade_documents.save(doc.document_id, doc)

    def issue_phytosanitary(
        self,
        *,
        shipment_id: str,
        crop: str = "",
        issuer: str = "Plant Protection Authority",
    ) -> TradeDocument:
        doc = TradeDocument(
            shipment_id=shipment_id,
            document_type=DocumentType.PHYTOSANITARY,
            title="Phytosanitary Certificate",
            reference=f"PHYTO-{shipment_id[:8].upper()}",
            issuer=issuer,
            payload={"crop": crop},
        )
        return self._store.trade_documents.save(doc.document_id, doc)

    def list_for_shipment(self, shipment_id: str) -> list[TradeDocument]:
        types = {DocumentType.CERTIFICATE_OF_ORIGIN, DocumentType.PHYTOSANITARY}
        return [
            d
            for d in self._store.trade_documents.list_all()
            if d.shipment_id == shipment_id and d.document_type in types
        ]


export_certificates_service = ExportCertificatesService()
