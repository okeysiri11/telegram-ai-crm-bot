# Digital Twin Engine — real-time aggregated port state.

from __future__ import annotations

from events.publisher import publish

from applications.port_erp.digital_twin.events import TwinSnapshotTakenEvent
from applications.port_erp.digital_twin.models import TwinSnapshot, WeatherCondition, WeatherState
from applications.port_erp.shared.store import PortStore, port_store


class DigitalTwinEngine:
    def __init__(self, store: PortStore | None = None) -> None:
        self._store = store or port_store
        self._weather = WeatherState()

    def set_weather(
        self,
        *,
        condition: WeatherCondition | str = WeatherCondition.CLEAR,
        wind_knots: float = 0.0,
        visibility_km: float = 10.0,
        temperature_c: float = 25.0,
    ) -> WeatherState:
        cond = WeatherCondition(condition) if isinstance(condition, str) else condition
        self._weather = WeatherState(
            condition=cond,
            wind_knots=wind_knots,
            visibility_km=visibility_km,
            temperature_c=temperature_c,
        )
        return self._weather

    def weather(self) -> WeatherState:
        return self._weather

    def _count_occupied_berths(self) -> int:
        return len([b for b in self._store.berths.list_all() if getattr(b, "status", "") == "occupied"])

    def _yard_stats(self) -> tuple[int, int]:
        slots = self._store.yard_slots.list_all()
        occupied = len([s for s in slots if getattr(s, "status", None) and s.status.value == "occupied"])
        return len(slots), occupied

    def _live_counts(self) -> dict[str, int]:
        vessels = 0
        trucks = 0
        rail = 0
        for pos in self._store.live_positions.list_all():
            asset = getattr(pos.asset_type, "value", str(pos.asset_type))
            if asset == "vessel":
                vessels += 1
            elif asset == "truck":
                trucks += 1
            elif asset == "rail":
                rail += 1
        return {"vessels": vessels, "trucks": trucks, "rail": rail}

    async def snapshot(self, *, port_id: str = "") -> TwinSnapshot:
        yard_total, yard_occ = self._yard_stats()
        live = self._live_counts()
        berths = self._store.berths.count()
        occupied = self._count_occupied_berths()
        ships = max(self._store.vessels.count(), live["vessels"])
        utilization = 0.0
        if berths:
            utilization = round(occupied / berths, 4)
        elif yard_total:
            utilization = round(yard_occ / yard_total, 4)

        snap = TwinSnapshot(
            port_id=port_id,
            ships=ships,
            berths=berths,
            berths_occupied=occupied,
            warehouses=self._store.warehouses.count(),
            yards_slots=yard_total,
            yards_occupied=yard_occ,
            equipment=self._store.equipment.count(),
            containers=self._store.containers.count(),
            vehicles=live["trucks"] or self._store.truck_tracks.count(),
            rail_assets=live["rail"],
            road_assets=live["trucks"] or self._store.truck_tracks.count(),
            weather=self._weather,
            utilization=utilization,
            metadata={
                "gates": self._store.gates.count(),
                "terminals": self._store.terminals.count(),
                "voyages": self._store.voyages.count(),
            },
        )
        saved = self._store.twin_snapshots.save(snap.snapshot_id, snap)
        await publish(
            TwinSnapshotTakenEvent(snapshot_id=saved.snapshot_id, utilization=saved.utilization)
        )
        return saved

    def latest(self) -> TwinSnapshot | None:
        items = sorted(self._store.twin_snapshots.list_all(), key=lambda s: s.created_at, reverse=True)
        return items[0] if items else None

    def list_snapshots(self, *, limit: int = 20) -> list[TwinSnapshot]:
        items = sorted(self._store.twin_snapshots.list_all(), key=lambda s: s.created_at, reverse=True)
        return items[:limit]

    def state(self) -> dict:
        latest = self.latest()
        return {
            "weather": self._weather.to_dict(),
            "latest_snapshot": latest.to_dict() if latest else None,
            "entities": {
                "ships": self._store.vessels.count(),
                "berths": self._store.berths.count(),
                "warehouses": self._store.warehouses.count(),
                "yards": self._store.yard_blocks.count(),
                "equipment": self._store.equipment.count(),
                "containers": self._store.containers.count(),
                "vehicles": self._store.truck_tracks.count(),
            },
        }


digital_twin_engine = DigitalTwinEngine()
