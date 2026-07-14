# Partner Cabinet v1 — partner dashboard, commissions, owner controls.

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from database.models.partner_cabinet_v1 import (
    PARTNER_CABINET_ROLE_DISPLAY,
    PARTNER_TYPE_TO_CABINET_ROLE,
    PartnerCabinetCommissionStatus,
)
from database.session import get_session
from repositories.partner_cabinet_v1_repository import PartnerCabinetV1Repository

logger = logging.getLogger(__name__)


class PartnerCabinetV1Error(Exception):
    pass


class PartnerCabinetV1:
    @staticmethod
    def role_display(role: str | None) -> str:
        if not role:
            return "—"
        return PARTNER_CABINET_ROLE_DISPLAY.get(role, role.replace("_", " ").title())

    @staticmethod
    async def get_partner_cabinet(telegram_user_id: int) -> dict[str, Any]:
        async with get_session() as session:
            repo = PartnerCabinetV1Repository(session)
            profile = await repo.get_profile_by_telegram(telegram_user_id)
            if profile is None:
                raise PartnerCabinetV1Error("Partner profile not linked")
            if profile.is_blocked:
                raise PartnerCabinetV1Error("Partner account is blocked")

            partner = await repo.get_partner(profile.partner_id)
            if partner is None:
                raise PartnerCabinetV1Error("Partner not found")

            received_leads = await repo.count_deals(profile.partner_id)
            active_deals = await repo.count_deals(profile.partner_id, active_only=True)
            completed_deals = await repo.count_deals(profile.partner_id, completed_only=True)
            accrued = await repo.sum_commissions(profile.partner_id)
            paid = await repo.sum_commissions(
                profile.partner_id,
                status=PartnerCabinetCommissionStatus.PAID.value,
            )
            pending = await repo.sum_commissions(
                profile.partner_id,
                status=PartnerCabinetCommissionStatus.PENDING.value,
            )
            accrued_only = await repo.sum_commissions(
                profile.partner_id,
                status=PartnerCabinetCommissionStatus.ACCRUED.value,
            )
            recent = await repo.list_recent_deals(profile.partner_id, limit=5)

        return {
            "partner_id": str(profile.partner_id),
            "partner_code": partner.code,
            "partner_name": partner.name,
            "cabinet_role": profile.cabinet_role,
            "commission_rate": profile.commission_rate,
            "received_leads": received_leads,
            "active_deals": active_deals,
            "completed_deals": completed_deals,
            "accrued_commissions": accrued,
            "paid_commissions": paid,
            "pending_commissions": pending + accrued_only,
            "recent_deals": [
                {
                    "id": str(d.id),
                    "title": d.title,
                    "status": d.status,
                    "amount": str(d.amount),
                    "currency": d.currency,
                }
                for d in recent
            ],
        }

    @staticmethod
    async def get_owner_overview() -> dict[str, Any]:
        async with get_session() as session:
            repo = PartnerCabinetV1Repository(session)
            profiles = await repo.list_profiles()
            pending = await repo.list_pending_commissions(limit=10)
            partners: list[dict[str, Any]] = []
            for profile in profiles:
                partner = await repo.get_partner(profile.partner_id)
                if partner is None:
                    continue
                partners.append({
                    "partner_id": str(profile.partner_id),
                    "code": partner.code,
                    "name": partner.name,
                    "role": profile.cabinet_role,
                    "commission_rate": profile.commission_rate,
                    "is_blocked": profile.is_blocked,
                    "telegram_user_id": profile.telegram_user_id,
                    "pending": await repo.sum_commissions(
                        profile.partner_id,
                        status=PartnerCabinetCommissionStatus.PENDING.value,
                    ),
                    "accrued": await repo.sum_commissions(
                        profile.partner_id,
                        status=PartnerCabinetCommissionStatus.ACCRUED.value,
                    ),
                })

        return {
            "partners": partners,
            "pending_payouts": [
                {
                    "id": str(c.id),
                    "partner_id": str(c.partner_id),
                    "amount": c.amount,
                    "currency": c.currency,
                    "status": c.status,
                }
                for c in pending
            ],
        }

    @staticmethod
    async def on_revenue_created(
        *,
        deal_id: uuid.UUID,
        partner_id: uuid.UUID | None,
        revenue_entry_id: uuid.UUID,
        partner_income: Decimal,
        currency: str,
    ) -> None:
        if not partner_id or partner_income <= 0:
            return
        try:
            async with get_session() as session:
                repo = PartnerCabinetV1Repository(session)
                existing = await repo.get_commission_by_revenue(revenue_entry_id)
                if existing is not None:
                    return
                profile = await repo.get_profile_by_partner(partner_id)
                if profile and profile.is_blocked:
                    return
                await repo.create_commission(
                    partner_id=partner_id,
                    deal_id=deal_id,
                    revenue_entry_id=revenue_entry_id,
                    amount=partner_income,
                    currency=currency,
                    status=PartnerCabinetCommissionStatus.ACCRUED.value,
                )
        except Exception:
            logger.exception(
                "Partner commission accrual failed deal=%s partner=%s",
                deal_id,
                partner_id,
            )

    @staticmethod
    async def approve_payout(
        commission_id: uuid.UUID,
        *,
        actor_telegram_id: int,
        mark_paid: bool = True,
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        async with get_session() as session:
            repo = PartnerCabinetV1Repository(session)
            commission = await repo.get_commission(commission_id)
            if commission is None:
                raise PartnerCabinetV1Error("Commission not found")
            if commission.status == PartnerCabinetCommissionStatus.PAID.value:
                raise PartnerCabinetV1Error("Already paid")

            profile = await repo.get_profile_by_partner(commission.partner_id)
            if profile and profile.is_blocked:
                raise PartnerCabinetV1Error("Partner is blocked")

            updates: dict[str, Any] = {
                "approved_at": now,
                "approved_by_telegram_id": actor_telegram_id,
            }
            if mark_paid:
                updates.update({
                    "status": PartnerCabinetCommissionStatus.PAID.value,
                    "paid_at": now,
                    "paid_by_telegram_id": actor_telegram_id,
                })
            else:
                updates["status"] = PartnerCabinetCommissionStatus.PENDING.value

            await repo.update_commission(commission_id, **updates)

        return {
            "commission_id": str(commission_id),
            "status": updates["status"],
            "amount": str(commission.amount),
        }

    @staticmethod
    async def block_partner(
        partner_code: str,
        *,
        actor_telegram_id: int,
        blocked: bool = True,
    ) -> dict[str, Any]:
        async with get_session() as session:
            repo = PartnerCabinetV1Repository(session)
            partner = await repo.get_partner_by_code(partner_code)
            if partner is None:
                raise PartnerCabinetV1Error(f"Partner {partner_code} not found")
            profile = await repo.get_profile_by_partner(partner.id)
            if profile is None:
                raise PartnerCabinetV1Error("Cabinet profile not found")

            now = datetime.now(timezone.utc) if blocked else None
            await repo.update_profile(
                profile.id,
                is_blocked=blocked,
                blocked_at=now,
                blocked_by_telegram_id=actor_telegram_id if blocked else None,
            )
            partner.is_active = not blocked
            await session.flush()

        return {
            "partner_code": partner_code,
            "is_blocked": blocked,
        }

    @staticmethod
    async def set_commission_rate(
        partner_code: str,
        rate: Decimal | float | str,
    ) -> dict[str, Any]:
        rate_dec = Decimal(str(rate))
        if rate_dec < 0 or rate_dec > 1:
            raise PartnerCabinetV1Error("Rate must be between 0 and 1")

        async with get_session() as session:
            repo = PartnerCabinetV1Repository(session)
            partner = await repo.get_partner_by_code(partner_code)
            if partner is None:
                raise PartnerCabinetV1Error(f"Partner {partner_code} not found")
            profile = await repo.get_profile_by_partner(partner.id)
            if profile is None:
                raise PartnerCabinetV1Error("Cabinet profile not found")
            await repo.update_profile(profile.id, commission_rate=rate_dec)

        return {
            "partner_code": partner_code,
            "commission_rate": str(rate_dec),
        }

    @staticmethod
    async def link_partner_telegram(
        partner_code: str,
        telegram_user_id: int,
    ) -> dict[str, Any]:
        async with get_session() as session:
            repo = PartnerCabinetV1Repository(session)
            partner = await repo.get_partner_by_code(partner_code)
            if partner is None:
                raise PartnerCabinetV1Error(f"Partner {partner_code} not found")
            existing = await repo.get_profile_by_telegram(telegram_user_id)
            if existing is not None:
                raise PartnerCabinetV1Error("Telegram already linked to another partner")
            profile = await repo.link_telegram(partner.id, telegram_user_id)
            if profile is None:
                raise PartnerCabinetV1Error("Cabinet profile not found")

        return {
            "partner_code": partner_code,
            "telegram_user_id": telegram_user_id,
        }

    @staticmethod
    def format_partner_cabinet(data: dict[str, Any]) -> str:
        rate = data.get("commission_rate")
        rate_label = f"{float(rate) * 100:.1f}%" if rate is not None else "default"
        lines = [
            "🤝 Partner Cabinet v1",
            "",
            f"Partner: {data.get('partner_name')} ({data.get('partner_code')})",
            f"Role: {PartnerCabinetV1.role_display(data.get('cabinet_role'))}",
            f"Commission rate: {rate_label}",
            "",
            f"📥 Received leads: {data.get('received_leads', 0)}",
            f"⚙ Active deals: {data.get('active_deals', 0)}",
            f"✅ Completed deals: {data.get('completed_deals', 0)}",
            "",
            f"💰 Accrued commissions: {data.get('accrued_commissions', 0)}",
            f"⏳ Pending commissions: {data.get('pending_commissions', 0)}",
            f"✅ Paid commissions: {data.get('paid_commissions', 0)}",
        ]
        recent = data.get("recent_deals") or []
        if recent:
            lines.append("")
            lines.append("Recent deals:")
            for deal in recent:
                lines.append(
                    f"  • {deal['title'][:30]} — {deal['status']} "
                    f"({deal['amount']} {deal['currency']})"
                )
        return "\n".join(lines)

    @staticmethod
    def format_owner_overview(data: dict[str, Any]) -> str:
        lines = [
            "🤝 Partner Cabinet — Owner",
            "",
            "Partners:",
        ]
        for p in data.get("partners") or []:
            blocked = "🚫" if p.get("is_blocked") else "✅"
            tg = p.get("telegram_user_id") or "—"
            rate = p.get("commission_rate")
            rate_label = f"{float(rate) * 100:.1f}%" if rate is not None else "default"
            lines.append(
                f"  {blocked} {p['name']} ({p['code']}) — "
                f"{PartnerCabinetV1.role_display(p.get('role'))}, rate {rate_label}, "
                f"accrued {p.get('accrued', 0)}, pending {p.get('pending', 0)}, tg={tg}"
            )
        if not data.get("partners"):
            lines.append("  • —")

        lines.append("")
        lines.append("Pending payouts:")
        for payout in data.get("pending_payouts") or []:
            lines.append(
                f"  • {payout['id'][:8]}… — {payout['amount']} {payout['currency']} "
                f"({payout['status']})"
            )
        if not data.get("pending_payouts"):
            lines.append("  • —")

        lines.append("")
        lines.append("Owner commands:")
        lines.append("  /approve_payout <commission_uuid>")
        lines.append("  /block_partner <partner_code>")
        lines.append("  /unblock_partner <partner_code>")
        lines.append("  /set_partner_rate <partner_code> <0.30>")
        lines.append("  /link_partner <partner_code> <telegram_id>")
        return "\n".join(lines)

    @staticmethod
    def cabinet_role_from_partner_type(partner_type: str) -> str:
        return PARTNER_TYPE_TO_CABINET_ROLE.get(
            partner_type.upper(),
            "dealers",
        )
