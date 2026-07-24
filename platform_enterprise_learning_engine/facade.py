"""Learning Engine library facade — Sprint 24.8."""

from __future__ import annotations

from typing import Any

from platform_enterprise_learning_engine.collector import KnowledgeCollector
from platform_enterprise_learning_engine.cross_tenant import CrossTenantLearning
from platform_enterprise_learning_engine.dashboard import ContinuousImprovementDashboard
from platform_enterprise_learning_engine.evolution import RecommendationEvolution
from platform_enterprise_learning_engine.feedback import FeedbackIntelligence
from platform_enterprise_learning_engine.integrations import LearningIntegrations
from platform_enterprise_learning_engine.models import PRINCIPLES
from platform_enterprise_learning_engine.owner import OwnerLearningDecision
from platform_enterprise_learning_engine.patterns import PatternDetectionEngine
from platform_enterprise_learning_engine.product import ProductEvolution
from platform_enterprise_learning_engine.registry import LearningRegistry
from platform_enterprise_learning_engine.safety import AISafety
from platform_enterprise_learning_engine.score import LearningScore


class LearningEngineLibrary:
    def __init__(self) -> None:
        self.registry = LearningRegistry()
        self.collector = KnowledgeCollector()
        self.feedback = FeedbackIntelligence()
        self.patterns = PatternDetectionEngine()
        self.cross_tenant = CrossTenantLearning()
        self.evolution = RecommendationEvolution()
        self.score = LearningScore()
        self.dashboard = ContinuousImprovementDashboard()
        self.product = ProductEvolution()
        self.owner = OwnerLearningDecision()
        self.safety = AISafety()
        self.integrations = LearningIntegrations()

    def principles(self) -> list[str]:
        return list(PRINCIPLES)

    def bootstrap(self) -> dict[str, Any]:
        self.__init__()
        collected = self.collector.collect(
            events=[
                {"source": "commerce", "confirmed": True, "kind": "success"},
                {"source": "crm", "confirmed": False, "kind": "error"},
                {"source": "marketing_os", "confirmed": True, "kind": "best_practice"},
            ]
        )
        record = self.registry.create(
            learning_id="lrn_best_rebook",
            source="commerce",
            tenant="tenant_demo",
            module="commerce_core",
            knowledge_type="best_practice",
            trust_level=0.8,
            author="ops",
            payload={"pattern": "rebook_within_7d"},
            confirmed=True,
        )
        fb = self.feedback.classify(text="Great success case with rebooking")
        patterns = self.patterns.detect(
            items=[
                {"kind": "success"},
                {"kind": "success"},
                {"kind": "error"},
                {"kind": "error"},
                {"kind": "profit"},
                {"kind": "profit"},
            ]
        )
        cross = self.cross_tenant.aggregate(
            anonymized_signals=[
                {"pattern": "rebook_within_7d", "anonymized": True},
                {"pattern": "rebook_within_7d", "anonymized": True},
                {"pattern": "upsell_package", "anonymized": True},
            ]
        )
        evo = self.evolution.evolve(
            past_success_rate=0.7,
            acceptance_rate=0.6,
            completion_rate=0.55,
            outcome_score=0.65,
            industry="beauty",
        )
        score = self.score.score(
            agent_id="business_ai",
            accuracy=0.8,
            usefulness=0.75,
            accepted_advice_pct=0.6,
            successful_implementations_pct=0.55,
            user_trust=0.7,
        )
        record = self.registry.set_status(record, status="awaiting_owner")
        decision = self.owner.decide(action="approve", actor="platform_owner", learning_id=record["learning_id"])
        product = self.product.push(improvement="Add rebook reminder template", confirmed=True)
        blocked = self.safety.enforce(intent="modify_algorithms")
        dash = self.dashboard.render(
            learned=["rebook_within_7d"],
            improved=["upsell_timing"],
            degraded=[],
            awaiting_confirmation=[],
            rejected=["unconfirmed_crm_error"],
        )
        links = self.integrations.link()
        return {
            "bootstrap": True,
            "principles": self.principles(),
            "learning_engine_ready": True,
            "confirmed_learning_ready": True,
            "cross_tenant_learning_ready": True,
            "owner_learning_ready": True,
            "ai_may_act": False,
            "autonomous_learn": False,
            "confirmed_only": True,
            "pii_transferred": False,
            "may_change_algorithms": False,
            "duplicates_core_logic": False,
            "status": "ready",
            "integrations": links,
            "full": {
                "collected": collected,
                "record": record,
                "feedback": fb,
                "patterns": patterns,
                "cross_tenant": cross,
                "evolution": evo,
                "score": score,
                "decision": decision,
                "product": product,
                "safety_blocked": blocked,
                "dashboard": dash,
                "links": links,
            },
        }

    def status(self) -> dict[str, Any]:
        return {
            "components": [
                "registry",
                "collector",
                "feedback",
                "patterns",
                "cross_tenant",
                "evolution",
                "score",
                "dashboard",
                "product",
                "owner",
                "safety",
            ],
            "principles": self.principles(),
            "confirmed_only": True,
        }


learning_engine_library = LearningEngineLibrary()
