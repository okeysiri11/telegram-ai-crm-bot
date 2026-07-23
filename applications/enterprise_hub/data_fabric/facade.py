"""Data Fabric Suite facade — Sprint 20.7."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.data_fabric.analytics.optimization import OptimizationAnalytics
from applications.enterprise_hub.data_fabric.analytics.quality import QualityAnalytics
from applications.enterprise_hub.data_fabric.analytics.usage import UsageAnalytics
from applications.enterprise_hub.data_fabric.cache_manager import CacheManager
from applications.enterprise_hub.data_fabric.connectors.custom import CustomConnector
from applications.enterprise_hub.data_fabric.connectors.data_warehouse import DataWarehouseConnector
from applications.enterprise_hub.data_fabric.connectors.elasticsearch import ElasticsearchConnector
from applications.enterprise_hub.data_fabric.connectors.mongodb import MongodbConnector
from applications.enterprise_hub.data_fabric.connectors.mysql import MysqlConnector
from applications.enterprise_hub.data_fabric.connectors.object_storage import ObjectStorageConnector
from applications.enterprise_hub.data_fabric.connectors.postgresql import PostgresqlConnector
from applications.enterprise_hub.data_fabric.connectors.redis import RedisConnector
from applications.enterprise_hub.data_fabric.connectors.vector_db import VectorDbConnector
from applications.enterprise_hub.data_fabric.data_catalog import DataCatalog
from applications.enterprise_hub.data_fabric.data_fabric import DataFabricCore
from applications.enterprise_hub.data_fabric.data_quality import DataQualityEngine
from applications.enterprise_hub.data_fabric.data_virtualization import DataVirtualization
from applications.enterprise_hub.data_fabric.federation import FederationEngine
from applications.enterprise_hub.data_fabric.governance import DataGovernance
from applications.enterprise_hub.data_fabric.lineage_manager import LineageManager
from applications.enterprise_hub.data_fabric.metadata_manager import MetadataManager
from applications.enterprise_hub.data_fabric.query_router import QueryRouter
from applications.enterprise_hub.data_fabric.schema_manager import SchemaManager
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


class DataFabricSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.core = DataFabricCore(self.store)
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
        self.postgresql = PostgresqlConnector(self.store)
        self.mysql = MysqlConnector(self.store)
        self.mongodb = MongodbConnector(self.store)
        self.redis = RedisConnector(self.store)
        self.elasticsearch = ElasticsearchConnector(self.store)
        self.vector_db = VectorDbConnector(self.store)
        self.object_storage = ObjectStorageConnector(self.store)
        self.data_warehouse = DataWarehouseConnector(self.store)
        self.custom = CustomConnector(self.store)
        self.usage = UsageAnalytics(self.store)
        self.quality_analytics = QualityAnalytics(self.store)
        self.optimization = OptimizationAnalytics(self.store)

    def dashboard(self) -> dict[str, Any]:
        usage = self.usage.report()
        quality = self.quality_analytics.report()
        opt = self.optimization.report()
        connectors = self.store.edf_connectors.list_all()
        violations = [
            a for a in self.store.edf_gov_audit.list_all() if a.get("action") == "policy_violation"
        ]
        return {
            "sources": len(connectors),
            "assets": self.catalog.status()["assets"],
            "quality_avg": quality.get("avg_score"),
            "usage_queries": usage.get("query_count"),
            "avg_latency_ms": opt.get("avg_latency_ms"),
            "cache_hits": usage.get("cache_hits"),
            "storage_volume_mb": 128 + self.catalog.status()["assets"] * 4,
            "connector_status": {
                "connected": sum(1 for c in connectors if c.get("status") == "connected"),
                "total": len(connectors),
            },
            "policy_violations": len(violations),
            "optimization_suggestions": opt.get("suggestions"),
            "usage_id": usage["analytics_id"],
            "quality_id": quality["analytics_id"],
            "optimization_id": opt["analytics_id"],
        }

    def bootstrap(self) -> dict[str, Any]:
        a1 = self.catalog.register(name="crm.leads", kind="table", source="crm", owner="crm-ops", tags=["crm"])
        a2 = self.catalog.register(name="erp.orders", kind="table", source="erp", owner="erp-ops", tags=["erp"])
        a3 = self.catalog.register(
            name="kb.embeddings", kind="vector_index", source="knowledge", owner="ai-ops", tags=["ai", "vector"]
        )
        a4 = self.catalog.register(
            name="analytics.facts", kind="table", source="analytics", owner="bi-ops", tags=["analytics"]
        )
        a5 = self.catalog.register(
            name="events.bus", kind="event", source="event_stream", owner="platform", tags=["events"]
        )
        a6 = self.catalog.register(
            name="docs.contracts", kind="document", source="object_storage", owner="legal-ops"
        )
        a7 = self.catalog.register(name="forecast.model", kind="ai_model", source="custom", owner="ai-ops")

        m1 = self.metadata.set_metadata(
            asset_id=a1["asset_id"], sensitivity="confidential", classification="pii", version="1.0"
        )
        sch = self.schemas.register(
            name="crm.leads",
            asset_id=a1["asset_id"],
            fields=[{"name": "id", "type": "string"}, {"name": "email", "type": "string"}],
        )
        view = self.virtualization.create_view(
            name="customer_360",
            mode="sql",
            sources=["crm", "erp", "knowledge", "analytics"],
            projection=["entity_id", "lead", "order", "insight"],
        )
        vq = self.virtualization.query_view(view_id=view["view_id"], predicate="active=true")

        pg = self.postgresql.connect(name="primary-pg", endpoint="pg://hub")
        es = self.elasticsearch.connect(name="search", endpoint="es://hub")
        vd = self.vector_db.connect(name="vectors", endpoint="vec://hub")
        self.mysql.connect(name="legacy-mysql")
        self.mongodb.connect(name="docs-mongo")
        self.redis.connect(name="cache-redis")
        self.object_storage.connect(name="blobs")
        self.data_warehouse.connect(name="warehouse")
        self.custom.connect(name="custom-api")

        self.cache.put(query="SELECT * FROM crm.leads", source="postgresql", result={"n": 10}, kind="query")
        route = self.router.route(query="SELECT * FROM crm.leads", preferred_sources=["postgresql"], use_cache=True)
        unified = self.core.unified_query(
            query="customer profile E1", sources=["crm", "erp", "knowledge", "analytics"]
        )
        # second call hits cache path via cache.put inside first unified + router cache check
        unified2 = self.core.unified_query(
            query="customer profile E1", sources=["crm", "erp", "knowledge", "analytics"]
        )

        gov = self.governance.enforce(asset_id=a1["asset_id"], mask_fields=["email"])
        self.governance.audit(asset_id=a1["asset_id"], action="enforce")
        lin = self.lineage.record(
            asset_id=a4["asset_id"],
            upstream=[a1["asset_id"], a2["asset_id"]],
            transforms=["join", "aggregate"],
            consumers=["dashboard", "forecast.model"],
        )
        qual = self.quality.assess(asset_id=a1["asset_id"], metrics={"completeness": 0.99, "freshness": 0.9})
        dash = self.dashboard()

        return {
            "bootstrap": True,
            "asset_ids": [a1["asset_id"], a2["asset_id"], a3["asset_id"], a4["asset_id"], a5["asset_id"], a6["asset_id"], a7["asset_id"]],
            "metadata_id": m1["metadata_id"],
            "schema_id": sch["schema_id"],
            "view_id": view["view_id"],
            "virtual_query_id": vq["query_id"],
            "connector_ids": [pg["connector_id"], es["connector_id"], vd["connector_id"]],
            "route_id": route["route_id"],
            "route_cache_hit": route["cache_hit"],
            "unified_id": unified.get("unified_id") or unified.get("from_cache") and unified.get("route_id"),
            "unified_from_cache": bool(unified2.get("from_cache")),
            "governance_id": gov["governance_id"],
            "lineage_id": lin["lineage_id"],
            "quality_id": qual["quality_id"],
            "quality_passed": qual["passed"],
            "dashboard": dash,
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return self.core.status()


data_fabric = DataFabricSuite()
