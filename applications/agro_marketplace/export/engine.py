# ExportEngine — international export workflow facade.

from __future__ import annotations

import time
from typing import Any

from events.publisher import publish

from applications.agro_marketplace.certificates.service import (
    ExportCertificatesService,
    export_certificates_service,
)
from applications.agro_marketplace.containers.service import ContainersService, containers_service
from applications.agro_marketplace.customs.service import CustomsService, customs_service
from applications.agro_marketplace.documents.trade_service import TradeDocumentsService, trade_documents_service
from applications.agro_marketplace.export.ai_integration import ExportAIIntegration, export_ai
from applications.agro_marketplace.export.events import (
    DeliveryConfirmedEvent,
    ExportCompletedEvent,
    IntlShipmentCreatedEvent,
    PortArrivedEvent,
    RiskDetectedEvent,
    ShipmentDispatchedEvent,
)
from applications.agro_marketplace.export.models import (
    CustomsDeclaration,
    IncotermCode,
    InternationalExportShipment,
    InternationalShipmentStatus,
    ShipmentItem,
    TrackingEvent,
)
from applications.agro_marketplace.incoterms.service import IncotermsService, incoterms_service
from applications.agro_marketplace.insurance.service import InsuranceService, insurance_service
from applications.agro_marketplace.integrations.platform_bridge import PlatformBridge, platform_bridge
from applications.agro_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.agro_marketplace.shared.models import ExportShipment as LegacyExportShipment
from applications.agro_marketplace.shared.models import ExportStatus
from applications.agro_marketplace.shared.store import AgroStore, agro_store
from applications.agro_marketplace.shipping.service import ShippingService, shipping_service
from applications.agro_marketplace.tracking.service import TrackingService, tracking_service


