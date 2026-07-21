# Port Registry service.

from __future__ import annotations

from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.models import Port
from applications.port_erp.shared.store import PortStore, port_store


class PortRegistry:
    def __init__(self, store: PortStore | None = None) -> None:
        self._store = store or port_store

    def register(self, port: Port) -> Port:
        if not port.name or not port.code:
            raise ValidationError("name and code are required")
        return self._store.ports.save(port.port_id, port)

    def get(self, port_id: str) -> Port:
        port = self._store.ports.get(port_id)
        if port is None:
            raise NotFoundError("Port", port_id)
        return port

    def list_ports(self, *, country: str | None = None) -> list[Port]:
        items = self._store.ports.list_all()
        if country:
            items = [p for p in items if p.country.lower() == country.lower()]
        return items


port_registry = PortRegistry()
