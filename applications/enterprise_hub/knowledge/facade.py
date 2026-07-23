"""Unified Knowledge Suite facade — Sprint 19.2."""

from __future__ import annotations

from typing import Any

from applications.enterprise_hub.config import DEFAULT_CONFIG
from applications.enterprise_hub.knowledge.ai_intel import KnowledgeAI
from applications.enterprise_hub.knowledge.context import CrossPlatformContext
from applications.enterprise_hub.knowledge.graph import UnifiedKnowledgeGraph
from applications.enterprise_hub.knowledge.memory import AIMemory
from applications.enterprise_hub.knowledge.semantic import SemanticIntelligence
from applications.enterprise_hub.knowledge.services import (
    UnifiedKnowledgeDashboard,
    UnifiedKnowledgeMeta,
)
from applications.enterprise_hub.knowledge.sync import KnowledgeSynchronization
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


class UnifiedKnowledgeSuite:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store
        self.graph = UnifiedKnowledgeGraph(self.store)
        self.memory = AIMemory(self.store)
        self.semantic = SemanticIntelligence(self.store)
        self.context = CrossPlatformContext(self.store)
        self.ai = KnowledgeAI(self.store)
        self.sync = KnowledgeSynchronization(self.store)
        self.meta = UnifiedKnowledgeMeta(self.store)
        self.dashboard = UnifiedKnowledgeDashboard(self.store)

    def bootstrap(self) -> dict[str, Any]:
        person = self.graph.register_entity(name="Alex CFO", entity_type="person", platform="finance")
        org = self.graph.register_entity(name="Bidex Holdings", entity_type="organization")
        cust = self.graph.register_entity(name="Acme Trading", entity_type="customer", platform="finance")
        supp = self.graph.register_entity(name="Global Supplies", entity_type="supplier", platform="agro")
        partner = self.graph.register_entity(name="Port Partner LLC", entity_type="partner", platform="port")
        asset = self.graph.register_entity(name="Warehouse A", entity_type="asset", platform="agro")
        vehicle = self.graph.register_entity(name="VIN-1001", entity_type="vehicle", platform="automotive")
        contract = self.graph.register_entity(name="CTR-2026-01", entity_type="contract", platform="legal")
        invoice = self.graph.register_entity(name="INV-9001", entity_type="invoice", platform="finance")
        case = self.graph.register_entity(name="CASE-88", entity_type="case", platform="legal")
        crypto = self.graph.register_entity(name="USDT Vault", entity_type="crypto_asset", platform="crypto")

        rel1 = self.graph.relate(
            from_entity_id=person["entity_id"],
            to_entity_id=org["entity_id"],
            relation="works_for",
        )
        rel2 = self.graph.relate(
            from_entity_id=invoice["entity_id"],
            to_entity_id=cust["entity_id"],
            relation="billed_to",
        )
        rel3 = self.graph.relate(
            from_entity_id=contract["entity_id"],
            to_entity_id=partner["entity_id"],
            relation="covers",
        )
        graph = self.graph.build_graph(label="enterprise_master")
        link = self.graph.link_cross_platform(
            entity_id=invoice["entity_id"], platform="finance", external_id="bil_inv_seed"
        )
        ont = self.graph.register_ontology(
            name="Enterprise Core Ontology",
            concepts=["person", "organization", "asset", "contract", "invoice"],
        )
        ver = self.graph.version_graph(graph_id=graph["graph_id"], note="bootstrap snapshot")

        mem_lt = self.memory.remember(
            memory_type="long_term", subject="Bidex", content="Group operates across six verticals"
        )
        mem_conv = self.memory.remember(
            memory_type="conversation", subject="cfo_chat", content="Asked about Q2 liquidity"
        )
        mem_biz = self.memory.remember(
            memory_type="business", subject="margin", content="Gross margin target 42%"
        )
        mem_proj = self.memory.remember(
            memory_type="project", subject="hub_rollout", content="Sprint 19 knowledge graph"
        )
        mem_dec = self.memory.remember(
            memory_type="decision", subject="cash_pool", content="Approved enterprise cash pooling"
        )
        mem_wf = self.memory.remember(
            memory_type="workflow", subject="settlement", content="Sequential settlement template"
        )

        sem_search = self.semantic.operate(operation="semantic_search", query="Bidex")
        sem_res = self.semantic.operate(operation="entity_resolution", query="Acme Trading")
        sem_dup = self.semantic.operate(operation="duplicate_detection", query="Acme")
        sem_inf = self.semantic.operate(operation="knowledge_inference", query="invoice customer")
        sem_rel = self.semantic.operate(operation="relationship_discovery", query="works_for")
        sem_ctx = self.semantic.operate(operation="context_expansion", query="finance")
        sem_sim = self.semantic.operate(operation="similarity_analysis", query="partner")

        ctx_auto = self.context.attach(context_type="automotive", subject=vehicle["entity_id"])
        ctx_agro = self.context.attach(context_type="agro", subject=asset["entity_id"])
        ctx_port = self.context.attach(context_type="port", subject=partner["entity_id"])
        ctx_cry = self.context.attach(context_type="crypto", subject=crypto["entity_id"])
        ctx_leg = self.context.attach(context_type="legal", subject=case["entity_id"])
        ctx_fin = self.context.attach(context_type="finance", subject=invoice["entity_id"])
        ctx_uni = self.context.attach(
            context_type="unified",
            subject=org["entity_id"],
            payload={"verticals": 6},
        )

        ai_rec = self.ai.insight(insight_type="recommendation", subject="link supplier to agro warehouse")
        ai_reas = self.ai.insight(insight_type="context_reasoning", subject="invoice settlement path")
        ai_corr = self.ai.insight(insight_type="cross_platform_correlation", subject="port+finance billing")
        ai_ins = self.ai.insight(insight_type="business_insight", subject="customer concentration")
        ai_pred = self.ai.insight(insight_type="predictive", subject="working capital")
        ai_nl = self.ai.nl_query(question="What entities relate to Bidex Holdings?", audience="cfo")

        sync_fin = self.sync.sync(platform="finance", mode="incremental", changes=12)
        sync_leg = self.sync.sync(platform="legal", mode="incremental", changes=4)
        conf = self.sync.conflict(entity_ref=cust["entity_id"], detail="name variance")
        res = self.sync.resolve(conflict_id=conf["conflict_id"], resolution="keep_hub")
        aud = self.sync.audit(action="bootstrap", actor="system", detail="Sprint 19.2 seed")
        mon = self.sync.monitor()

        self.meta.publish(base="master", key=graph["graph_id"], payload={"label": "enterprise_master"})
        self.meta.publish(base="ontology", key=ont["ontology_id"], payload={"name": ont["name"]})
        self.meta.publish(base="memory", key=mem_lt["memory_id"], payload={"type": "long_term"})
        self.meta.publish(base="entity", key=org["entity_id"], payload={"name": org["name"]})
        self.meta.publish(base="relationship", key=rel1["relationship_id"], payload={"relation": "works_for"})

        dash_k = self.dashboard.render(dashboard_type="knowledge")
        dash_e = self.dashboard.render(dashboard_type="entity")
        dash_r = self.dashboard.render(dashboard_type="relationship")
        dash_m = self.dashboard.render(dashboard_type="ai_memory")
        dash_s = self.dashboard.render(dashboard_type="semantic")

        return {
            "bootstrap": True,
            "person_id": person["entity_id"],
            "organization_id": org["entity_id"],
            "customer_id": cust["entity_id"],
            "supplier_id": supp["entity_id"],
            "partner_id": partner["entity_id"],
            "asset_id": asset["entity_id"],
            "vehicle_id": vehicle["entity_id"],
            "contract_id": contract["entity_id"],
            "invoice_id": invoice["entity_id"],
            "case_id": case["entity_id"],
            "crypto_asset_id": crypto["entity_id"],
            "relationship_id": rel1["relationship_id"],
            "relationship_invoice_id": rel2["relationship_id"],
            "relationship_contract_id": rel3["relationship_id"],
            "graph_id": graph["graph_id"],
            "link_id": link["link_id"],
            "ontology_id": ont["ontology_id"],
            "version_id": ver["version_id"],
            "memory_long_term_id": mem_lt["memory_id"],
            "memory_conversation_id": mem_conv["memory_id"],
            "memory_business_id": mem_biz["memory_id"],
            "memory_project_id": mem_proj["memory_id"],
            "memory_decision_id": mem_dec["memory_id"],
            "memory_workflow_id": mem_wf["memory_id"],
            "semantic_search_id": sem_search["semantic_id"],
            "semantic_resolution_id": sem_res["semantic_id"],
            "semantic_duplicate_id": sem_dup["semantic_id"],
            "semantic_inference_id": sem_inf["semantic_id"],
            "semantic_relationship_id": sem_rel["semantic_id"],
            "semantic_context_id": sem_ctx["semantic_id"],
            "semantic_similarity_id": sem_sim["semantic_id"],
            "context_automotive_id": ctx_auto["context_id"],
            "context_agro_id": ctx_agro["context_id"],
            "context_port_id": ctx_port["context_id"],
            "context_crypto_id": ctx_cry["context_id"],
            "context_legal_id": ctx_leg["context_id"],
            "context_finance_id": ctx_fin["context_id"],
            "context_unified_id": ctx_uni["context_id"],
            "ai_recommendation_id": ai_rec["insight_id"],
            "ai_reasoning_id": ai_reas["insight_id"],
            "ai_correlation_id": ai_corr["insight_id"],
            "ai_insight_id": ai_ins["insight_id"],
            "ai_predictive_id": ai_pred["insight_id"],
            "ai_nl_id": ai_nl["insight_id"],
            "sync_finance_id": sync_fin["sync_id"],
            "sync_legal_id": sync_leg["sync_id"],
            "conflict_id": conf["conflict_id"],
            "resolution_id": res["resolution_id"],
            "audit_id": aud["audit_id"],
            "monitor_id": mon["monitor_id"],
            "dashboard_knowledge_id": dash_k["dashboard_id"],
            "dashboard_entity_id": dash_e["dashboard_id"],
            "dashboard_relationship_id": dash_r["dashboard_id"],
            "dashboard_memory_id": dash_m["dashboard_id"],
            "dashboard_semantic_id": dash_s["dashboard_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "graph": self.graph.status(),
            "memory": self.memory.status(),
            "semantic": self.semantic.status(),
            "context": self.context.status(),
            "ai": self.ai.status(),
            "sync": self.sync.status(),
            "meta": self.meta.status(),
            "dashboard": self.dashboard.status(),
        }


unified_knowledge = UnifiedKnowledgeSuite()
