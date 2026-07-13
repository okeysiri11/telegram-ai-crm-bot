# Automotive Partner Integration v1 repositories.

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.automotive_partner_integration import (
    AutomotiveDealerSource,
    AutomotiveInsuranceOffer,
    AutomotivePartnerBranding,
    AutomotivePartnerCta,
    AutomotivePartnerProduct,
    AutomotiveRegistryPartner,
)


class AutomotivePartnerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_partner_by_id(self, partner_id: uuid.UUID) -> AutomotiveRegistryPartner | None:
        result = await self._session.execute(
            select(AutomotiveRegistryPartner).where(AutomotiveRegistryPartner.id == partner_id)
        )
        return result.scalar_one_or_none()

    async def get_partner_by_code(self, code: str) -> AutomotiveRegistryPartner | None:
        result = await self._session.execute(
            select(AutomotiveRegistryPartner).where(
                AutomotiveRegistryPartner.code == code,
                AutomotiveRegistryPartner.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def list_partners(
        self,
        *,
        partner_type: str | None = None,
    ) -> list[AutomotiveRegistryPartner]:
        stmt = select(AutomotiveRegistryPartner).where(
            AutomotiveRegistryPartner.is_active.is_(True)
        )
        if partner_type:
            stmt = stmt.where(AutomotiveRegistryPartner.partner_type == partner_type)
        stmt = stmt.order_by(AutomotiveRegistryPartner.name)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_products_for_partner(
        self,
        partner_id: uuid.UUID,
        *,
        active_only: bool = True,
    ) -> list[AutomotivePartnerProduct]:
        stmt = (
            select(AutomotivePartnerProduct)
            .where(AutomotivePartnerProduct.partner_id == partner_id)
            .order_by(AutomotivePartnerProduct.sort_order, AutomotivePartnerProduct.name)
        )
        if active_only:
            stmt = stmt.where(AutomotivePartnerProduct.is_active.is_(True))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_product_by_code(
        self,
        partner_id: uuid.UUID,
        product_code: str,
    ) -> AutomotivePartnerProduct | None:
        result = await self._session.execute(
            select(AutomotivePartnerProduct).where(
                AutomotivePartnerProduct.partner_id == partner_id,
                AutomotivePartnerProduct.product_code == product_code,
            )
        )
        return result.scalar_one_or_none()

    async def list_dealer_sources(
        self,
        *,
        tenant_id: uuid.UUID | None = None,
        partner_id: uuid.UUID | None = None,
    ) -> list[AutomotiveDealerSource]:
        stmt = select(AutomotiveDealerSource).where(
            AutomotiveDealerSource.is_active.is_(True)
        )
        if partner_id:
            stmt = stmt.where(AutomotiveDealerSource.partner_id == partner_id)
        if tenant_id is None:
            stmt = stmt.where(AutomotiveDealerSource.tenant_id.is_(None))
        else:
            stmt = stmt.where(
                (AutomotiveDealerSource.tenant_id == tenant_id)
                | (AutomotiveDealerSource.tenant_id.is_(None))
            )
        stmt = stmt.order_by(AutomotiveDealerSource.source_code)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_insurance_offers(
        self,
        *,
        partner_id: uuid.UUID | None = None,
        tenant_id: uuid.UUID | None = None,
    ) -> list[AutomotiveInsuranceOffer]:
        stmt = select(AutomotiveInsuranceOffer).where(
            AutomotiveInsuranceOffer.is_active.is_(True)
        )
        if partner_id:
            stmt = stmt.where(AutomotiveInsuranceOffer.partner_id == partner_id)
        if tenant_id is None:
            stmt = stmt.where(AutomotiveInsuranceOffer.tenant_id.is_(None))
        else:
            stmt = stmt.where(
                (AutomotiveInsuranceOffer.tenant_id == tenant_id)
                | (AutomotiveInsuranceOffer.tenant_id.is_(None))
            )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_insurance_offer_for_product(
        self,
        product_id: uuid.UUID,
        *,
        tenant_id: uuid.UUID | None = None,
    ) -> AutomotiveInsuranceOffer | None:
        stmt = select(AutomotiveInsuranceOffer).where(
            AutomotiveInsuranceOffer.product_id == product_id,
            AutomotiveInsuranceOffer.is_active.is_(True),
        )
        if tenant_id is None:
            stmt = stmt.where(AutomotiveInsuranceOffer.tenant_id.is_(None))
        else:
            stmt = stmt.where(
                (AutomotiveInsuranceOffer.tenant_id == tenant_id)
                | (AutomotiveInsuranceOffer.tenant_id.is_(None))
            )
        stmt = stmt.order_by(AutomotiveInsuranceOffer.created_at.desc()).limit(1)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_branding(self, partner_id: uuid.UUID) -> AutomotivePartnerBranding | None:
        result = await self._session.execute(
            select(AutomotivePartnerBranding).where(
                AutomotivePartnerBranding.partner_id == partner_id,
                AutomotivePartnerBranding.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def list_ctas(self, partner_id: uuid.UUID) -> list[AutomotivePartnerCta]:
        result = await self._session.execute(
            select(AutomotivePartnerCta)
            .where(
                AutomotivePartnerCta.partner_id == partner_id,
                AutomotivePartnerCta.is_active.is_(True),
            )
            .order_by(AutomotivePartnerCta.sort_order, AutomotivePartnerCta.label)
        )
        return list(result.scalars().all())
