# AI Skill Engine v1 — tenant AI skills, prompts, escalation, manager handoff.

from __future__ import annotations

import logging
import re
import uuid
from typing import Any

from aiogram import Bot

from config import BOT_TOKEN, MANAGER_ID, OWNER_ID
from database.models.ai_skill_engine import (
    SKILL_CODES,
    CommunicationStyle,
    SkillCode,
    SkillHandoffStatus,
)
from database.models.audit_log import AuditAction
from database.session import get_session
from openrouter import ask_openrouter
from repositories.ai_skill_repository import (
    SkillExecutionRepository,
    SkillHandoffRepository,
    TenantSkillConfigRepository,
    TenantSkillProfileRepository,
)
from repositories.audit_repository import AuditRepository
from repositories.partner_tenant_repository import PartnerTenantRepository
from repositories.user_role_repository import UserRoleRepository
from services.pg_partner_tenant_engine import (
    PartnerTenantEngineV1,
    TenantAccessDeniedError,
)

logger = logging.getLogger(__name__)

PLATFORM_ADMIN_ROLES = frozenset({"OWNER", "ADMIN"})

DEFAULT_ESCALATION_RULES: dict[str, Any] = {
    "keywords": [
        "менеджер",
        "человек",
        "оператор",
        "жалоба",
        "руковод",
        "manager",
        "complaint",
    ],
    "intents": ["manager_request", "complaint", "legal", "urgent"],
    "max_turns_without_resolution": 10,
    "auto_handoff_on_financing_ready": True,
}

DEFAULT_MANAGER_HANDOFF: dict[str, Any] = {
    "default_manager_id": MANAGER_ID,
    "notify_via_telegram": True,
    "handoff_triggers": ["escalation", "hot_lead", "financing_ready"],
}

SKILL_LABELS: dict[str, str] = {
    SkillCode.SALES.value: "Sales Skill",
    SkillCode.AUTOMOTIVE.value: "Automotive Skill",
    SkillCode.NEGOTIATION.value: "Negotiation Skill",
    SkillCode.OBJECTION_HANDLING.value: "Objection Handling Skill",
    SkillCode.LEAD_QUALIFICATION.value: "Lead Qualification Skill",
    SkillCode.FINANCING.value: "Financing Skill",
    SkillCode.CUSTOMER_SUPPORT.value: "Customer Support Skill",
}

DEFAULT_SKILL_PROMPTS: dict[str, str] = {
    SkillCode.SALES.value: (
        "You are a dealership sales specialist. Help customers choose vehicles, "
        "explain value, guide toward test drive or purchase. Be consultative, not pushy."
    ),
    SkillCode.AUTOMOTIVE.value: (
        "You are an automotive expert. Answer technical questions about specs, "
        "condition, maintenance, VIN, mileage, options, and comparisons accurately."
    ),
    SkillCode.NEGOTIATION.value: (
        "You are a negotiation assistant for a dealership. Help find win-win deals, "
        "explain pricing logic, trade-in value, and package options within policy."
    ),
    SkillCode.OBJECTION_HANDLING.value: (
        "You handle customer objections empathetically. Address price, timing, trust, "
        "competition, and financing concerns with facts and reassurance."
    ),
    SkillCode.LEAD_QUALIFICATION.value: (
        "You qualify leads: budget, timeline, vehicle preferences, trade-in, "
        "financing need, contact info. Ask one focused question at a time."
    ),
    SkillCode.FINANCING.value: (
        "You explain financing options: down payment, term, rate, monthly payment. "
        "Collect numbers and give clear estimates. Do not guarantee approval."
    ),
    SkillCode.CUSTOMER_SUPPORT.value: (
        "You provide post-sale support: service appointments, warranty, documents, "
        "delivery status. Stay helpful and route complex issues to a manager."
    ),
}

