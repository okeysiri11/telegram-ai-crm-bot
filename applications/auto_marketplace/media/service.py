# MediaService — photos, videos, 360 images, documents.

from __future__ import annotations

from events.publisher import publish
from applications.auto_marketplace.media.models import MediaType, VehicleMedia
from applications.auto_marketplace.shared.exceptions import NotFoundError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store
from applications.auto_marketplace.vehicle_catalog.events import MediaUploadedEvent
from applications.auto_marketplace.vehicle_catalog.service import VehicleCatalogService, vehicle_catalog_service


class MediaService:
    def __init__(
        self,
        store: MarketplaceStore | None = None,
        catalog: VehicleCatalogService | None = None,
    ) -> None:
        self._store = store or marketplace_store
        self._catalog = catalog or vehicle_catalog_service

    async def upload(self, media: VehicleMedia) -> VehicleMedia:
        self._catalog.get(media.vehicle_id)
        saved = self._store.media.save(media.media_id, media)
        vehicle = self._catalog.get(media.vehicle_id)
        if media.media_id not in vehicle.media_ids:
            vehicle.media_ids.append(media.media_id)
            await self._catalog.update(media.vehicle_id, media_ids=vehicle.media_ids)
        await publish(
            MediaUploadedEvent(
                media_id=saved.media_id,
                vehicle_id=saved.vehicle_id,
                media_type=saved.media_type.value,
            )
        )
        return saved

    def get(self, media_id: str) -> VehicleMedia:
        item = self._store.media.get(media_id)
        if item is None:
            raise NotFoundError("VehicleMedia", media_id)
        return item

    def list_for_vehicle(self, vehicle_id: str) -> list[VehicleMedia]:
        return sorted(
            [m for m in self._store.media.list_all() if m.vehicle_id == vehicle_id],
            key=lambda m: m.sort_order,
        )

    async def reorder(self, vehicle_id: str, media_ids: list[str]) -> list[VehicleMedia]:
        items = []
        for order, mid in enumerate(media_ids):
            media = self.get(mid)
            if media.vehicle_id != vehicle_id:
                continue
            media.sort_order = order
            media.optimized = media.optimized or order == 0
            items.append(self._store.media.save(mid, media))
        return items

    def optimize(self, media_id: str) -> VehicleMedia:
        media = self.get(media_id)
        media.optimized = True
        if not media.thumbnail_url:
            media.thumbnail_url = f"{media.url}?thumb=1"
        if media.file_size_bytes > 0:
            media.file_size_bytes = int(media.file_size_bytes * 0.7)
        return self._store.media.save(media_id, media)

    def delete(self, media_id: str) -> bool:
        return self._store.media.delete(media_id)


media_service = MediaService()
