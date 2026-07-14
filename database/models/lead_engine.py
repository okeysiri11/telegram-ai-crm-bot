# Universal Lead Engine v1 — cross-vertical lead tracking.

from __future__ import annotations

import enum
import uuid

from sqlalchemy import BigInteger, Boolean, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class LeadEngineStatus(str, enum.Enum):
    NEW = "NEW"
    CONTACTED = "CONTACTED"
    QUALIFIED = "QUALIFIED"
    NEGOTIATION = "NEGOTIATION"
    PAYMENT_PENDING = "PAYMENT_PENDING"
    WON = "WON"
    LOST = "LOST"


LEAD_ENGINE_STATUSES = frozenset(s.value for s in LeadEngineStatus)
LEAD_ENGINE_TERMINAL_STATUSES = frozenset({
    LeadEngineStatus.WON.value,
    LeadEngineStatus.LOST.value,
})
LEAD_ENGINE_OPEN_STATUSES = LEAD_ENGINE_STATUSES - LEAD_ENGINE_TERMINAL_STATUSES


class LeadEngineLead(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "lead_engine_v1_leads"
    __table_args__ = (
        Index("ix_lead_engine_v1_vertical", "vertical"),
        Index("ix_lead_engine_v1_status", "status"),
        Index("ix_lead_engine_v1_pipeline_stage", "pipeline_stage"),
        Index("ix_lead_engine_v1_source_link", "source_link"),
        Index("ix_lead_engine_v1_telegram", "telegram_user_id"),
        Index("ix_lead_engine_v1_phone_norm", "phone_normalized"),
        Index("ix_lead_engine_v1_vin", "vin"),
        Index("ix_lead_engine_v1_vehicle_reg", "vehicle_registration"),
        Index("ix_lead_engine_v1_manager", "assigned_manager_id"),
        Index("ix_lead_engine_v1_created", "created_at"),
        Index("ix_lead_engine_v1_utm_source", "utm_source"),
        Index("ix_lead_engine_v1_utm_campaign", "utm_campaign"),
        Index("ix_lead_engine_v1_marketing_source", "marketing_source"),
        Index("ix_lead_engine_v1_referrer", "referrer"),
    )

    vertical: Mapped[str] = mapped_column(String(50), nullable=False)
    role: Mapped[str | None] = mapped_column(String(50), nullable=True)
    language: Mapped[str | None] = mapped_column(String(8), nullable=True)
    source_link: Mapped[str | None] = mapped_column(String(255), nullable=True)
    utm_source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    utm_campaign: Mapped[str | None] = mapped_column(String(255), nullable=True)
    utm_medium: Mapped[str | None] = mapped_column(String(255), nullable=True)
    referral_code: Mapped[str | None] = mapped_column(String(255), nullable=True)
    referrer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    marketing_source: Mapped[str | None] = mapped_column(String(50), nullable=True)

    telegram_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    telegram_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    phone_normalized: Mapped[str | None] = mapped_column(String(32), nullable=True)

    vin: Mapped[str | None] = mapped_column(String(17), nullable=True)
    vehicle_registration: Mapped[str | None] = mapped_column(String(32), nullable=True)
    agro_product: Mapped[str | None] = mapped_column(String(120), nullable=True)
    agro_volume: Mapped[str | None] = mapped_column(String(64), nullable=True)
    agro_location: Mapped[str | None] = mapped_column(String(120), nullable=True)

    client_request_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    client_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    client_photo_file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    duplicate_of_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lead_engine_v1_leads.id", ondelete="SET NULL"),
        nullable=True,
    )
    merged_into_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lead_engine_v1_leads.id", ondelete="SET NULL"),
        nullable=True,
    )

    assigned_manager_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default=LeadEngineStatus.NEW.value,
        nullable=False,
    )
    pipeline_stage: Mapped[str] = mapped_column(
        String(50),
        default=LeadEngineStatus.NEW.value,
        nullable=False,
    )