SKILL_ROUTE_KEYWORDS: dict[str, tuple[str, ...]] = {
    SkillCode.FINANCING.value: (
        "кредит",
        "финанс",
        "рассроч",
        "payment",
        "loan",
        "ставк",
        "взнос",
    ),
    SkillCode.NEGOTIATION.value: (
        "скидк",
        "торг",
        "deal",
        "negotiat",
        "уступ",
        "trade",
        "trade-in",
    ),
    SkillCode.OBJECTION_HANDLING.value: (
        "дорого",
        "дорог",
        "expensive",
        "сомнева",
        "не уверен",
        "подума",
        "конкур",
    ),
    SkillCode.LEAD_QUALIFICATION.value: (
        "ищу",
        "нужен",
        "бюджет",
        "когда",
        "looking for",
        "budget",
        "планиру",
    ),
    SkillCode.AUTOMOTIVE.value: (
        "vin",
        "пробег",
        "двигат",
        "коробк",
        "комплек",
        "spec",
        "mileage",
        "engine",
    ),
    SkillCode.CUSTOMER_SUPPORT.value: (
        "гарант",
        "сервис",
        "документ",
        "достав",
        "support",
        "warranty",
        "service",
    ),
    SkillCode.SALES.value: (
        "куп",
        "цена",
        "авто",
        "машин",
        "buy",
        "price",
        "car",
        "test drive",
    ),
}

STYLE_INSTRUCTIONS: dict[str, str] = {
    CommunicationStyle.FORMAL.value: "Use formal, respectful language.",
    CommunicationStyle.FRIENDLY.value: "Use warm, friendly, approachable language.",
    CommunicationStyle.PROFESSIONAL.value: "Use professional, confident dealership tone.",
    CommunicationStyle.CONCISE.value: "Be brief and direct. Short paragraphs.",
}


class AiSkillEngineError(Exception):
    pass


