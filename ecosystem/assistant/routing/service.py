# AI routing — intent detection and multi-target routing.

from __future__ import annotations

from events.publisher import publish

from ecosystem.assistant.events import AgentRoutedEvent, IntentDetectedEvent
from ecosystem.assistant.models import IntentType, RouteTarget, RoutingDecision
from ecosystem.config import DEFAULT_CONFIG
from ecosystem.shared.store import EcosystemStore, ecosystem_store


INTENT_KEYWORDS: dict[IntentType, list[str]] = {
    IntentType.KNOWLEDGE: ["what is", "explain", "knowledge", "define", "tell me about"],
    IntentType.WORKFLOW: ["workflow", "process", "pipeline", "onboard", "approve"],
    IntentType.TOOL: ["search", "lookup", "calculate", "fetch", "tool"],
    IntentType.AGENT: ["agent", "negotiate", "qualify", "recommend", "assist"],
    IntentType.TASK: ["plan", "do", "complete", "task", "help me"],
    IntentType.APPLICATION: ["marketplace", "vehicle", "crm", "finance", "dealer", "portal"],
}


class AIRouter:
    def __init__(self, store: EcosystemStore | None = None) -> None:
        self._store = store or ecosystem_store

    def detect_intent(self, message: str, *, application_id: str = "") -> RoutingDecision:
        text = message.lower().strip()
        best = IntentType.GENERAL
        best_score = 0.0
        label = "general"
        for intent, keywords in INTENT_KEYWORDS.items():
            score = sum(1.0 for kw in keywords if kw in text)
            if application_id and intent == IntentType.APPLICATION:
                score += 0.5
            if score > best_score:
                best_score = score
                best = intent
                label = intent.value

        confidence = min(1.0, best_score / 3.0) if best_score else 0.2
        decision = RoutingDecision(
            intent=best,
            intent_label=label,
            confidence=confidence,
            application_id=application_id,
        )
        self._apply_routing(decision, text, application_id)
        self._store.routing_decisions.save(decision.decision_id, decision)
        return decision

    def _apply_routing(self, decision: RoutingDecision, text: str, application_id: str) -> None:
        apps = list(DEFAULT_CONFIG.registered_applications)
        if decision.intent == IntentType.APPLICATION or any(a.replace("_", " ") in text or a in text for a in apps):
            decision.target_type = RouteTarget.APPLICATION
            decision.application_id = application_id or "auto_marketplace"
            decision.target_id = decision.application_id
            decision.priority = 20
        elif decision.intent == IntentType.AGENT:
            decision.target_type = RouteTarget.AGENT
            decision.agent_id = "ecosystem-agent"
            decision.target_id = decision.agent_id
            decision.priority = 30
        elif decision.intent == IntentType.TOOL:
            decision.target_type = RouteTarget.TOOL
            decision.tool_id = "search_knowledge"
            decision.target_id = decision.tool_id
            decision.priority = 40
        elif decision.intent == IntentType.WORKFLOW:
            decision.target_type = RouteTarget.WORKFLOW
            decision.workflow_id = "generic_workflow"
            decision.target_id = decision.workflow_id
            decision.priority = 50
        elif decision.intent == IntentType.KNOWLEDGE:
            decision.target_type = RouteTarget.TOOL
            decision.tool_id = "search_knowledge"
            decision.target_id = "search_knowledge"
            decision.priority = 35
        else:
            decision.target_type = RouteTarget.FALLBACK
            decision.fallback_used = True
            decision.priority = 100
            if application_id:
                decision.application_id = application_id

    async def route(
        self,
        user_id: str,
        message: str,
        *,
        application_id: str = "",
    ) -> RoutingDecision:
        decision = self.detect_intent(message, application_id=application_id)
        await publish(
            IntentDetectedEvent(
                user_id=user_id,
                intent=decision.intent.value,
                confidence=decision.confidence,
                intent_label=decision.intent_label,
            )
        )
        if decision.target_type == RouteTarget.AGENT:
            await publish(
                AgentRoutedEvent(
                    user_id=user_id,
                    agent_id=decision.agent_id,
                    intent=decision.intent.value,
                    application_id=decision.application_id,
                )
            )
        return decision

    def prioritize(self, decisions: list[RoutingDecision]) -> RoutingDecision:
        if not decisions:
            return RoutingDecision(fallback_used=True, target_type=RouteTarget.FALLBACK)
        return sorted(decisions, key=lambda d: (d.priority, -d.confidence))[0]


ai_router = AIRouter()
