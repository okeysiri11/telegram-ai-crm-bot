"""AI Legal Assistant Suite facade — Sprint 17.6."""

from __future__ import annotations

from typing import Any

from applications.legal_enterprise.ai_legal_assistant.analysis import LegalAnalysisEngine
from applications.legal_enterprise.ai_legal_assistant.assistant import LegalAssistant
from applications.legal_enterprise.ai_legal_assistant.document_bridge import DocumentBridge
from applications.legal_enterprise.ai_legal_assistant.explainability import AIExplainability
from applications.legal_enterprise.ai_legal_assistant.knowledge_intel import KnowledgeIntelligence
from applications.legal_enterprise.ai_legal_assistant.opinions import LegalOpinionSupport
from applications.legal_enterprise.ai_legal_assistant.research import LegalResearchEngine
from applications.legal_enterprise.ai_legal_assistant.services import AILegalAssistantDashboard
from applications.legal_enterprise.config import DEFAULT_CONFIG
from applications.legal_enterprise.shared.store import LegalEnterpriseStore, legal_enterprise_store


class AILegalAssistantSuite:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store
        self.assistant = LegalAssistant(self.store)
        self.research = LegalResearchEngine(self.store)
        self.analysis = LegalAnalysisEngine(self.store)
        self.opinions = LegalOpinionSupport(self.store)
        self.documents = DocumentBridge(self.store)
        self.knowledge = KnowledgeIntelligence(self.store)
        self.explainability = AIExplainability(self.store)
        self.dashboard = AILegalAssistantDashboard(self.store)

    def bootstrap(self) -> dict[str, Any]:
        ws = self.assistant.create_workspace(name="Lex Research Desk", owner="GC")
        conv = self.assistant.start_conversation(
            workspace_id=ws["workspace_id"], title="Breach of contract consultation"
        )
        qa = self.assistant.ask(
            question="What remedies are available for material breach of an MSA?",
            conversation_id=conv["conversation_id"],
            context={"matter": "MSA-1"},
        )
        self.assistant.chat(
            conversation_id=conv["conversation_id"],
            message="Also consider force majeure defenses.",
        )
        self.assistant.remember(
            conversation_id=conv["conversation_id"], key="matter_ref", value="MSA-1"
        )

        semantic = self.research.semantic(query="material breach remedies")
        multi = self.research.multi_source(query="force majeure commercial contracts")
        statute = self.research.statute(query="Civil Code damages")
        cases = self.research.case_law(query="anticipatory breach")
        docs = self.research.document(query="MSA limitation of liability")
        xref = self.research.cross_reference(query="Art. 10 damages")
        cite = self.research.cite(authority="Civil Code Art. 10", citation_type="statute")
        related = self.research.related_authorities(authority="Civil Code Art. 10")

        issues = self.analysis.identify_issues(query="MSA material breach")
        law = self.analysis.applicable_law(query="commercial MSA breach")
        articles = self.analysis.extract_articles(query="damages calculation")
        corr = self.analysis.correlate_case_law(query="material breach")
        conflict = self.analysis.detect_conflicts(query="soft-law vs statute on liability caps")
        args = self.analysis.map_arguments(query="breach claim defenses")
        reasoning = self.analysis.reason(query="Is termination for cause supportable?")

        opinion = self.opinions.draft_opinion(
            issue="Material breach remedies under MSA-1",
            conclusion="Termination and damages are supportable subject to notice provisions.",
            authorities=["Civil Code Art. 10", "JUD-2026-100"],
            notes="Force majeure unlikely on these facts.",
        )

        contract = self.documents.analyze_document(
            action="contract_analysis", document_ref="MSA-1", detail="liability and termination"
        )
        evidence = self.documents.analyze_document(
            action="evidence_review", document_ref="EMAIL-BUNDLE-9"
        )
        interp = self.documents.analyze_document(
            action="interpretation", document_ref="MSA-1 §4"
        )
        compl = self.documents.analyze_document(
            action="compliance_verification", document_ref="MSA-1"
        )
        risk = self.documents.analyze_document(
            action="risk_correlation", document_ref="MSA-1"
        )
        xdoc = self.documents.analyze_document(
            action="cross_document", document_ref="MSA-1+SOW-2"
        )

        nav = self.knowledge.navigate(from_node="material_breach")
        concept = self.knowledge.map_concept(concept="material_breach")
        rel = self.knowledge.discover_relationship(
            from_entity="Civil Code Art. 10", to_entity="JUD-2026-100", relation="applied_in"
        )
        term = self.knowledge.terminology(term="material breach")
        entity = self.knowledge.resolve_entity(name="civil code art. 10", entity_type="statute")
        self.knowledge.publish(base="assistant", key=conv["conversation_id"], payload={"title": conv["title"]})
        self.knowledge.publish(base="research", key=semantic["search_id"], payload={"query": semantic["query"]})
        self.knowledge.publish(base="opinion", key=opinion["opinion_id"], payload={"issue": opinion["issue"]})
        self.knowledge.publish(base="authority", key=cite["citation_id"], payload={"authority": cite["authority"]})
        self.knowledge.publish(
            base="reasoning", key=reasoning["analysis_id"], payload={"kind": reasoning["kind"]}
        )

        explanation = self.explainability.explain(
            subject="MSA material breach remedies",
            reasoning_steps=["Issue", "Authorities", "Facts", "Conclusion"],
            confidence=0.86,
            citations=["Civil Code Art. 10", "JUD-2026-100"],
        )

        dash_a = self.dashboard.render(dashboard_type="assistant")
        dash_r = self.dashboard.render(dashboard_type="research")
        dash_k = self.dashboard.render(dashboard_type="knowledge")
        dash_i = self.dashboard.render(dashboard_type="intelligence")

        return {
            "bootstrap": True,
            "workspace_id": ws["workspace_id"],
            "conversation_id": conv["conversation_id"],
            "message_id": qa["message_id"],
            "semantic_id": semantic["search_id"],
            "multi_id": multi["search_id"],
            "statute_id": statute["search_id"],
            "case_law_id": cases["search_id"],
            "document_search_id": docs["search_id"],
            "xref_id": xref["search_id"],
            "citation_id": cite["citation_id"],
            "authority_id": related["authority_id"],
            "issue_id": issues["analysis_id"],
            "law_id": law["analysis_id"],
            "article_id": articles["analysis_id"],
            "correlation_id": corr["analysis_id"],
            "conflict_id": conflict["analysis_id"],
            "argument_id": args["analysis_id"],
            "reasoning_id": reasoning["analysis_id"],
            "opinion_id": opinion["opinion_id"],
            "contract_id": contract["analysis_id"],
            "evidence_id": evidence["analysis_id"],
            "interpretation_id": interp["analysis_id"],
            "compliance_id": compl["analysis_id"],
            "risk_id": risk["analysis_id"],
            "cross_doc_id": xdoc["analysis_id"],
            "nav_id": nav["nav_id"],
            "concept_id": concept["concept_id"],
            "relationship_id": rel["relationship_id"],
            "term_id": term["term_id"],
            "entity_id": entity["entity_id"],
            "explanation_id": explanation["explanation_id"],
            "dashboard_assistant_id": dash_a["dashboard_id"],
            "dashboard_research_id": dash_r["dashboard_id"],
            "dashboard_knowledge_id": dash_k["dashboard_id"],
            "dashboard_intelligence_id": dash_i["dashboard_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "assistant": self.assistant.status(),
            "research": self.research.status(),
            "analysis": self.analysis.status(),
            "opinions": self.opinions.status(),
            "documents": self.documents.status(),
            "knowledge": self.knowledge.status(),
            "explainability": self.explainability.status(),
            "dashboard": self.dashboard.status(),
        }


ai_legal_assistant = AILegalAssistantSuite()