class AiSkillEngineV1:
    @staticmethod
    async def is_platform_admin(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in PLATFORM_ADMIN_ROLES for role in roles)

    @staticmethod
    def _profile_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "tenant_id": str(row.tenant_id),
            "company_id": str(row.company_id),
            "dealership_name": row.dealership_name,
            "personality": row.personality,
            "communication_style": row.communication_style,
            "language": row.language,
            "tone": row.tone,
            "escalation_rules": row.escalation_rules or DEFAULT_ESCALATION_RULES,
            "manager_handoff": row.manager_handoff or DEFAULT_MANAGER_HANDOFF,
            "metadata": row.metadata_ or {},
        }

    @staticmethod
    def _skill_config_snapshot(row, *, label: str) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "skill_code": row.skill_code,
            "label": label,
            "custom_prompt": row.custom_prompt,
            "is_enabled": row.is_enabled,
            "default_prompt": DEFAULT_SKILL_PROMPTS.get(row.skill_code, ""),
        }

    @staticmethod
    def _handoff_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "tenant_id": str(row.tenant_id),
            "session_ref": row.session_ref,
            "skill_code": row.skill_code,
            "reason": row.reason,
            "manager_id": row.manager_id,
            "status": row.status,
            "context": row.context or {},
            "created_at": row.created_at.isoformat(),
        }

    @staticmethod
    async def _audit(
        session,
        *,
        actor_id: int,
        action: str,
        entity_id: str,
        company_id: uuid.UUID,
        tenant_id: uuid.UUID,
        new_value: dict | None = None,
    ) -> None:
        await AuditRepository(session).create_log(
            user_id=actor_id,
            company_id=company_id,
            tenant_id=tenant_id,
            entity_type="ai_skill",
            entity_id=entity_id,
            action=action,
            new_value=new_value,
        )

    @staticmethod
    async def upsert_tenant_profile(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        dealership_name: str,
        personality: str | None = None,
        communication_style: str = CommunicationStyle.PROFESSIONAL.value,
        language: str = "ru",
        tone: str = "friendly",
        escalation_rules: dict | None = None,
        manager_handoff: dict | None = None,
    ) -> dict[str, Any]:
        ctx = await PartnerTenantEngineV1.resolve_context(actor_id, tenant_id)
        if not await AiSkillEngineV1.is_platform_admin(actor_id):
            await PartnerTenantEngineV1.assert_tenant_write(ctx)

        async with get_session() as session:
            profile = await TenantSkillProfileRepository(session).upsert(
                tenant_id=tenant_id,
                company_id=ctx.company_id,
                dealership_name=dealership_name,
                personality=personality,
                communication_style=communication_style,
                language=language,
                tone=tone,
                escalation_rules=escalation_rules or DEFAULT_ESCALATION_RULES,
                manager_handoff=manager_handoff or DEFAULT_MANAGER_HANDOFF,
            )
            await AiSkillEngineV1._ensure_default_skills(session, tenant_id, ctx.company_id)
            await AiSkillEngineV1._audit(
                session,
                actor_id=actor_id,
                action=AuditAction.CREATE.value,
                entity_id=str(profile.id),
                company_id=ctx.company_id,
                tenant_id=tenant_id,
                new_value=AiSkillEngineV1._profile_snapshot(profile),
            )
            return AiSkillEngineV1._profile_snapshot(profile)

    @staticmethod
    async def _ensure_default_skills(
        session,
        tenant_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> None:
        repo = TenantSkillConfigRepository(session)
        for skill_code in SKILL_CODES:
            existing = await repo.get(tenant_id, skill_code)
            if existing is None:
                await repo.upsert(
                    tenant_id=tenant_id,
                    company_id=company_id,
                    skill_code=skill_code,
                    is_enabled=True,
                )

    @staticmethod
    async def get_tenant_profile(
        actor_id: int,
        tenant_id: uuid.UUID,
    ) -> dict[str, Any] | None:
        await PartnerTenantEngineV1.resolve_context(actor_id, tenant_id)
        async with get_session() as session:
            row = await TenantSkillProfileRepository(session).get_by_tenant(tenant_id)
            return AiSkillEngineV1._profile_snapshot(row) if row else None

    @staticmethod
    async def configure_skill(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        skill_code: str,
        custom_prompt: str | None = None,
        is_enabled: bool = True,
    ) -> dict[str, Any]:
        ctx = await PartnerTenantEngineV1.resolve_context(actor_id, tenant_id)
        if not await AiSkillEngineV1.is_platform_admin(actor_id):
            await PartnerTenantEngineV1.assert_tenant_write(ctx)
        if skill_code not in SKILL_CODES:
            raise AiSkillEngineError(f"Unknown skill: {skill_code}")

        async with get_session() as session:
            row = await TenantSkillConfigRepository(session).upsert(
                tenant_id=tenant_id,
                company_id=ctx.company_id,
                skill_code=skill_code,
                custom_prompt=custom_prompt,
                is_enabled=is_enabled,
            )
            await AiSkillEngineV1._audit(
                session,
                actor_id=actor_id,
                action=AuditAction.UPDATE.value,
                entity_id=str(row.id),
                company_id=ctx.company_id,
                tenant_id=tenant_id,
                new_value={"skill_code": skill_code, "is_enabled": is_enabled},
            )
            return AiSkillEngineV1._skill_config_snapshot(
                row,
                label=SKILL_LABELS.get(skill_code, skill_code),
            )

    @staticmethod
    async def list_skills(
        actor_id: int,
        tenant_id: uuid.UUID,
    ) -> list[dict[str, Any]]:
        await PartnerTenantEngineV1.resolve_context(actor_id, tenant_id)
        async with get_session() as session:
            rows = await TenantSkillConfigRepository(session).list_by_tenant(tenant_id)
            if not rows:
                tenant = await PartnerTenantRepository(session).get_by_id(tenant_id)
                if tenant:
                    await AiSkillEngineV1._ensure_default_skills(
                        session,
                        tenant_id,
                        tenant.company_id,
                    )
                    rows = await TenantSkillConfigRepository(session).list_by_tenant(tenant_id)
            return [
                AiSkillEngineV1._skill_config_snapshot(
                    row,
                    label=SKILL_LABELS.get(row.skill_code, row.skill_code),
                )
                for row in rows
            ]

    @staticmethod
    async def route_skill(tenant_id: uuid.UUID, user_message: str) -> str:
        text = user_message.lower()
        best_skill = SkillCode.SALES.value
        best_score = 0

        async with get_session() as session:
            configs = await TenantSkillConfigRepository(session).list_by_tenant(tenant_id)
            enabled = {c.skill_code for c in configs if c.is_enabled}
            if not enabled:
                enabled = set(SKILL_CODES)

        for skill_code, keywords in SKILL_ROUTE_KEYWORDS.items():
            if skill_code not in enabled:
                continue
            score = sum(1 for kw in keywords if kw in text)
            if score > best_score:
                best_score = score
                best_skill = skill_code

        return best_skill

    @staticmethod
    async def build_system_prompt(
        tenant_id: uuid.UUID,
        skill_code: str,
    ) -> str:
        async with get_session() as session:
            profile = await TenantSkillProfileRepository(session).get_by_tenant(tenant_id)
            config = await TenantSkillConfigRepository(session).get(tenant_id, skill_code)

        if profile is None:
            raise AiSkillEngineError("Tenant skill profile not configured")

        skill_prompt = (
            config.custom_prompt
            if config and config.custom_prompt
            else DEFAULT_SKILL_PROMPTS.get(skill_code, DEFAULT_SKILL_PROMPTS[SkillCode.SALES.value])
        )
        style = STYLE_INSTRUCTIONS.get(
            profile.communication_style,
            STYLE_INSTRUCTIONS[CommunicationStyle.PROFESSIONAL.value],
        )

        parts = [
            f"You represent {profile.dealership_name}.",
            skill_prompt,
            style,
        ]
        if profile.personality:
            parts.append(f"Dealership personality: {profile.personality.strip()}")

        rules = profile.escalation_rules or DEFAULT_ESCALATION_RULES
        parts.append(
            "Escalation: if customer asks for a manager, expresses strong complaint, "
            "or issue is beyond your scope — acknowledge and say you will connect a manager."
        )
        if rules.get("keywords"):
            parts.append(f"Escalation keywords: {', '.join(rules['keywords'][:8])}")

        return "\n\n".join(parts)

    @staticmethod
    def should_escalate(
        user_message: str,
        *,
        escalation_rules: dict | None,
        turn_count: int = 0,
        intent: str | None = None,
    ) -> tuple[bool, str | None]:
        rules = escalation_rules or DEFAULT_ESCALATION_RULES
        lowered = user_message.lower()

        for keyword in rules.get("keywords", []):
            if keyword.lower() in lowered:
                return True, f"keyword:{keyword}"

        if intent and intent in rules.get("intents", []):
            return True, f"intent:{intent}"

        max_turns = int(rules.get("max_turns_without_resolution", 10))
        if turn_count >= max_turns:
            return True, "max_turns_exceeded"

        return False, None

    @staticmethod
    async def create_manager_handoff(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        reason: str,
        session_ref: str | None = None,
        skill_code: str | None = None,
        context: dict | None = None,
        manager_id: int | None = None,
    ) -> dict[str, Any]:
        ctx = await PartnerTenantEngineV1.resolve_context(actor_id, tenant_id)

        async with get_session() as session:
            profile = await TenantSkillProfileRepository(session).get_by_tenant(tenant_id)
            handoff_cfg = (profile.manager_handoff if profile else None) or DEFAULT_MANAGER_HANDOFF
            target_manager = manager_id or int(handoff_cfg.get("default_manager_id", MANAGER_ID))

            handoff = await SkillHandoffRepository(session).create(
                tenant_id=tenant_id,
                company_id=ctx.company_id,
                manager_id=target_manager,
                reason=reason,
                session_ref=session_ref,
                skill_code=skill_code,
                context=context,
            )

            if handoff_cfg.get("notify_via_telegram", True):
                await AiSkillEngineV1._notify_manager(
                    manager_id=target_manager,
                    tenant_id=tenant_id,
                    reason=reason,
                    session_ref=session_ref,
                    skill_code=skill_code,
                )

            await AiSkillEngineV1._audit(
                session,
                actor_id=actor_id,
                action=AuditAction.ASSIGN.value,
                entity_id=str(handoff.id),
                company_id=ctx.company_id,
                tenant_id=tenant_id,
                new_value={"reason": reason, "manager_id": target_manager},
            )
            return AiSkillEngineV1._handoff_snapshot(handoff)

    @staticmethod
    async def _notify_manager(
        *,
        manager_id: int,
        tenant_id: uuid.UUID,
        reason: str,
        session_ref: str | None,
        skill_code: str | None,
    ) -> None:
        if not BOT_TOKEN:
            return
        bot = Bot(token=BOT_TOKEN)
        try:
            text = (
                f"🤖 AI Skill Handoff\n\n"
                f"Tenant: {tenant_id}\n"
                f"Skill: {skill_code or '—'}\n"
                f"Session: {session_ref or '—'}\n"
                f"Reason: {reason[:500]}"
            )
            await bot.send_message(chat_id=manager_id, text=text)
        except Exception:
            logger.exception("AI skill handoff notify failed for manager %s", manager_id)
        finally:
            await bot.session.close()

    @staticmethod
    async def execute_skill(
        tenant_id: uuid.UUID,
        *,
        skill_code: str,
        user_message: str,
        conversation_history: list[dict[str, str]] | None = None,
        session_ref: str | None = None,
        context: dict | None = None,
        actor_id: int | None = None,
    ) -> dict[str, Any]:
        if skill_code not in SKILL_CODES:
            raise AiSkillEngineError(f"Unknown skill: {skill_code}")

        async with get_session() as session:
            config = await TenantSkillConfigRepository(session).get(tenant_id, skill_code)
            if config is not None and not config.is_enabled:
                raise AiSkillEngineError(f"Skill disabled: {skill_code}")
            profile = await TenantSkillProfileRepository(session).get_by_tenant(tenant_id)
            if profile is None:
                raise AiSkillEngineError("Tenant skill profile not configured")
            company_id = profile.company_id
            profile_language = profile.language
            profile_tone = profile.tone
            escalation_rules = profile.escalation_rules

        system_prompt = await AiSkillEngineV1.build_system_prompt(tenant_id, skill_code)
        if context:
            system_prompt += f"\n\nContext:\n{context}"

        messages = list(conversation_history or [])
        messages.append({"role": "user", "content": user_message})

        response = await ask_openrouter(
            messages,
            user_memory=system_prompt,
            ai_settings={"language": profile_language, "tone": profile_tone},
        )

        turn_count = len([m for m in messages if m.get("role") == "user"])
        escalated, escalation_reason = AiSkillEngineV1.should_escalate(
            user_message,
            escalation_rules=escalation_rules,
            turn_count=turn_count,
            intent=(context or {}).get("intent"),
        )

        handoff_snapshot = None
        if escalated:
            handoff_snapshot = await AiSkillEngineV1.create_manager_handoff(
                actor_id or OWNER_ID,
                tenant_id,
                reason=escalation_reason or "escalation",
                session_ref=session_ref,
                skill_code=skill_code,
                context={"user_message": user_message[:500], **(context or {})},
            )
            response = (
                f"{response.strip()}\n\n"
                "Передаю ваш запрос менеджеру — он свяжется с вами в ближайшее время."
            )

        async with get_session() as session:
            handoff_id = uuid.UUID(handoff_snapshot["id"]) if handoff_snapshot else None
            execution = await SkillExecutionRepository(session).create(
                tenant_id=tenant_id,
                company_id=company_id,
                skill_code=skill_code,
                user_message=user_message,
                response=response,
                session_ref=session_ref,
                escalated=escalated,
                handoff_id=handoff_id,
                metadata={"escalation_reason": escalation_reason},
            )

        return {
            "execution_id": str(execution.id),
            "skill_code": skill_code,
            "skill_label": SKILL_LABELS.get(skill_code, skill_code),
            "response": response,
            "escalated": escalated,
            "escalation_reason": escalation_reason,
            "handoff": handoff_snapshot,
        }

    @staticmethod
    async def run_conversation(
        tenant_id: uuid.UUID,
        *,
        user_message: str,
        conversation_history: list[dict[str, str]] | None = None,
        session_ref: str | None = None,
        skill_code: str | None = None,
        context: dict | None = None,
        actor_id: int | None = None,
    ) -> dict[str, Any]:
        selected_skill = skill_code or await AiSkillEngineV1.route_skill(tenant_id, user_message)
        result = await AiSkillEngineV1.execute_skill(
            tenant_id,
            skill_code=selected_skill,
            user_message=user_message,
            conversation_history=conversation_history,
            session_ref=session_ref,
            context=context,
            actor_id=actor_id,
        )
        result["routed_skill"] = selected_skill
        return result

    @staticmethod
    async def list_handoffs(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        await PartnerTenantEngineV1.resolve_context(actor_id, tenant_id)
        async with get_session() as session:
            rows = await SkillHandoffRepository(session).list_by_tenant(tenant_id, limit=limit)
            return [AiSkillEngineV1._handoff_snapshot(r) for r in rows]

    @staticmethod
    async def list_skill_catalog() -> list[dict[str, str]]:
        return [
            {"code": code, "label": SKILL_LABELS.get(code, code)}
            for code in sorted(SKILL_CODES)
        ]

    @staticmethod
    async def ensure_default_profile(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        dealership_name: str | None = None,
    ) -> dict[str, Any]:
        existing = await AiSkillEngineV1.get_tenant_profile(actor_id, tenant_id)
        if existing:
            return existing

        async with get_session() as session:
            tenant = await PartnerTenantRepository(session).get_by_id(tenant_id)
            if tenant is None:
                raise AiSkillEngineError(f"Tenant not found: {tenant_id}")
            name = dealership_name or tenant.name

        return await AiSkillEngineV1.upsert_tenant_profile(
            actor_id,
            tenant_id,
            dealership_name=name,
            personality="Trusted automotive partner focused on transparency and service.",
            communication_style=CommunicationStyle.PROFESSIONAL.value,
        )
