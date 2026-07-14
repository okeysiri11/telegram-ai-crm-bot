# Universal Revenue Engine v1 — split calculation, deal hook, owner dashboard.

from __future__ import annotations

import uuid
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from database.models.deal_engine_v1 import DealEngineV1Deal, DealEngineV1Status
from database.models.revenue_engine_v1 import (
    REVENUE_ENGINE_V1_SUPPORTED_VERTICALS,
    RevenueEngineV1Entry,
    RevenueEngineV1PaymentStatus,
)
from database.session import get_session
from repositories.deal_engine_v1_repository import DealEngineV1Repository
from repositories.lead_engine_repository import LeadEngineRepository
from repositories.revenue_engine_v1_repository import RevenueEngineV1Repository

_MONEY = Decimal("0.01")

_VERTICAL_RATES: dict[str, dict[str, Decimal]] = {
    "auto": {
        "partner": Decimal("0.30"),
        "manager": Decimal("0.05"),
        "referral": Decimal("0.03"),
    },
    "agro": {
        "partner": Decimal("0.25"),
        "manager": Decimal("0.05"),
        "referral": Decimal("0.02"),
    },
}


class RevenueEngineV1Error(Exception):
    pass


class RevenueEngineV1:
    @staticmethod
    async def create_from_completed_deal(deal_id: uuid.UUID) -> dict[str, Any] | None:
        async with get_session() as session:
            deal_repo = DealEngineV1Repository(session)
            revenue_repo = RevenueEngineV1Repository(session)

            deal = await deal_repo.get_by_id(deal_id)
            if deal is None:
                raise RevenueEngineV1Error(f"Deal {deal_id} not found")
            if deal.status != DealEngineV1Status.COMPLETED.value:
                raise RevenueEngineV1Error("Revenue entry requires COMPLETED deal")

            existing = await revenue_repo.get_by_deal_id(deal_id)
            if existing is not None:
                return RevenueEngineV1._snapshot(existing)

            has_referral = False
            if deal.lead_id:
                lead = await LeadEngineRepository(session).get_by_id(deal.lead_id)
                has_referral = bool(lead and lead.referral_code)

            partner_rate = None
            if deal.partner_id:
                from repositories.partner_cabinet_v1_repository import PartnerCabinetV1Repository

                profile = await PartnerCabinetV1Repository(session).get_profile_by_partner(
                    deal.partner_id
                )
                if profile and profile.commission_rate is not None:
                    partner_rate = profile.commission_rate

            split = RevenueEngineV1._calculate_split(
                deal,
                has_referral=has_referral,
                partner_rate=partner_rate,
            )
            row = await revenue_repo.create(
                deal_id=deal.id,
                gross_amount=split["gross_amount"],
                platform_income=split["platform_income"],
                partner_income=split["partner_income"],
                manager_income=split["manager_income"],
                referral_income=split["referral_income"],
                currency=deal.currency,
                payment_status=RevenueEngineV1PaymentStatus.PENDING.value,
            )
        snapshot = RevenueEngineV1._snapshot(row)
        if deal.partner_id and split["partner_income"] > 0:
            from services.pg_partner_cabinet_v1 import PartnerCabinetV1

            await PartnerCabinetV1.on_revenue_created(
                deal_id=deal.id,
                partner_id=deal.partner_id,
                revenue_entry_id=row.id,
                partner_income=split["partner_income"],
                currency=deal.currency,
            )
        return snapshot

    @staticmethod
    def _calculate_split(
        deal: DealEngineV1Deal,
        *,
        has_referral: bool,
        partner_rate: Decimal | None = None,
    ) -> dict[str, Decimal]:
        vertical = deal.vertical.lower()
        if vertical not in REVENUE_ENGINE_V1_SUPPORTED_VERTICALS:
            raise RevenueEngineV1Error(f"Unsupported vertical: {deal.vertical}")

        gross = Decimal(deal.amount).quantize(_MONEY, rounding=ROUND_HALF_UP)
        rates = _VERTICAL_RATES[vertical]

        effective_partner_rate = partner_rate if partner_rate is not None else rates["partner"]
        partner_income = (
            (gross * effective_partner_rate).quantize(_MONEY, rounding=ROUND_HALF_UP)
            if deal.partner_id
            else Decimal("0")
        )
        manager_income = (
            (gross * rates["manager"]).quantize(_MONEY, rounding=ROUND_HALF_UP)
            if deal.manager_id
            else Decimal("0")
        )
        referral_income = (
            (gross * rates["referral"]).quantize(_MONEY, rounding=ROUND_HALF_UP)
            if has_referral
            else Decimal("0")
        )
        platform_income = gross - partner_income - manager_income - referral_income
        if platform_income < 0:
            platform_income = Decimal("0")

        return {
            "gross_amount": gross,
            "platform_income": platform_income.quantize(_MONEY, rounding=ROUND_HALF_UP),
            "partner_income": partner_income,
            "manager_income": manager_income,
            "referral_income": referral_income,
        }

    @staticmethod
    async def get_owner_dashboard() -> dict[str, Any]:
        today = RevenueEngineV1Repository.start_of_today()
        month = RevenueEngineV1Repository.start_of_month()

        async with get_session() as session:
            repo = RevenueEngineV1Repository(session)
            income_today = await repo.sum_platform_income(since=today)
            income_month = await repo.sum_platform_income(since=month)
            gross_month = await repo.sum_gross(since=month)
            by_vertical = await repo.income_by_vertical(since=month)
            by_partner = await repo.income_by_partner(since=month)
            recent = await repo.list_recent(limit=8)

        return {
            "income_today": income_today,
            "income_month": income_month,
            "gross_month": gross_month,
            "by_vertical": by_vertical,
            "by_partner": by_partner,
            "recent": [RevenueEngineV1._snapshot(row) for row in recent],
        }

    @staticmethod
    def format_owner_dashboard(data: dict[str, Any]) -> str:
        lines = [
            "💰 Revenue Engine Dashboard",
            "",
            f"💵 Today income: {data['income_today']}",
            f"💵 Monthly income: {data['income_month']}",
            f"📊 Monthly gross: {data['gross_month']}",
            "",
            "📈 Income by vertical (month):",
        ]
        if data["by_vertical"]:
            for vertical, amount in data["by_vertical"]:
                lines.append(f"  • {vertical}: {amount}")
        else:
            lines.append("  • —")

        lines.append("")
        lines.append("📈 Income by partner (month):")
        if data["by_partner"]:
            for partner_id, partner_income, platform_income in data["by_partner"]:
                label = "direct" if partner_id == "direct" else f"{partner_id[:8]}…"
                lines.append(
                    f"  • {label}: partner {partner_income} | platform {platform_income}"
                )
        else:
            lines.append("  • —")

        recent = data.get("recent") or []
        if recent:
            lines.append("")
            lines.append("Recent entries:")
            for entry in recent[:5]:
                lines.append(
                    f"  • deal {entry.get('deal_id', '—')[:8]}… | "
                    f"gross {entry.get('gross_amount')} | "
                    f"platform {entry.get('platform_income')} | "
                    f"{entry.get('payment_status')}"
                )
        return "\n".join(lines)

    @staticmethod
    def _snapshot(row: RevenueEngineV1Entry) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "deal_id": str(row.deal_id),
            "gross_amount": str(row.gross_amount),
            "platform_income": str(row.platform_income),
            "partner_income": str(row.partner_income),
            "manager_income": str(row.manager_income),
            "referral_income": str(row.referral_income),
            "currency": row.currency,
            "payment_status": row.payment_status,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
