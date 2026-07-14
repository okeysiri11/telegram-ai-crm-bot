# Anti Loss Layer v1 — duplicate prevention and merge tracking.

from __future__ import annotations

import enum
import uuid

from sqlalchemy import BigInteger, Boolean, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import CreatedAtMixin, TimestampMixin, UUIDPrimaryKeyMixin


class AntiLossEntityType(str, enum.Enum):
    LEAD = "lead"
    DEAL = "deal"


class AntiLossFingerprintType(str, enum.Enum):
    VIN = "vin"
    PHONE = "phone"
    TELEGRAM_ID = "telegram_id"
    VEHICLE_REGISTRATION = "vehicle_registration"
    AGRO_BUNDLE = "agro_bundle"


class AntiLossEventType(str, enum.Enum):
    LEAD_DUPLICATE_PREVENTED = "lead_duplicate_prevented"
    DEAL_DUPLICATE_PREVENTED = "deal_duplicate_prevented"
    LEAD_MERGED = "lead_merged"
    DEAL_MERGED = "deal_merged"


class AntiLossLayerV1Fingerprint(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "anti_loss_layer_v1_fingerprints"
    __table_args__ = (
        UniqueConstraint(
            "vertical",
            "fingerprint_type",
            "fingerprint_value",
            name="uq_anti_loss_v1_fingerprint",
        ),
        Index("ix_anti_loss_v1_fp_entity", "entity_type", "entity_id"),
        Index("ix_anti_loss_v1_fp_vertical", "vertical"),
        Index("ix_anti_loss_v1_fp_active", "is_active"),
    )

    entity_type: Mapped[str] = mapped_column(String(20), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    vertical: Mapped[str] = mapped_column(String(50), nullable=False)
    fingerprint_type: Mapped[str] = mapped_column(String(40), nullable=False)
    fingerprint_value: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class AntiLossLayerV1Event(CreatedAtMixin, UUIDPrimaryKeyMixin, Base):
    __tablename__ = "anti_loss_layer_v1_events"
    __table_args__ = (
        Index("ix_anti_loss_v1_events_type", "event_type"),
        Index("ix_anti_loss_v1_events_vertical", "vertical"),
        Index("ix_anti_loss_v1_events_entity", "entity_id"),
    )

    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    vertical: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(20), nullable=False)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    matched_entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    match_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    actor_telegram_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
