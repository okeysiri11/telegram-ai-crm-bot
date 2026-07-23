"""Judicial Intelligence Suite facade — Sprint 17.2."""

from __future__ import annotations

from typing import Any

from applications.legal_enterprise.config import DEFAULT_CONFIG
from applications.legal_enterprise.judicial_intelligence.analysis import AIJudicialAnalysis
from applications.legal_enterprise.judicial_intelligence.analytics import JudicialAnalytics
from applications.legal_enterprise.judicial_intelligence.case_law import CaseLawIntelligence
from applications.legal_enterprise.judicial_intelligence.judges import JudgeIntelligence
from applications.legal_enterprise.judicial_intelligence.repository import CourtDecisionRepository
from applications.legal_enterprise.judicial_intelligence.search import JudicialSearch
from applications.legal_enterprise.judicial_intelligence.services import JudicialDashboard, JudicialKnowledge
from applications.legal_enterprise.shared.store import LegalEnterpriseStore, legal_enterprise_store


class JudicialIntelligenceSuite:
    def __init__(self, store: LegalEnterpriseStore | None = None) -> None:
        self.store = store or legal_enterprise_store
        self.repository = CourtDecisionRepository(self.store)
        self.search = JudicialSearch(self.store)
        self.case_law = CaseLawIntelligence(self.store)
        self.judges = JudgeIntelligence(self.store)
        self.analysis = AIJudicialAnalysis(self.store)
        self.analytics = JudicialAnalytics(self.store)
        self.dashboard = JudicialDashboard(self.store)
        self.knowledge = JudicialKnowledge(self.store)

    def bootstrap(self) -> dict[str, Any]:
        judge = self.judges.register_judge(
            full_name="Hon. Morgan Ellis",
            court_name="Central Commercial Court",
            title="Presiding Judge",
            subjects=["contracts", "commercial"],
        )
        judge2 = self.judges.register_judge(
            full_name="Hon. Riley Chen",
            court_name="Court of Appeal",
            title="Appellate Judge",
            subjects=["appeals", "privacy"],
        )

        judgment = self.repository.register_judgment(
            title="LexCorp v Contoso — Final Judgment",
            decision_number="JUD-2026-100",
            case_number="CASE-2026-001",
            court_name="Central Commercial Court",
            judge_id=judge["judge_id"],
            judge_name=judge["full_name"],
            decided_on="2026-03-15",
            outcome="plaintiff_win",
            summary="Contract breach established; damages awarded.",
            body="The court finds Contoso breached the MSA.",
            participants=["LexCorp Holdings", "Contoso Trading LLC"],
            articles=["CIV-10", "CIV-11"],
            metadata={"region": "central"},
        )
        ruling = self.repository.register_ruling(
            title="Interim Evidence Ruling",
            decision_number="RUL-2026-44",
            case_number="CASE-2026-001",
            court_name="Central Commercial Court",
            judge_id=judge["judge_id"],
            judge_name=judge["full_name"],
            decided_on="2026-01-20",
            outcome="granted",
            summary="Discovery motion granted in part.",
            participants=["LexCorp Holdings", "Contoso Trading LLC"],
            articles=["CIV-10"],
            metadata={"region": "central"},
        )
        order = self.repository.register_order(
            title="Stay Order Pending Appeal",
            decision_number="ORD-2026-12",
            case_number="CASE-2026-001",
            court_name="Court of Appeal",
            judge_id=judge2["judge_id"],
            judge_name=judge2["full_name"],
            decided_on="2026-04-01",
            outcome="stay_granted",
            summary="Enforcement stayed pending appeal.",
            metadata={"region": "central"},
        )
        opinion = self.repository.register_opinion(
            title="Concurring Opinion on Damages Methodology",
            decision_number="OPN-2026-3",
            case_number="CASE-2026-001",
            court_name="Central Commercial Court",
            judge_id=judge["judge_id"],
            judge_name=judge["full_name"],
            decided_on="2026-03-15",
            outcome="concurrence",
            summary="Agrees with majority; clarifies damages formula.",
            articles=["CIV-11"],
            metadata={"region": "central"},
        )
        self.repository.record_version(
            decision_id=judgment["decision_id"], version="1.1", summary="Corrected party caption"
        )

        self.judges.record_decision(judge_id=judge["judge_id"], decision_id=judgment["decision_id"])
        self.judges.record_decision(judge_id=judge["judge_id"], decision_id=ruling["decision_id"])
        self.judges.record_decision(judge_id=judge["judge_id"], decision_id=opinion["decision_id"])
        self.judges.record_decision(judge_id=judge2["judge_id"], decision_id=order["decision_id"])
        jstat = self.judges.decision_statistics(judge_id=judge["judge_id"])
        subj = self.judges.subject_matter_analysis(judge_id=judge["judge_id"])
        work = self.judges.workload_analytics(judge_id=judge["judge_id"])

        self.case_law.classify_case(decision_id=judgment["decision_id"], label="commercial")
        self.case_law.classify_topic(decision_id=judgment["decision_id"], label="contracts")
        self.case_law.classify_case(decision_id=order["decision_id"], label="appellate")
        cite_a = self.case_law.cite_article(decision_id=judgment["decision_id"], article_ref="CIV-10")
        cite_d = self.case_law.cite_decision(
            decision_id=order["decision_id"],
            referenced_decision_id=judgment["decision_id"],
            detail="appeals final judgment",
        )
        self.case_law.relate(
            from_decision_id=ruling["decision_id"],
            to_decision_id=judgment["decision_id"],
            relation="precedes",
            detail="interim to final",
        )
        conflict = self.case_law.detect_conflict(
            decision_a=opinion["decision_id"],
            decision_b=ruling["decision_id"],
            severity="low",
            detail="damages methodology nuance",
        )

        search = self.search.semantic(query="contract breach damages", limit=5)
        self.search.decision_number(query="JUD-2026", limit=5)
        self.search.case_number(query="CASE-2026-001", limit=5)
        self.search.judge(query="Ellis", limit=5)
        self.search.court(query="Commercial", limit=5)
        self.search.participant(query="LexCorp", limit=5)
        self.search.article(query="CIV-10", limit=5)
        self.search.keyword(query="stay", limit=5)
        self.search.similar(query="breach", limit=5)

        summary = self.analysis.summarize(decision_id=judgment["decision_id"])
        self.analysis.extract_reasoning(decision_id=judgment["decision_id"])
        self.analysis.identify_legal_basis(decision_id=judgment["decision_id"])
        self.analysis.extract_key_arguments(decision_id=judgment["decision_id"])
        self.analysis.classify_outcome(decision_id=judgment["decision_id"])
        self.analysis.trend_analysis(decision_id=judgment["decision_id"])
        self.analysis.detect_pattern(decision_id=ruling["decision_id"])
        similar = self.analysis.similar_case(decision_id=judgment["decision_id"])

        timeline = self.analytics.report(kind="timeline")
        self.analytics.report(kind="regional")
        self.analytics.report(kind="court")
        self.analytics.report(kind="judge")
        self.analytics.report(kind="category")
        outcome = self.analytics.report(kind="outcome")

        self.knowledge.publish(base="decision", key=judgment["decision_id"], payload={"number": "JUD-2026-100"})
        self.knowledge.publish(base="judge", key=judge["judge_id"], payload={"name": judge["full_name"]})
        self.knowledge.publish(base="court", key="central-commercial", payload={"name": "Central Commercial Court"})
        self.knowledge.publish(base="case_law", key=cite_d["citation_id"], payload={"type": "decision"})
        self.knowledge.publish(base="judicial", key=conflict["conflict_id"], payload={"severity": "low"})

        dash = self.dashboard.render(dashboard_type="court")
        return {
            "bootstrap": True,
            "judge_id": judge["judge_id"],
            "judge2_id": judge2["judge_id"],
            "judgment_id": judgment["decision_id"],
            "ruling_id": ruling["decision_id"],
            "order_id": order["decision_id"],
            "opinion_id": opinion["decision_id"],
            "search_id": search["search_id"],
            "cite_article_id": cite_a["citation_id"],
            "cite_decision_id": cite_d["citation_id"],
            "conflict_id": conflict["conflict_id"],
            "summary_id": summary["analysis_id"],
            "similar_id": similar["analysis_id"],
            "judge_stat_id": jstat["stat_id"],
            "subject_id": subj["analysis_id"],
            "workload_id": work["workload_id"],
            "timeline_id": timeline["report_id"],
            "outcome_report_id": outcome["report_id"],
            "dashboard_id": dash["dashboard_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "repository": self.repository.status(),
            "search": self.search.status(),
            "case_law": self.case_law.status(),
            "judges": self.judges.status(),
            "analysis": self.analysis.status(),
            "analytics": self.analytics.status(),
            "knowledge": self.knowledge.status(),
            "dashboard": self.dashboard.status(),
        }


judicial_intelligence = JudicialIntelligenceSuite()
