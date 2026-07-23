"""EDP Suite facade — Sprint 19.7."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.data_platform.analytics import (
    AIDataAssistant,
    DataProfiler,
    DataStatistics,
    QualityDashboard,
)
from applications.enterprise_hub.data_platform.data_manager import DataManager
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


class DataPlatformSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.manager = DataManager(self.store)
        self.master = self.manager.master
        self.metadata = self.manager.metadata
        self.catalog = self.manager.catalog
        self.quality = self.manager.quality
        self.governance = self.manager.governance
        self.lineage = self.manager.lineage
        self.versioning = self.manager.versioning
        self.profiler = DataProfiler(self.store)
        self.statistics = DataStatistics(self.store)
        self.ai = AIDataAssistant(self.store)
        self.dashboard = QualityDashboard(self.store)

    def bootstrap(self) -> dict[str, Any]:
        user = self.manager.create_master(
            entity_type="user", name="Alex CFO", attributes={"email": "cfo@bidex.io"}, owner="hr"
        )
        company = self.manager.create_master(
            entity_type="company", name="Bidex Holdings", attributes={"jurisdiction": "US-DE"}
        )
        contact = self.manager.create_master(
            entity_type="contact", name="Acme Contact", attributes={"phone": "+1-555-0100"}
        )
        customer = self.manager.create_master(
            entity_type="customer", name="Acme Trading", attributes={"tier": "gold"}
        )
        supplier = self.manager.create_master(
            entity_type="supplier", name="Global Supplies", attributes={"region": "EU"}
        )
        project = self.manager.create_master(
            entity_type="project", name="Hub Rollout", attributes={"status": "active"}
        )
        product = self.manager.create_master(
            entity_type="product", name="Enterprise Hub", attributes={"sku": "HUB-1"}
        )
        service = self.manager.create_master(
            entity_type="service", name="Managed AI Ops", attributes={"sla": "99.9"}
        )
        asset = self.manager.create_master(
            entity_type="asset", name="Warehouse A", attributes={"site": "NL"}
        )
        equipment = self.manager.create_master(
            entity_type="equipment", name="Crane-01", attributes={"port": "RTM"}
        )
        document = self.manager.create_master(
            entity_type="document", name="CTR-2026-01", attributes={"kind": "contract"}
        )
        financial = self.manager.create_master(
            entity_type="financial_object", name="INV-9001", attributes={"currency": "USD"}
        )
        location = self.manager.create_master(
            entity_type="location", name="HQ Delaware", attributes={"country": "US"}
        )

        # intentional near-duplicate for quality demo
        dup_cust = self.master.upsert(entity_type="customer", name="Acme Trading", source="import")

        rel1 = self.master.relate(
            from_entity_id=user["entity_id"],
            to_entity_id=company["entity_id"],
            relation="works_for",
        )
        rel2 = self.master.relate(
            from_entity_id=financial["entity_id"],
            to_entity_id=customer["entity_id"],
            relation="billed_to",
        )
        rel3 = self.master.relate(
            from_entity_id=document["entity_id"],
            to_entity_id=project["entity_id"],
            relation="covers",
        )

        schema_user = self.metadata.register_schema(
            name="UserSchema",
            entity_type="user",
            attributes=[{"name": "email", "type": "string"}],
            constraints=["email_required"],
            indexes=["email"],
            dependencies=["company"],
        )
        schema_co = self.metadata.register_schema(
            name="CompanySchema",
            entity_type="company",
            attributes=[{"name": "jurisdiction", "type": "string"}],
            indexes=["name"],
        )

        qual = self.quality.run(entity_type="customer")
        norm = self.quality.normalizer.normalize(value="  acme trading ", kind="name")
        rule = self.quality.rules.evaluate(rule="name_required", payload={"name": "Acme"})

        pol = self.governance.set_policy(
            entity_id=customer["entity_id"],
            classification="confidential",
            retention_days=2555,
            access=["cfo", "compliance"],
        )
        aud = self.governance.audit(
            entity_id=customer["entity_id"],
            actor="cfo",
            action="classify",
            detail="confidential",
        )

        lin = self.lineage.record(
            entity_id=financial["entity_id"],
            source="finance",
            actor="billing",
            process="invoice_create",
            ai_agent="finance_agent",
            integration="stripe",
            detail="bootstrap",
        )
        ver1 = self.versioning.snapshot(entity_id=customer["entity_id"], note="v2 after import")
        # mutate then snapshot again
        cust = self.master.get(entity_id=customer["entity_id"])
        cust["attributes"] = {**(cust.get("attributes") or {}), "tier": "platinum"}
        self.store.edp_entities.save(customer["entity_id"], cust)
        ver2 = self.versioning.snapshot(entity_id=customer["entity_id"], note="tier upgrade")
        cmp = self.versioning.compare(version_id_a=ver1["version_id"], version_id_b=ver2["version_id"])
        rb = self.versioning.rollback(version_id=ver1["version_id"])

        prof = self.profiler.profile()
        stats = self.statistics.summarize()
        ai1 = self.ai.assist(action="find_duplicates", subject="customer")
        ai2 = self.ai.assist(action="merge_records", subject=dup_cust["entity_id"])
        ai3 = self.ai.assist(action="suggest_normalization", subject="company names")
        ai4 = self.ai.assist(action="score_quality", subject="customer master")

        dash_q = self.dashboard.render(dashboard_type="quality")
        dash_c = self.dashboard.render(dashboard_type="catalog")
        dash_g = self.dashboard.render(dashboard_type="governance")
        dash_l = self.dashboard.render(dashboard_type="lineage")
        dash_a = self.dashboard.render(dashboard_type="analytics")

        return {
            "bootstrap": True,
            "user_id": user["entity_id"],
            "company_id": company["entity_id"],
            "contact_id": contact["entity_id"],
            "customer_id": customer["entity_id"],
            "supplier_id": supplier["entity_id"],
            "project_id": project["entity_id"],
            "product_id": product["entity_id"],
            "service_id": service["entity_id"],
            "asset_id": asset["entity_id"],
            "equipment_id": equipment["entity_id"],
            "document_id": document["entity_id"],
            "financial_object_id": financial["entity_id"],
            "location_id": location["entity_id"],
            "duplicate_customer_id": dup_cust["entity_id"],
            "relationship_user_company_id": rel1["relationship_id"],
            "relationship_invoice_customer_id": rel2["relationship_id"],
            "relationship_doc_project_id": rel3["relationship_id"],
            "schema_user_id": schema_user["schema_id"],
            "schema_company_id": schema_co["schema_id"],
            "quality_id": qual["quality_id"],
            "normalization_id": norm["normalization_id"],
            "rule_id": rule["rule_id"],
            "policy_id": pol["policy_id"],
            "audit_id": aud["audit_id"],
            "lineage_id": lin["lineage_id"],
            "version_1_id": ver1["version_id"],
            "version_2_id": ver2["version_id"],
            "compare_id": cmp["compare_id"],
            "rollback_id": rb["rollback_id"],
            "profile_id": prof["profile_id"],
            "stats_id": stats["stats_id"],
            "ai_duplicates_id": ai1["assist_id"],
            "ai_merge_id": ai2["assist_id"],
            "ai_normalize_id": ai3["assist_id"],
            "ai_score_id": ai4["assist_id"],
            "dashboard_quality_id": dash_q["dashboard_id"],
            "dashboard_catalog_id": dash_c["dashboard_id"],
            "dashboard_governance_id": dash_g["dashboard_id"],
            "dashboard_lineage_id": dash_l["dashboard_id"],
            "dashboard_analytics_id": dash_a["dashboard_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "manager": self.manager.status(),
            "profiler": self.profiler.status(),
            "statistics": self.statistics.status(),
            "ai": self.ai.status(),
            "dashboard": self.dashboard.status(),
        }


edp = DataPlatformSuite()
