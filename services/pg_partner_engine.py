# Partner Engine v1 — PostgreSQL partner and counterparty management.

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from config import OWNER_ID
from database.models.audit_log import AuditAction
from database.models.partner_engine import (
    Partner,
    PartnerCommission,
    PartnerContact,
    PartnerLimit,
    PartnerStatus,
    PartnerWallet,
)
from database.session import get_session
from repositories.audit_repository import AuditRepository
from repositories.partner_engine_repositories import (
    PartnerCommissionRepository,
    PartnerContactRepository,
    PartnerLimitRepository,
    PartnerRepository,
    PartnerWalletRepository,
)
from repositories.user_role_repository import UserRoleRepository

PARTNER_ADMIN_ROLES = frozenset({"OWNER", "ADMIN", "MANAGER"})
PARTNER_WRITE_ROLES = frozenset({"OWNER", "ADMIN", "MANAGER"})


class PartnerEngineError(Exception):
    pass


class PermissionDeniedError(PartnerEngineError):
    pass


def format_partner(partner: Partner) -> str:
    return (
        f"Partner `{partner.id}`\n"
        f"Type: {partner.partner_type}\n"
        f"Company: {partner.company_name}\n"
        f"Display: {partner.display_name or '—'}\n"
        f"Location: {partner.city or '—'}, {partner.country or '—'}\n"
        f"Status: {partner.status}\n"
        f"Risk: {partner.risk_level}\n"
        f"KYC: {partner.kyc_status} | AML: {partner.aml_status}"
    )


