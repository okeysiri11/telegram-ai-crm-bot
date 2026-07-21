# HarvestService — harvest registration, batches, season and yield tracking.

from __future__ import annotations

from events.publisher import publish

from applications.agro_marketplace.product_catalog.ai_integration import CatalogAIIntegration, catalog_ai
from applications.agro_marketplace.product_catalog.events import HarvestRegisteredEvent
from applications.agro_marketplace.product_catalog.models import (
    HarvestBatch,
    HarvestRecord,
    QualityGrade,
    Season,
)
from applications.agro_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.agro_marketplace.shared.store import AgroStore, agro_store


class HarvestService:
    def __init__(
        self,
        store: AgroStore | None = None,
        ai: CatalogAIIntegration | None = None,
    ) -> None:
        self._store = store or agro_store
        self._ai = ai or catalog_ai

    def create_season(self, season: Season) -> Season:
        if not season.name or not season.year:
            raise ValidationError("name and year are required")
        return self._store.seasons.save(season.season_id, season)

    def list_seasons(self) -> list[Season]:
        return self._store.seasons.list_all()

    async def register_harvest(self, harvest: HarvestRecord) -> HarvestRecord:
        if harvest.quantity <= 0:
            raise ValidationError("quantity must be positive")
        assessment = await self._ai.assess_quality(harvest)
        if not harvest.quality_grade or harvest.quality_grade == QualityGrade.A:
            suggested = assessment.get("suggested_grade", "A")
            harvest.quality_grade = QualityGrade(suggested)
        saved = self._store.harvest_records.save(harvest.harvest_id, harvest)
        await publish(
            HarvestRegisteredEvent(
                harvest_id=saved.harvest_id,
                farm_id=saved.farm_id,
                crop_id=saved.crop_id,
                quantity=saved.quantity,
                quality_grade=saved.quality_grade.value,
            )
        )
        return saved

    def get_harvest(self, harvest_id: str) -> HarvestRecord:
        harvest = self._store.harvest_records.get(harvest_id)
        if harvest is None:
            raise NotFoundError("Harvest", harvest_id)
        return harvest

    def list_harvests(
        self,
        *,
        farm_id: str | None = None,
        season_id: str | None = None,
        region: str | None = None,
        crop_id: str | None = None,
    ) -> list[HarvestRecord]:
        items = self._store.harvest_records.list_all()
        if farm_id:
            items = [h for h in items if h.farm_id == farm_id]
        if season_id:
            items = [h for h in items if h.season_id == season_id]
        if region:
            items = [h for h in items if h.region.lower() == region.lower()]
        if crop_id:
            items = [h for h in items if h.crop_id == crop_id]
        return items

    def create_batch(self, batch: HarvestBatch) -> HarvestBatch:
        self.get_harvest(batch.harvest_id)
        if not batch.batch_code:
            batch.batch_code = f"BATCH-{batch.batch_id[:8].upper()}"
        return self._store.harvest_batches.save(batch.batch_id, batch)

    def list_batches(self, *, harvest_id: str | None = None) -> list[HarvestBatch]:
        items = self._store.harvest_batches.list_all()
        if harvest_id:
            items = [b for b in items if b.harvest_id == harvest_id]
        return items

    def record_yield(
        self,
        harvest_id: str,
        *,
        yield_per_hectare: float,
        quantity: float | None = None,
    ) -> HarvestRecord:
        harvest = self.get_harvest(harvest_id)
        harvest.yield_per_hectare = yield_per_hectare
        if quantity is not None:
            harvest.quantity = quantity
        return self._store.harvest_records.save(harvest_id, harvest)

    def grade_quality(
        self,
        harvest_id: str,
        *,
        grade: QualityGrade | str,
        moisture_pct: float | None = None,
        protein_pct: float | None = None,
        foreign_material_pct: float | None = None,
    ) -> HarvestRecord:
        harvest = self.get_harvest(harvest_id)
        harvest.quality_grade = QualityGrade(grade) if isinstance(grade, str) else grade
        if moisture_pct is not None:
            harvest.moisture_pct = moisture_pct
        if protein_pct is not None:
            harvest.protein_pct = protein_pct
        if foreign_material_pct is not None:
            harvest.foreign_material_pct = foreign_material_pct
        return self._store.harvest_records.save(harvest_id, harvest)


harvest_service = HarvestService()