class ExportEngine:
    def __init__(
        self,
        store: AgroStore | None = None,
        documents: TradeDocumentsService | None = None,
        certificates: ExportCertificatesService | None = None,
        customs: CustomsService | None = None,
        containers: ContainersService | None = None,
        shipping: ShippingService | None = None,
        tracking: TrackingService | None = None,
        insurance: InsuranceService | None = None,
        incoterms: IncotermsService | None = None,
        ai: ExportAIIntegration | None = None,
        platform: PlatformBridge | None = None,
    ) -> None:
        self._store = store or agro_store
        self.documents = documents or trade_documents_service
        self.certificates = certificates or export_certificates_service
        self.customs = customs or customs_service
        self.containers = containers or containers_service
        self.shipping = shipping or shipping_service
        self.tracking = tracking or tracking_service
        self.insurance = insurance or insurance_service
        self.incoterms = incoterms or incoterms_service
        self._ai = ai or export_ai
        self._platform = platform or platform_bridge

    def _sync_legacy(self, shipment: InternationalExportShipment) -> None:
        status_map = {
            InternationalShipmentStatus.DRAFT: ExportStatus.DRAFT,
            InternationalShipmentStatus.PLANNED: ExportStatus.DRAFT,
            InternationalShipmentStatus.LOADED: ExportStatus.STARTED,
            InternationalShipmentStatus.DISPATCHED: ExportStatus.IN_TRANSIT,
            InternationalShipmentStatus.IN_TRANSIT: ExportStatus.IN_TRANSIT,
            InternationalShipmentStatus.PORT_ARRIVED: ExportStatus.IN_TRANSIT,
            InternationalShipmentStatus.CUSTOMS: ExportStatus.CLEARED,
            InternationalShipmentStatus.CLEARED: ExportStatus.CLEARED,
            InternationalShipmentStatus.DELIVERED: ExportStatus.COMPLETED,
            InternationalShipmentStatus.COMPLETED: ExportStatus.COMPLETED,
            InternationalShipmentStatus.CANCELLED: ExportStatus.CANCELLED,
            InternationalShipmentStatus.AT_RISK: ExportStatus.STARTED,
        }
        legacy = LegacyExportShipment(
            shipment_id=shipment.shipment_id,
            order_id=shipment.order_id,
            exporter_id=shipment.exporter_id,
            destination_country=shipment.destination_country,
            status=status_map.get(shipment.status, ExportStatus.DRAFT),
            documents=list(shipment.document_ids),
        )
        self._store.export_shipments.save(legacy.shipment_id, legacy)

    async def create_shipment(self, shipment: InternationalExportShipment) -> InternationalExportShipment:
        if not self.incoterms.supports(shipment.incoterm.value):
            raise ValidationError(f"unsupported incoterm: {shipment.incoterm}")
        if not shipment.destination_country:
            raise ValidationError("destination_country is required")
        shipment.status = InternationalShipmentStatus.PLANNED
        shipment.updated_at = time.time()
        saved = self._store.intl_shipments.save(shipment.shipment_id, shipment)
        self._sync_legacy(saved)
        self.tracking.record(
            TrackingEvent(
                shipment_id=saved.shipment_id,
                event_type="created",
                status=saved.status.value,
                location=saved.origin_country,
            )
        )
        await self._platform.start_order_workflow(
            saved.shipment_id,
            {"workflow": "export", "destination": saved.destination_country},
        )
        await publish(
            IntlShipmentCreatedEvent(
                shipment_id=saved.shipment_id,
                order_id=saved.order_id,
                destination_country=saved.destination_country,
                incoterm=saved.incoterm.value,
            )
        )
        return saved

    def get_shipment(self, shipment_id: str) -> InternationalExportShipment:
        shipment = self._store.intl_shipments.get(shipment_id)
        if shipment is None:
            raise NotFoundError("ExportShipment", shipment_id)
        return shipment

    def list_shipments(self, *, status: InternationalShipmentStatus | None = None) -> list[InternationalExportShipment]:
        items = self._store.intl_shipments.list_all()
        if status:
            items = [s for s in items if s.status == status]
        return items

    def add_item(self, item: ShipmentItem) -> ShipmentItem:
        shipment = self.get_shipment(item.shipment_id)
        saved = self._store.shipment_items.save(item.item_id, item)
        if saved.item_id not in shipment.items:
            shipment.items.append(saved.item_id)
            shipment.updated_at = time.time()
            self._store.intl_shipments.save(shipment.shipment_id, shipment)
        return saved

    async def prepare_documents(self, shipment_id: str, *, cargo_value: float = 0.0) -> list[dict[str, Any]]:
        shipment = self.get_shipment(shipment_id)
        docs = self.documents.prepare_standard_pack(shipment, cargo_value=cargo_value)
        origin = self.certificates.issue_certificate_of_origin(
            shipment_id=shipment_id,
            country_of_origin=shipment.origin_country or "KE",
        )
        phyto = self.certificates.issue_phytosanitary(shipment_id=shipment_id)
        all_docs = [*docs, origin, phyto]
        shipment.document_ids = [d.document_id for d in all_docs]
        shipment.updated_at = time.time()
        self._store.intl_shipments.save(shipment_id, shipment)
        self._sync_legacy(shipment)
        return [d.to_dict() for d in all_docs]

    async def verify_documents(self, shipment_id: str) -> dict[str, Any]:
        shipment = self.get_shipment(shipment_id)
        for doc in self.documents.list_documents(shipment_id=shipment_id):
            self.documents.verify(doc.document_id)
        return await self.documents.validate_for_shipment(shipment)

    async def assess_risk(self, shipment_id: str) -> dict[str, Any]:
        shipment = self.get_shipment(shipment_id)
        assessment = await self._ai.assess_export_risk(shipment)
        shipment.risk_score = float(assessment["risk_score"])
        if assessment.get("high_risk"):
            shipment.status = InternationalShipmentStatus.AT_RISK
            await publish(
                RiskDetectedEvent(
                    shipment_id=shipment_id,
                    risk_score=shipment.risk_score,
                    reasons=list(assessment.get("reasons", [])),
                )
            )
        shipment.updated_at = time.time()
        self._store.intl_shipments.save(shipment_id, shipment)
        return assessment

    async def dispatch(self, shipment_id: str) -> InternationalExportShipment:
        shipment = self.get_shipment(shipment_id)
        if not shipment.carrier_id or not shipment.origin_port_id:
            raise ValidationError("carrier_id and origin_port_id required for dispatch")
        shipment.status = InternationalShipmentStatus.DISPATCHED
        shipment.actual_departure = time.time()
        shipment.updated_at = time.time()
        saved = self._store.intl_shipments.save(shipment_id, shipment)
        self._sync_legacy(saved)
        self.tracking.record(
            TrackingEvent(
                shipment_id=shipment_id,
                event_type="dispatched",
                status=saved.status.value,
                location=saved.origin_port_id,
            )
        )
        await publish(
            ShipmentDispatchedEvent(
                shipment_id=shipment_id,
                carrier_id=saved.carrier_id,
                origin_port_id=saved.origin_port_id,
            )
        )
        return saved

    async def arrive_port(self, shipment_id: str, *, port_id: str = "") -> InternationalExportShipment:
        shipment = self.get_shipment(shipment_id)
        shipment.status = InternationalShipmentStatus.PORT_ARRIVED
        shipment.actual_arrival = time.time()
        port = port_id or shipment.destination_port_id
        shipment.updated_at = time.time()
        saved = self._store.intl_shipments.save(shipment_id, shipment)
        self._sync_legacy(saved)
        self.tracking.record(
            TrackingEvent(
                shipment_id=shipment_id,
                event_type="port_arrived",
                status=saved.status.value,
                location=port,
            )
        )
        await publish(PortArrivedEvent(shipment_id=shipment_id, port_id=port))
        return saved

    async def clear_customs(self, shipment_id: str, *, country: str = "") -> dict[str, Any]:
        shipment = self.get_shipment(shipment_id)
        declaration = self.customs.create_declaration(
            CustomsDeclaration(
                shipment_id=shipment_id,
                country=country or shipment.destination_country,
                declared_value=sum(
                    (self._store.shipment_items.get(i).quantity * self._store.shipment_items.get(i).unit_value)
                    for i in shipment.items
                    if self._store.shipment_items.get(i)
                ),
            )
        )
        await self.customs.submit(declaration.declaration_id)
        cleared = await self.customs.clear(declaration.declaration_id)
        shipment.status = InternationalShipmentStatus.CLEARED
        shipment.updated_at = time.time()
        self._store.intl_shipments.save(shipment_id, shipment)
        self._sync_legacy(shipment)
        self.tracking.record(
            TrackingEvent(
                shipment_id=shipment_id,
                event_type="customs_cleared",
                status=shipment.status.value,
                location=cleared.country,
            )
        )
        return {"shipment": shipment.to_dict(), "declaration": cleared.to_dict()}

    async def confirm_delivery(self, shipment_id: str, *, location: str = "") -> InternationalExportShipment:
        shipment = self.get_shipment(shipment_id)
        shipment.status = InternationalShipmentStatus.DELIVERED
        shipment.updated_at = time.time()
        saved = self._store.intl_shipments.save(shipment_id, shipment)
        self._sync_legacy(saved)
        loc = location or shipment.destination_country
        self.tracking.record(
            TrackingEvent(
                shipment_id=shipment_id,
                event_type="delivery_confirmed",
                status=saved.status.value,
                location=loc,
            )
        )
        await publish(DeliveryConfirmedEvent(shipment_id=shipment_id, location=loc))
        return saved

    async def complete_export(self, shipment_id: str) -> InternationalExportShipment:
        shipment = self.get_shipment(shipment_id)
        shipment.status = InternationalShipmentStatus.COMPLETED
        shipment.updated_at = time.time()
        saved = self._store.intl_shipments.save(shipment_id, shipment)
        self._sync_legacy(saved)
        self.tracking.record(
            TrackingEvent(
                shipment_id=shipment_id,
                event_type="export_completed",
                status=saved.status.value,
                location=saved.destination_country,
            )
        )
        await publish(
            ExportCompletedEvent(
                shipment_id=shipment_id,
                order_id=saved.order_id,
                destination_country=saved.destination_country,
            )
        )
        return saved

    def metrics(self) -> dict[str, Any]:
        return {
            "shipments": self._store.intl_shipments.count(),
            "containers": self._store.containers.count(),
            "customs": self._store.customs_declarations.count(),
            "documents": self._store.trade_documents.count(),
            "tracking_events": self._store.tracking_events.count(),
            "insurance_policies": self._store.insurance_policies.count(),
        }


export_engine = ExportEngine()
