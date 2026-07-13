# Channel Integration Engine v1 — tenant-scoped social channel connections.

from __future__ import annotations

import enum
import uuid

from sqlalchemy import ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class IntegrationChannelType(str, enum.Enum):
    TELEGRAM_CHANNEL = "TELEGRAM_CHANNEL"
    TELEGRAM_GROUP = "TELEGRAM_GROUP"
    INSTAGRAM = "INSTAGRAM"
    FACEBOOK = "FACEBOOK"
    TIKTOK = "TIKTOK"
    WHATSAPP_BUSINESS = "WHATSAPP_BUSINESS"


INTEGRATION_CHANNEL_TYPES = frozenset(c.value for c in IntegrationChannelType)


class ChannelPermission(str, enum.Enum):
    READ_ONLY = "READ_ONLY"
    POST_ONLY = "POST_ONLY"
    POST_AND_ANALYTICS = "POST_AND_ANALYTICS"


CHANNEL_PERMISSIONS = frozenset(p.value for p in ChannelPermission)


class ChannelIntegrationStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    DISCONNECTED = "DISCONNECTED"
    ERROR = "ERROR"


class ChannelIntegration(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "channel_integration_engine_v1_channels"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "channel_type",
            "channel_id",
            name="uq_channel_integration_engine_v1_channels_tenant_type_id",
        ),
        Index("ix_channel_integration_engine_v1_channels_tenant", "tenant_id"),
        Index("ix_channel_integration_engine_v1_channels_company", "company_id"),
        Index("ix_channel_integration_engine_v1_channels_type", "channel_type"),
        Index("ix_channel_integration_engine_v1_channels_status", "status"),
        Index("ix_channel_integration_engine_v1_channels_channel_id", "channel_id"),
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
    channel_id: Mapped[str] = mapped_column(String(120), nullable=False)
    channel_type: Mapped[str] = mapped_column(String(40), nullable=False)
    permissions: Mapped[str] = mapped_column(String(40), nullable=False)
    token_reference: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        default=ChannelIntegrationStatus.ACTIVE.value,
        nullable=False,
    )
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<ChannelIntegration tenant={self.tenant_id} "
            f"type={self.channel_type} channel={self.channel_id}>"
        )
