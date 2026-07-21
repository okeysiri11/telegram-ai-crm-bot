# Vessel Registry service.

from __future__ import annotations

import time

from events.publisher import publish

from applications.port_erp.shared.events import VesselArrivedEvent, VesselDepartedEvent
from applications.port_erp.shared.exceptions import NotFoundError, ValidationError
from applications.port_erp.shared.models import Vessel, VesselStatus, Voyage
from applications.port_erp.shared.store import PortStore, port_store


class VesselRegistry:
    def __init__(self, store: PortStore | None = None) -> None:
        self._store = store or port_store

    def register(self, vessel: Vessel) -> Vessel:
        if not vessel.name:
            raise ValidationError("name is required")
        return self._store.vessels.save(vessel.vessel_id, vessel)

    def get(self, vessel_id: str) -> Vessel:
        vessel = self._store.vessels.get(vessel_id)
        if vessel is None:
            raise NotFoundError("Vessel", vessel_id)
        return vessel

    def list_vessels(self, *, status: VesselStatus | None = None) -> list[Vessel]:
        items = self._store.vessels.list_all()
        if status:
            items = [v for v in items if v.status == status]
        return items

    def create_voyage(self, voyage: Voyage) -> Voyage:
        self.get(voyage.vessel_id)
        if not voyage.voyage_number:
            raise ValidationError("voyage_number is required")
        return self._store.voyages.save(voyage.voyage_id, voyage)

    def get_voyage(self, voyage_id: str) -> Voyage:
        voyage = self._store.voyages.get(voyage_id)
        if voyage is None:
            raise NotFoundError("Voyage", voyage_id)
        return voyage

    def list_voyages(self, *, vessel_id: str | None = None) -> list[Voyage]:
        items = self._store.voyages.list_all()
        if vessel_id:
            items = [v for v in items if v.vessel_id == vessel_id]
        return items

    async def arrive(self, voyage_id: str, *, port_id: str = "") -> Voyage:
        voyage = self.get_voyage(voyage_id)
        vessel = self.get(voyage.vessel_id)
        voyage.status = "arrived"
        voyage.ata = time.time()
        vessel.status = VesselStatus.ARRIVED
        self._store.vessels.save(vessel.vessel_id, vessel)
        saved = self._store.voyages.save(voyage_id, voyage)
        await publish(
            VesselArrivedEvent(
                vessel_id=vessel.vessel_id,
                voyage_id=voyage_id,
                port_id=port_id or voyage.destination_port_id,
            )
        )
        return saved

    async def depart(self, voyage_id: str, *, port_id: str = "") -> Voyage:
        voyage = self.get_voyage(voyage_id)
        vessel = self.get(voyage.vessel_id)
        voyage.status = "departed"
        voyage.atd = time.time()
        vessel.status = VesselStatus.DEPARTED
        self._store.vessels.save(vessel.vessel_id, vessel)
        saved = self._store.voyages.save(voyage_id, voyage)
        await publish(
            VesselDepartedEvent(
                vessel_id=vessel.vessel_id,
                voyage_id=voyage_id,
                port_id=port_id or voyage.origin_port_id,
            )
        )
        return saved


vessel_registry = VesselRegistry()
