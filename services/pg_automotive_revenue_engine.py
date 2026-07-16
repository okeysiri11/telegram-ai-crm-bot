# Automotive Revenue Engine v1 — cross-vertical revenue tracking.

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from database.models.automotive_partner_integration import AutomotivePartnerType
from database.models.automotive_revenue_engine import (
    CommissionStatus,
    RevenueServiceType,
)
from database.session import get_session
from repositories.automotive_partner_repository import AutomotivePartnerRepository
from repositories.automotive_revenue_repository import AutomotiveRevenueRepository
from services.tenant_context import TenantContextService

DEFAULT_LEAD_COMMISSION = Decimal("500")
DEFAULT_REFERRAL_COMMISSION = Decimal("1000")

SERVICE_COMMISSION_RATES: dict[str, Decimal] = {
    RevenueServiceType.INSURANCE.value: Decimal("3.0"),
    RevenueServiceType.CREDIT.value: Decimal("1.5"),
    RevenueServiceType.LEASING.value: Decimal("2.0"),
    RevenueServiceType.LOGISTICS.value: Decimal("2.5"),
    RevenueServiceType.NOTARY.value: Decimal("1.0"),
    RevenueServiceType.LEGAL.value: Decimal("2.0"),
    RevenueServiceType.DEALER_REFERRAL.value: Decimal("1.5"),
}

PARTNER_TYPE_TO_SERVICE: dict[str, str] = {
    AutomotivePartnerType.INSURANCE.value: RevenueServiceType.INSURANCE.value,
    AutomotivePartnerType.CREDIT.value: RevenueServiceType.CREDIT.value,
    AutomotivePartnerType.LEASING.value: RevenueServiceType.LEASING.value,
    AutomotivePartnerType.LOGISTICS.value: RevenueServiceType.LOGISTICS.value,
    AutomotivePartnerType.LEGAL.value: RevenueServiceType.LEGAL.value,
    AutomotivePartnerType.DEALER.value: RevenueServiceType.DEALER_REFERRAL.value,
}


class AutomotiveRevenueEngineError(Exception):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _month_key(dt: datetime | None = None) -> str:
    value = dt or _now()
    return value.strftime("%Y-%m")


class AutomotiveRevenueLeadRecorder:
    """Partner-lead commission recorder (not the CRM LeadEngineV1)."""

    @staticmethod
    async def record_partner_lead(
        *,
        partner_id: uuid.UUID,
        lead_id: uuid.UUID,
        tenant_id: uuid.UUID | None,
        source_id: str | None,
        vertical: str,
        commission_amount: Decimal,
        payload: dict | None = None,
    ) -> dict[str, Any]:
        async with get_session() as session:
            row = await AutomotiveRevenueRepository(session).create_partner_lead(
                tenant_id=tenant_id,
                partner_id=partner_id,
                lead_id=lead_id,
                source_id=source_id,
                vertical=vertical,
                commission_amount=commission_amount,
                payload=payload,
            )
        return {
            "lead_id": str(lead_id),
            "tenant_id": str(tenant_id) if tenant_id else None,
            "partner_id": str(partner_id),
            "source_id": source_id,
            "commission_amount": str(commission_amount),
            "commission_status": row.commission_status,
            "partner_lead_id": str(row.id),
        }


class ReferralEngineV1:
    @staticmethod
    async def record_dealer_referral(
        *,
        partner_id: uuid.UUID,
        lead_id: uuid.UUID,
        tenant_id: uuid.UUID | None,
        source_id: str | None,
        referrer_user_id: int | None,
        customer_name: str,
        commission_amount: Decimal | None = None,
    ) -> dict[str, Any]:
        amount = commission_amount or DEFAULT_REFERRAL_COMMISSION
        async with get_session() as session:
            row = await AutomotiveRevenueRepository(session).create_dealer_referral(
                tenant_id=tenant_id,
                partner_id=partner_id,
                lead_id=lead_id,
                source_id=source_id,
                referrer_user_id=referrer_user_id,
                customer_name=customer_name,
                commission_amount=amount,
            )
        return {
            "referral_id": str(row.id),
            "lead_id": str(lead_id),
            "partner_id": str(partner_id),
            "commission_amount": str(amount),
            "commission_status": row.commission_status,
        }


