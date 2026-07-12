# Partner Engine repositories — PostgreSQL async data access.

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.partner_engine import (
    Partner,
    PartnerAmlStatus,
    PartnerCommission,
    PartnerCommissionType,
    PartnerContact,
    PartnerKycStatus,
    PartnerLimit,
    PartnerRiskLevel,
    PartnerStatus,
    PartnerType,
    PartnerWallet,
    PartnerWalletType,
)


class PartnerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        partner_type: str,
        company_name: str,
        display_name: str | None = None,
        country: str | None = None,
        city: str | None = None,
        status: str = PartnerStatus.ACTIVE.value,
        risk_level: str = PartnerRiskLevel.LOW.value,
        kyc_status: str = PartnerKycStatus.NOT_STARTED.value,
        aml_status: str = PartnerAmlStatus.CLEAR.value,
        **extra: Any,
    ) -> Partner:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if partner_type not in {t.value for t in PartnerType}:
            raise ValueError(f"Invalid partner_type: {partner_type}")
        if status not in {s.value for s in PartnerStatus}:
            raise ValueError(f"Invalid status: {status}")

        partner = Partner(
            partner_type=partner_type,
            company_name=company_name,
            display_name=display_name or company_name,
            country=country,
            city=city,
            status=status,
            risk_level=risk_level,
            kyc_status=kyc_status,
            aml_status=aml_status,
        )
        self._session.add(partner)
        await self._session.flush()
        return partner

    async def get_by_id(self, partner_id: uuid.UUID) -> Partner | None:
        result = await self._session.execute(
            select(Partner).where(Partner.id == partner_id)
        )
        return result.scalar_one_or_none()

    async def update(
        self,
        partner_id: uuid.UUID,
        **fields: Any,
    ) -> Partner | None:
        partner = await self.get_by_id(partner_id)
        if partner is None:
            return None

        allowed = {
            "partner_type",
            "company_name",
            "display_name",
            "country",
            "city",
            "status",
            "risk_level",
            "kyc_status",
            "aml_status",
        }
        for key, value in fields.items():
            if key not in allowed:
                raise TypeError(f"Unsupported field: {key}")
            setattr(partner, key, value)
        await self._session.flush()
        return partner

    async def list_partners(
        self,
        *,
        partner_type: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[Partner]:
        stmt = select(Partner).order_by(Partner.created_at.desc()).limit(limit)
        if partner_type is not None:
            stmt = stmt.where(Partner.partner_type == partner_type)
        if status is not None:
            stmt = stmt.where(Partner.status == status)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def block(self, partner_id: uuid.UUID) -> Partner | None:
        return await self.update(
            partner_id,
            status=PartnerStatus.BLOCKED.value,
            aml_status=PartnerAmlStatus.BLOCKED.value,
        )

    async def approve_kyc(self, partner_id: uuid.UUID) -> Partner | None:
        return await self.update(
            partner_id,
            kyc_status=PartnerKycStatus.APPROVED.value,
        )

    async def reject_kyc(self, partner_id: uuid.UUID) -> Partner | None:
        return await self.update(
            partner_id,
            kyc_status=PartnerKycStatus.REJECTED.value,
            status=PartnerStatus.SUSPENDED.value,
        )


class PartnerContactRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        partner_id: uuid.UUID,
        full_name: str,
        position: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        telegram: str | None = None,
        whatsapp: str | None = None,
        is_primary: bool = False,
        **extra: Any,
    ) -> PartnerContact:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")

        if is_primary:
            await self._clear_primary(partner_id)

        contact = PartnerContact(
            partner_id=partner_id,
            full_name=full_name,
            position=position,
            phone=phone,
            email=email,
            telegram=telegram,
            whatsapp=whatsapp,
            is_primary=is_primary,
        )
        self._session.add(contact)
        await self._session.flush()
        return contact

    async def _clear_primary(self, partner_id: uuid.UUID) -> None:
        result = await self._session.execute(
            select(PartnerContact).where(
                PartnerContact.partner_id == partner_id,
                PartnerContact.is_primary.is_(True),
            )
        )
        for contact in result.scalars().all():
            contact.is_primary = False
        await self._session.flush()

    async def get_by_id(self, contact_id: uuid.UUID) -> PartnerContact | None:
        result = await self._session.execute(
            select(PartnerContact).where(PartnerContact.id == contact_id)
        )
        return result.scalar_one_or_none()

    async def list_by_partner(self, partner_id: uuid.UUID) -> list[PartnerContact]:
        result = await self._session.execute(
            select(PartnerContact)
            .where(PartnerContact.partner_id == partner_id)
            .order_by(PartnerContact.is_primary.desc(), PartnerContact.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_primary(self, partner_id: uuid.UUID) -> PartnerContact | None:
        result = await self._session.execute(
            select(PartnerContact).where(
                PartnerContact.partner_id == partner_id,
                PartnerContact.is_primary.is_(True),
            )
        )
        return result.scalar_one_or_none()


class PartnerWalletRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        partner_id: uuid.UUID,
        asset: str,
        wallet_type: str,
        wallet_address: str,
        is_active: bool = True,
        **extra: Any,
    ) -> PartnerWallet:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if wallet_type not in {w.value for w in PartnerWalletType}:
            raise ValueError(f"Invalid wallet_type: {wallet_type}")

        wallet = PartnerWallet(
            partner_id=partner_id,
            asset=asset,
            wallet_type=wallet_type,
            wallet_address=wallet_address,
            is_active=is_active,
        )
        self._session.add(wallet)
        await self._session.flush()
        return wallet

    async def get_by_id(self, wallet_id: uuid.UUID) -> PartnerWallet | None:
        result = await self._session.execute(
            select(PartnerWallet).where(PartnerWallet.id == wallet_id)
        )
        return result.scalar_one_or_none()

    async def list_by_partner(
        self,
        partner_id: uuid.UUID,
        *,
        active_only: bool = False,
    ) -> list[PartnerWallet]:
        stmt = select(PartnerWallet).where(PartnerWallet.partner_id == partner_id)
        if active_only:
            stmt = stmt.where(PartnerWallet.is_active.is_(True))
        stmt = stmt.order_by(PartnerWallet.created_at.asc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def deactivate(self, wallet_id: uuid.UUID) -> PartnerWallet | None:
        wallet = await self.get_by_id(wallet_id)
        if wallet is None:
            return None
        wallet.is_active = False
        await self._session.flush()
        return wallet


class PartnerLimitRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_or_create(self, partner_id: uuid.UUID) -> PartnerLimit:
        result = await self._session.execute(
            select(PartnerLimit).where(PartnerLimit.partner_id == partner_id)
        )
        limit = result.scalar_one_or_none()
        if limit is not None:
            return limit

        limit = PartnerLimit(partner_id=partner_id)
        self._session.add(limit)
        await self._session.flush()
        return limit

    async def get_by_partner(self, partner_id: uuid.UUID) -> PartnerLimit | None:
        result = await self._session.execute(
            select(PartnerLimit).where(PartnerLimit.partner_id == partner_id)
        )
        return result.scalar_one_or_none()

    async def update_limits(
        self,
        partner_id: uuid.UUID,
        *,
        daily_limit: Decimal | None = None,
        monthly_limit: Decimal | None = None,
    ) -> PartnerLimit:
        limit = await self.get_or_create(partner_id)
        if daily_limit is not None:
            if daily_limit < 0:
                raise ValueError("daily_limit must be non-negative")
            limit.daily_limit = daily_limit
        if monthly_limit is not None:
            if monthly_limit < 0:
                raise ValueError("monthly_limit must be non-negative")
            limit.monthly_limit = monthly_limit
        await self._session.flush()
        return limit

    async def record_volume(
        self,
        partner_id: uuid.UUID,
        amount: Decimal,
    ) -> tuple[PartnerLimit, bool, bool]:
        if amount < 0:
            raise ValueError("amount must be non-negative")

        limit = await self.get_or_create(partner_id)
        limit.current_daily_volume += amount
        limit.current_monthly_volume += amount
        await self._session.flush()

        daily_exceeded = (
            limit.daily_limit > 0 and limit.current_daily_volume > limit.daily_limit
        )
        monthly_exceeded = (
            limit.monthly_limit > 0
            and limit.current_monthly_volume > limit.monthly_limit
        )
        return limit, daily_exceeded, monthly_exceeded

    async def reset_daily_volume(self, partner_id: uuid.UUID) -> PartnerLimit | None:
        limit = await self.get_by_partner(partner_id)
        if limit is None:
            return None
        limit.current_daily_volume = Decimal("0")
        await self._session.flush()
        return limit

    async def reset_monthly_volume(self, partner_id: uuid.UUID) -> PartnerLimit | None:
        limit = await self.get_by_partner(partner_id)
        if limit is None:
            return None
        limit.current_monthly_volume = Decimal("0")
        await self._session.flush()
        return limit


class PartnerCommissionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        partner_id: uuid.UUID,
        asset: str,
        commission_type: str,
        value: Decimal,
        **extra: Any,
    ) -> PartnerCommission:
        if extra:
            raise TypeError(f"Unsupported fields: {', '.join(sorted(extra))}")
        if commission_type not in {c.value for c in PartnerCommissionType}:
            raise ValueError(f"Invalid commission_type: {commission_type}")
        if value < 0:
            raise ValueError("value must be non-negative")

        commission = PartnerCommission(
            partner_id=partner_id,
            asset=asset,
            commission_type=commission_type,
            value=value,
        )
        self._session.add(commission)
        await self._session.flush()
        return commission

    async def get_by_id(self, commission_id: uuid.UUID) -> PartnerCommission | None:
        result = await self._session.execute(
            select(PartnerCommission).where(PartnerCommission.id == commission_id)
        )
        return result.scalar_one_or_none()

    async def list_by_partner(self, partner_id: uuid.UUID) -> list[PartnerCommission]:
        result = await self._session.execute(
            select(PartnerCommission)
            .where(PartnerCommission.partner_id == partner_id)
            .order_by(PartnerCommission.asset.asc())
        )
        return list(result.scalars().all())

    async def update_value(
        self,
        commission_id: uuid.UUID,
        value: Decimal,
    ) -> PartnerCommission | None:
        if value < 0:
            raise ValueError("value must be non-negative")
        commission = await self.get_by_id(commission_id)
        if commission is None:
            return None
        commission.value = value
        await self._session.flush()
        return commission
