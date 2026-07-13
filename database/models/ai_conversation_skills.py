# AI Conversation Skills v1 — skills, personalities, templates, conversation memory.

from __future__ import annotations

import enum
import uuid

from sqlalchemy import (
    BigInteger,
    Boolean,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class ConversationSkillCode(str, enum.Enum):
    EMPATHY = "EMPATHY"
    OBJECTION_HANDLING = "OBJECTION_HANDLING"
    NEGOTIATION = "NEGOTIATION"
    URGENCY_CREATION = "URGENCY_CREATION"
    FINANCING_EXPLANATION = "FINANCING_EXPLANATION"
    TRADE_IN_CONSULTATION = "TRADE_IN_CONSULTATION"
    DELIVERY_CONSULTATION = "DELIVERY_CONSULTATION"


class ConversationTone(str, enum.Enum):
    POSITIVE = "POSITIVE"
    NEUTRAL = "NEUTRAL"
    NEGATIVE = "NEGATIVE"
    FRUSTRATED = "FRUSTRATED"
    EXCITED = "EXCITED"


class ConversationStyle(str, enum.Enum):
    FORMAL = "FORMAL"
    FRIENDLY = "FRIENDLY"
    PROFESSIONAL = "PROFESSIONAL"
    CONCISE = "CONCISE"
    EMPATHETIC = "EMPATHETIC"


CONVERSATION_SKILL_CODES = frozenset(s.value for s in ConversationSkillCode)
CONVERSATION_TONES = frozenset(t.value for t in ConversationTone)
CONVERSATION_STYLES = frozenset(s.value for s in ConversationStyle)


class AiSkill(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_conversation_skills_v1_skills"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "skill_code",
            name="uq_ai_conversation_skills_v1_skills_tenant_code",
        ),
        Index("ix_ai_conversation_skills_v1_skills_tenant", "tenant_id"),
        Index("ix_ai_conversation_skills_v1_skills_code", "skill_code"),
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
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<AiSkill tenant={self.tenant_id} code={self.skill_code}>"


class AiPersonality(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_conversation_skills_v1_personalities"
    __table_args__ = (
        Index("ix_ai_conversation_skills_v1_personalities_tenant", "tenant_id"),
        Index("ix_ai_conversation_skills_v1_personalities_default", "is_default"),
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
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    tone: Mapped[str] = mapped_column(String(30), default="friendly", nullable=False)
    communication_style: Mapped[str] = mapped_column(
        String(30),
        default=ConversationStyle.PROFESSIONAL.value,
        nullable=False,
    )
    traits: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<AiPersonality tenant={self.tenant_id} name={self.name}>"


class AiResponseTemplate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_conversation_skills_v1_response_templates"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "template_code",
            name="uq_ai_conversation_skills_v1_templates_tenant_code",
        ),
        Index("ix_ai_conversation_skills_v1_templates_tenant", "tenant_id"),
        Index("ix_ai_conversation_skills_v1_templates_skill", "skill_id"),
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
    skill_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_conversation_skills_v1_skills.id", ondelete="SET NULL"),
        nullable=True,
    )
    template_code: Mapped[str] = mapped_column(String(80), nullable=False)
    channel: Mapped[str | None] = mapped_column(String(30), nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    template_text: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<AiResponseTemplate code={self.template_code}>"


class ConversationMemory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_conversation_skills_v1_conversation_memory"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "session_ref",
            name="uq_ai_conversation_skills_v1_memory_tenant_session",
        ),
        Index("ix_ai_conversation_skills_v1_memory_tenant", "tenant_id"),
        Index("ix_ai_conversation_skills_v1_memory_conversation", "conversation_id"),
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
    session_ref: Mapped[str] = mapped_column(String(120), nullable=False)
    conversation_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    customer_profile: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    context_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    emotional_tone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    communication_style_used: Mapped[str | None] = mapped_column(String(30), nullable=True)
    active_skill_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    turn_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    memory_items: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<ConversationMemory session={self.session_ref} turns={self.turn_count}>"
