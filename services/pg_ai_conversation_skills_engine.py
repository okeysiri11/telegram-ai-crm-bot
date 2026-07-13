# AI Conversation Skills v1 — skills, personalities, templates, conversation memory.

from __future__ import annotations

import uuid
from typing import Any

from config import OWNER_ID
from database.models.ai_conversation_skills import (
    ConversationSkillCode,
    ConversationStyle,
    ConversationTone,
)
from database.models.audit_log import AuditAction
from database.session import get_session
from repositories.ai_conversation_skills_repository import (
    AiPersonalityRepository,
    AiResponseTemplateRepository,
    AiSkillRepository,
    ConversationMemoryRepository,
)
from repositories.audit_repository import AuditRepository
from repositories.user_role_repository import UserRoleRepository
from services.pg_partner_tenant_engine import PartnerTenantEngineV1

CONVERSATION_SKILLS_ROLES = frozenset({"OWNER", "ADMIN", "MANAGER"})
MODEL_VERSION = "ai-conversation-skills-v1.0.0"

DEFAULT_SKILL_DEFINITIONS: dict[str, dict[str, str]] = {
    ConversationSkillCode.EMPATHY.value: {
        "name": "Empathy",
        "description": "Acknowledge feelings and build rapport.",
        "system_prompt": "Respond with empathy. Validate the customer's concerns before offering solutions.",
    },
    ConversationSkillCode.OBJECTION_HANDLING.value: {
        "name": "Objection Handling",
        "description": "Address price, timing, and trust objections.",
        "system_prompt": "Handle objections calmly with facts, reassurance, and alternative options.",
    },
    ConversationSkillCode.NEGOTIATION.value: {
        "name": "Negotiation",
        "description": "Guide toward win-win deals.",
        "system_prompt": "Help negotiate fairly within dealership policy. Focus on value, not pressure.",
    },
    ConversationSkillCode.URGENCY_CREATION.value: {
        "name": "Urgency Creation",
        "description": "Highlight limited availability ethically.",
        "system_prompt": "Create appropriate urgency using inventory scarcity and time-sensitive offers without pressure tactics.",
    },
    ConversationSkillCode.FINANCING_EXPLANATION.value: {
        "name": "Financing Explanation",
        "description": "Explain loans, terms, and monthly payments.",
        "system_prompt": "Explain financing clearly: down payment, term, rate, monthly payment. Never guarantee approval.",
    },
    ConversationSkillCode.TRADE_IN_CONSULTATION.value: {
        "name": "Trade-in Consultation",
        "description": "Discuss trade-in value and process.",
        "system_prompt": "Consult on trade-in condition, mileage, market value, and appraisal next steps.",
    },
    ConversationSkillCode.DELIVERY_CONSULTATION.value: {
        "name": "Delivery Consultation",
        "description": "Coordinate pickup, paperwork, and handover.",
        "system_prompt": "Guide the customer through delivery scheduling, documents needed, and vehicle handover.",
    },
}

SKILL_ROUTE_KEYWORDS: dict[str, tuple[str, ...]] = {
    ConversationSkillCode.FINANCING_EXPLANATION.value: (
        "finance", "loan", "credit", "payment", "rate", "кредит", "финанс", "платеж",
    ),
    ConversationSkillCode.OBJECTION_HANDLING.value: (
        "expensive", "too much", "not sure", "дорого", "сомнева", "objection",
    ),
    ConversationSkillCode.NEGOTIATION.value: (
        "discount", "deal", "offer", "negotiat", "скидк", "торг",
    ),
    ConversationSkillCode.TRADE_IN_CONSULTATION.value: (
        "trade", "trade-in", "exchange", "обмен",
    ),
    ConversationSkillCode.DELIVERY_CONSULTATION.value: (
        "delivery", "pickup", "pick up", "доставк", "получ",
    ),
    ConversationSkillCode.URGENCY_CREATION.value: (
        "available", "how long", "hold", "reserve", "сколько", "успеть",
    ),
}

