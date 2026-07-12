# AI agent models.

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text, DateTime, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from database.models.users import User


class AiAgent(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "ai_agents"
    __table_args__ = (
        UniqueConstraint("code", name="uq_ai_agents_code"),
        Index("ix_ai_agents_code", "code"),
        Index("ix_ai_agents_active", "active"),
    )

    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    model: Mapped[str] = mapped_column(String(128), default="openai/gpt-5-mini", nullable=False)
    prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    settings: Mapped[list[AiAgentSetting]] = relationship(
        back_populates="agent", cascade="all, delete-orphan",
    )
    memory_entries: Mapped[list[AiAgentMemory]] = relationship(
        back_populates="agent", cascade="all, delete-orphan",
    )
    dialogs: Mapped[list[AiDialog]] = relationship(
        back_populates="agent", cascade="all, delete-orphan",
    )


class AiAgentSetting(Base):
    __tablename__ = "ai_agent_settings"
    __table_args__ = (
        Index("ix_ai_agent_settings_user_id", "user_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True,
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_agents.id", ondelete="CASCADE"), primary_key=True,
    )
    model: Mapped[str] = mapped_column(String(128), default="openai/gpt-5-mini", nullable=False)
    tone: Mapped[str] = mapped_column(String(32), default="neutral", nullable=False)
    language: Mapped[str] = mapped_column(String(8), default="ru", nullable=False)
    context_depth: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False,
    )

    user: Mapped[User] = relationship(foreign_keys=[user_id])
    agent: Mapped[AiAgent] = relationship(back_populates="settings")


class AiAgentMemory(Base):
    __tablename__ = "ai_agent_memory"
    __table_args__ = (
        Index("ix_ai_agent_memory_user_id", "user_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True,
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_agents.id", ondelete="CASCADE"), primary_key=True,
    )
    memory_key: Mapped[str] = mapped_column(String(255), primary_key=True)
    memory_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False,
    )

    user: Mapped[User] = relationship(foreign_keys=[user_id])
    agent: Mapped[AiAgent] = relationship(back_populates="memory_entries")


class AiDialog(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_dialogs"
    __table_args__ = (
        Index("ix_ai_dialogs_user_id", "user_id"),
        Index("ix_ai_dialogs_agent_id", "agent_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_agents.id", ondelete="CASCADE"), nullable=False,
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    user: Mapped[User] = relationship(foreign_keys=[user_id])
    agent: Mapped[AiAgent] = relationship(back_populates="dialogs")