class CommissionEngineV1:
    @staticmethod
    def calculate_amount(
        *,
        service_type: str,
        base_amount: Decimal = Decimal("0"),
        flat_lead_fee: Decimal | None = None,
    ) -> tuple[Decimal, Decimal | None]:
        rate = SERVICE_COMMISSION_RATES.get(service_type, Decimal("1.0"))
        if base_amount > 0:
            return (base_amount * rate / Decimal("100")).quantize(Decimal("0.01")), rate
        fee = flat_lead_fee or DEFAULT_LEAD_COMMISSION
        return fee, rate

    @staticmethod
    async def accrue(
        *,
        tenant_id: uuid.UUID | None,
        partner_id: uuid.UUID,
        lead_id: uuid.UUID,
        partner_lead_id: uuid.UUID | None,
        source_id: str | None,
        service_type: str,
        commission_amount: Decimal,
        rate_pct: Decimal | None = None,
        deal_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        async with get_session() as session:
            row = await AutomotiveRevenueRepository(session).create_partner_commission(
                tenant_id=tenant_id,
                partner_id=partner_id,
                lead_id=lead_id,
                partner_lead_id=partner_lead_id,
                source_id=source_id,
                service_type=service_type,
                commission_amount=commission_amount,
                rate_pct=rate_pct,
                deal_id=deal_id,
            )
        return {
            "commission_id": str(row.id),
            "lead_id": str(lead_id),
            "tenant_id": str(tenant_id) if tenant_id else None,
            "partner_id": str(partner_id),
            "source_id": source_id,
            "commission_amount": str(commission_amount),
            "commission_status": row.commission_status,
        }


class AutomotiveRevenueDealRecorder:
    """Deal profit/commission recorder (not the CRM DealEngineV1)."""

    @staticmethod
    async def record_deal_completion(
        *,
        tenant_id: uuid.UUID | None,
        deal_id: uuid.UUID | None,
        lead_id: uuid.UUID | None,
        partner_id: uuid.UUID | None,
        source_id: str | None,
        service_type: str,
        revenue: Decimal,
        cost: Decimal,
        commission_amount: Decimal | None = None,
    ) -> dict[str, Any]:
        async with get_session() as session:
            repo = AutomotiveRevenueRepository(session)
            profit_row = await repo.upsert_deal_profit(
                tenant_id=tenant_id,
                deal_id=deal_id,
                lead_id=lead_id,
                revenue=revenue,
                cost=cost,
                period_month=_month_key(),
            )
            commission_row = None
            if partner_id and commission_amount is not None:
                commission_row = await repo.create_deal_commission(
                    tenant_id=tenant_id,
                    deal_id=deal_id,
                    partner_id=partner_id,
                    lead_id=lead_id,
                    source_id=source_id,
                    service_type=service_type,
                    commission_amount=commission_amount,
                )
        return {
            "deal_id": str(deal_id) if deal_id else None,
            "profit_id": str(profit_row.id) if profit_row else None,
            "profit": str(profit_row.profit) if profit_row else "0",
            "deal_commission_id": str(commission_row.id) if commission_row else None,
        }


class PartnerSettlementEngineV1:
    @staticmethod
    async def create_settlement_batch(
        *,
        tenant_id: uuid.UUID | None,
        partner_id: uuid.UUID,
        period_start: datetime,
        period_end: datetime,
        total_amount: Decimal,
    ) -> dict[str, Any]:
        async with get_session() as session:
            row = await AutomotiveRevenueRepository(session).create_settlement(
                tenant_id=tenant_id,
                partner_id=partner_id,
                period_start=period_start,
                period_end=period_end,
                total_amount=total_amount,
            )
        return {
            "settlement_id": str(row.id),
            "partner_id": str(partner_id),
            "total_amount": str(total_amount),
            "status": row.status,
        }


class RevenueAnalyticsEngineV1:
    @staticmethod
    async def revenue_by_partner(*, tenant_id: uuid.UUID | None = None) -> list[dict[str, Any]]:
        async with get_session() as session:
            rows = await AutomotiveRevenueRepository(session).sum_commissions_by_partner(
                tenant_id=tenant_id
            )
            partner_repo = AutomotivePartnerRepository(session)
            result = []
            for partner_id, amount in rows:
                partner = await partner_repo.get_partner_by_id(partner_id)
                result.append({
                    "partner_id": str(partner_id),
                    "partner_code": partner.code if partner else None,
                    "partner_name": partner.name if partner else None,
                    "revenue": str(amount),
                })
            return result

    @staticmethod
    async def revenue_by_service(*, tenant_id: uuid.UUID | None = None) -> list[dict[str, Any]]:
        async with get_session() as session:
            rows = await AutomotiveRevenueRepository(session).sum_commissions_by_service(
                tenant_id=tenant_id
            )
        return [{"service_type": svc, "revenue": str(amt)} for svc, amt in rows]

    @staticmethod
    async def revenue_by_vertical(*, tenant_id: uuid.UUID | None = None) -> list[dict[str, Any]]:
        return await RevenueAnalyticsEngineV1.revenue_by_service(tenant_id=tenant_id)

    @staticmethod
    async def monthly_profit(*, tenant_id: uuid.UUID | None = None) -> list[dict[str, Any]]:
        async with get_session() as session:
            rows = await AutomotiveRevenueRepository(session).sum_profit_by_month(tenant_id=tenant_id)
        return [{"period_month": month or "unknown", "profit": str(profit)} for month, profit in rows]

    @staticmethod
    async def lifetime_value(*, tenant_id: uuid.UUID | None = None) -> dict[str, Any]:
        async with get_session() as session:
            ltv = await AutomotiveRevenueRepository(session).lifetime_value(tenant_id=tenant_id)
        return {"lifetime_value": str(ltv), "currency": "UAH"}


class AutomotiveRevenueEngineV1:
    LeadEngine = AutomotiveRevenueLeadRecorder
    ReferralEngine = ReferralEngineV1
    CommissionEngine = CommissionEngineV1
    DealEngine = AutomotiveRevenueDealRecorder
    PartnerSettlementEngine = PartnerSettlementEngineV1
    AnalyticsEngine = RevenueAnalyticsEngineV1

    @staticmethod
    async def _resolve_partner(partner_code: str):
        async with get_session() as session:
            partner = await AutomotivePartnerRepository(session).get_partner_by_code(partner_code)
        if partner is None:
            raise AutomotiveRevenueEngineError(f"Partner {partner_code} not found")
        return partner

    @staticmethod
    async def record_customer_action(
        *,
        partner_code: str,
        lead_id: uuid.UUID | str,
        actor_id: int | None = None,
        tenant_id: uuid.UUID | None = None,
        source_id: str | None = None,
        service_type: str | None = None,
        base_amount: Decimal = Decimal("0"),
        customer_name: str | None = None,
        referrer_user_id: int | None = None,
        payload: dict | None = None,
    ) -> dict[str, Any]:
        partner = await AutomotiveRevenueEngineV1._resolve_partner(partner_code)
        lead_uuid = uuid.UUID(str(lead_id))

        if tenant_id is None and actor_id is not None:
            try:
                tenant_id = await TenantContextService.require_tenant_id(actor_id)
            except Exception:
                tenant_id = None

        vertical = service_type or PARTNER_TYPE_TO_SERVICE.get(
            partner.partner_type, partner.partner_type
        )
        amount, rate = CommissionEngineV1.calculate_amount(
            service_type=vertical,
            base_amount=base_amount,
        )

        partner_lead = await AutomotiveRevenueLeadRecorder.record_partner_lead(
            partner_id=partner.id,
            lead_id=lead_uuid,
            tenant_id=tenant_id,
            source_id=source_id,
            vertical=vertical,
            commission_amount=amount,
            payload=payload,
        )

        commission = await CommissionEngineV1.accrue(
            tenant_id=tenant_id,
            partner_id=partner.id,
            lead_id=lead_uuid,
            partner_lead_id=uuid.UUID(partner_lead["partner_lead_id"]),
            source_id=source_id,
            service_type=vertical,
            commission_amount=amount,
            rate_pct=rate,
        )

        referral = None
        if partner.partner_type == AutomotivePartnerType.DEALER.value:
            referral = await ReferralEngineV1.record_dealer_referral(
                partner_id=partner.id,
                lead_id=lead_uuid,
                tenant_id=tenant_id,
                source_id=source_id,
                referrer_user_id=referrer_user_id or actor_id,
                customer_name=customer_name or "Customer",
                commission_amount=amount,
            )

        return {
            "lead_id": str(lead_uuid),
            "tenant_id": str(tenant_id) if tenant_id else None,
            "partner_id": str(partner.id),
            "source_id": source_id,
            "commission_amount": str(amount),
            "commission_status": CommissionStatus.PENDING.value,
            "partner_lead": partner_lead,
            "commission": commission,
            "referral": referral,
        }

    @staticmethod
    async def get_admin_dashboard(*, tenant_id: uuid.UUID | None = None) -> dict[str, Any]:
        async with get_session() as session:
            repo = AutomotiveRevenueRepository(session)
            pending = await repo.list_pending_commissions(tenant_id=tenant_id, limit=20)
            settlements = await repo.list_settlements(tenant_id=tenant_id, limit=10)
            completed_deals = await repo.count_completed_deals(tenant_id=tenant_id)
            ltv = await repo.lifetime_value(tenant_id=tenant_id)
            by_service = await repo.sum_commissions_by_service(tenant_id=tenant_id)
            by_month = await repo.sum_profit_by_month(tenant_id=tenant_id)

        return {
            "pending_commissions": [
                {
                    "id": str(row.id),
                    "partner_id": str(row.partner_id),
                    "service_type": row.service_type,
                    "amount": str(row.commission_amount),
                    "status": row.commission_status,
                }
                for row in pending
            ],
            "partner_settlements": [
                {
                    "id": str(row.id),
                    "partner_id": str(row.partner_id),
                    "total": str(row.total_amount),
                    "status": row.status,
                }
                for row in settlements
            ],
            "completed_deals": completed_deals,
            "lifetime_value": str(ltv),
            "revenue_by_service": {svc: str(amt) for svc, amt in by_service},
            "monthly_profit": {month or "?": str(profit) for month, profit in by_month},
        }

    @staticmethod
    def format_admin_dashboard(dashboard: dict[str, Any]) -> str:
        lines = [
            "💰 Automotive Revenue Dashboard",
            "",
            f"Pending commissions: {len(dashboard.get('pending_commissions', []))}",
            f"Partner settlements: {len(dashboard.get('partner_settlements', []))}",
            f"Completed deals: {dashboard.get('completed_deals', 0)}",
            f"Lifetime value: {dashboard.get('lifetime_value', '0')} UAH",
            "",
            "Pending commissions:",
        ]
        for item in (dashboard.get("pending_commissions") or [])[:8]:
            lines.append(
                f"• {item['service_type']} — {item['amount']} UAH [{item['status']}]"
            )
        settlements = dashboard.get("partner_settlements") or []
        if settlements:
            lines.append("")
            lines.append("Partner settlements:")
            for item in settlements[:5]:
                lines.append(f"• {item['total']} UAH — {item['status']}")
        by_service = dashboard.get("revenue_by_service") or {}
        if by_service:
            lines.append("")
            lines.append("Revenue by service:")
            for svc, amt in sorted(by_service.items()):
                lines.append(f"• {svc}: {amt} UAH")
        monthly = dashboard.get("monthly_profit") or {}
        if monthly:
            lines.append("")
            lines.append("Monthly profit:")
            for month, profit in sorted(monthly.items()):
                lines.append(f"• {month}: {profit} UAH")
        return "\n".join(lines)
