# Communication Hub v1 — unified inbox, routing, campaigns across channels.

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class HubChannelType(str, enum.Enum):
    TELEGRAM = "TELEGRAM"
    INSTAGRAM = "INSTAGRAM"
    FACEBOOK = "FACEBOOK"
    TIKTOK = "TIKTOK"
    WEBSITE_CHAT = "WEBSITE_CHAT"


class HubMessageDirection(str, enum.Enum):
    INBOUND = "INBOUND"
    OUTBOUND = "OUTBOUND"


class HubMessageStatus(str, enum.Enum):
    NEW = "NEW"
    ROUTED = "ROUTED"
    REPLIED = "REPLIED"
    ESCALATED = "ESCALATED"
    CLOSED = "CLOSED"


class HubSenderType(str, enum.Enum):
    CUSTOMER = "CUSTOMER"
    BOT = "BOT"
    AGENT = "AGENT"
    SYSTEM = "SYSTEM"


class HubCampaignStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"


HUB_CHANNEL_TYPES = frozenset(c.value for c in HubChannelType)
HUB_MESSAGE_DIRECTIONS = frozenset(d.value for d in HubMessageDirection)
HUB_MESSAGE_STATUSES = frozenset(s.value for s in HubMessageStatus)
HUB_SENDER_TYPES = frozenset(s.value for s in HubSenderType)
HUB_CAMPAIGN_STATUSES = frozenset(s.value for s in HubCampaignStatus)


class CommunicationChannel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "communication_hub_v1_channels"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "channel_type",
            "external_id",
            name="uq_communication_hub_v1_channels_tenant_type_ext",
        ),
        Index("ix_communication_hub_v1_channels_tenant", "tenant_id"),
        Index("ix_communication_hub_v1_channels_type", "channel_type"),
        Index("ix_communication_hub_v1_channels_active", "is_active"),
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
    channel_type: Mapped[str] = mapped_column(String(30), nullable=False)
    external_id: Mapped[str] = mapped_column(String(120), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<CommunicationChannel {self.channel_type} name={self.name}>"


class CommunicationCampaign(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "communication_hub_v1_campaigns"
    __table_args__ = (
        Index("ix_communication_hub_v1_campaigns_tenant", "tenant_id"),
        Index("ix_communication_hub_v1_campaigns_status", "status"),
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
    channel_types: Mapped[list] = mapped_column(JSONB, nullable=False)
    message_template: Mapped[str | None] = mapped_column(Text, nullable=True)
    auto_response_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    routing_rules: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(
        String(30),
        default=HubCampaignStatus.DRAFT.value,
        nullable=False,
    )
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<CommunicationCampaign name={self.name} status={self.status}>"


class CommunicationMessage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "communication_hub_v1_messages"
    __table_args__ = (
        Index("ix_communication_hub_v1_messages_tenant", "tenant_id"),
        Index("ix_communication_hub_v1_messages_channel", "channel_id"),
        Index("ix_communication_hub_v1_messages_conversation", "conversation_id"),
        Index("ix_communication_hub_v1_messages_status", "status"),
        Index("ix_communication_hub_v1_messages_sales_lead", "sales_lead_id"),
        Index("ix_communication_hub_v1_messages_manager", "assigned_manager_id"),
    )

    channel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("communication_hub_v1_channels.id", ondelete="CASCADE"),
        nullable=False,
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
    conversation_id: Mapped[str] = mapped_column(String(120), nullable=False)
    direction: Mapped[str] = mapped_column(String(20), nullable=False)
    sender_type: Mapped[str] = mapped_column(String(20), nullable=False)
    sender_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    message_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        default=HubMessageStatus.NEW.value,
        nullable=False,
    )
    sales_lead_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_sales_agent_v1_sales_leads.id", ondelete="SET NULL"),
        nullable=True,
    )
    automation_lead_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lead_automation_engine_v1_leads.id", ondelete="SET NULL"),
        nullable=True,
    )
    assigned_manager_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("communication_hub_v1_campaigns.id", ondelete="SET NULL"),
        nullable=True,
    )
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    def __repr__(self) -> str:
        return f"<CommunicationMessage conv={self.conversation_id} status={self.status}>"

