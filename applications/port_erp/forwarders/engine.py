# Freight Forwarder Engine — bookings support + consolidation.

from __future__ import annotations

from applications.port_erp.companies.service import CompanyRegistry, company_registry
from applications.port_erp.multimodal.models import ConsolidationBatch
from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.models import Forwarder
from applications.port_erp.shared.store import PortStore, port_store


class FreightForwarderEngine:
    def __init__(
        self,
        store: PortStore | None = None,
        companies: CompanyRegistry | None = None,
    ) -> None:
        self._store = store or port_store
        self._companies = companies or company_registry

    def register(self, forwarder: Forwarder) -> Forwarder:
        return self._companies.register_forwarder(forwarder)

    def list_forwarders(self) -> list[Forwarder]:
        return self._store.forwarders.list_all()

    def get(self, forwarder_id: str) -> Forwarder:
        item = self._store.forwarders.get(forwarder_id)
        if item is None:
            raise NotFoundError("Forwarder", forwarder_id)
        return item

    def consolidate(
        self,
        *,
        forwarder_id: str,
        route_id: str = "",
        booking_ids: list[str] | None = None,
        container_ids: list[str] | None = None,
    ) -> ConsolidationBatch:
        self.get(forwarder_id)
        bookings = booking_ids or []
        containers = container_ids or []
        if not bookings and not containers:
            raise ValidationError("booking_ids or container_ids required")
        batch = ConsolidationBatch(
            forwarder_id=forwarder_id,
            route_id=route_id,
            booking_ids=list(bookings),
            container_ids=list(containers),
        )
        return self._store.consolidation_batches.save(batch.batch_id, batch)

    def list_consolidations(self, *, forwarder_id: str | None = None) -> list[ConsolidationBatch]:
        items = self._store.consolidation_batches.list_all()
        if forwarder_id:
            items = [b for b in items if b.forwarder_id == forwarder_id]
        return items


freight_forwarder_engine = FreightForwarderEngine()
