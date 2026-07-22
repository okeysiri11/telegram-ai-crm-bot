# Storage Optimizer — yard density + warehouse zone utilization.

from __future__ import annotations

from applications.port_erp.warehouse_management.engine import WarehouseEngine, warehouse_engine
from applications.port_erp.yard_management.engine import YardManagementEngine, yard_management_engine


class StorageOptimizer:
    def __init__(
        self,
        yard: YardManagementEngine | None = None,
        warehouse: WarehouseEngine | None = None,
    ) -> None:
        self._yard = yard or yard_management_engine
        self._warehouse = warehouse or warehouse_engine

    def optimize(self, *, terminal_id: str = "", warehouse_id: str = "") -> dict:
        yard = self._yard.optimize_density(terminal_id=terminal_id)
        zones = self._warehouse.list_zones(warehouse_id=warehouse_id or None)
        zone_util = []
        for zone in zones:
            util = (zone.used_units / zone.capacity_units) if zone.capacity_units else 0.0
            zone_util.append(
                {
                    "zone_id": zone.zone_id,
                    "name": zone.name,
                    "utilization": round(util, 4),
                    "suggest_rebalance": util > 0.9,
                }
            )
        return {
            "yard": yard,
            "warehouse_zones": zone_util,
        }


storage_optimizer = StorageOptimizer()
