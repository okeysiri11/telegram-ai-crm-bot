# Cargo Flow Engine — booking → completed international cargo stages.

from __future__ import annotations

import time

from applications.port_erp.customs.models import CargoFlowStage, TradeShipment
from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.store import PortStore, port_store


_FLOW_ORDER = [
    CargoFlowStage.BOOKING,
    CargoFlowStage.DOCUMENTATION,
    CargoFlowStage.CUSTOMS_CLEARANCE,
    CargoFlowStage.LOADING,
    CargoFlowStage.DEPARTURE,
    CargoFlowStage.TRANSIT,
    CargoFlowStage.ARRIVAL,
    CargoFlowStage.DISCHARGE,
    CargoFlowStage.WAREHOUSE,
    CargoFlowStage.DELIVERY,
    CargoFlowStage.COMPLETED,
]


class CargoFlowEngine:
    def __init__(self, store: PortStore | None = None) -> None:
        self._store = store or port_store

    def stages(self) -> list[str]:
        return [s.value for s in _FLOW_ORDER]

    def get_shipment(self, shipment_id: str) -> TradeShipment:
        shipment = self._store.trade_shipments.get(shipment_id)
        if shipment is None:
            raise NotFoundError("TradeShipment", shipment_id)
        return shipment

    def advance(self, shipment_id: str, to_stage: CargoFlowStage | str) -> TradeShipment:
        shipment = self.get_shipment(shipment_id)
        target = CargoFlowStage(to_stage) if isinstance(to_stage, str) else to_stage
        if target not in _FLOW_ORDER:
            raise ValidationError(f"unsupported stage: {target}")
        current_idx = _FLOW_ORDER.index(shipment.stage)
        target_idx = _FLOW_ORDER.index(target)
        if target_idx < current_idx:
            raise ValidationError("cannot move cargo flow backwards")
        shipment.stage = target
        if target == CargoFlowStage.COMPLETED:
            shipment.completed_at = time.time()
        return self._store.trade_shipments.save(shipment_id, shipment)


cargo_flow_engine = CargoFlowEngine()
