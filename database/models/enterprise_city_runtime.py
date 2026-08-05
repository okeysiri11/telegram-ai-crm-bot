"""Enterprise City Runtime ORM — Sprint 37.0."""

from __future__ import annotations

from sqlalchemy import Float, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin, VersionMixin


class PlatformRegistryRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "platform_registry"
    __table_args__ = (
        UniqueConstraint("service_key", name="uq_platform_registry_service_key"),
        Index("ix_platform_registry_category", "category"),
    )

    service_key: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    display_name: Mapped[str] = mapped_column(String(256), nullable=False)
    route: Mapped[str] = mapped_column(String(256), nullable=False, default="/platform")
    category: Mapped[str] = mapped_column(String(64), nullable=False, default="platform")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="healthy")
    sprint: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    api_prefixes_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    dependencies_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class PlatformSessionRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "platform_sessions"
    __table_args__ = (
        UniqueConstraint("session_key", name="uq_platform_sessions_session_key"),
        Index("ix_platform_sessions_user_id", "user_id"),
    )

    session_key: Mapped[str] = mapped_column(String(128), nullable=False)
    user_id: Mapped[str] = mapped_column(String(128), nullable=False)
    roles_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    permissions_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    shared_context_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    shared_memory_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    active_module: Mapped[str | None] = mapped_column(String(128), nullable=True)
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class PlatformMetricRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "platform_metrics"
    __table_args__ = (
        UniqueConstraint("metric_key", name="uq_platform_metrics_metric_key"),
        Index("ix_platform_metrics_name", "name"),
        Index("ix_platform_metrics_category", "category"),
    )

    metric_key: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    unit: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    category: Mapped[str] = mapped_column(String(64), nullable=False, default="kpi")
    labels_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class PlatformHealthRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "platform_health"
    __table_args__ = (
        UniqueConstraint("component_key", name="uq_platform_health_component_key"),
        Index("ix_platform_health_level", "level"),
    )

    component_key: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    level: Mapped[str] = mapped_column(String(32), nullable=False, default="healthy")
    message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class PlatformUsageRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "platform_usage"
    __table_args__ = (
        Index("ix_platform_usage_module", "module"),
        Index("ix_platform_usage_action", "action"),
    )

    usage_key: Mapped[str] = mapped_column(String(128), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    module: Mapped[str] = mapped_column(String(128), nullable=False)
    user_id: Mapped[str] = mapped_column(String(128), nullable=False, default="system")
    details_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)


class PlatformConfigurationRow(UUIDPrimaryKeyMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "platform_configuration"
    __table_args__ = (
        UniqueConstraint("config_key", name="uq_platform_configuration_config_key"),
        Index("ix_platform_configuration_category", "category"),
    )

    config_key: Mapped[str] = mapped_column(String(256), nullable=False)
    value_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    category: Mapped[str] = mapped_column(String(64), nullable=False, default="general")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
