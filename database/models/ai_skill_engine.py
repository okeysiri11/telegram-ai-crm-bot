# AI Skill Engine v1 — tenant-scoped AI skills, prompts, escalation, handoff.

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class SkillCode(str, enum.Enum):
    SALES = "SALES"
    AUTOMOTIVE = "AUTOMOTIVE"
    NEGOTIATION = "NEGOTIATION"
    OBJECTION_HANDLING = "OBJECTION_HANDLING"
    LEAD_QUALIFICATION = "LEAD_QUALIFICATION"
    FINANCING = "FINANCING"
    CUSTOMER_SUPPORT = "CUSTOMER_SUPPORT"


SKILL_CODES = frozenset(s.value for s in SkillCode)


class CommunicationStyle(str, enum.Enum):
    FORMAL = "FORMAL"
    FRIENDLY = "FRIENDLY"
    PROFESSIONAL = "PROFESSIONAL"
    CONCISE = "CONCISE"


COMMUNICATION_STYLES = frozenset(s.value for s in CommunicationStyle)


class SkillHandoffStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    CLOSED = "CLOSED"


class TenantSkillProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_skill_engine_v1_tenant_profiles"
    __table_args__ = (
        UniqueConstraint("tenant_id", name="uq_ai_skill_engine_v1_profiles_tenant"),
        Index("ix_ai_skill_engine_v1_profiles_company", "company_id"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("partner_tenant_engine_v1_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("multi_company_v1_companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    dealership_name: Mapped[str] = mapped_column(String(255), nullable=False)
    personality: Mapped[str | None] = mapped_column(Text, nullable=True)
    communication_style: Mapped[str] = mapped_column(
        String(30),
        default=CommunicationStyle.PROFESSIONAL.value,
        nullable=False,
    )
    language: Mapped[str] = mapped_column(String(10), default="ru", nullable=False)
    tone: Mapped[str] = mapped_column(String(30), default="friendly", nullable=False)
    escalation_rules: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    manager_handoff: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<TenantSkillProfile tenant={self.tenant_id} name={self.dealership_name}>"


class TenantSkillConfig(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_skill_engine_v1_skill_configs"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "skill_code",
            name="uq_ai_skill_engine_v1_skill_configs_tenant_code",
        ),
        Index("ix_ai_skill_engine_v1_skill_configs_tenant", "tenant_id"),
        Index("ix_ai_skill_engine_v1_skill_configs_code", "skill_code"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("partner_tenant_engine_v1_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("multi_company_v1_companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    skill_code: Mapped[str] = mapped_column(String(40), nullable=False)
    custom_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<TenantSkillConfig tenant={self.tenant_id} skill={self.skill_code}>"


class SkillHandoff(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_skill_engine_v1_handoffs"
    __table_args__ = (
        Index("ix_ai_skill_engine_v1_handoffs_tenant", "tenant_id"),
        Index("ix_ai_skill_engine_v1_handoffs_manager", "manager_id"),
        Index("ix_ai_skill_engine_v1_handoffs_status", "status"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("partner_tenant_engine_v1_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("multi_company_v1_companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    session_ref: Mapped[str | None] = mapped_column(String(120), nullable=True)
    skill_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    manager_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        default=SkillHandoffStatus.PENDING.value,
        nullable=False,
    )
    context: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<SkillHandoff tenant={self.tenant_id} manager={self.manager_id}>"


class SkillExecution(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_skill_engine_v1_executions"
    __table_args__ = (
        Index("ix_ai_skill_engine_v1_executions_tenant", "tenant_id"),
        Index("ix_ai_skill_engine_v1_executions_skill", "skill_code"),
        Index("ix_ai_skill_engine_v1_executions_session", "session_ref"),
    )

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("partner_tenant_engine_v1_tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("multi_company_v1_companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    skill_code: Mapped[str] = mapped_column(String(40), nullable=False)
    session_ref: Mapped[str | None] = mapped_column(String(120), nullable=True)
    user_message: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=False)
    escalated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    handoff_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_skill_engine_v1_handoffs.id", ondelete="SET NULL"),
        nullable=True,
    )
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<SkillExecution tenant={self.tenant_id} skill={self.skill_code}>"
