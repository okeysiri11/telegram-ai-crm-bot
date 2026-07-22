# International Trade Engine — shipments, incoterms, cargo flow orchestration.

from __future__ import annotations

import time

from applications.port_erp.cargo_flow.engine import CargoFlowEngine, cargo_flow_engine
from applications.port_erp.customs.engine import CustomsEngine, customs_engine
from applications.port_erp.customs.models import (
    CargoFlowStage,
    CustomsDeclaration,
    CustomsProcedure,
    Incoterm,
    TradeShipment,
)
from applications.port_erp.incoterms.service import IncotermsService, incoterms_service
from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.store import PortStore, port_store
from applications.port_erp.tariffs.engine import TariffEngine, tariff_engine


class InternationalTradeEngine:
    def __init__(
        self,
        store: PortStore | None = None,
        incoterms: IncotermsService | None = None,
        flow: CargoFlowEngine | None = None,
        customs: CustomsEngine | None = None,
        tariffs: TariffEngine | None = None,
    ) -> None:
        self._store = store or port_store
        self._incoterms = incoterms or incoterms_service
        self._flow = flow or cargo_flow_engine
        self._customs = customs or customs_engine
        self._tariffs = tariffs or tariff_engine

    def create_shipment(self, shipment: TradeShipment) -> TradeShipment:
        if not shipment.cargo_id and not shipment.seller:
            raise ValidationError("cargo_id or seller is required")
        shipment.incoterm = self._incoterms.parse(shipment.incoterm)
        return self._store.trade_shipments.save(shipment.shipment_id, shipment)

    def get_shipment(self, shipment_id: str) -> TradeShipment:
        shipment = self._store.trade_shipments.get(shipment_id)
        if shipment is None:
            raise NotFoundError("TradeShipment", shipment_id)
        return shipment

    def list_shipments(self, *, stage: CargoFlowStage | None = None) -> list[TradeShipment]:
        items = self._store.trade_shipments.list_all()
        if stage:
            items = [s for s in items if s.stage == stage]
        return items

    def set_incoterm(self, shipment_id: str, code: str | Incoterm) -> TradeShipment:
        shipment = self.get_shipment(shipment_id)
        shipment.incoterm = self._incoterms.parse(code)
        return self._store.trade_shipments.save(shipment_id, shipment)

    def advance_flow(self, shipment_id: str, to_stage: CargoFlowStage | str) -> TradeShipment:
        return self._flow.advance(shipment_id, to_stage)

    async def start_customs(
        self,
        shipment_id: str,
        *,
        procedure: CustomsProcedure | str = CustomsProcedure.IMPORT,
        hs_code: str = "",
        broker_id: str = "",
    ) -> CustomsDeclaration:
        shipment = self.get_shipment(shipment_id)
        proc = CustomsProcedure(procedure) if isinstance(procedure, str) else procedure
        decl = self._customs.create_declaration(
            CustomsDeclaration(
                procedure=proc,
                cargo_id=shipment.cargo_id,
                shipment_id=shipment_id,
                broker_id=broker_id or shipment.broker_id,
                hs_code=hs_code,
                country_of_origin=shipment.origin_country,
                country_of_destination=shipment.destination_country,
                declared_value=shipment.declared_value,
                currency=shipment.currency,
            )
        )
        self._flow.advance(shipment_id, CargoFlowStage.CUSTOMS_CLEARANCE)
        return await self._customs.submit(decl.declaration_id)

    def duty_estimate(self, shipment_id: str, *, hs_code: str) -> dict:
        shipment = self.get_shipment(shipment_id)
        return self._tariffs.calculate_duties(
            hs_code=hs_code,
            value=shipment.declared_value,
            country=shipment.destination_country,
        )

    def complete_shipment(self, shipment_id: str) -> TradeShipment:
        shipment = self._flow.advance(shipment_id, CargoFlowStage.COMPLETED)
        shipment.completed_at = time.time()
        return self._store.trade_shipments.save(shipment_id, shipment)

    def flow_stages(self) -> list[str]:
        return self._flow.stages()

    def incoterms(self) -> list[dict]:
        return self._incoterms.list_incoterms()


international_trade_engine = InternationalTradeEngine()
