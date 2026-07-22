# Fleet Coordination Engine — assign fleet assets to transport orders.

from __future__ import annotations

from applications.port_erp.multimodal.models import FleetAssignment, TransportMode, TransportOrder
from applications.port_erp.shared.exceptions import ValidationError
from applications.port_erp.shared.store import PortStore, port_store
from applications.port_erp.transport_orders.engine import TransportOrderEngine, transport_order_engine


class FleetCoordinationEngine:
    """Coordinates logistics fleet assets (distinct from GPS FleetTrackingEngine)."""

    def __init__(
        self,
        store: PortStore | None = None,
        orders: TransportOrderEngine | None = None,
    ) -> None:
        self._store = store or port_store
        self._orders = orders or transport_order_engine

    def assign_asset(
        self,
        *,
        order_id: str,
        asset_id: str,
        mode: TransportMode | str = TransportMode.ROAD,
    ) -> FleetAssignment:
        if not asset_id:
            raise ValidationError("asset_id is required")
        order = self._orders.get(order_id)
        mode_enum = TransportMode(mode) if isinstance(mode, str) else mode
        assignment = FleetAssignment(
            order_id=order_id,
            asset_id=asset_id,
            mode=mode_enum,
        )
        order.fleet_asset_id = asset_id
        self._store.transport_orders.save(order.order_id, order)
        return self._store.fleet_assignments.save(assignment.assignment_id, assignment)

    def list_assignments(self, *, order_id: str | None = None) -> list[FleetAssignment]:
        items = self._store.fleet_assignments.list_all()
        if order_id:
            items = [a for a in items if a.order_id == order_id]
        return items

    def active_orders_for_asset(self, asset_id: str) -> list[TransportOrder]:
        order_ids = {
            a.order_id for a in self._store.fleet_assignments.list_all() if a.asset_id == asset_id
        }
        return [o for o in self._orders.list_orders() if o.order_id in order_ids]


fleet_coordination_engine = FleetCoordinationEngine()
