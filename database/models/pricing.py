# Pricing Engine models — sources, rules, spreads, markups.

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class PricingSourceType(str, enum.Enum):
    API = "API"
    MANUAL = "MANUAL"
    AGGREGATOR = "AGGREGATOR"
    INTERNAL = "INTERNAL"


class PricingRuleType(str, enum.Enum):
    DEFAULT = "DEFAULT"
    DYNAMIC = "DYNAMIC"
    PARTNER = "PARTNER"
    MANAGER = "MANAGER"
    VIP = "VIP"


class SpreadType(str, enum.Enum):
    FIXED = "FIXED"
    PERCENTAGE = "PERCENTAGE"


class MarkupType(str, enum.Enum):
    FIXED = "FIXED"
    PERCENTAGE = "PERCENTAGE"


class MarkupAppliesTo(str, enum.Enum):
    PARTNER = "PARTNER"
    MANAGER = "MANAGER"
    VIP = "VIP"
    CLIENT = "CLIENT"
    GLOBAL = "GLOBAL"


class PricingSource(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "pricing_engine_sources"
    __table_args__ = (
        UniqueConstraint("code", name="uq_pricing_engine_sources_code"),
        CheckConstraint("base_rate > 0", name="ck_pricing_engine_sources_base_rate"),
        Index("ix_pricing_engine_sources_asset_pair", "asset_in", "asset_out"),
        Index("ix_pricing_engine_sources_is_active", "is_active"),
    )

    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    asset_in: Mapped[str] = mapped_column(String(20), nullable=False)
    asset_out: Mapped[str] = mapped_column(String(20), nullable=False)
    base_rate: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_fetched_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    metadata_: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"<PricingSource id={self.id} code={self.code} "
            f"{self.asset_in}/{self.asset_out} rate={self.base_rate}>"
        )


class PricingRule(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "pricing_engine_rules"
    __table_args__ = (
        UniqueConstraint("code", name="uq_pricing_engine_rules_code"),
        Index("ix_pricing_engine_rules_rule_type", "rule_type"),
        Index("ix_pricing_engine_rules_asset_pair", "asset_in", "asset_out"),
        Index("ix_pricing_engine_rules_partner_id", "partner_id"),
        Index("ix_pricing_engine_rules_manager_id", "manager_id"),
        Index("ix_pricing_engine_rules_vip_user_id", "vip_user_id"),
        Index("ix_pricing_engine_rules_is_active", "is_active"),
    )

    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    rule_type: Mapped[str] = mapped_column(String(32), nullable=False)
    asset_in: Mapped[str] = mapped_column(String(20), nullable=False)
    asset_out: Mapped[str] = mapped_column(String(20), nullable=False)
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pricing_engine_sources.id", ondelete="SET NULL"),
        nullable=True,
    )
    partner_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    manager_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    vip_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    conditions: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<PricingRule id={self.id} code={self.code} "
            f"type={self.rule_type} {self.asset_in}/{self.asset_out}>"
        )


class Spread(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "pricing_engine_spreads"
    __table_args__ = (
        CheckConstraint("bid_spread >= 0", name="ck_pricing_engine_spreads_bid"),
        CheckConstraint("ask_spread >= 0", name="ck_pricing_engine_spreads_ask"),
        Index("ix_pricing_engine_spreads_rule_id", "rule_id"),
        Index("ix_pricing_engine_spreads_source_id", "source_id"),
        Index("ix_pricing_engine_spreads_asset_pair", "asset_in", "asset_out"),
        Index("ix_pricing_engine_spreads_is_active", "is_active"),
    )

    rule_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pricing_engine_rules.id", ondelete="CASCADE"),
        nullable=True,
    )
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pricing_engine_sources.id", ondelete="SET NULL"),
        nullable=True,
    )
    asset_in: Mapped[str] = mapped_column(String(20), nullable=False)
    asset_out: Mapped[str] = mapped_column(String(20), nullable=False)
    spread_type: Mapped[str] = mapped_column(String(20), nullable=False)
    bid_spread: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    ask_spread: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    min_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)
    max_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 8), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return (
            f"<Spread id={self.id} {self.asset_in}/{self.asset_out} "
            f"bid={self.bid_spread} ask={self.ask_spread}>"
        )


class Markup(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "pricing_engine_markups"
    __table_args__ = (
        Index("ix_pricing_engine_markups_rule_id", "rule_id"),
        Index("ix_pricing_engine_markups_applies_to", "applies_to"),
        Index("ix_pricing_engine_markups_target_id", "target_id"),
        Index("ix_pricing_engine_markups_is_active", "is_active"),
    )

    rule_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pricing_engine_rules.id", ondelete="CASCADE"),
        nullable=True,
    )
    applies_to: Mapped[str] = mapped_column(String(32), nullable=False)
    target_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    markup_type: Mapped[str] = mapped_column(String(20), nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    asset_in: Mapped[str | None] = mapped_column(String(20), nullable=True)
    asset_out: Mapped[str | None] = mapped_column(String(20), nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<Markup id={self.id} applies_to={self.applies_to} "
            f"type={self.markup_type} value={self.value}>"
        )
