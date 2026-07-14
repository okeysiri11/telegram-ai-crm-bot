# Owner Payment Profile v1 repository.

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.owner_payment_profile_v1 import (
    OWNER_PAYMENT_PROFILE_DEFAULT_ID,
    OWNER_PAYMENT_PROFILE_SINGLETON_KEY,
    OwnerPaymentProfileV1,
)


class OwnerPaymentProfileV1Repository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_singleton(self) -> OwnerPaymentProfileV1 | None:
        result = await self._session.execute(
            select(OwnerPaymentProfileV1).where(
                OwnerPaymentProfileV1.profile_key == OWNER_PAYMENT_PROFILE_SINGLETON_KEY
            )
        )
        return result.scalar_one_or_none()

    async def get_or_create_singleton(self) -> OwnerPaymentProfileV1:
        row = await self.get_singleton()
        if row is not None:
            return row
        row = OwnerPaymentProfileV1(
            id=OWNER_PAYMENT_PROFILE_DEFAULT_ID,
            profile_key=OWNER_PAYMENT_PROFILE_SINGLETON_KEY,
            card_holder_name="Platform Services LLC",
            card_mask="**** **** **** 0000",
            iban="UA21322313000002600723356601",
            usdt_trc20_wallet="TXYZplatformWalletTRC20Example",
            usdt_erc20_wallet="0xPlatformWalletERC20Example",
            cash_instructions="Офис: Киев, ул. Примерная 1\nЧасы: Пн–Пт 10:00–18:00",
            card_enabled=True,
            iban_enabled=True,
            usdt_trc20_enabled=True,
            usdt_erc20_enabled=True,
            cash_enabled=True,
            default_payment_method="CARD",
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def update(self, profile_id, **fields) -> OwnerPaymentProfileV1 | None:
        result = await self._session.execute(
            select(OwnerPaymentProfileV1).where(OwnerPaymentProfileV1.id == profile_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        for key, value in fields.items():
            setattr(row, key, value)
        await self._session.flush()
        return row
