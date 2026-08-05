"""Service Builder ORM — Sprint 36.0."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, VersionMixin


class ServiceRegistryRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "service_registry"
    __table_args__ = (
        UniqueConstraint("service_key", name="uq_service_registry_service_key"),
        Index("ix_service_registry_state", "state"),
        Index("ix_service_registry_category", "category"),
        Index("ix_service_registry_owner", "owner"),
    )

    service_key: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    display_name: Mapped[str] = mapped_column(String(256), nullable=False)
    semver: Mapped[str] = mapped_column(String(64), nullable=False, default="0.1.0")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner: Mapped[str] = mapped_column(String(128), nullable=False, default="platform")
    category: Mapped[str] = mapped_column(String(64), nullable=False, default="other")
    state: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    icon: Mapped[str] = mapped_column(String(64), nullable=False, default="box")
    manifest_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    configuration_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    module_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    entrypoint: Mapped[str | None] = mapped_column(String(256), nullable=True)
    sandbox_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    restart_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class ServiceVersionRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "service_versions"
    __table_args__ = (
        UniqueConstraint("service_key", "semver", name="uq_service_versions_key_semver"),
        Index("ix_service_versions_service_key", "service_key"),
    )

    service_key: Mapped[str] = mapped_column(String(128), nullable=False)
    semver: Mapped[str] = mapped_column(String(64), nullable=False)
    changelog: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    manifest_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class ServiceDependencyRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "service_dependencies"
    __table_args__ = (
        UniqueConstraint("service_key", "depends_on", name="uq_service_dependencies_edge"),
        Index("ix_service_dependencies_service_key", "service_key"),
        Index("ix_service_dependencies_depends_on", "depends_on"),
    )

    service_key: Mapped[str] = mapped_column(String(128), nullable=False)
    depends_on: Mapped[str] = mapped_column(String(128), nullable=False)
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class ServiceHealthRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "service_health"
    __table_args__ = (
        Index("ix_service_health_service_key", "service_key"),
        Index("ix_service_health_recorded_at", "recorded_at"),
    )

    service_key: Mapped[str] = mapped_column(String(128), nullable=False)
    healthy: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    response_time_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    memory_mb: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    cpu_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    errors: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    restart_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    availability_pct: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    details_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class ServiceLogRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "service_logs"
    __table_args__ = (
        Index("ix_service_logs_service_key", "service_key"),
        Index("ix_service_logs_operation", "operation"),
        Index("ix_service_logs_created_at", "created_at"),
    )

    service_key: Mapped[str] = mapped_column(String(128), nullable=False)
    level: Mapped[str] = mapped_column(String(16), nullable=False, default="info")
    message: Mapped[str] = mapped_column(Text, nullable=False)
    actor: Mapped[str] = mapped_column(String(128), nullable=False, default="system")
    operation: Mapped[str | None] = mapped_column(String(64), nullable=True)
    old_state: Mapped[str | None] = mapped_column(String(32), nullable=True)
    new_state: Mapped[str | None] = mapped_column(String(32), nullable=True)
    duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    result: Mapped[str] = mapped_column(String(32), nullable=False, default="ok")
    details_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class ServicePermissionRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "service_permissions"
    __table_args__ = (
        UniqueConstraint("service_key", name="uq_service_permissions_service_key"),
        Index("ix_service_permissions_service_key", "service_key"),
    )

    service_key: Mapped[str] = mapped_column(String(128), nullable=False)
    allowed_apis: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    allowed_events: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    allowed_storage: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    allowed_ai_tools: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    allowed_integrations: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
