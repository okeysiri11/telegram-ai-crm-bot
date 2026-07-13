# AI Skill Engine v1 repositories.

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.ai_skill_engine import (
    COMMUNICATION_STYLES,
    SKILL_CODES,
    SkillExecution,
    SkillHandoff,
    SkillHandoffStatus,
    TenantSkillConfig,
    TenantSkillProfile,
)


class TenantSkillProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(
        self,
        *,
        tenant_id: uuid.UUID,
        company_id: uuid.UUID,
        dealership_name: str,
        personality: str | None = None,
        communication_style: str = "PROFESSIONAL",
        language: str = "ru",
        tone: str = "friendly",
        escalation_rules: dict | None = None,
        manager_handoff: dict | None = None,
        metadata: dict | None = None,
    ) -> TenantSkillProfile:
        if communication_style not in COMMUNICATION_STYLES:
            raise ValueError(f"Invalid communication_style: {communication_style}")

        existing = await self.get_by_tenant(tenant_id)
        if existing is not None:
            existing.dealership_name = dealership_name.strip()
            existing.personality = personality
            existing.communication_style = communication_style
            existing.language = language
            existing.tone = tone
            existing.escalation_rules = escalation_rules
            existing.manager_handoff = manager_handoff
            existing.metadata_ = metadata
            await self._session.flush()
            return existing

        row = TenantSkillProfile(
            tenant_id=tenant_id,
            company_id=company_id,
            dealership_name=dealership_name.strip(),
            personality=personality,
            communication_style=communication_style,
            language=language,
            tone=tone,
            escalation_rules=escalation_rules,
            manager_handoff=manager_handoff,
            metadata_=metadata,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def get_by_tenant(self, tenant_id: uuid.UUID) -> TenantSkillProfile | None:
        result = await self._session.execute(
            select(TenantSkillProfile).where(TenantSkillProfile.tenant_id == tenant_id)
        )
        return result.scalar_one_or_none()


class TenantSkillConfigRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(
        self,
        *,
        tenant_id: uuid.UUID,
        company_id: uuid.UUID,
        skill_code: str,
        custom_prompt: str | None = None,
        is_enabled: bool = True,
    ) -> TenantSkillConfig:
        if skill_code not in SKILL_CODES:
            raise ValueError(f"Invalid skill_code: {skill_code}")

        existing = await self.get(tenant_id, skill_code)
        if existing is not None:
            existing.custom_prompt = custom_prompt
            existing.is_enabled = is_enabled
            await self._session.flush()
            return existing

        row = TenantSkillConfig(
            tenant_id=tenant_id,
            company_id=company_id,
            skill_code=skill_code,
            custom_prompt=custom_prompt,
            is_enabled=is_enabled,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def get(self, tenant_id: uuid.UUID, skill_code: str) -> TenantSkillConfig | None:
        result = await self._session.execute(
            select(TenantSkillConfig).where(
                TenantSkillConfig.tenant_id == tenant_id,
                TenantSkillConfig.skill_code == skill_code,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_tenant(self, tenant_id: uuid.UUID) -> list[TenantSkillConfig]:
        result = await self._session.execute(
            select(TenantSkillConfig)
            .where(TenantSkillConfig.tenant_id == tenant_id)
            .order_by(TenantSkillConfig.skill_code.asc())
        )
        return list(result.scalars().all())


class SkillHandoffRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        tenant_id: uuid.UUID,
        company_id: uuid.UUID,
        manager_id: int,
        reason: str,
        session_ref: str | None = None,
        skill_code: str | None = None,
        context: dict | None = None,
        status: str = SkillHandoffStatus.PENDING.value,
    ) -> SkillHandoff:
        row = SkillHandoff(
            tenant_id=tenant_id,
            company_id=company_id,
            manager_id=manager_id,
            reason=reason,
            session_ref=session_ref,
            skill_code=skill_code,
            context=context,
            status=status,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def list_by_tenant(
        self,
        tenant_id: uuid.UUID,
        *,
        limit: int = 50,
    ) -> list[SkillHandoff]:
        result = await self._session.execute(
            select(SkillHandoff)
            .where(SkillHandoff.tenant_id == tenant_id)
            .order_by(SkillHandoff.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


class SkillExecutionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        tenant_id: uuid.UUID,
        company_id: uuid.UUID,
        skill_code: str,
        user_message: str,
        response: str,
        session_ref: str | None = None,
        escalated: bool = False,
        handoff_id: uuid.UUID | None = None,
        metadata: dict | None = None,
    ) -> SkillExecution:
        row = SkillExecution(
            tenant_id=tenant_id,
            company_id=company_id,
            skill_code=skill_code,
            user_message=user_message,
            response=response,
            session_ref=session_ref,
            escalated=escalated,
            handoff_id=handoff_id,
            metadata_=metadata,
        )
        self._session.add(row)
        await self._session.flush()
        return row
