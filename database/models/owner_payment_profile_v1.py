# Owner Payment Profile v1 — singleton owner payment settings.

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from database.models.payment_engine_v1 import PaymentEngineMethod

OWNER_PAYMENT_PROFILE_SINGLETON_KEY = "default"
OWNER_PAYMENT_PROFILE_DEFAULT_ID = uuid.UUID("00000000-0000-4000-8000-000000000001")

METHOD_ENABLE_FIELDS = {
    PaymentEngineMethod.CARD.value: "card_enabled",
    PaymentEngineMethod.IBAN.value: "iban_enabled",
    PaymentEngineMethod.USDT_TRC20.value: "usdt_trc20_enabled",
    PaymentEngineMethod.USDT_ERC20.value: "usdt_erc20_enabled",
    PaymentEngineMethod.CASH.value: "cash_enabled",
}


class OwnerPaymentProfileV1(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "owner_payment_profile_v1"
    __table_args__ = (
        UniqueConstraint("profile_key", name="uq_owner_payment_profile_v1_key"),
    )

    profile_key: Mapped[str] = mapped_column(
        String(50),
        default=OWNER_PAYMENT_PROFILE_SINGLETON_KEY,
        nullable=False,
    )

    card_holder_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    card_mask: Mapped[str | None] = mapped_column(String(64), nullable=True)
    iban: Mapped[str | None] = mapped_column(String(64), nullable=True)
    usdt_trc20_wallet: Mapped[str | None] = mapped_column(String(128), nullable=True)
    usdt_erc20_wallet: Mapped[str | None] = mapped_column(String(128), nullable=True)
    cash_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)

    card_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    iban_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    usdt_trc20_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    usdt_erc20_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    cash_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    default_payment_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
