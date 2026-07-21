# Port operations — gates, warehouses, operational actions.

from __future__ import annotations

from events.publisher import publish

from applications.port_erp.integrations.platform_bridge import PlatformBridge, platform_bridge
from applications.port_erp.shared.events import GateClosedEvent, GateOpenedEvent
from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.models import Gate, GateStatus, Warehouse
from applications.port_erp.shared.store import PortStore, port_store


class OperationsService:
    def __init__(
        self,
        store: PortStore | None = None,
        platform: PlatformBridge | None = None,
    ) -> None:
        self._store = store or port_store
        self._platform = platform or platform_bridge

    def register_warehouse(self, warehouse: Warehouse) -> Warehouse:
        if not warehouse.name:
            raise ValidationError("name is required")
        return self._store.warehouses.save(warehouse.warehouse_id, warehouse)

    def list_warehouses(self, *, port_id: str | None = None) -> list[Warehouse]:
        items = self._store.warehouses.list_all()
        if port_id:
            items = [w for w in items if w.port_id == port_id]
        return items

    def register_gate(self, gate: Gate) -> Gate:
        if not gate.name:
            raise ValidationError("name is required")
        return self._store.gates.save(gate.gate_id, gate)

    def get_gate(self, gate_id: str) -> Gate:
        gate = self._store.gates.get(gate_id)
        if gate is None:
            raise NotFoundError("Gate", gate_id)
        return gate

    def list_gates(self, *, port_id: str | None = None) -> list[Gate]:
        items = self._store.gates.list_all()
        if port_id:
            items = [g for g in items if g.port_id == port_id]
        return items

    async def open_gate(self, gate_id: str) -> Gate:
        gate = self.get_gate(gate_id)
        gate.status = GateStatus.OPEN
        saved = self._store.gates.save(gate_id, gate)
        await publish(
            GateOpenedEvent(gate_id=gate_id, port_id=saved.port_id, terminal_id=saved.terminal_id)
        )
        await self._platform.start_port_workflow("gate_open", {"gate_id": gate_id})
        return saved

    async def close_gate(self, gate_id: str) -> Gate:
        gate = self.get_gate(gate_id)
        gate.status = GateStatus.CLOSED
        saved = self._store.gates.save(gate_id, gate)
        await publish(
            GateClosedEvent(gate_id=gate_id, port_id=saved.port_id, terminal_id=saved.terminal_id)
        )
        return saved

    def metrics(self) -> dict:
        return {
            "warehouses": self._store.warehouses.count(),
            "gates": self._store.gates.count(),
            "open_gates": sum(1 for g in self._store.gates.list_all() if g.status == GateStatus.OPEN),
        }


operations_service = OperationsService()
