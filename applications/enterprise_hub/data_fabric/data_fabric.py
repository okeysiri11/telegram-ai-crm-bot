from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"



from applications.enterprise_hub.data_fabric.cache_manager import CacheManager
from applications.enterprise_hub.data_fabric.data_catalog import DataCatalog
from applications.enterprise_hub.data_fabric.data_quality import DataQualityEngine
from applications.enterprise_hub.data_fabric.data_virtualization import DataVirtualization
from applications.enterprise_hub.data_fabric.federation import FederationEngine
from applications.enterprise_hub.data_fabric.governance import DataGovernance
from applications.enterprise_hub.data_fabric.lineage_manager import LineageManager
from applications.enterprise_hub.data_fabric.metadata_manager import MetadataManager
from applications.enterprise_hub.data_fabric.query_router import QueryRouter
from applications.enterprise_hub.data_fabric.schema_manager import SchemaManager


class DataFabricCore:
    """Orchestrates catalog → virtualization → federation → routing with cache/governance."""

    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.catalog = DataCatalog(self.store)
        self.metadata = MetadataManager(self.store)
        self.virtualization = DataVirtualization(self.store)
        self.federation = FederationEngine(self.store)
        self.router = QueryRouter(self.store)
        self.lineage = LineageManager(self.store)
        self.governance = DataGovernance(self.store)
        self.quality = DataQualityEngine(self.store)
        self.schemas = SchemaManager(self.store)
        self.cache = CacheManager(self.store)

    def unified_query(
        self,
        *,
        query: str,
        sources: list[str] | None = None,
        principal: str = "system",
    ) -> dict[str, Any]:
        srcs = list(sources or ["crm", "erp", "knowledge"])
        route = self.router.route(query=query, preferred_sources=srcs, principal=principal)
        cached = self.cache.get(query=query, source=route["chosen_source"])
        if cached:
            return {
                "unified_id": cached["cache_id"],
                "from_cache": True,
                "route_id": route["route_id"],
                "result": cached.get("result"),
            }
        if len(srcs) >= 2:
            fed = self.federation.federate(sources=srcs, query=query)
            result = fed["result"]
            federation_id = fed["federation_id"]
        else:
            result = {"source": srcs[0], "query": query}
            federation_id = None
        entry = self.cache.put(query=query, source=route["chosen_source"], result=result, kind="federation")
        uid = _id("edf_uq")
        return self.store.edf_unified.save(
            uid,
            {
                "unified_id": uid,
                "from_cache": False,
                "route_id": route["route_id"],
                "federation_id": federation_id,
                "cache_id": entry["cache_id"],
                "result": result,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "catalog": self.catalog.status(),
            "router": self.router.status(),
            "federation": self.federation.status(),
            "cache": self.cache.status(),
            "governance": self.governance.status(),
            "quality": self.quality.status(),
        }