class PartnerEngine:
    @staticmethod
    async def user_can_read(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in PARTNER_ADMIN_ROLES for role in roles)

    @staticmethod
    async def user_can_write(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in PARTNER_WRITE_ROLES for role in roles)

    @staticmethod
    async def _audit(
        session,
        *,
        user_id: int,
        action: str,
        entity_id: str,
        old_value: dict | None = None,
        new_value: dict | None = None,
    ) -> None:
        await AuditRepository(session).create_log(
            user_id=user_id,
            entity_type="partner",
            entity_id=entity_id,
            action=action,
            old_value=old_value,
            new_value=new_value,
        )

    @staticmethod
    async def _publish_event(
        event_type: str,
        partner_id: uuid.UUID,
        payload: dict[str, Any],
    ) -> None:
        try:
            from events.crm_publisher import publish_crm_event

            await publish_crm_event(
                event_type,
                "partner",
                partner_id,
                payload,
            )
        except Exception:
            pass

    @staticmethod
    def _partner_snapshot(partner: Partner) -> dict[str, Any]:
        return {
            "id": str(partner.id),
            "partner_type": partner.partner_type,
            "company_name": partner.company_name,
            "display_name": partner.display_name,
            "country": partner.country,
            "city": partner.city,
            "status": partner.status,
            "risk_level": partner.risk_level,
            "kyc_status": partner.kyc_status,
            "aml_status": partner.aml_status,
        }

    @staticmethod
    async def create_partner(
        actor_id: int,
        *,
        partner_type: str,
        company_name: str,
        display_name: str | None = None,
        country: str | None = None,
        city: str | None = None,
        risk_level: str = "LOW",
        contact: dict[str, Any] | None = None,
        daily_limit: Decimal | None = None,
        monthly_limit: Decimal | None = None,
    ) -> Partner:
        if not await PartnerEngine.user_can_write(actor_id):
            raise PermissionDeniedError("Access denied")

        async with get_session() as session:
            repo = PartnerRepository(session)
            partner = await repo.create(
                partner_type=partner_type,
                company_name=company_name,
                display_name=display_name,
                country=country,
                city=city,
                risk_level=risk_level,
            )

            if contact:
                await PartnerContactRepository(session).create(
                    partner_id=partner.id,
                    is_primary=True,
                    **contact,
                )

            if daily_limit is not None or monthly_limit is not None:
                await PartnerLimitRepository(session).update_limits(
                    partner.id,
                    daily_limit=daily_limit,
                    monthly_limit=monthly_limit,
                )

            await PartnerEngine._audit(
                session,
                user_id=actor_id,
                action=AuditAction.CREATE_PARTNER.value,
                entity_id=str(partner.id),
                new_value=PartnerEngine._partner_snapshot(partner),
            )
            await session.flush()

        await PartnerEngine._publish_event(
            "partner.created",
            partner.id,
            PartnerEngine._partner_snapshot(partner),
        )
        return partner

    @staticmethod
    async def get_partner(partner_id: uuid.UUID, actor_id: int) -> Partner | None:
        if not await PartnerEngine.user_can_read(actor_id):
            raise PermissionDeniedError("Access denied")
        async with get_session() as session:
            return await PartnerRepository(session).get_by_id(partner_id)

    @staticmethod
    async def list_partners(
        actor_id: int,
        *,
        partner_type: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[Partner]:
        if not await PartnerEngine.user_can_read(actor_id):
            raise PermissionDeniedError("Access denied")
        async with get_session() as session:
            return await PartnerRepository(session).list_partners(
                partner_type=partner_type,
                status=status,
                limit=limit,
            )

    @staticmethod
    async def update_partner(
        actor_id: int,
        partner_id: uuid.UUID,
        **fields: Any,
    ) -> Partner:
        if not await PartnerEngine.user_can_write(actor_id):
            raise PermissionDeniedError("Access denied")

        async with get_session() as session:
            repo = PartnerRepository(session)
            existing = await repo.get_by_id(partner_id)
            if existing is None:
                raise PartnerEngineError(f"Partner not found: {partner_id}")

            old_value = PartnerEngine._partner_snapshot(existing)
            partner = await repo.update(partner_id, **fields)
            if partner is None:
                raise PartnerEngineError(f"Partner not found: {partner_id}")

            await PartnerEngine._audit(
                session,
                user_id=actor_id,
                action=AuditAction.UPDATE_PARTNER.value,
                entity_id=str(partner_id),
                old_value=old_value,
                new_value=PartnerEngine._partner_snapshot(partner),
            )

        await PartnerEngine._publish_event(
            "partner.updated",
            partner_id,
            {
                "old": old_value,
                "new": PartnerEngine._partner_snapshot(partner),
            },
        )
        return partner

    @staticmethod
    async def block_partner(actor_id: int, partner_id: uuid.UUID) -> Partner:
        if not await PartnerEngine.user_can_write(actor_id):
            raise PermissionDeniedError("Access denied")

        async with get_session() as session:
            repo = PartnerRepository(session)
            existing = await repo.get_by_id(partner_id)
            if existing is None:
                raise PartnerEngineError(f"Partner not found: {partner_id}")

            old_value = PartnerEngine._partner_snapshot(existing)
            partner = await repo.block(partner_id)
            if partner is None:
                raise PartnerEngineError(f"Partner not found: {partner_id}")

            await PartnerEngine._audit(
                session,
                user_id=actor_id,
                action=AuditAction.BLOCK_PARTNER.value,
                entity_id=str(partner_id),
                old_value=old_value,
                new_value=PartnerEngine._partner_snapshot(partner),
            )

        await PartnerEngine._publish_event(
            "partner.blocked",
            partner_id,
            PartnerEngine._partner_snapshot(partner),
        )
        return partner

    @staticmethod
    async def approve_kyc(actor_id: int, partner_id: uuid.UUID) -> Partner:
        if not await PartnerEngine.user_can_write(actor_id):
            raise PermissionDeniedError("Access denied")

        async with get_session() as session:
            repo = PartnerRepository(session)
            partner = await repo.approve_kyc(partner_id)
            if partner is None:
                raise PartnerEngineError(f"Partner not found: {partner_id}")

            await PartnerEngine._audit(
                session,
                user_id=actor_id,
                action=AuditAction.STATUS_CHANGE.value,
                entity_id=str(partner_id),
                new_value={"kyc_status": partner.kyc_status},
            )

        await PartnerEngine._publish_event(
            "partner.kyc_approved",
            partner_id,
            PartnerEngine._partner_snapshot(partner),
        )
        return partner

    @staticmethod
    async def reject_kyc(actor_id: int, partner_id: uuid.UUID) -> Partner:
        if not await PartnerEngine.user_can_write(actor_id):
            raise PermissionDeniedError("Access denied")

        async with get_session() as session:
            repo = PartnerRepository(session)
            partner = await repo.reject_kyc(partner_id)
            if partner is None:
                raise PartnerEngineError(f"Partner not found: {partner_id}")

            await PartnerEngine._audit(
                session,
                user_id=actor_id,
                action=AuditAction.STATUS_CHANGE.value,
                entity_id=str(partner_id),
                new_value={"kyc_status": partner.kyc_status, "status": partner.status},
            )

        await PartnerEngine._publish_event(
            "partner.kyc_rejected",
            partner_id,
            PartnerEngine._partner_snapshot(partner),
        )
        return partner

    @staticmethod
    async def add_contact(
        actor_id: int,
        partner_id: uuid.UUID,
        **contact_fields: Any,
    ) -> PartnerContact:
        if not await PartnerEngine.user_can_write(actor_id):
            raise PermissionDeniedError("Access denied")

        async with get_session() as session:
            partner = await PartnerRepository(session).get_by_id(partner_id)
            if partner is None:
                raise PartnerEngineError(f"Partner not found: {partner_id}")
            return await PartnerContactRepository(session).create(
                partner_id=partner_id,
                **contact_fields,
            )

    @staticmethod
    async def add_wallet(
        actor_id: int,
        partner_id: uuid.UUID,
        *,
        asset: str,
        wallet_type: str,
        wallet_address: str,
    ) -> PartnerWallet:
        if not await PartnerEngine.user_can_write(actor_id):
            raise PermissionDeniedError("Access denied")

        async with get_session() as session:
            partner = await PartnerRepository(session).get_by_id(partner_id)
            if partner is None:
                raise PartnerEngineError(f"Partner not found: {partner_id}")
            return await PartnerWalletRepository(session).create(
                partner_id=partner_id,
                asset=asset,
                wallet_type=wallet_type,
                wallet_address=wallet_address,
            )

    @staticmethod
    async def set_limits(
        actor_id: int,
        partner_id: uuid.UUID,
        *,
        daily_limit: Decimal | None = None,
        monthly_limit: Decimal | None = None,
    ) -> PartnerLimit:
        if not await PartnerEngine.user_can_write(actor_id):
            raise PermissionDeniedError("Access denied")

        async with get_session() as session:
            limit_repo = PartnerLimitRepository(session)
            existing = await limit_repo.get_by_partner(partner_id)
            old_value = None
            if existing is not None:
                old_value = {
                    "daily_limit": str(existing.daily_limit),
                    "monthly_limit": str(existing.monthly_limit),
                }

            limit = await limit_repo.update_limits(
                partner_id,
                daily_limit=daily_limit,
                monthly_limit=monthly_limit,
            )

            await PartnerEngine._audit(
                session,
                user_id=actor_id,
                action=AuditAction.CHANGE_LIMIT.value,
                entity_id=str(partner_id),
                old_value=old_value,
                new_value={
                    "daily_limit": str(limit.daily_limit),
                    "monthly_limit": str(limit.monthly_limit),
                },
            )
            return limit

    @staticmethod
    async def record_volume(
        actor_id: int,
        partner_id: uuid.UUID,
        amount: Decimal,
    ) -> PartnerLimit:
        if not await PartnerEngine.user_can_write(actor_id):
            raise PermissionDeniedError("Access denied")

        async with get_session() as session:
            partner = await PartnerRepository(session).get_by_id(partner_id)
            if partner is None:
                raise PartnerEngineError(f"Partner not found: {partner_id}")
            if partner.status == PartnerStatus.BLOCKED.value:
                raise PartnerEngineError("Partner is blocked")

            limit, daily_exceeded, monthly_exceeded = await PartnerLimitRepository(
                session
            ).record_volume(partner_id, amount)

        if daily_exceeded or monthly_exceeded:
            await PartnerEngine._publish_event(
                "partner.limit_exceeded",
                partner_id,
                {
                    "amount": str(amount),
                    "daily_exceeded": daily_exceeded,
                    "monthly_exceeded": monthly_exceeded,
                    "current_daily_volume": str(limit.current_daily_volume),
                    "daily_limit": str(limit.daily_limit),
                    "current_monthly_volume": str(limit.current_monthly_volume),
                    "monthly_limit": str(limit.monthly_limit),
                },
            )
        return limit

    @staticmethod
    async def set_commission(
        actor_id: int,
        partner_id: uuid.UUID,
        *,
        asset: str,
        commission_type: str,
        value: Decimal,
    ) -> PartnerCommission:
        if not await PartnerEngine.user_can_write(actor_id):
            raise PermissionDeniedError("Access denied")

        async with get_session() as session:
            partner = await PartnerRepository(session).get_by_id(partner_id)
            if partner is None:
                raise PartnerEngineError(f"Partner not found: {partner_id}")

            commission = await PartnerCommissionRepository(session).create(
                partner_id=partner_id,
                asset=asset,
                commission_type=commission_type,
                value=value,
            )

            await PartnerEngine._audit(
                session,
                user_id=actor_id,
                action=AuditAction.CHANGE_COMMISSION.value,
                entity_id=str(partner_id),
                new_value={
                    "asset": asset,
                    "commission_type": commission_type,
                    "value": str(value),
                },
            )
            return commission

    @staticmethod
    async def get_partner_profile(
        actor_id: int,
        partner_id: uuid.UUID,
    ) -> dict[str, Any]:
        if not await PartnerEngine.user_can_read(actor_id):
            raise PermissionDeniedError("Access denied")

        async with get_session() as session:
            partner = await PartnerRepository(session).get_by_id(partner_id)
            if partner is None:
                raise PartnerEngineError(f"Partner not found: {partner_id}")

            contacts = await PartnerContactRepository(session).list_by_partner(partner_id)
            wallets = await PartnerWalletRepository(session).list_by_partner(partner_id)
            limits = await PartnerLimitRepository(session).get_by_partner(partner_id)
            commissions = await PartnerCommissionRepository(session).list_by_partner(
                partner_id
            )

            return {
                "partner": PartnerEngine._partner_snapshot(partner),
                "contacts": [
                    {
                        "id": str(c.id),
                        "full_name": c.full_name,
                        "position": c.position,
                        "phone": c.phone,
                        "email": c.email,
                        "telegram": c.telegram,
                        "is_primary": c.is_primary,
                    }
                    for c in contacts
                ],
                "wallets": [
                    {
                        "id": str(w.id),
                        "asset": w.asset,
                        "wallet_type": w.wallet_type,
                        "wallet_address": w.wallet_address,
                        "is_active": w.is_active,
                    }
                    for w in wallets
                ],
                "limits": {
                    "daily_limit": str(limits.daily_limit),
                    "monthly_limit": str(limits.monthly_limit),
                    "current_daily_volume": str(limits.current_daily_volume),
                    "current_monthly_volume": str(limits.current_monthly_volume),
                }
                if limits
                else None,
                "commissions": [
                    {
                        "id": str(c.id),
                        "asset": c.asset,
                        "commission_type": c.commission_type,
                        "value": str(c.value),
                    }
                    for c in commissions
                ],
            }
