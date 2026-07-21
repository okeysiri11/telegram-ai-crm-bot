# Berth Manager service.

from __future__ import annotations

from events.publisher import publish

from applications.port_erp.shared.events import BerthAssignedEvent
from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.models import Berth
from applications.port_erp.shared.store import PortStore, port_store
from applications.port_erp.terminals.service import TerminalRegistry, terminal_registry


class BerthManager:
    def __init__(
        self,
        store: PortStore | None = None,
        terminals: TerminalRegistry | None = None,
    ) -> None:
        self._store = store or port_store
        self._terminals = terminals or terminal_registry

    def register(self, berth: Berth) -> Berth:
        if not berth.name or not berth.terminal_id:
            raise ValidationError("name and terminal_id are required")
        terminal = self._terminals.get(berth.terminal_id)
        if not berth.port_id:
            berth.port_id = terminal.port_id
        return self._store.berths.save(berth.berth_id, berth)

    def get(self, berth_id: str) -> Berth:
        berth = self._store.berths.get(berth_id)
        if berth is None:
            raise NotFoundError("Berth", berth_id)
        return berth

    def list_berths(self, *, terminal_id: str | None = None) -> list[Berth]:
        items = self._store.berths.list_all()
        if terminal_id:
            items = [b for b in items if b.terminal_id == terminal_id]
        return items

    async def assign(self, berth_id: str, *, vessel_id: str, voyage_id: str = "") -> Berth:
        berth = self.get(berth_id)
        if berth.status == "occupied" and berth.assigned_vessel_id not in {"", vessel_id}:
            raise ValidationError("berth already occupied")
        berth.status = "occupied"
        berth.assigned_vessel_id = vessel_id
        saved = self._store.berths.save(berth_id, berth)
        await publish(
            BerthAssignedEvent(berth_id=berth_id, vessel_id=vessel_id, voyage_id=voyage_id)
        )
        return saved

    def release(self, berth_id: str) -> Berth:
        berth = self.get(berth_id)
        berth.status = "available"
        berth.assigned_vessel_id = ""
        return self._store.berths.save(berth_id, berth)


berth_manager = BerthManager()
