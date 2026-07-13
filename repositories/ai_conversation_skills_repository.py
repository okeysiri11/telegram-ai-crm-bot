# AI Conversation Skills v1 repositories.

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.ai_conversation_skills import (
    CONVERSATION_SKILL_CODES,
    CONVERSATION_STYLES,
    AiPersonality,
    AiResponseTemplate,
    AiSkill,
    ConversationMemory,
    ConversationSkillCode,
    ConversationStyle,
)


class AiSkillRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        tenant_id: uuid.UUID,
        company_id: uuid.UUID,
        skill_code: str,
        name: str,
        description: str | None = None,
        system_prompt: str | None = None,
        is_enabled: bool = True,
        metadata: dict | None = None,
        **extra: Any,
    ) -> AiSkill:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if skill_code not in CONVERSATION_SKILL_CODES:
            raise ValueError(f"Invalid skill_code: {skill_code}")

        row = AiSkill(
            tenant_id=tenant_id,
            company_id=company_id,
            skill_code=skill_code,
            name=name,
            description=description,
            system_prompt=system_prompt,
            is_enabled=is_enabled,
            metadata_=metadata,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_by_code(
        self,
        tenant_id: uuid.UUID,
        skill_code: str,
    ) -> AiSkill | None:
        result = await self._session.execute(
            select(AiSkill).where(
                AiSkill.tenant_id == tenant_id,
                AiSkill.skill_code == skill_code,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_tenant(
        self,
        tenant_id: uuid.UUID,
        *,
        enabled_only: bool = False,
        limit: int = 20,
    ) -> list[AiSkill]:
        stmt = (
            select(AiSkill)
            .where(AiSkill.tenant_id == tenant_id)
            .order_by(AiSkill.skill_code.asc())
            .limit(limit)
        )
        if enabled_only:
            stmt = stmt.where(AiSkill.is_enabled.is_(True))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


class AiPersonalityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        tenant_id: uuid.UUID,
        company_id: uuid.UUID,
        name: str,
        tone: str = "friendly",
        communication_style: str = ConversationStyle.PROFESSIONAL.value,
        traits: dict | None = None,
        is_default: bool = False,
        metadata: dict | None = None,
        **extra: Any,
    ) -> AiPersonality:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if communication_style not in CONVERSATION_STYLES:
            raise ValueError(f"Invalid communication_style: {communication_style}")

        row = AiPersonality(
            tenant_id=tenant_id,
            company_id=company_id,
            name=name,
            tone=tone,
            communication_style=communication_style,
            traits=traits,
            is_default=is_default,
            metadata_=metadata,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_default(self, tenant_id: uuid.UUID) -> AiPersonality | None:
        result = await self._session.execute(
            select(AiPersonality).where(
                AiPersonality.tenant_id == tenant_id,
                AiPersonality.is_default.is_(True),
            )
        )
        return result.scalar_one_or_none()


class AiResponseTemplateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        tenant_id: uuid.UUID,
        company_id: uuid.UUID,
        template_code: str,
        template_text: str,
        skill_id: uuid.UUID | None = None,
        channel: str | None = None,
        language: str = "en",
        variables: dict | None = None,
        is_active: bool = True,
        **extra: Any,
    ) -> AiResponseTemplate:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")

        row = AiResponseTemplate(
            tenant_id=tenant_id,
            company_id=company_id,
            template_code=template_code,
            template_text=template_text,
            skill_id=skill_id,
            channel=channel,
            language=language,
            variables=variables,
            is_active=is_active,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_by_code(
        self,
        tenant_id: uuid.UUID,
        template_code: str,
    ) -> AiResponseTemplate | None:
        result = await self._session.execute(
            select(AiResponseTemplate).where(
                AiResponseTemplate.tenant_id == tenant_id,
                AiResponseTemplate.template_code == template_code,
                AiResponseTemplate.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()


class ConversationMemoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_or_create(
        self,
        *,
        tenant_id: uuid.UUID,
        company_id: uuid.UUID,
        session_ref: str,
        conversation_id: str | None = None,
    ) -> ConversationMemory:
        result = await self._session.execute(
            select(ConversationMemory).where(
                ConversationMemory.tenant_id == tenant_id,
                ConversationMemory.session_ref == session_ref,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            row = ConversationMemory(
                tenant_id=tenant_id,
                company_id=company_id,
                session_ref=session_ref,
                conversation_id=conversation_id,
                memory_items=[],
            )
            self._session.add(row)
            await self._session.flush()
        return row

    async def update_fields(
        self,
        memory_id: uuid.UUID,
        **fields: Any,
    ) -> ConversationMemory | None:
        result = await self._session.execute(
            select(ConversationMemory).where(ConversationMemory.id == memory_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        allowed = {
            "conversation_id",
            "customer_profile",
            "context_summary",
            "emotional_tone",
            "communication_style_used",
            "active_skill_code",
            "turn_count",
            "memory_items",
            "metadata_",
        }
        for key, value in fields.items():
            attr = "metadata_" if key == "metadata" else key
            if attr not in allowed:
                raise TypeError(f"Unsupported field: {key}")
            setattr(row, attr, value)
        await self._session.flush()
        return row
