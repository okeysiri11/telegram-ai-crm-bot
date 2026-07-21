# Unified AI Assistant engine — planning, orchestration, conversational interface.

from __future__ import annotations

import logging
from typing import Any

from events.publisher import publish

from ecosystem.assistant.context.service import ContextEngine, context_engine
from ecosystem.assistant.conversation.service import ConversationService, conversation_service
from ecosystem.assistant.events import AssistantInvokedEvent, TaskCompletedEvent
from ecosystem.assistant.global_memory.service import GlobalMemory, global_memory
from ecosystem.assistant.knowledge_graph.service import KnowledgeGraph, knowledge_graph
from ecosystem.assistant.models import AssistantResponse, IntentType, RouteTarget, SkillType, TaskPlan
from ecosystem.assistant.prompts.templates import render_prompt
from ecosystem.assistant.routing.service import AIRouter, ai_router
from ecosystem.assistant.skills.service import SkillRegistry, skill_registry
from ecosystem.config import DEFAULT_CONFIG
from ecosystem.shared.store import EcosystemStore, ecosystem_store

logger = logging.getLogger(__name__)


class AssistantEngine:
    """Central AI assistant for the ecosystem — NLU, routing, skills, knowledge, conversation."""

    def __init__(
        self,
        store: EcosystemStore | None = None,
        memory: GlobalMemory | None = None,
        knowledge: KnowledgeGraph | None = None,
        context: ContextEngine | None = None,
        skills: SkillRegistry | None = None,
        router: AIRouter | None = None,
        conversations: ConversationService | None = None,
    ) -> None:
        self._store = store or ecosystem_store
        self.memory = memory or global_memory
        self.knowledge = knowledge or knowledge_graph
        self.context = context or context_engine
        self.skills = skills or skill_registry
        self.router = router or ai_router
        self.conversations = conversations or conversation_service

    async def invoke(
        self,
        user_id: str,
        message: str,
        *,
        application_id: str = "",
        organization_id: str = "",
        conversation_id: str = "",
        locale: str = "en",
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if conversation_id:
            conversation = self.conversations.get(conversation_id)
        else:
            conversation = await self.conversations.create(
                user_id,
                application_id=application_id,
                organization_id=organization_id,
                locale=locale,
                title=message[:48],
            )

        self.conversations.append_turn(conversation.conversation_id, "user", message, locale=locale)
        self.context.update(
            user_id,
            application_context={"application_id": application_id} if application_id else None,
            user_context={"locale": locale},
            organization_context={"organization_id": organization_id} if organization_id else None,
            conversation_context={"conversation_id": conversation.conversation_id, "last_message": message},
            global_context=context,
        )
        assembled = self.context.assemble(user_id)

        await publish(
            AssistantInvokedEvent(
                user_id=user_id,
                conversation_id=conversation.conversation_id,
                application_id=application_id,
                message=message,
            )
        )

        routing = await self.router.route(user_id, message, application_id=application_id)
        plan = self.plan_task(user_id, message)
        knowledge_hits = self.knowledge.semantic_search(message, application_id=application_id, limit=5)
        skills_executed: list[str] = []

        if routing.target_type == RouteTarget.TOOL or routing.intent == IntentType.KNOWLEDGE:
            skill = self.skills.find_by_name("search_knowledge")
            if skill:
                await self.skills.execute(skill.skill_id, user_id, {"query": message, "application_id": application_id})
                skills_executed.append(skill.name)

        if routing.intent == IntentType.TASK:
            skill = self.skills.find_by_name("plan_task")
            if skill:
                await self.skills.execute(skill.skill_id, user_id, {"goal": message})
                skills_executed.append(skill.name)

        if routing.target_type == RouteTarget.AGENT:
            skill = self.skills.find_by_name("route_agent")
            if skill:
                await self.skills.execute(skill.skill_id, user_id, {"agent_id": routing.agent_id})
                skills_executed.append(skill.name)

        if routing.application_id == "auto_marketplace" or "vehicle" in message.lower():
            skill = self.skills.find_by_name("auto_marketplace_search")
            if skill:
                await self.skills.execute(skill.skill_id, user_id, {"query": message})
                skills_executed.append(skill.name)

        reply = await self._generate_reply(
            user_id,
            message,
            application_id=application_id or routing.application_id,
            routing=routing.to_dict(),
            knowledge_hits=knowledge_hits,
            context=assembled,
            locale=locale,
        )

        self.conversations.append_turn(conversation.conversation_id, "assistant", reply, locale=locale)
        self.conversations.summarize(conversation.conversation_id)
        self.conversations.save_context_snapshot(conversation.conversation_id, assembled)
        await self.memory.remember(user_id, f"User: {message}", application_id=application_id, tags=["conversation"])
        await self.memory.remember(user_id, f"Assistant: {reply}", application_id=application_id, tags=["conversation"])

        plan.status = "completed"
        self._store.task_plans.save(plan.plan_id, plan)
        await publish(
            TaskCompletedEvent(
                plan_id=plan.plan_id,
                user_id=user_id,
                goal=plan.goal,
                status="completed",
                result={"reply": reply, "skills": skills_executed},
            )
        )

        response = AssistantResponse(
            conversation_id=conversation.conversation_id,
            reply=reply,
            intent=routing.intent_label,
            routing=routing.to_dict(),
            skills_executed=skills_executed,
            plan=plan.to_dict(),
            knowledge_hits=knowledge_hits,
            locale=locale,
        )
        payload = response.to_dict()
        payload["session_id"] = conversation.conversation_id
        return payload

    def plan_task(self, user_id: str, goal: str) -> TaskPlan:
        plan = TaskPlan(
            user_id=user_id,
            goal=goal,
            steps=[
                {"step": 1, "action": "detect_intent", "status": "pending"},
                {"step": 2, "action": "gather_context", "status": "pending"},
                {"step": 3, "action": "execute_skills", "status": "pending"},
                {"step": 4, "action": "generate_response", "status": "pending"},
            ],
        )
        for step in plan.steps:
            step["status"] = "done"
        self._store.task_plans.save(plan.plan_id, plan)
        return plan

    def decompose_task(self, goal: str) -> list[dict[str, Any]]:
        parts = [p.strip() for p in goal.replace(" then ", ".").split(".") if p.strip()]
        if len(parts) <= 1:
            return [
                {"step": 1, "action": "analyze", "detail": goal},
                {"step": 2, "action": "execute", "detail": goal},
                {"step": 3, "action": "confirm", "detail": "Report result"},
            ]
        return [{"step": i + 1, "action": "subtask", "detail": part} for i, part in enumerate(parts)]

    async def orchestrate(
        self,
        user_id: str,
        goal: str,
        *,
        agents: list[str] | None = None,
    ) -> dict[str, Any]:
        plan = self.plan_task(user_id, goal)
        plan.steps = self.decompose_task(goal)
        results = []
        for agent_id in agents or ["ecosystem-agent"]:
            try:
                from ecosystem.integrations.platform_bridge import platform_bridge

                result = await platform_bridge.delegate_task(goal, {"user_id": user_id}, agent_id=agent_id)
            except Exception:
                result = {"status": "fallback", "agent_id": agent_id}
            results.append({"agent_id": agent_id, "result": result})
        plan.status = "orchestrated"
        self._store.task_plans.save(plan.plan_id, plan)
        return {"plan": plan.to_dict(), "agent_results": results}

    async def _generate_reply(
        self,
        user_id: str,
        message: str,
        *,
        application_id: str,
        routing: dict[str, Any],
        knowledge_hits: list[dict[str, Any]],
        context: dict[str, Any],
        locale: str,
    ) -> str:
        try:
            from ecosystem.integrations.platform_bridge import platform_bridge

            result = await platform_bridge.route_assistant(
                user_id,
                message,
                application_id=application_id,
                context=context,
            )
            if result and result.get("reply"):
                return str(result["reply"])
        except Exception:
            logger.debug("platform assistant bridge unavailable")

        template_key = "auto_marketplace" if application_id == "auto_marketplace" else "default"
        if knowledge_hits:
            template_key = "knowledge"
        prompt = render_prompt(template_key, message=message, context=context, locale=locale)
        hit_labels = [h["node"]["label"] for h in knowledge_hits[:3] if "node" in h]
        knowledge_bit = f" Related knowledge: {', '.join(hit_labels)}." if hit_labels else ""
        intent = routing.get("intent_label", "general")
        return (
            f"Unified assistant ({intent}). {prompt.split(chr(10))[-1].replace('[user] ', '')}"
            f"{knowledge_bit}"
        )

    def metrics(self) -> dict[str, Any]:
        return {
            "ecosystem_version": DEFAULT_CONFIG.ecosystem_version,
            "assistant_layer": DEFAULT_CONFIG.assistant_layer,
            "global_knowledge": DEFAULT_CONFIG.global_knowledge,
            "conversations": self._store.conversations.count(),
            "knowledge_nodes": self._store.knowledge_nodes.count(),
            "memories": self._store.global_memories.count(),
            "skills": self._store.skills.count(),
            "contexts": self._store.context_bundles.count(),
            "knowledge": self.knowledge.stats(),
        }


assistant_engine = AssistantEngine()
