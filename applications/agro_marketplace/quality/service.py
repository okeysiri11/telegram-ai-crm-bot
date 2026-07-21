# QualityService — grading and laboratory quality records.

from __future__ import annotations

from applications.agro_marketplace.product_catalog.ai_integration import CatalogAIIntegration, catalog_ai
from applications.agro_marketplace.product_catalog.models import LaboratoryResult, QualityGrade
from applications.agro_marketplace.shared.exceptions import NotFoundError
from applications.agro_marketplace.shared.store import AgroStore, agro_store
from applications.agro_marketplace.harvest.service import HarvestService, harvest_service


class QualityService:
    def __init__(
        self,
        store: AgroStore | None = None,
        harvests: HarvestService | None = None,
        ai: CatalogAIIntegration | None = None,
    ) -> None:
        self._store = store or agro_store
        self._harvests = harvests or harvest_service
        self._ai = ai or catalog_ai

    def record_lab_result(self, result: LaboratoryResult) -> LaboratoryResult:
        if result.harvest_id:
            self._harvests.get_harvest(result.harvest_id)
        if result.moisture_pct > 14 or result.foreign_material_pct > 3 or result.toxins_ppm > 0:
            result.grade = QualityGrade.C if result.toxins_ppm > 0 else QualityGrade.B
        return self._store.lab_results.save(result.result_id, result)

    def list_lab_results(self, *, harvest_id: str | None = None) -> list[LaboratoryResult]:
        items = self._store.lab_results.list_all()
        if harvest_id:
            items = [r for r in items if r.harvest_id == harvest_id]
        return items

    def get_lab_result(self, result_id: str) -> LaboratoryResult:
        result = self._store.lab_results.get(result_id)
        if result is None:
            raise NotFoundError("LaboratoryResult", result_id)
        return result

    async def assess_harvest(self, harvest_id: str) -> dict:
        harvest = self._harvests.get_harvest(harvest_id)
        return await self._ai.assess_quality(harvest)


quality_service = QualityService()
