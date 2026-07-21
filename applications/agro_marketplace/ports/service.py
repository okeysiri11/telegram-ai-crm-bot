# Ports and terminals management.

from __future__ import annotations

from applications.agro_marketplace.export.models import Port, Terminal
from applications.agro_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.agro_marketplace.shared.store import AgroStore, agro_store

_SEED_PORTS = [
    {"name": "Mombasa", "code": "KEMBA", "country": "KE", "city": "Mombasa"},
    {"name": "Rotterdam", "code": "NLRTM", "country": "NL", "city": "Rotterdam"},
    {"name": "Singapore", "code": "SGSIN", "country": "SG", "city": "Singapore"},
    {"name": "Jebel Ali", "code": "AEJEA", "country": "AE", "city": "Dubai"},
]


class PortsService:
    def __init__(self, store: AgroStore | None = None) -> None:
        self._store = store or agro_store
        self._seeded = False

    def _ensure_seeded(self) -> None:
        if self._seeded and self._store.ports.count() > 0:
            return
        if self._store.ports.count() == 0:
            for item in _SEED_PORTS:
                port = Port(**item)
                self._store.ports.save(port.port_id, port)
        self._seeded = True

    def create_port(self, port: Port) -> Port:
        if not port.name or not port.country:
            raise ValidationError("name and country are required")
        self._ensure_seeded()
        return self._store.ports.save(port.port_id, port)

    def list_ports(self, *, country: str | None = None) -> list[Port]:
        self._ensure_seeded()
        items = self._store.ports.list_all()
        if country:
            items = [p for p in items if p.country.lower() == country.lower()]
        return items

    def get_port(self, port_id: str) -> Port:
        self._ensure_seeded()
        port = self._store.ports.get(port_id)
        if port is None:
            raise NotFoundError("Port", port_id)
        return port

    def create_terminal(self, terminal: Terminal) -> Terminal:
        self.get_port(terminal.port_id)
        return self._store.terminals.save(terminal.terminal_id, terminal)

    def list_terminals(self, *, port_id: str | None = None) -> list[Terminal]:
        items = self._store.terminals.list_all()
        if port_id:
            items = [t for t in items if t.port_id == port_id]
        return items


ports_service = PortsService()
