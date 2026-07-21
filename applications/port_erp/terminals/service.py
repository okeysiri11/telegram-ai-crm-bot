# Terminal Registry service.

from __future__ import annotations

from applications.port_erp.port_management.service import PortRegistry, port_registry
from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.models import Terminal
from applications.port_erp.shared.store import PortStore, port_store


class TerminalRegistry:
    def __init__(
        self,
        store: PortStore | None = None,
        ports: PortRegistry | None = None,
    ) -> None:
        self._store = store or port_store
        self._ports = ports or port_registry

    def register(self, terminal: Terminal) -> Terminal:
        if not terminal.name or not terminal.port_id:
            raise ValidationError("name and port_id are required")
        self._ports.get(terminal.port_id)
        return self._store.terminals.save(terminal.terminal_id, terminal)

    def get(self, terminal_id: str) -> Terminal:
        terminal = self._store.terminals.get(terminal_id)
        if terminal is None:
            raise NotFoundError("Terminal", terminal_id)
        return terminal

    def list_terminals(self, *, port_id: str | None = None) -> list[Terminal]:
        items = self._store.terminals.list_all()
        if port_id:
            items = [t for t in items if t.port_id == port_id]
        return items


terminal_registry = TerminalRegistry()
