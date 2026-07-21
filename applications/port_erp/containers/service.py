# Container Registry service.

from __future__ import annotations

from events.publisher import publish

from applications.port_erp.shared.events import ContainerReceivedEvent, ContainerReleasedEvent
from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.models import Container, ContainerStatus
from applications.port_erp.shared.store import PortStore, port_store


class ContainerRegistry:
    def __init__(self, store: PortStore | None = None) -> None:
        self._store = store or port_store

    def register(self, container: Container) -> Container:
        if not container.container_number:
            raise ValidationError("container_number is required")
        return self._store.containers.save(container.container_id, container)

    def get(self, container_id: str) -> Container:
        container = self._store.containers.get(container_id)
        if container is None:
            raise NotFoundError("Container", container_id)
        return container

    def list_containers(self, *, status: ContainerStatus | None = None) -> list[Container]:
        items = self._store.containers.list_all()
        if status:
            items = [c for c in items if c.status == status]
        return items

    async def receive(self, container_id: str, *, terminal_id: str = "") -> Container:
        container = self.get(container_id)
        container.status = ContainerStatus.AT_PORT
        if terminal_id:
            container.terminal_id = terminal_id
        saved = self._store.containers.save(container_id, container)
        await publish(
            ContainerReceivedEvent(
                container_id=container_id,
                terminal_id=saved.terminal_id,
                container_number=saved.container_number,
            )
        )
        return saved

    async def release(self, container_id: str) -> Container:
        container = self.get(container_id)
        container.status = ContainerStatus.OUT_FOR_DELIVERY
        saved = self._store.containers.save(container_id, container)
        await publish(
            ContainerReleasedEvent(
                container_id=container_id,
                terminal_id=saved.terminal_id,
                container_number=saved.container_number,
            )
        )
        return saved

    def transition(
        self,
        container_id: str,
        to_status: ContainerStatus | str,
        *,
        location: str = "",
        notes: str = "",
    ) -> Container:
        container = self.get(container_id)
        previous = container.status.value
        container.status = ContainerStatus(to_status) if isinstance(to_status, str) else to_status
        return self._store.containers.save(container_id, container)


container_registry = ContainerRegistry()
