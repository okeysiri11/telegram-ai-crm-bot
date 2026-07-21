# Container Tracking Engine — lifecycle + positions.

from __future__ import annotations

from events.publisher import publish

from applications.port_erp.containers.service import ContainerRegistry, container_registry
from applications.port_erp.shared.exceptions import ValidationError
from applications.port_erp.shared.models import ContainerStatus, TrackAssetType
from applications.port_erp.shared.store import PortStore, port_store
from applications.port_erp.tracking.events import ContainerPositionUpdatedEvent
from applications.port_erp.tracking.live import LivePositionEngine, live_position_engine
from applications.port_erp.tracking.models import ContainerLifecycleRecord, TimelineEvent
from applications.port_erp.timeline.engine import TimelineEngine, timeline_engine

_LIFECYCLE_ORDER = [
    ContainerStatus.CREATED,
    ContainerStatus.BOOKED,
    ContainerStatus.LOADED,
    ContainerStatus.AT_PORT,
    ContainerStatus.ON_VESSEL,
    ContainerStatus.IN_TRANSIT,
    ContainerStatus.TRANSSHIPMENT,
    ContainerStatus.CUSTOMS,
    ContainerStatus.ARRIVED,
    ContainerStatus.WAREHOUSE,
    ContainerStatus.OUT_FOR_DELIVERY,
    ContainerStatus.DELIVERED,
    ContainerStatus.COMPLETED,
]


class ContainerTrackingEngine:
    def __init__(
        self,
        store: PortStore | None = None,
        containers: ContainerRegistry | None = None,
        live: LivePositionEngine | None = None,
        timeline: TimelineEngine | None = None,
    ) -> None:
        self._store = store or port_store
        self._containers = containers or container_registry
        self._live = live or live_position_engine
        self._timeline = timeline or timeline_engine

    async def update_position(
        self,
        container_id: str,
        *,
        latitude: float,
        longitude: float,
        status: str | None = None,
        last_checkpoint: str = "",
        destination: str = "",
    ):
        container = self._containers.get(container_id)
        if status:
            await self.advance(container_id, status, location=last_checkpoint)
            container = self._containers.get(container_id)
        live = await self._live.update(
            asset_type=TrackAssetType.CONTAINER,
            asset_id=container_id,
            latitude=latitude,
            longitude=longitude,
            destination=destination,
            last_checkpoint=last_checkpoint,
            source="container_gps",
        )
        await publish(
            ContainerPositionUpdatedEvent(
                container_id=container_id,
                latitude=latitude,
                longitude=longitude,
                status=container.status.value,
            )
        )
        return live

    async def advance(
        self,
        container_id: str,
        to_status: ContainerStatus | str,
        *,
        location: str = "",
        notes: str = "",
    ):
        container = self._containers.get(container_id)
        target = ContainerStatus(to_status) if isinstance(to_status, str) else to_status
        # Resolve aliases to canonical members by value
        target = ContainerStatus(target.value)
        previous = container.status.value
        if target not in _LIFECYCLE_ORDER and target.value not in {s.value for s in _LIFECYCLE_ORDER}:
            raise ValidationError(f"unsupported container status: {target}")
        container.status = target
        saved = self._store.containers.save(container_id, container)
        record = ContainerLifecycleRecord(
            container_id=container_id,
            from_status=previous,
            to_status=saved.status.value,
            location=location,
            notes=notes,
        )
        self._store.container_lifecycle.save(record.record_id, record)
        self._timeline.record(
            TimelineEvent(
                asset_type="container",
                asset_id=container_id,
                event_type="lifecycle",
                title=f"{previous} → {saved.status.value}",
                location=location,
                detail=notes,
            )
        )
        return saved

    def history(self, container_id: str) -> list[ContainerLifecycleRecord]:
        items = [
            r for r in self._store.container_lifecycle.list_all() if r.container_id == container_id
        ]
        return sorted(items, key=lambda r: r.occurred_at)

    def statuses(self) -> list[str]:
        return [s.value for s in _LIFECYCLE_ORDER]


container_tracking_engine = ContainerTrackingEngine()
