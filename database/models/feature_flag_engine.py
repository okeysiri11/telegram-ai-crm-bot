# Feature Flag Engine v1 — gradual rollout, targeting, and A/B testing.

from __future__ import annotations

import enum
import uuid

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
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
from database.models.mixins import CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin


class FeatureFlagStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    ARCHIVED = "ARCHIVED"


class AssignmentType(str, enum.Enum):
    COMPANY = "COMPANY"
    ROLE = "ROLE"
    USER = "USER"
    AB_VARIANT = "AB_VARIANT"


class FeatureHistoryAction(str, enum.Enum):
    CREATED = "CREATED"
    UPDATED = "UPDATED"
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"
    ASSIGNED = "ASSIGNED"
    UNASSIGNED = "UNASSIGNED"
    ROLLOUT_CHANGED = "ROLLOUT_CHANGED"
    VARIANT_CHANGED = "VARIANT_CHANGED"


class FeatureFlag(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "feature_flag_engine_v1_feature_flags"
    __table_args__ = (
        UniqueConstraint("flag_key", name="uq_feature_flag_engine_v1_flags_key"),
        Index("ix_feature_flag_engine_v1_flags_status", "status"),
    )

    flag_key: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    rollout_percentage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default=FeatureFlagStatus.ACTIVE.value,
        nullable=False,
    )
    default_variant: Mapped[str] = mapped_column(String(32), default="control", nullable=False)
    config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    owner_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    def __repr__(self) -> str:
        return f"<FeatureFlag key={self.flag_key} enabled={self.enabled}>"


class FeatureAssignment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "feature_flag_engine_v1_feature_assignments"
    __table_args__ = (
        Index("ix_feature_flag_engine_v1_assign_flag", "flag_id"),
        Index("ix_feature_flag_engine_v1_assign_type", "assignment_type"),
        Index("ix_feature_flag_engine_v1_assign_target", "target_key"),
        UniqueConstraint(
            "flag_id",
            "assignment_type",
            "target_key",
            name="uq_feature_flag_engine_v1_assignments",
        ),
    )

    flag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("feature_flag_engine_v1_feature_flags.id", ondelete="CASCADE"),
        nullable=False,
    )
    assignment_type: Mapped[str] = mapped_column(String(20), nullable=False)
    target_key: Mapped[str] = mapped_column(String(128), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    rollout_percentage: Mapped[int | None] = mapped_column(Integer, nullable=True)
    variant: Mapped[str | None] = mapped_column(String(32), nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<FeatureAssignment flag={self.flag_id} "
            f"type={self.assignment_type} target={self.target_key}>"
        )


class FeatureHistory(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "feature_flag_engine_v1_feature_history"
    __table_args__ = (
        Index("ix_feature_flag_engine_v1_hist_flag", "flag_id"),
        Index("ix_feature_flag_engine_v1_hist_action", "action"),
    )

    flag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("feature_flag_engine_v1_feature_flags.id", ondelete="CASCADE"),
        nullable=False,
    )
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    actor_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    old_value: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    new_value: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<FeatureHistory flag={self.flag_id} action={self.action}>"
