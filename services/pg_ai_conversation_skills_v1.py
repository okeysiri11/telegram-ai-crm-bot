# AI Conversation Skills v1 — product layer.

from __future__ import annotations

import uuid
from typing import Any

from database.models.ai_conversation_skills import ConversationSkillCode
from services.pg_ai_conversation_skills_engine import (
    AiConversationSkillsError,
    AiConversationSkillsV1,
)

SKILLS_FEATURES = frozenset({
    "context_memory",
    "customer_profile_adaptation",
    "communication_style_adaptation",
    "emotional_tone_detection",
})


class ConversationSkillsProductError(Exception):
    pass


class AiConversationSkillsV1Product:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        return await AiConversationSkillsV1.user_can_access(user_id)

    @staticmethod
    def list_features() -> list[dict[str, str]]:
        labels = {
            "context_memory": "Context Memory",
            "customer_profile_adaptation": "Customer Profile Adaptation",
            "communication_style_adaptation": "Communication Style Adaptation",
            "emotional_tone_detection": "Emotional Tone Detection",
        }
        return [{"code": k, "label": labels[k]} for k in sorted(SKILLS_FEATURES)]

    @staticmethod
    def list_skills() -> list[dict[str, str]]:
        return [
            {"code": code.value, "label": code.value.replace("_", " ").title()}
            for code in ConversationSkillCode
        ]

    @staticmethod
    async def get_engine(actor_id: int, tenant_id: uuid.UUID) -> dict[str, Any]:
        try:
            dashboard = await AiConversationSkillsV1.get_skills_dashboard(actor_id, tenant_id)
            if not dashboard["skills"]:
                dashboard["skills"] = await AiConversationSkillsV1.bootstrap_skills(actor_id, tenant_id)
            return {
                **dashboard,
                "features": list(SKILLS_FEATURES),
                "skill_catalog": AiConversationSkillsV1Product.list_skills(),
            }
        except AiConversationSkillsError as exc:
            raise ConversationSkillsProductError(str(exc)) from exc

    @staticmethod
    async def get_feature(
        actor_id: int,
        tenant_id: uuid.UUID,
        feature: str,
        *,
        session_ref: str = "demo-session",
    ) -> dict[str, Any]:
        if feature not in SKILLS_FEATURES:
            raise ConversationSkillsProductError(f"Unknown feature: {feature}")
        try:
            if feature == "context_memory":
                return {
                    "feature": feature,
                    **await AiConversationSkillsV1.get_context_memory(actor_id, tenant_id, session_ref),
                }
            if feature == "emotional_tone_detection":
                sample = "I'm frustrated with the price but excited about the car"
                return {
                    "feature": feature,
                    "detected_tone": AiConversationSkillsV1.detect_emotional_tone(sample),
                    "sample_text": sample,
                }
            if feature == "communication_style_adaptation":
                return {
                    "feature": feature,
                    **await AiConversationSkillsV1.adapt_communication_style(
                        actor_id, tenant_id, session_ref
                    ),
                }
            if feature == "customer_profile_adaptation":
                return {
                    "feature": feature,
                    **await AiConversationSkillsV1.adapt_to_customer_profile(
                        actor_id,
                        tenant_id,
                        session_ref,
                        {"budget_max": "30000", "preferred_makes": ["Toyota"]},
                    ),
                }
            raise ConversationSkillsProductError(f"Unknown feature: {feature}")
        except AiConversationSkillsError as exc:
            raise ConversationSkillsProductError(str(exc)) from exc
