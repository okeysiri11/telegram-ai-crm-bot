# Port Resource Engine — equipment, warehouse, truck/rail balancing.

from __future__ import annotations

from events.publisher import publish

from applications.port_erp.digital_twin.events import OptimizationProposedEvent
from applications.port_erp.digital_twin.models import OptimizationPlan
from applications.port_erp.shared.store import PortStore, port_store
from applications.port_erp.terminal_operations.models import EquipmentStatus


class PortResourceEngine:
    def __init__(self, store: PortStore | None = None) -> None:
        self._store = store or port_store

    async def balance(self) -> OptimizationPlan:
        equipment = self._store.equipment.list_all()
        available = [
            e for e in equipment if getattr(e, "status", None) == EquipmentStatus.AVAILABLE
        ]
        maintenance = [
            e for e in equipment if getattr(e, "status", None) == EquipmentStatus.MAINTENANCE
        ]
        warehouses = self._store.warehouses.list_all()
        wh_actions = []
        for wh in warehouses:
            capacity = getattr(wh, "capacity_tons", 0) or 0
            used = getattr(wh, "used_tons", 0) or 0
            if capacity and used / capacity > 0.85:
                wh_actions.append(
                    {"action": "rebalance_warehouse", "warehouse_id": wh.warehouse_id, "load": used / capacity}
                )

        actions = [
            {"action": "equipment_pool", "available": len(available), "maintenance": len(maintenance)},
            {"action": "schedule_trucks", "pending_gate_visits": self._store.gate_visits.count()},
            {"action": "schedule_rail", "rail_positions": len(
                [p for p in self._store.live_positions.list_all() if getattr(p.asset_type, "value", "") == "rail"]
            )},
            *wh_actions,
        ]
        score = 0.8 if available else 0.4
        plan = OptimizationPlan(
            plan_type="resource_balancing",
            title="Port resource balancing",
            actions=actions,
            score=score,
        )
        saved = self._store.optimization_plans.save(plan.plan_id, plan)
        await publish(
            OptimizationProposedEvent(
                plan_id=saved.plan_id, plan_type=saved.plan_type, score=saved.score
            )
        )
        return saved


port_resource_engine = PortResourceEngine()
