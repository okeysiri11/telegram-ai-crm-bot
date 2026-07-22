# Terminal Operations Engine — facade for yard, warehouse, gate, equipment, planning.

from __future__ import annotations

from typing import Any

from applications.port_erp.cranes.engine import CraneSchedulingEngine, crane_scheduling_engine
from applications.port_erp.dispatch.engine import DispatchEngine, dispatch_engine
from applications.port_erp.equipment.engine import EquipmentManager, equipment_manager
from applications.port_erp.gate_management.engine import GateControlEngine, gate_control_engine
from applications.port_erp.integrations.platform_bridge import PlatformBridge, platform_bridge
from applications.port_erp.inventory.service import InventoryService, inventory_service
from applications.port_erp.planning.engine import PlanningEngine, planning_engine
from applications.port_erp.storage.engine import StorageOptimizer, storage_optimizer
from applications.port_erp.warehouse_management.engine import WarehouseEngine, warehouse_engine
from applications.port_erp.yard_management.engine import YardManagementEngine, yard_management_engine


class TerminalOperationsEngine:
    def __init__(
        self,
        yard: YardManagementEngine | None = None,
        warehouse: WarehouseEngine | None = None,
        gate: GateControlEngine | None = None,
        equipment: EquipmentManager | None = None,
        cranes: CraneSchedulingEngine | None = None,
        dispatch: DispatchEngine | None = None,
        planning: PlanningEngine | None = None,
        storage: StorageOptimizer | None = None,
        inventory: InventoryService | None = None,
        platform: PlatformBridge | None = None,
    ) -> None:
        self.yard = yard or yard_management_engine
        self.warehouse = warehouse or warehouse_engine
        self.gate = gate or gate_control_engine
        self.equipment = equipment or equipment_manager
        self.cranes = cranes or crane_scheduling_engine
        self.dispatch = dispatch or dispatch_engine
        self.planning = planning or planning_engine
        self.storage = storage or storage_optimizer
        self.inventory = inventory or inventory_service
        self._platform = platform or platform_bridge

    def metrics(self) -> dict[str, Any]:
        return {
            "yard_blocks": len(self.yard.list_blocks()),
            "yard_slots": len(self.yard.list_slots()),
            "warehouses": len(self.warehouse.list_warehouses()),
            "zones": len(self.warehouse.list_zones()),
            "inventory_items": len(self.warehouse.list_inventory()),
            "gates": len(self.gate.list_gates()),
            "gate_visits": len(self.gate.list_visits()),
            "equipment": len(self.equipment.list_equipment()),
            "crane_assignments": len(self.cranes.list_assignments()),
            "dispatch_jobs": len(self.dispatch.list_jobs()),
            "plans": len(self.planning.list_plans()),
        }

    async def remember_snapshot(self) -> None:
        await self._platform.remember_context("terminal:snapshot", self.metrics())


terminal_operations_engine = TerminalOperationsEngine()
