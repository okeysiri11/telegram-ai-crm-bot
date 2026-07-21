# ExporterService — exporter registry and profiles.

from __future__ import annotations

from applications.agro_marketplace.crm.engine import CRMEngine, crm_engine
from applications.agro_marketplace.marketplace.models import ExporterProfile
from applications.agro_marketplace.shared.exceptions import NotFoundError
from applications.agro_marketplace.shared.store import AgroStore, agro_store


class ExporterService:
    def __init__(self, store: AgroStore | None = None, crm: CRMEngine | None = None) -> None:
        self._store = store or agro_store
        self._crm = crm or crm_engine

    def register(self, profile: ExporterProfile) -> ExporterProfile:
        return self._crm.register_exporter(profile)

    def list_exporters(self) -> list[ExporterProfile]:
        return self._crm.list_exporter_profiles()

    def get(self, exporter_id: str) -> ExporterProfile:
        for profile in self._store.exporter_profiles.list_all():
            if profile.exporter_id == exporter_id or profile.profile_id == exporter_id:
                return profile
        raise NotFoundError("ExporterProfile", exporter_id)


exporter_service = ExporterService()
