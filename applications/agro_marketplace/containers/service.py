# Container planning and loading.

from __future__ import annotations

from events.publisher import publish

from applications.agro_marketplace.export.ai_integration import ExportAIIntegration, export_ai
from applications.agro_marketplace.export.events import ShipmentLoadedEvent
from applications.agro_marketplace.export.models import Container, ContainerLoad
from applications.agro_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.agro_marketplace.shared.store import AgroStore, agro_store


class ContainersService:
    def __init__(
        self,
        store: AgroStore | None = None,
        ai: ExportAIIntegration | None = None,
    ) -> None:
        self._store = store or agro_store
        self._ai = ai or export_ai

    def create_container(self, container: Container) -> Container:
        if not container.container_number:
            container.container_number = f"CONT-{container.container_id[:8].upper()}"
        return self._store.containers.save(container.container_id, container)

    def list_containers(self, *, status: str | None = None) -> list[Container]:
        items = self._store.containers.list_all()
        if status:
            items = [c for c in items if c.status == status]
        return items

    def get_container(self, container_id: str) -> Container:
        container = self._store.containers.get(container_id)
        if container is None:
            raise NotFoundError("Container", container_id)
        return container

    async def load_container(
        self,
        *,
        container_id: str,
        shipment_id: str,
        product_id: str = "",
        quantity_tons: float,
        volume_cbm: float = 0.0,
    ) -> ContainerLoad:
        container = self.get_container(container_id)
        volume = volume_cbm or quantity_tons * 1.4
        optimization = await self._ai.optimize_container(container, quantity_tons, volume)
        if not optimization["fits"]:
            raise ValidationError("load exceeds container capacity")
        load = ContainerLoad(
            container_id=container_id,
            shipment_id=shipment_id,
            product_id=product_id,
            quantity_tons=quantity_tons,
            volume_cbm=volume,
            sealed=True,
        )
        container.used_weight_tons += quantity_tons
        container.used_cbm += volume
        container.status = "loaded"
        self._store.containers.save(container_id, container)
        saved = self._store.container_loads.save(load.load_id, load)
        await publish(
            ShipmentLoadedEvent(
                shipment_id=shipment_id,
                container_id=container_id,
                quantity_tons=quantity_tons,
            )
        )
        return saved

    def list_loads(self, *, shipment_id: str | None = None) -> list[ContainerLoad]:
        items = self._store.container_loads.list_all()
        if shipment_id:
            items = [load for load in items if load.shipment_id == shipment_id]
        return items


containers_service = ContainersService()
