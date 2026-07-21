# Trade document generation and verification.

from __future__ import annotations

from applications.agro_marketplace.export.ai_integration import ExportAIIntegration, export_ai
from applications.agro_marketplace.export.models import (
    CountryRequirement,
    DocumentType,
    InternationalExportShipment,
    TradeDocument,
)
from applications.agro_marketplace.shared.exceptions import NotFoundError
from applications.agro_marketplace.shared.store import AgroStore, agro_store

_DEFAULT_REQUIREMENTS = [
    CountryRequirement(
        country="NL",
        required_documents=[
            DocumentType.COMMERCIAL_INVOICE.value,
            DocumentType.PACKING_LIST.value,
            DocumentType.BILL_OF_LADING.value,
            DocumentType.PHYTOSANITARY.value,
            DocumentType.CERTIFICATE_OF_ORIGIN.value,
        ],
        notes="EU agri imports require phytosanitary certificate",
    ),
    CountryRequirement(
        country="AE",
        required_documents=[
            DocumentType.COMMERCIAL_INVOICE.value,
            DocumentType.PACKING_LIST.value,
            DocumentType.BILL_OF_LADING.value,
            DocumentType.CERTIFICATE_OF_ORIGIN.value,
        ],
    ),
    CountryRequirement(
        country="KE",
        required_documents=[
            DocumentType.COMMERCIAL_INVOICE.value,
            DocumentType.PACKING_LIST.value,
            DocumentType.CERTIFICATE_OF_ORIGIN.value,
        ],
    ),
]


class TradeDocumentsService:
    def __init__(
        self,
        store: AgroStore | None = None,
        ai: ExportAIIntegration | None = None,
    ) -> None:
        self._store = store or agro_store
        self._ai = ai or export_ai
        self._seeded = False

    def _ensure_seeded(self) -> None:
        if self._seeded and self._store.country_requirements.count() > 0:
            return
        if self._store.country_requirements.count() == 0:
            for req in _DEFAULT_REQUIREMENTS:
                self._store.country_requirements.save(req.requirement_id, req)
        self._seeded = True

    def create_document(self, document: TradeDocument) -> TradeDocument:
        return self._store.trade_documents.save(document.document_id, document)

    def list_documents(self, *, shipment_id: str | None = None) -> list[TradeDocument]:
        items = self._store.trade_documents.list_all()
        if shipment_id:
            items = [d for d in items if d.shipment_id == shipment_id]
        return items

    def get(self, document_id: str) -> TradeDocument:
        document = self._store.trade_documents.get(document_id)
        if document is None:
            raise NotFoundError("TradeDocument", document_id)
        return document

    def verify(self, document_id: str) -> TradeDocument:
        document = self.get(document_id)
        document.verified = True
        return self._store.trade_documents.save(document_id, document)

    def country_requirements(self, country: str) -> CountryRequirement | None:
        self._ensure_seeded()
        for req in self._store.country_requirements.list_all():
            if req.country.lower() == country.lower():
                return req
        return None

    def prepare_standard_pack(
        self,
        shipment: InternationalExportShipment,
        *,
        cargo_value: float = 0.0,
        currency: str = "USD",
    ) -> list[TradeDocument]:
        docs = [
            TradeDocument(
                shipment_id=shipment.shipment_id,
                document_type=DocumentType.COMMERCIAL_INVOICE,
                title="Commercial Invoice",
                reference=f"INV-{shipment.shipment_id[:8].upper()}",
                payload={"value": cargo_value, "currency": currency, "incoterm": shipment.incoterm.value},
            ),
            TradeDocument(
                shipment_id=shipment.shipment_id,
                document_type=DocumentType.PACKING_LIST,
                title="Packing List",
                reference=f"PKG-{shipment.shipment_id[:8].upper()}",
                payload={"containers": list(shipment.container_ids)},
            ),
            TradeDocument(
                shipment_id=shipment.shipment_id,
                document_type=DocumentType.BILL_OF_LADING,
                title="Bill of Lading",
                reference=f"BL-{shipment.shipment_id[:8].upper()}",
                payload={"carrier_id": shipment.carrier_id, "ports": [shipment.origin_port_id, shipment.destination_port_id]},
            ),
        ]
        saved = []
        for doc in docs:
            saved.append(self.create_document(doc))
        return saved

    async def validate_for_shipment(self, shipment: InternationalExportShipment) -> dict:
        self._ensure_seeded()
        req = self.country_requirements(shipment.destination_country)
        required = req.required_documents if req else [
            DocumentType.COMMERCIAL_INVOICE.value,
            DocumentType.PACKING_LIST.value,
            DocumentType.BILL_OF_LADING.value,
        ]
        documents = [d.to_dict() for d in self.list_documents(shipment_id=shipment.shipment_id)]
        return await self._ai.validate_customs_documents(shipment, documents, required)


trade_documents_service = TradeDocumentsService()
