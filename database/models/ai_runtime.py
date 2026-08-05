"""AI Runtime ORM — Sprint 36.3."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, VersionMixin


class AIProviderRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "ai_providers"
    __table_args__ = (
        UniqueConstraint("provider_key", name="uq_ai_providers_provider_key"),
        Index("ix_ai_providers_status", "status"),
    )

    provider_key: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="available")
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    config_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    models_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)


class AIModelRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "ai_models"
    __table_args__ = (
        UniqueConstraint("provider_key", "model_key", name="uq_ai_models_provider_model"),
        Index("ix_ai_models_provider_key", "provider_key"),
    )

    provider_key: Mapped[str] = mapped_column(String(64), nullable=False)
    model_key: Mapped[str] = mapped_column(String(128), nullable=False)
    display_name: Mapped[str] = mapped_column(String(256), nullable=False)
    context_window: Mapped[int] = mapped_column(Integer, nullable=False, default=8192)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="available")
    capabilities_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    pricing_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    task_types_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)


class AIRuntimeSessionRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "ai_runtime_sessions"
    __table_args__ = (
        UniqueConstraint("session_key", name="uq_ai_runtime_sessions_session_key"),
        Index("ix_ai_runtime_sessions_status", "status"),
    )

    session_key: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    provider_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    user_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    tenant_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    request_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    context_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PromptTemplateRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "prompt_templates"
    __table_args__ = (
        UniqueConstraint("template_key", name="uq_prompt_templates_template_key"),
    )

    template_key: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    active_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    variables_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)


class PromptVersionRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "prompt_versions"
    __table_args__ = (
        UniqueConstraint("template_key", "semver", name="uq_prompt_versions_template_semver"),
        Index("ix_prompt_versions_template_key", "template_key"),
    )

    template_key: Mapped[str] = mapped_column(String(128), nullable=False)
    semver: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    changelog: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    variables_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)


class ToolRegistryRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "tool_registry"
    __table_args__ = (
        UniqueConstraint("tool_key", name="uq_tool_registry_tool_key"),
        Index("ix_tool_registry_enabled", "enabled"),
    )

    tool_key: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    parameters_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    permission: Mapped[str] = mapped_column(String(32), nullable=False, default="allow")
    mcp_compatible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    timeout_sec: Mapped[float] = mapped_column(Float, nullable=False, default=30.0)
    sandbox: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class ToolExecutionRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "tool_executions"
    __table_args__ = (
        Index("ix_tool_executions_tool_key", "tool_key"),
        Index("ix_tool_executions_session_key", "session_key"),
    )

    execution_key: Mapped[str] = mapped_column(String(64), nullable=False)
    tool_key: Mapped[str] = mapped_column(String(128), nullable=False)
    session_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    arguments_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    result_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)


class AIRuntimeLogRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "ai_runtime_logs"
    __table_args__ = (
        Index("ix_ai_runtime_logs_session_key", "session_key"),
        Index("ix_ai_runtime_logs_level", "level"),
    )

    log_key: Mapped[str] = mapped_column(String(64), nullable=False)
    level: Mapped[str] = mapped_column(String(16), nullable=False, default="info")
    message: Mapped[str] = mapped_column(Text, nullable=False)
    session_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    provider_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    details_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
