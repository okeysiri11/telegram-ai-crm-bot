"""Product Intelligence library facade — Sprint 22.0."""

from __future__ import annotations

from typing import Any

from platform_product_intelligence.analysis import AnalysisEngine
from platform_product_intelligence.approval import OwnerApprovalCenter
from platform_product_intelligence.experts import ExpertBoard
from platform_product_intelligence.feedback import FeedbackCollector
from platform_product_intelligence.knowledge import DecisionKnowledgeBase
from platform_product_intelligence.models import INTEGRATION_TARGETS, PRINCIPLES
from platform_product_intelligence.pipeline import DevelopmentPipeline
from platform_product_intelligence.reports import DecisionReportGenerator
from platform_product_intelligence.validation import ReleaseValidation


class ProductIntelligenceLibrary:
    def __init__(self) -> None:
        self.feedback = FeedbackCollector()
        self.analysis = AnalysisEngine()
        self.experts = ExpertBoard()
        self.reports = DecisionReportGenerator()
        self.approval = OwnerApprovalCenter()
        self.pipeline = DevelopmentPipeline()
        self.validation = ReleaseValidation()
        self.knowledge = DecisionKnowledgeBase()

    def integrations(self) -> dict[str, Any]:
        return {"targets": list(INTEGRATION_TARGETS), "linked": True, "universal_intake": True}

    def principles(self) -> list[str]:
        return list(PRINCIPLES)

    def bootstrap(self) -> dict[str, Any]:
        self.__init__()
        samples = [
            self.feedback.normalize(
                source="user_feedback",
                title="Need unified product decision center",
                module="enterprise_hub",
            ),
            self.feedback.normalize(
                source="support",
                title="Need unified product decision center",
                module="enterprise_hub",
            ),
            self.feedback.normalize(
                source="suggestion",
                title="Expose intake API for all modules",
                module="event_platform",
            ),
        ]
        analysis = self.analysis.analyze(samples, history=self.knowledge.history())
        board = self.experts.evaluate(
            problem="Fragmented product decisions across modules",
            proposal="Introduce Enterprise Product Intelligence as mandatory decision center",
        )
        report = self.reports.generate(
            problem="Fragmented product decisions across modules",
            proposal="Introduce Enterprise Product Intelligence as mandatory decision center",
            analysis=analysis,
            expert_board=board,
        )
        owner = self.approval.decide(
            decision="approve",
            owner_id="platform_owner",
            notes="Foundation approval for Sprint 22.0",
        )
        pipeline = self.pipeline.create(report=report, approval=owner)
        validation = self.validation.validate(expected_kpi=report["kpi"])
        kb = self.knowledge.record(
            {
                "discussion": samples,
                "ai_conclusions": report["expert_conclusions"],
                "owner_decision": owner,
                "implementation_results": pipeline,
                "effectiveness": validation,
                "report_id": "bootstrap",
                "decision_id": "bootstrap",
            }
        )
        return {
            "bootstrap": True,
            "principles": self.principles(),
            "feedback_sources": self.feedback.sources(),
            "feedback_ingested": len(samples),
            "analysis_passed": analysis["passed"],
            "expert_consensus": board["consensus"],
            "report_ready": True,
            "owner_decision": owner["decision"],
            "development_allowed": owner["development_allowed"],
            "pipeline_artifacts": pipeline["count"],
            "validation_passed": validation["passed"],
            "knowledge_entries": kb["history_size"],
            "ai_never_modifies_system": True,
            "universal_intake": True,
            "status": "ready",
            "integrations": self.integrations(),
            "full": {
                "samples": samples,
                "analysis": analysis,
                "board": board,
                "report": report,
                "owner": owner,
                "pipeline": pipeline,
                "validation": validation,
                "knowledge": kb,
            },
        }

    def status(self) -> dict[str, Any]:
        return {
            "knowledge": self.knowledge.status(),
            "components": [
                "feedback",
                "analysis",
                "experts",
                "reports",
                "approval",
                "pipeline",
                "validation",
                "knowledge",
            ],
            "principles": self.principles(),
        }


product_intelligence_library = ProductIntelligenceLibrary()
