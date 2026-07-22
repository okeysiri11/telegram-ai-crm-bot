# Customs Engine — export/import/transit declarations, channels, hold/release.

from __future__ import annotations

import time

from events.publisher import publish

from applications.port_erp.customs.events import (
    CargoHeldEvent,
    CargoReleasedEvent,
    CustomsDeclarationCreatedEvent,
    CustomsReleasedEvent,
    ExportCompletedEvent,
    ImportCompletedEvent,
)
from applications.port_erp.customs.models import (
    CustomsChannel,
    CustomsDeclaration,
    CustomsProcedure,
    CustomsStatus,
    InspectionRecord,
    InspectionType,
)
from applications.port_erp.inspection.engine import InspectionEngine, inspection_engine
from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.store import PortStore, port_store
from applications.port_erp.tariffs.engine import TariffEngine, tariff_engine


class CustomsEngine:
    def __init__(
        self,
        store: PortStore | None = None,
        inspection: InspectionEngine | None = None,
        tariffs: TariffEngine | None = None,
    ) -> None:
        self._store = store or port_store
        self._inspection = inspection or inspection_engine
        self._tariffs = tariffs or tariff_engine

    def create_declaration(self, declaration: CustomsDeclaration) -> CustomsDeclaration:
        if not declaration.cargo_id and not declaration.shipment_id:
            raise ValidationError("cargo_id or shipment_id is required")
        saved = self._store.customs_declarations.save(declaration.declaration_id, declaration)
        return saved

    async def submit(self, declaration_id: str) -> CustomsDeclaration:
        decl = self.get(declaration_id)
        decl.status = CustomsStatus.SUBMITTED
        saved = self._store.customs_declarations.save(declaration_id, decl)
        await publish(
            CustomsDeclarationCreatedEvent(
                declaration_id=declaration_id,
                procedure=saved.procedure.value,
                cargo_id=saved.cargo_id,
                shipment_id=saved.shipment_id,
            )
        )
        return await self.assess_risk(declaration_id)

    def get(self, declaration_id: str) -> CustomsDeclaration:
        decl = self._store.customs_declarations.get(declaration_id)
        if decl is None:
            raise NotFoundError("CustomsDeclaration", declaration_id)
        return decl

    def list_declarations(
        self,
        *,
        procedure: CustomsProcedure | None = None,
        status: CustomsStatus | None = None,
    ) -> list[CustomsDeclaration]:
        items = self._store.customs_declarations.list_all()
        if procedure:
            items = [d for d in items if d.procedure == procedure]
        if status:
            items = [d for d in items if d.status == status]
        return items

    async def assess_risk(self, declaration_id: str) -> CustomsDeclaration:
        decl = self.get(declaration_id)
        score = 0.0
        if decl.declared_value >= 100000:
            score += 40
        if not decl.hs_code:
            score += 25
        if decl.procedure == CustomsProcedure.TRANSIT:
            score += 10
        tariff = self._tariffs.find_by_hs(decl.hs_code, country=decl.country_of_destination)
        if tariff and tariff.duty_rate_pct >= 20:
            score += 20
        decl.risk_score = min(100.0, score)
        if decl.risk_score >= 60:
            decl.channel = CustomsChannel.RED
        elif decl.risk_score >= 30:
            decl.channel = CustomsChannel.YELLOW
        else:
            decl.channel = CustomsChannel.GREEN
        decl.status = CustomsStatus.RISK_ASSESSMENT
        saved = self._store.customs_declarations.save(declaration_id, decl)

        if saved.channel == CustomsChannel.GREEN:
            return await self.release(declaration_id)
        if saved.channel in (CustomsChannel.YELLOW, CustomsChannel.RED):
            inspection_type = (
                InspectionType.RANDOM
                if saved.channel == CustomsChannel.YELLOW
                else InspectionType.CUSTOMS
            )
            record = self._inspection.schedule(
                InspectionRecord(
                    declaration_id=declaration_id,
                    cargo_id=saved.cargo_id,
                    inspection_type=inspection_type,
                    channel=saved.channel,
                )
            )
            await self._inspection.start(record.inspection_id)
            saved.status = CustomsStatus.INSPECTION
            return self._store.customs_declarations.save(declaration_id, saved)
        return saved

    async def hold(self, declaration_id: str, *, reason: str = "customs_hold") -> CustomsDeclaration:
        decl = self.get(declaration_id)
        decl.status = CustomsStatus.HOLD
        decl.hold_reason = reason
        saved = self._store.customs_declarations.save(declaration_id, decl)
        await publish(
            CargoHeldEvent(
                declaration_id=declaration_id,
                cargo_id=saved.cargo_id,
                reason=reason,
            )
        )
        return saved

    async def release(self, declaration_id: str) -> CustomsDeclaration:
        decl = self.get(declaration_id)
        decl.status = CustomsStatus.RELEASED
        decl.hold_reason = ""
        decl.released_at = time.time()
        saved = self._store.customs_declarations.save(declaration_id, decl)
        await publish(
            CustomsReleasedEvent(
                declaration_id=declaration_id,
                cargo_id=saved.cargo_id,
                channel=saved.channel.value,
            )
        )
        await publish(
            CargoReleasedEvent(declaration_id=declaration_id, cargo_id=saved.cargo_id)
        )
        return saved

    async def complete(self, declaration_id: str) -> CustomsDeclaration:
        decl = self.get(declaration_id)
        if decl.status != CustomsStatus.RELEASED:
            decl = await self.release(declaration_id)
        decl.status = CustomsStatus.COMPLETED
        saved = self._store.customs_declarations.save(declaration_id, decl)
        if saved.procedure == CustomsProcedure.EXPORT:
            await publish(
                ExportCompletedEvent(
                    shipment_id=saved.shipment_id,
                    cargo_id=saved.cargo_id,
                    declaration_id=declaration_id,
                )
            )
        elif saved.procedure == CustomsProcedure.IMPORT:
            await publish(
                ImportCompletedEvent(
                    shipment_id=saved.shipment_id,
                    cargo_id=saved.cargo_id,
                    declaration_id=declaration_id,
                )
            )
        return saved

    def channels(self) -> list[str]:
        return [c.value for c in CustomsChannel]

    def procedures(self) -> list[str]:
        return [p.value for p in CustomsProcedure]


customs_engine = CustomsEngine()
