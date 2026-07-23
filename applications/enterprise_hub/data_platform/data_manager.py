"""Data manager — central orchestration of EDP operations."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.data_platform.data_catalog import DataCatalog
from applications.enterprise_hub.data_platform.data_governance import DataGovernance
from applications.enterprise_hub.data_platform.data_lineage import DataLineage
from applications.enterprise_hub.data_platform.data_quality import DataQuality
from applications.enterprise_hub.data_platform.master_data import MasterData
from applications.enterprise_hub.data_platform.metadata import MetadataManager
from applications.enterprise_hub.data_platform.versioning import DataVersioning
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


class DataManager:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.master = MasterData(self.store)
        self.metadata = MetadataManager(self.store)
        self.catalog = DataCatalog(self.store)
        self.quality = DataQuality(self.store)
        self.governance = DataGovernance(self.store)
        self.lineage = DataLineage(self.store)
        self.versioning = DataVersioning(self.store)

    def create_master(
        self,
        *,
        entity_type: str,
        name: str,
        attributes: dict[str, Any] | None = None,
        owner: str = "system",
        source: str = "mdm",
    ) -> dict[str, Any]:
        entity = self.master.upsert(
            entity_type=entity_type,
            name=name,
            attributes=attributes,
            owner=owner,
            source=source,
        )
        self.catalog.publish(
            name=name,
            object_type=entity_type,
            owner=owner,
            source=source,
            description=f"Master {entity_type}",
            schema_ref=entity_type,
            links=[],
        )
        self.lineage.record(
            entity_id=entity["entity_id"],
            source=source,
            actor=owner,
            detail="create_master",
        )
        self.governance.audit(
            entity_id=entity["entity_id"],
            actor=owner,
            action="create",
            detail=entity_type,
        )
        return entity

    def status(self) -> dict[str, Any]:
        return {
            "master": self.master.status(),
            "metadata": self.metadata.status(),
            "catalog": self.catalog.status(),
            "quality": self.quality.status(),
            "governance": self.governance.status(),
            "lineage": self.lineage.status(),
            "versioning": self.versioning.status(),
        }
