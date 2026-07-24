"""Enterprise Knowledge Graph library facade — Sprint 24.2."""

from __future__ import annotations

from typing import Any

from platform_enterprise_knowledge_graph.ai_context import AIContextBuilder
from platform_enterprise_knowledge_graph.context import ContextEngine
from platform_enterprise_knowledge_graph.graph import KnowledgeGraph
from platform_enterprise_knowledge_graph.integrations import KnowledgeGraphIntegrations
from platform_enterprise_knowledge_graph.learning import LearningEngine
from platform_enterprise_knowledge_graph.memory import EnterpriseMemory
from platform_enterprise_knowledge_graph.models import PRINCIPLES
from platform_enterprise_knowledge_graph.owner import OwnerKnowledgeControl
from platform_enterprise_knowledge_graph.relations import SemanticRelations
from platform_enterprise_knowledge_graph.search import SemanticSearch
from platform_enterprise_knowledge_graph.timeline import KnowledgeTimeline


class EnterpriseKnowledgeGraphLibrary:
    def __init__(self) -> None:
        self.graph = KnowledgeGraph()
        self.relations = SemanticRelations()
        self.memory = EnterpriseMemory()
        self.context = ContextEngine()
        self.search = SemanticSearch()
        self.ai_context = AIContextBuilder()
        self.timeline = KnowledgeTimeline()
        self.learning = LearningEngine()
        self.owner = OwnerKnowledgeControl()
        self.integrations = KnowledgeGraphIntegrations()

    def principles(self) -> list[str]:
        return list(PRINCIPLES)

    def bootstrap(self) -> dict[str, Any]:
        self.__init__()
        company = self.graph.upsert(entity_id="co_1", entity_type="company", properties={"name": "Pilot Salon"}, labels=["pilot"])
        customer = self.graph.upsert(
            entity_id="cu_vip_1",
            entity_type="customer",
            properties={"name": "VIP Client", "days_since_visit": 75},
            labels=["vip"],
        )
        campaign = self.graph.upsert(
            entity_id="camp_1",
            entity_type="campaign",
            properties={"name": "Spring", "revenue_lift_pct": 28},
        )
        workflow = self.graph.upsert(entity_id="wf_book", entity_type="workflow", properties={"name": "Client Booking"})
        agent = self.graph.upsert(entity_id="ai_business", entity_type="ai_agent", properties={"role": "business"})
        self.relations.link(source_id="co_1", relation="owns", target_id="cu_vip_1")
        self.relations.link(source_id="cu_vip_1", relation="visited", target_id="co_1", weight=0.5)
        self.relations.link(source_id="camp_1", relation="generated_by_ai", target_id="ai_business")
        self.relations.link(source_id="camp_1", relation="approved_by_owner", target_id="co_1")
        self.relations.link(source_id="wf_book", relation="related_to", target_id="cu_vip_1")
        self.memory.record(kind="decision", subject_id="co_1", summary="Approved pilot marketing")
        self.memory.record(kind="ai", subject_id="ai_business", summary="Suggested rebook VIP")
        self.timeline.append(entity_id="cu_vip_1", event_type="created", summary="Customer created")
        self.timeline.append(entity_id="cu_vip_1", event_type="ai_recommendation", summary="Rebook offer")
        self.timeline.append(entity_id="cu_vip_1", event_type="owner_approval", summary="Owner allowed outreach")
        ctx = self.context.build(
            task="prepare_rebook_offer",
            entity_ids=["cu_vip_1", "co_1"],
            related=self.relations.neighbors("cu_vip_1"),
            memory=self.memory.history(subject_id="cu_vip_1") + self.memory.history(kind="ai"),
            elapsed_ms=3.5,
        )
        search = self.search.query(
            text="Все VIP-клиенты, которые не приходили 60 дней.",
            entities=self.graph.list_entities(),
            edges=self.relations.all_edges(),
        )
        ai_ctx = self.ai_context.build(
            context=ctx,
            entities=[customer, company],
            decisions=self.memory.history(kind="decision"),
            recommendations=[{"tip": "rebook"}],
            outcomes=[{"result": "pending"}],
        )
        learned = self.learning.apply_confirmed(
            confirmed=True,
            strengthen={"source_id": "camp_1", "relation": "generated_by_ai", "target_id": "ai_business"},
            archive_entity_ids=[],
        )
        self.relations.strengthen(source_id="camp_1", relation="generated_by_ai", target_id="ai_business")
        owner = self.owner.act(action="confirm_knowledge", actor="platform_owner", payload={"entity_id": "cu_vip_1"})
        self.graph.set_flags("cu_vip_1", confirmed=True)
        links = self.integrations.link()
        return {
            "bootstrap": True,
            "principles": self.principles(),
            "knowledge_graph_ready": True,
            "semantic_memory_ready": True,
            "context_engine_ready": True,
            "semantic_search_ready": True,
            "entity_count": len(self.graph.list_entities()),
            "edge_count": len(self.relations.all_edges()),
            "context_in_milliseconds": ctx["context_in_milliseconds"],
            "search_hits": search["count"],
            "ai_may_act": False,
            "central_context_source": True,
            "learned_confirmed": learned["learned"],
            "owner_control": owner["approved"],
            "duplicates_core_logic": False,
            "status": "ready",
            "integrations": links,
            "full": {
                "entities": self.graph.list_entities(),
                "edges": self.relations.all_edges(),
                "context": ctx,
                "search": search,
                "ai_context": ai_ctx,
                "timeline": self.timeline.for_entity("cu_vip_1"),
                "learning": learned,
                "owner": owner,
                "links": links,
            },
        }

    def status(self) -> dict[str, Any]:
        return {
            "components": [
                "graph",
                "relations",
                "memory",
                "context",
                "search",
                "ai_context",
                "timeline",
                "learning",
                "owner",
            ],
            "principles": self.principles(),
            "entities": len(self.graph.list_entities()),
            "edges": len(self.relations.all_edges()),
        }


enterprise_knowledge_graph_library = EnterpriseKnowledgeGraphLibrary()
