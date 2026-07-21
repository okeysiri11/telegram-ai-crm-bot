# ExportService — export shipments and certificates.

from __future__ import annotations

from events.publisher import publish

from applications.agro_marketplace.shared.events import ExportStartedEvent, ShipmentCreatedEvent
from applications.agro_marketplace.shared.exceptions import NotFoundError
from applications.agro_marketplace.shared.models import ExportShipment, ExportStatus, QualityCertificate
from applications.agro_marketplace.shared.store import AgroStore, agro_store


class ExportService:
    def __init__(self, store: AgroStore | None = None) -> None:
        self._store = store or agro_store

    def list_shipments(self) -> list[ExportShipment]:
        return self._store.export_shipments.list_all()

    def get_shipment(self, shipment_id: str) -> ExportShipment:
        shipment = self._store.export_shipments.get(shipment_id)
        if shipment is None:
            raise NotFoundError("ExportShipment", shipment_id)
        return shipment

    async def create_shipment(self, shipment: ExportShipment) -> ExportShipment:
        if self._store.orders.get(shipment.order_id) is None:
            raise NotFoundError("Order", shipment.order_id)
        saved = self._store.export_shipments.save(shipment.shipment_id, shipment)
        await publish(
            ShipmentCreatedEvent(
                shipment_id=saved.shipment_id,
                order_id=saved.order_id,
                destination_country=saved.destination_country,
            )
        )
        return saved

    async def start_export(self, shipment_id: str) -> ExportShipment:
        shipment = self.get_shipment(shipment_id)
        shipment.status = ExportStatus.STARTED
        saved = self._store.export_shipments.save(shipment_id, shipment)
        await publish(
            ExportStartedEvent(
                shipment_id=saved.shipment_id,
                order_id=saved.order_id,
                exporter_id=saved.exporter_id,
            )
        )
        return saved

    def issue_certificate(self, certificate: QualityCertificate) -> QualityCertificate:
        return self._store.certificates.save(certificate.certificate_id, certificate)

    def list_certificates(self) -> list[QualityCertificate]:
        return self._store.certificates.list_all()


export_service = ExportService()