TONE_KEYWORDS: dict[str, tuple[str, ...]] = {
    ConversationTone.FRUSTRATED.value: ("angry", "frustrated", "upset", "bad service", "злой", "бесит"),
    ConversationTone.NEGATIVE.value: ("disappointed", "unhappy", "problem", "issue", "проблем"),
    ConversationTone.EXCITED.value: ("excited", "love", "perfect", "great", "отлично", "супер"),
    ConversationTone.POSITIVE.value: ("thanks", "thank you", "good", "спасибо", "хорош"),
}


class AiConversationSkillsError(Exception):
    pass


class AiConversationSkillsV1:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in CONVERSATION_SKILLS_ROLES for role in roles)

    @staticmethod
    async def _require_access(actor_id: int, tenant_id: uuid.UUID):
        if not await AiConversationSkillsV1.user_can_access(actor_id):
            raise AiConversationSkillsError("AI conversation skills access denied")
        return await PartnerTenantEngineV1.resolve_context(actor_id, tenant_id)

    @staticmethod
    def _skill_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "skill_code": row.skill_code,
            "name": row.name,
            "description": row.description,
            "is_enabled": row.is_enabled,
        }

    @staticmethod
    def _personality_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "name": row.name,
            "tone": row.tone,
            "communication_style": row.communication_style,
            "traits": row.traits or {},
            "is_default": row.is_default,
        }

    @staticmethod
    def _memory_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "session_ref": row.session_ref,
            "conversation_id": row.conversation_id,
            "customer_profile": row.customer_profile or {},
            "context_summary": row.context_summary,
            "emotional_tone": row.emotional_tone,
            "communication_style_used": row.communication_style_used,
            "active_skill_code": row.active_skill_code,
            "turn_count": row.turn_count,
            "memory_items": row.memory_items or [],
        }

    @staticmethod
    def detect_emotional_tone(text: str) -> str:
        lowered = text.lower()
        for tone, keywords in TONE_KEYWORDS.items():
            if any(kw in lowered for kw in keywords):
                return tone
        return ConversationTone.NEUTRAL.value

    @staticmethod
    def route_skill(text: str) -> str:
        lowered = text.lower()
        scores: dict[str, int] = {code: 0 for code in SKILL_ROUTE_KEYWORDS}
        for code, keywords in SKILL_ROUTE_KEYWORDS.items():
            for kw in keywords:
                if kw in lowered:
                    scores[code] += 1
        best = max(scores, key=scores.get)
        if scores[best] > 0:
            return best
        return ConversationSkillCode.EMPATHY.value

    @staticmethod
    async def bootstrap_skills(actor_id: int, tenant_id: uuid.UUID) -> list[dict[str, Any]]:
        ctx = await AiConversationSkillsV1._require_access(actor_id, tenant_id)
        created: list[dict[str, Any]] = []
        async with get_session() as session:
            repo = AiSkillRepository(session)
            for code, definition in DEFAULT_SKILL_DEFINITIONS.items():
                existing = await repo.get_by_code(tenant_id, code)
                if existing:
                    created.append(AiConversationSkillsV1._skill_snapshot(existing))
                    continue
                row = await repo.create(
                    tenant_id=tenant_id,
                    company_id=ctx.company_id,
                    skill_code=code,
                    name=definition["name"],
                    description=definition["description"],
                    system_prompt=definition["system_prompt"],
                )
                created.append(AiConversationSkillsV1._skill_snapshot(row))
        return created

    @staticmethod
    async def create_personality(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        name: str,
        tone: str = "friendly",
        communication_style: str = ConversationStyle.PROFESSIONAL.value,
        traits: dict | None = None,
        is_default: bool = False,
    ) -> dict[str, Any]:
        ctx = await AiConversationSkillsV1._require_access(actor_id, tenant_id)
        async with get_session() as session:
            row = await AiPersonalityRepository(session).create(
                tenant_id=tenant_id,
                company_id=ctx.company_id,
                name=name,
                tone=tone,
                communication_style=communication_style,
                traits=traits,
                is_default=is_default,
            )
            await session.refresh(row)
            return AiConversationSkillsV1._personality_snapshot(row)

    @staticmethod
    async def create_response_template(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        template_code: str,
        template_text: str,
        skill_code: str | None = None,
        channel: str | None = None,
        language: str = "en",
    ) -> dict[str, Any]:
        ctx = await AiConversationSkillsV1._require_access(actor_id, tenant_id)
        async with get_session() as session:
            skill_id = None
            if skill_code:
                skill = await AiSkillRepository(session).get_by_code(tenant_id, skill_code)
                skill_id = skill.id if skill else None
            row = await AiResponseTemplateRepository(session).create(
                tenant_id=tenant_id,
                company_id=ctx.company_id,
                template_code=template_code,
                template_text=template_text,
                skill_id=skill_id,
                channel=channel,
                language=language,
            )
            await session.refresh(row)
            return {
                "id": str(row.id),
                "template_code": row.template_code,
                "template_text": row.template_text,
                "skill_id": str(row.skill_id) if row.skill_id else None,
                "channel": row.channel,
            }

    @staticmethod
    async def get_context_memory(
        actor_id: int,
        tenant_id: uuid.UUID,
        session_ref: str,
    ) -> dict[str, Any]:
        ctx = await AiConversationSkillsV1._require_access(actor_id, tenant_id)
        async with get_session() as session:
            row = await ConversationMemoryRepository(session).get_or_create(
                tenant_id=tenant_id,
                company_id=ctx.company_id,
                session_ref=session_ref,
            )
            await session.refresh(row)
            return AiConversationSkillsV1._memory_snapshot(row)

    @staticmethod
    async def update_context_memory(
        actor_id: int,
        tenant_id: uuid.UUID,
        session_ref: str,
        *,
        user_message: str | None = None,
        assistant_response: str | None = None,
        customer_profile: dict | None = None,
        conversation_id: str | None = None,
    ) -> dict[str, Any]:
        ctx = await AiConversationSkillsV1._require_access(actor_id, tenant_id)
        tone = AiConversationSkillsV1.detect_emotional_tone(user_message or "")
        skill_code = AiConversationSkillsV1.route_skill(user_message or "")

        async with get_session() as session:
            memory = await ConversationMemoryRepository(session).get_or_create(
                tenant_id=tenant_id,
                company_id=ctx.company_id,
                session_ref=session_ref,
                conversation_id=conversation_id,
            )
            items = list(memory.memory_items or [])
            if user_message:
                items.append({"role": "user", "text": user_message[:500]})
            if assistant_response:
                items.append({"role": "assistant", "text": assistant_response[:500]})
            items = items[-20:]

            summary_parts = [f"Turns: {memory.turn_count + 1}", f"Tone: {tone}", f"Skill: {skill_code}"]
            if customer_profile:
                summary_parts.append(f"Profile keys: {', '.join(customer_profile.keys())}")

            updated = await ConversationMemoryRepository(session).update_fields(
                memory.id,
                turn_count=memory.turn_count + (1 if user_message else 0),
                emotional_tone=tone,
                active_skill_code=skill_code,
                memory_items=items,
                context_summary="; ".join(summary_parts),
                customer_profile=customer_profile or memory.customer_profile,
                conversation_id=conversation_id or memory.conversation_id,
            )
            await session.refresh(updated)
            return AiConversationSkillsV1._memory_snapshot(updated)

    @staticmethod
    async def adapt_to_customer_profile(
        actor_id: int,
        tenant_id: uuid.UUID,
        session_ref: str,
        customer_profile: dict,
    ) -> dict[str, Any]:
        await AiConversationSkillsV1._require_access(actor_id, tenant_id)
        memory = await AiConversationSkillsV1.update_context_memory(
            actor_id,
            tenant_id,
            session_ref,
            customer_profile=customer_profile,
        )
        adaptations: list[str] = []
        budget = customer_profile.get("budget_max") or customer_profile.get("budget")
        if budget:
            adaptations.append(f"Focus on vehicles under {budget}")
        if customer_profile.get("preferred_makes"):
            adaptations.append(f"Highlight {', '.join(customer_profile['preferred_makes'])}")
        if customer_profile.get("timeline") == "urgent":
            adaptations.append("Emphasize immediate availability")

        return {
            "memory": memory,
            "adaptations": adaptations,
            "customer_profile": customer_profile,
        }

    @staticmethod
    async def adapt_communication_style(
        actor_id: int,
        tenant_id: uuid.UUID,
        session_ref: str,
        *,
        emotional_tone: str | None = None,
    ) -> dict[str, Any]:
        ctx = await AiConversationSkillsV1._require_access(actor_id, tenant_id)
        async with get_session() as session:
            memory = await ConversationMemoryRepository(session).get_or_create(
                tenant_id=tenant_id,
                company_id=ctx.company_id,
                session_ref=session_ref,
            )
            personality = await AiPersonalityRepository(session).get_default(tenant_id)
            tone = emotional_tone or memory.emotional_tone or ConversationTone.NEUTRAL.value

            style = ConversationStyle.PROFESSIONAL.value
            if personality:
                style = personality.communication_style
            if tone == ConversationTone.FRUSTRATED.value:
                style = ConversationStyle.EMPATHETIC.value
            elif tone == ConversationTone.EXCITED.value:
                style = ConversationStyle.FRIENDLY.value

            await ConversationMemoryRepository(session).update_fields(
                memory.id,
                communication_style_used=style,
                emotional_tone=tone,
            )

        return {
            "session_ref": session_ref,
            "emotional_tone": tone,
            "communication_style": style,
            "personality": AiConversationSkillsV1._personality_snapshot(personality) if personality else None,
        }

    @staticmethod
    async def generate_skill_response(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        session_ref: str,
        user_message: str,
        channel: str | None = None,
    ) -> dict[str, Any]:
        ctx = await AiConversationSkillsV1._require_access(actor_id, tenant_id)
        tone = AiConversationSkillsV1.detect_emotional_tone(user_message)
        skill_code = AiConversationSkillsV1.route_skill(user_message)
        style_adaptation = await AiConversationSkillsV1.adapt_communication_style(
            actor_id, tenant_id, session_ref, emotional_tone=tone
        )

        async with get_session() as session:
            skill = await AiSkillRepository(session).get_by_code(tenant_id, skill_code)
            template = await AiResponseTemplateRepository(session).get_by_code(
                tenant_id, f"{skill_code}_DEFAULT"
            )
            if template is None and channel:
                template = await AiResponseTemplateRepository(session).get_by_code(
                    tenant_id, f"{channel}_{skill_code}"
                )

        if template:
            response = template.template_text
        elif skill and skill.system_prompt:
            response = f"[{skill.name}] {skill.system_prompt[:120]}..."
        else:
            definition = DEFAULT_SKILL_DEFINITIONS.get(skill_code, {})
            response = definition.get("system_prompt", "How can I help you today?")[:200]

        if tone == ConversationTone.FRUSTRATED.value:
            response = f"I understand your concern. {response}"
        elif tone == ConversationTone.EXCITED.value:
            response = f"Great to hear! {response}"

        memory = await AiConversationSkillsV1.update_context_memory(
            actor_id,
            tenant_id,
            session_ref,
            user_message=user_message,
            assistant_response=response,
        )

        return {
            "response": response,
            "skill_code": skill_code,
            "emotional_tone": tone,
            "communication_style": style_adaptation["communication_style"],
            "memory": memory,
            "model_version": MODEL_VERSION,
        }

    @staticmethod
    async def get_skills_dashboard(
        actor_id: int,
        tenant_id: uuid.UUID,
    ) -> dict[str, Any]:
        await AiConversationSkillsV1._require_access(actor_id, tenant_id)
        async with get_session() as session:
            skills = await AiSkillRepository(session).list_by_tenant(tenant_id)
            personality = await AiPersonalityRepository(session).get_default(tenant_id)

        return {
            "tenant_id": str(tenant_id),
            "skills": [AiConversationSkillsV1._skill_snapshot(s) for s in skills],
            "skill_codes": [s.value for s in ConversationSkillCode],
            "default_personality": (
                AiConversationSkillsV1._personality_snapshot(personality) if personality else None
            ),
            "capabilities": [
                "context_memory",
                "customer_profile_adaptation",
                "communication_style_adaptation",
                "emotional_tone_detection",
            ],
        }
