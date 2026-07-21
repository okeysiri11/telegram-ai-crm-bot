# Cargo Registry service.

from __future__ import annotations

from events.publisher import publish

from applications.port_erp.shared.events import CargoLoadedEvent, CargoUnloadedEvent
from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.models import Cargo
from applications.port_erp.shared.store import PortStore, port_store


class CargoRegistry:
    def __init__(self, store: PortStore | None = None) -> None:
        self._store = store or port_store

    def register(self, cargo: Cargo) -> Cargo:
        if not cargo.description:
            raise ValidationError("description is required")
        return self._store.cargo.save(cargo.cargo_id, cargo)

    def get(self, cargo_id: str) -> Cargo:
        cargo = self._store.cargo.get(cargo_id)
        if cargo is None:
            raise NotFoundError("Cargo", cargo_id)
        return cargo

    def list_cargo(self, *, customer_id: str | None = None) -> list[Cargo]:
        items = self._store.cargo.list_all()
        if customer_id:
            items = [c for c in items if c.customer_id == customer_id]
        return items

    async def load(self, cargo_id: str) -> Cargo:
        cargo = self.get(cargo_id)
        cargo.status = "loaded"
        saved = self._store.cargo.save(cargo_id, cargo)
        await publish(
            CargoLoadedEvent(
                cargo_id=cargo_id,
                container_id=saved.container_id,
                voyage_id=saved.voyage_id,
            )
        )
        return saved

    async def unload(self, cargo_id: str) -> Cargo:
        cargo = self.get(cargo_id)
        cargo.status = "unloaded"
        saved = self._store.cargo.save(cargo_id, cargo)
        await publish(
            CargoUnloadedEvent(
                cargo_id=cargo_id,
                container_id=saved.container_id,
                voyage_id=saved.voyage_id,
            )
        )
        return saved


cargo_registry = CargoRegistry()
