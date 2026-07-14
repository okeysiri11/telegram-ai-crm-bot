# Financial Settlement Engine v1 — payment confirmation settlement orchestration.

from __future__ import annotations

import logging
import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import select

from database.models.deal_engine_v1 import DealEngineV1Deal
from database.models.financial_settlement_engine_v1 import (
    FinancialCommissionRecipientType,
    FinancialCommissionStatus,
    FinancialSettlementStatus,
    FinancialTreasuryDirection,
    FinancialTreasuryTransactionType,
)
from database.models.payment_engine_v1 import PaymentEngineStatus
from database.models.revenue_engine_v1 import RevenueEngineV1Entry
from database.models.users import User
from database.session import get_session
from repositories.deal_engine_v1_repository import DealEngineV1Repository
from repositories.financial_settlement_engine_v1_repository import FinancialSettlementV1Repository
from repositories.payment_engine_v1_repository import PaymentEngineV1Repository
from repositories.revenue_engine_v1_repository import RevenueEngineV1Repository

logger = logging.getLogger(__name__)


class FinancialSettlementEngineV1Error(Exception):
    pass


class FinancialSettlementEngineV1:
    @staticmethod
    async def on_payment_confirmed(payment_id: uuid.UUID) -> dict[str, Any]:
        async with get_session() as session:
            pay_repo = PaymentEngineV1Repository(session)
            fin_repo = FinancialSettlementV1Repository(session)

            payment = await pay_repo.get_by_id(payment_id)
            if payment is None:
                raise FinancialSettlementEngineV1Error(f"Payment {payment_id} not found")
            if payment.status != PaymentEngineStatus.CONFIRMED.value:
                raise FinancialSettlementEngineV1Error("Payment must be CONFIRMED")
            if payment.deal_id is None:
                raise FinancialSettlementEngineV1Error("Payment has no linked deal")

            existing = await fin_repo.get_settlement_by_payment(payment_id)
            if existing is not None:
                return await FinancialSettlementEngineV1._full_snapshot(session, existing.id)

            deal = await DealEngineV1Repository(session).get_by_id(payment.deal_id)
            if deal is None:
                raise FinancialSettlementEngineV1Error(f"Deal {payment.deal_id} not found")

            revenue_entry = await RevenueEngineV1Repository(session).get_by_deal_id(deal.id)
            if revenue_entry is None:
                from services.pg_revenue_engine_v1 import RevenueEngineV1

                await RevenueEngineV1.create_from_completed_deal(deal.id)
                revenue_entry = await RevenueEngineV1Repository(session).get_by_deal_id(deal.id)

            if revenue_entry is None:
                raise FinancialSettlementEngineV1Error("Revenue entry missing for confirmed payment")

            distribution = FinancialSettlementEngineV1._build_distribution(deal, revenue_entry, payment.amount)

            fin_revenue = await fin_repo.create_revenue(
                payment_id=payment.id,
                deal_id=deal.id,
                revenue_entry_id=revenue_entry.id,
                gross_amount=distribution["client_payment"],
                platform_profit=distribution["platform_profit"],
                currency=payment.currency,
            )

            settlement = await fin_repo.create_settlement(
                payment_id=payment.id,
                deal_id=deal.id,
                revenue_id=fin_revenue.id,
                partner_id=deal.partner_id,
                manager_id=deal.manager_id,
                client_payment=distribution["client_payment"],
                partner_share=distribution["partner_share"],
                manager_share=distribution["manager_share"],
                platform_profit=distribution["platform_profit"],
                referral_share=distribution["referral_share"],
                currency=payment.currency,
                status=FinancialSettlementStatus.PENDING.value,
            )

            commissions = await FinancialSettlementEngineV1._create_commissions(
                fin_repo,
                settlement_id=settlement.id,
                deal=deal,
                distribution=distribution,
                currency=payment.currency,
            )

            treasury = await FinancialSettlementEngineV1._create_treasury_transactions(
                fin_repo,
                payment_id=payment.id,
                settlement_id=settlement.id,
                distribution=distribution,
                currency=payment.currency,
            )

        snapshot = await FinancialSettlementEngineV1._full_snapshot_by_payment(payment_id)
        snapshot["commissions"] = commissions
        snapshot["treasury_transactions"] = treasury
        manager_tid = await FinancialSettlementEngineV1._manager_telegram_id(deal.manager_id)
        snapshot["manager_telegram_id"] = manager_tid
        return snapshot

    @staticmethod
    async def get_owner_metrics() -> dict[str, Any]:
        today = FinancialSettlementV1Repository.start_of_today()
        week = FinancialSettlementV1Repository.start_of_week()
        month = FinancialSettlementV1Repository.start_of_month()

        async with get_session() as session:
            repo = FinancialSettlementV1Repository(session)
            return {
                "revenue_today": await repo.sum_revenue(since=today),
                "revenue_week": await repo.sum_revenue(since=week),
                "revenue_month": await repo.sum_revenue(since=month),
                "pending_settlements": await repo.count_pending_settlements(),
                "partner_liabilities": await repo.sum_partner_liabilities(),
                "manager_commissions": await repo.sum_manager_commissions(),
                "recent_settlements": [
                    FinancialSettlementEngineV1._settlement_snapshot(row)
                    for row in await repo.list_recent_settlements(limit=5)
                ],
            }

    @staticmethod
    def format_owner_settlement_analytics(metrics: dict[str, Any]) -> str:
        lines = [
            "🏦 Settlement Analytics",
            "",
            f"💵 Today revenue: {metrics['revenue_today']}",
            f"💵 Week revenue: {metrics['revenue_week']}",
            f"💵 Month revenue: {metrics['revenue_month']}",
            "",
            f"⏳ Pending settlements: {metrics['pending_settlements']}",
            f"🤝 Partner liabilities: {metrics['partner_liabilities']}",
            f"👥 Manager commissions: {metrics['manager_commissions']}",
        ]
        recent = metrics.get("recent_settlements") or []
        if recent:
            lines.append("")
            lines.append("Recent settlements:")
            for row in recent[:5]:
                lines.append(
                    f"  • {row['id'][:8]}… | {row['client_payment']} {row['currency']} | "
                    f"platform {row['platform_profit']} | {row['status']}"
                )
        return "\n".join(lines)

    @staticmethod
    def format_owner_notification(settlement: dict[str, Any]) -> str:
        return (
            "🏦 Financial Settlement\n\n"
            f"Payment: {settlement.get('payment_id', '—')[:8]}…\n"
            f"Deal: {settlement.get('deal_id', '—')[:8]}…\n"
            f"Client payment: {settlement.get('client_payment')} {settlement.get('currency')}\n"
            f"Partner share: {settlement.get('partner_share')}\n"
            f"Manager share: {settlement.get('manager_share')}\n"
            f"Platform profit: {settlement.get('platform_profit')}\n"
            f"Status: {settlement.get('status')}"
        )

    @staticmethod
    def format_manager_notification(settlement: dict[str, Any]) -> str:
        return (
            "💰 Payment confirmed — commission accrued\n\n"
            f"Deal: {settlement.get('deal_id', '—')[:8]}…\n"
            f"Client payment: {settlement.get('client_payment')} {settlement.get('currency')}\n"
            f"Your share: {settlement.get('manager_share')} {settlement.get('currency')}\n"
            f"Settlement: {settlement.get('id', '—')[:8]}…"
        )

    @staticmethod
    def _build_distribution(
        deal: DealEngineV1Deal,
        revenue: RevenueEngineV1Entry,
        payment_amount: Decimal,
    ) -> dict[str, Decimal]:
        client_payment = Decimal(payment_amount)
        partner_share = Decimal(revenue.partner_income)
        manager_share = Decimal(revenue.manager_income)
        referral_share = Decimal(revenue.referral_income)
        platform_profit = Decimal(revenue.platform_income)
        return {
            "client_payment": client_payment,
            "partner_share": partner_share,
            "manager_share": manager_share + referral_share,
            "referral_share": referral_share,
            "platform_profit": platform_profit,
        }

    @staticmethod
    async def _create_commissions(
        fin_repo: FinancialSettlementV1Repository,
        *,
        settlement_id: uuid.UUID,
        deal: DealEngineV1Deal,
        distribution: dict[str, Decimal],
        currency: str,
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        if distribution["partner_share"] > 0 and deal.partner_id:
            row = await fin_repo.create_commission(
                settlement_id=settlement_id,
                recipient_type=FinancialCommissionRecipientType.PARTNER.value,
                recipient_id=deal.partner_id,
                amount=distribution["partner_share"],
                currency=currency,
                status=FinancialCommissionStatus.ACCRUED.value,
            )
            rows.append(FinancialSettlementEngineV1._commission_snapshot(row))

        manager_amount = distribution["manager_share"] - distribution["referral_share"]
        if manager_amount > 0 and deal.manager_id:
            row = await fin_repo.create_commission(
                settlement_id=settlement_id,
                recipient_type=FinancialCommissionRecipientType.MANAGER.value,
                recipient_id=deal.manager_id,
                amount=manager_amount,
                currency=currency,
                status=FinancialCommissionStatus.ACCRUED.value,
            )
            rows.append(FinancialSettlementEngineV1._commission_snapshot(row))

        if distribution["referral_share"] > 0:
            row = await fin_repo.create_commission(
                settlement_id=settlement_id,
                recipient_type=FinancialCommissionRecipientType.REFERRAL.value,
                recipient_id=None,
                amount=distribution["referral_share"],
                currency=currency,
                status=FinancialCommissionStatus.ACCRUED.value,
            )
            rows.append(FinancialSettlementEngineV1._commission_snapshot(row))

        return rows

    @staticmethod
    async def _create_treasury_transactions(
        fin_repo: FinancialSettlementV1Repository,
        *,
        payment_id: uuid.UUID,
        settlement_id: uuid.UUID,
        distribution: dict[str, Decimal],
        currency: str,
    ) -> list[dict[str, Any]]:
        specs = [
            (
                FinancialTreasuryTransactionType.CLIENT_PAYMENT.value,
                distribution["client_payment"],
                FinancialTreasuryDirection.IN.value,
            ),
            (
                FinancialTreasuryTransactionType.PLATFORM_PROFIT.value,
                distribution["platform_profit"],
                FinancialTreasuryDirection.IN.value,
            ),
            (
                FinancialTreasuryTransactionType.PARTNER_SHARE.value,
                distribution["partner_share"],
                FinancialTreasuryDirection.OUT.value,
            ),
            (
                FinancialTreasuryTransactionType.MANAGER_SHARE.value,
                distribution["manager_share"],
                FinancialTreasuryDirection.OUT.value,
            ),
        ]
        rows: list[dict[str, Any]] = []
        for tx_type, amount, direction in specs:
            if amount <= 0:
                continue
            row = await fin_repo.create_treasury_transaction(
                payment_id=payment_id,
                settlement_id=settlement_id,
                transaction_type=tx_type,
                amount=amount,
                currency=currency,
                direction=direction,
            )
            rows.append(FinancialSettlementEngineV1._treasury_snapshot(row))
        return rows

    @staticmethod
    async def _manager_telegram_id(manager_id: uuid.UUID | None) -> int | None:
        if manager_id is None:
            return None
        async with get_session() as session:
            result = await session.execute(
                select(User.telegram_id).where(User.id == manager_id)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def _full_snapshot_by_payment(payment_id: uuid.UUID) -> dict[str, Any]:
        async with get_session() as session:
            settlement = await FinancialSettlementV1Repository(session).get_settlement_by_payment(
                payment_id
            )
            if settlement is None:
                return {}
            return await FinancialSettlementEngineV1._full_snapshot(session, settlement.id)

    @staticmethod
    async def _full_snapshot(session, settlement_id: uuid.UUID) -> dict[str, Any]:
        from database.models.financial_settlement_engine_v1 import (
            FinancialSettlementV1Revenue,
            FinancialSettlementV1Settlement,
        )

        fin_repo = FinancialSettlementV1Repository(session)
        settlement_row = await session.get(FinancialSettlementV1Settlement, settlement_id)
        if settlement_row is None:
            return {}
        revenue_row = await session.get(FinancialSettlementV1Revenue, settlement_row.revenue_id)
        commissions = await fin_repo.list_commissions_for_settlement(settlement_id)
        treasury = await fin_repo.list_treasury_for_settlement(settlement_id)
        snapshot = FinancialSettlementEngineV1._settlement_snapshot(settlement_row)
        snapshot["revenue"] = (
            FinancialSettlementEngineV1._revenue_snapshot(revenue_row) if revenue_row else None
        )
        snapshot["commissions"] = [
            FinancialSettlementEngineV1._commission_snapshot(c) for c in commissions
        ]
        snapshot["treasury_transactions"] = [
            FinancialSettlementEngineV1._treasury_snapshot(t) for t in treasury
        ]
        return snapshot

    @staticmethod
    def _settlement_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "payment_id": str(row.payment_id),
            "deal_id": str(row.deal_id),
            "revenue_id": str(row.revenue_id),
            "partner_id": str(row.partner_id) if row.partner_id else None,
            "manager_id": str(row.manager_id) if row.manager_id else None,
            "client_payment": str(row.client_payment),
            "partner_share": str(row.partner_share),
            "manager_share": str(row.manager_share),
            "platform_profit": str(row.platform_profit),
            "referral_share": str(row.referral_share),
            "currency": row.currency,
            "status": row.status,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }

    @staticmethod
    def _revenue_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "payment_id": str(row.payment_id),
            "deal_id": str(row.deal_id),
            "revenue_entry_id": str(row.revenue_entry_id) if row.revenue_entry_id else None,
            "gross_amount": str(row.gross_amount),
            "platform_profit": str(row.platform_profit),
            "currency": row.currency,
        }

    @staticmethod
    def _commission_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "settlement_id": str(row.settlement_id),
            "recipient_type": row.recipient_type,
            "recipient_id": str(row.recipient_id) if row.recipient_id else None,
            "amount": str(row.amount),
            "currency": row.currency,
            "status": row.status,
        }

    @staticmethod
    def _treasury_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "payment_id": str(row.payment_id),
            "settlement_id": str(row.settlement_id),
            "transaction_type": row.transaction_type,
            "amount": str(row.amount),
            "currency": row.currency,
            "direction": row.direction,
        }
