# PostgreSQL Deal Workflow — orchestrates Deal, Ledger, Commission, Notification, Audit engines.

from __future__ import annotations

import uuid
from decimal import Decimal

from config import OWNER_ID
from database.models.audit_log import AuditAction
from database.models.commission import CommissionStatus, CommissionType
from database.models.deal import Deal, DealStatus
from database.models.ledger_entry import LedgerAccountType, LedgerDirection
from database.models.notification import NotificationChannel, NotificationType
from database.session import get_session
from repositories.audit_repository import AuditRepository
from repositories.commission_repository import CommissionRepository
from repositories.deal_repository import DealRepository
from repositories.ledger_repository import LedgerRepository
from repositories.notification_repository import NotificationRepository
from repositories.user_role_repository import UserRoleRepository

WORKFLOW_ROLES = frozenset({"OWNER", "ADMIN", "MANAGER"})

WORKFLOW_STATUSES = frozenset(
    {
        DealStatus.NEW.value,
        DealStatus.ASSIGNED.value,
        DealStatus.FUNDS_RECEIVED.value,
        DealStatus.PROCESSING.value,
        DealStatus.COMPLETED.value,
        DealStatus.CANCELLED.value,
    }
)

STATUS_TRANSITIONS: dict[str, frozenset[str]] = {
    DealStatus.NEW.value: frozenset({DealStatus.ASSIGNED.value, DealStatus.CANCELLED.value}),
    DealStatus.ASSIGNED.value: frozenset(
        {DealStatus.FUNDS_RECEIVED.value, DealStatus.CANCELLED.value}
    ),
    DealStatus.FUNDS_RECEIVED.value: frozenset(
        {DealStatus.PROCESSING.value, DealStatus.CANCELLED.value}
    ),
    DealStatus.PROCESSING.value: frozenset(
        {DealStatus.COMPLETED.value, DealStatus.CANCELLED.value}
    ),
}


def format_deal(deal: Deal) -> str:
    return (
        f"Deal `{deal.id}`\n"
        f"Status: {deal.status}\n"
        f"Client: {deal.client_id or '—'}\n"
        f"Manager: {deal.manager_id or '—'}\n"
        f"Partner: {deal.partner_id or '—'}\n"
        f"In: {deal.asset_in_amount or '—'} {deal.asset_in_type or ''}\n"
        f"Out: {deal.asset_out_amount or '—'} {deal.asset_out_type or ''}\n"
        f"Rate: {deal.exchange_rate or '—'}\n"
        f"Commission: {deal.commission_amount or '—'} {deal.commission_currency or ''}"
    )


class DealWorkflowService:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in WORKFLOW_ROLES for role in roles)

    @staticmethod
    async def user_is_admin(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in {"OWNER", "ADMIN"} for role in roles)

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
            entity_type="deal",
            entity_id=entity_id,
            action=action,
            old_value=old_value,
            new_value=new_value,
        )

    @staticmethod
    async def _notify(
        session,
        *,
        notification_type: str,
        title: str,
        message: str,
        user_id: int | None = None,
        deal_id: uuid.UUID | None = None,
    ) -> None:
        await NotificationRepository(session).create(
            user_id=user_id,
            deal_id=deal_id,
            notification_type=notification_type,
            channel=NotificationChannel.TELEGRAM.value,
            title=title,
            message=message,
        )

    @staticmethod
    async def _publish_event(
        event_type: str,
        deal_id: uuid.UUID,
        payload: dict,
    ) -> None:
        try:
            from events.crm_publisher import publish_crm_event

            await publish_crm_event(
                event_type,
                "deal",
                deal_id,
                payload,
            )
        except Exception:
            pass

    @staticmethod
    async def create_deal(
        actor_id: int,
        *,
        client_id: int | None = None,
        asset_in_type: str,
        asset_in_amount: Decimal,
        asset_out_type: str,
        asset_out_amount: Decimal,
        manager_id: int | None = None,
        partner_id: int | None = None,
        exchange_rate: Decimal | None = None,
        commission_amount: Decimal | None = None,
        commission_currency: str | None = None,
    ) -> Deal:
        if not await DealWorkflowService.user_can_access(actor_id):
            raise PermissionError("Access denied")

        async with get_session() as session:
            deal_repo = DealRepository(session)
            deal = await deal_repo.create(
                client_id=client_id or actor_id,
                manager_id=manager_id,
                partner_id=partner_id,
                asset_in_type=asset_in_type,
                asset_in_amount=asset_in_amount,
                asset_out_type=asset_out_type,
                asset_out_amount=asset_out_amount,
                exchange_rate=exchange_rate,
                commission_amount=commission_amount,
                commission_currency=commission_currency or asset_in_type,
            )
            await DealWorkflowService._audit(
                session,
                user_id=actor_id,
                action=AuditAction.CREATE.value,
                entity_id=str(deal.id),
                new_value={"status": deal.status, "client_id": deal.client_id},
            )
            await DealWorkflowService._notify(
                session,
                notification_type=NotificationType.DEAL_CREATED.value,
                title="Deal created",
                message=f"New deal {deal.id} created",
                user_id=deal.client_id,
                deal_id=deal.id,
            )
            await DealWorkflowService._publish_event(
                "deal.created",
                deal.id,
                {"client_id": deal.client_id, "status": deal.status},
            )
            return deal

    @staticmethod
    async def get_my_deals(user_id: int) -> list[Deal]:
        if not await DealWorkflowService.user_can_access(user_id):
            raise PermissionError("Access denied")
        async with get_session() as session:
            return await DealRepository(session).list_by_manager(user_id, limit=50)

    @staticmethod
    async def get_active_deals(user_id: int) -> list[Deal]:
        if not await DealWorkflowService.user_can_access(user_id):
            raise PermissionError("Access denied")
        async with get_session() as session:
            repo = DealRepository(session)
            if await DealWorkflowService.user_is_admin(user_id):
                return await repo.list_active(limit=50)
            return await repo.list_by_manager(user_id, active_only=True, limit=50)

    @staticmethod
    async def get_deal_info(user_id: int, deal_id: uuid.UUID) -> Deal | None:
        if not await DealWorkflowService.user_can_access(user_id):
            raise PermissionError("Access denied")
        async with get_session() as session:
            deal = await DealRepository(session).get_by_id(deal_id)
            if deal is None:
                return None
            if not await DealWorkflowService.user_is_admin(user_id):
                if deal.manager_id != user_id and deal.client_id != user_id:
                    raise PermissionError("Access denied")
            return deal

    @staticmethod
    async def assign_deal(
        actor_id: int,
        deal_id: uuid.UUID,
        manager_id: int,
    ) -> Deal | None:
        if not await DealWorkflowService.user_can_access(actor_id):
            raise PermissionError("Access denied")
        async with get_session() as session:
            deal_repo = DealRepository(session)
            deal = await deal_repo.get_by_id(deal_id)
            if deal is None:
                return None
            old = {"manager_id": deal.manager_id, "status": deal.status}
            deal = await deal_repo.assign_manager(deal_id, manager_id)
            await DealWorkflowService._audit(
                session,
                user_id=actor_id,
                action=AuditAction.ASSIGN.value,
                entity_id=str(deal_id),
                old_value=old,
                new_value={"manager_id": manager_id, "status": deal.status},
            )
            await DealWorkflowService._notify(
                session,
                notification_type=NotificationType.DEAL_ASSIGNED.value,
                title="Deal assigned",
                message=f"Deal {deal_id} assigned to manager {manager_id}",
                user_id=manager_id,
                deal_id=deal_id,
            )
            await DealWorkflowService._publish_event(
                "deal.updated",
                deal_id,
                {"manager_id": manager_id, "status": deal.status},
            )
            return deal

    @staticmethod
    async def update_status(
        actor_id: int,
        deal_id: uuid.UUID,
        new_status: str,
    ) -> Deal | None:
        if not await DealWorkflowService.user_can_access(actor_id):
            raise PermissionError("Access denied")
        new_status = new_status.upper()
        if new_status not in WORKFLOW_STATUSES:
            raise ValueError(f"Invalid status: {new_status}")

        async with get_session() as session:
            deal_repo = DealRepository(session)
            ledger_repo = LedgerRepository(session)
            commission_repo = CommissionRepository(session)

            deal = await deal_repo.get_by_id(deal_id)
            if deal is None:
                return None

            allowed = STATUS_TRANSITIONS.get(deal.status, frozenset())
            if new_status != deal.status:
                if new_status == DealStatus.CANCELLED.value:
                    if deal.status in {DealStatus.COMPLETED.value, DealStatus.CANCELLED.value}:
                        raise ValueError(f"Cannot cancel deal in status {deal.status}")
                elif new_status not in allowed:
                    raise ValueError(
                        f"Cannot transition {deal.status} → {new_status}"
                    )

            old_status = deal.status
            deal = await deal_repo.update_status(deal_id, new_status)
            if deal is None:
                return None

            if new_status == DealStatus.FUNDS_RECEIVED.value and deal.asset_in_amount:
                await ledger_repo.create_entry(
                    deal_id=deal_id,
                    account_type=LedgerAccountType.COMPANY.value,
                    account_id=None,
                    asset=deal.asset_in_type or "USDT",
                    amount=deal.asset_in_amount,
                    direction=LedgerDirection.CREDIT.value,
                    description="Funds received for deal",
                )
                await DealWorkflowService._notify(
                    session,
                    notification_type=NotificationType.FUNDS_RECEIVED.value,
                    title="Funds received",
                    message=f"Funds received for deal {deal_id}",
                    user_id=deal.manager_id,
                    deal_id=deal_id,
                )
                await DealWorkflowService._publish_event(
                    "payment.received",
                    deal_id,
                    {"amount": str(deal.asset_in_amount), "asset": deal.asset_in_type},
                )

            if new_status == DealStatus.PROCESSING.value:
                await DealWorkflowService._publish_event(
                    "deal.updated",
                    deal_id,
                    {"status": new_status},
                )

            await DealWorkflowService._audit(
                session,
                user_id=actor_id,
                action=AuditAction.STATUS_CHANGE.value,
                entity_id=str(deal_id),
                old_value={"status": old_status},
                new_value={"status": new_status},
            )
            await DealWorkflowService._notify(
                session,
                notification_type=NotificationType.STATUS_CHANGED.value,
                title="Deal status changed",
                message=f"Deal {deal_id}: {old_status} → {new_status}",
                user_id=deal.manager_id or deal.client_id,
                deal_id=deal_id,
            )
            return deal

    @staticmethod
    async def complete_deal(actor_id: int, deal_id: uuid.UUID) -> Deal | None:
        if not await DealWorkflowService.user_can_access(actor_id):
            raise PermissionError("Access denied")

        async with get_session() as session:
            deal_repo = DealRepository(session)
            ledger_repo = LedgerRepository(session)
            commission_repo = CommissionRepository(session)

            deal = await deal_repo.get_by_id(deal_id)
            if deal is None:
                return None
            if deal.status not in {
                DealStatus.PROCESSING.value,
                DealStatus.FUNDS_RECEIVED.value,
            }:
                raise ValueError(
                    f"Deal must be PROCESSING or FUNDS_RECEIVED, got {deal.status}"
                )

            old_status = deal.status
            deal = await deal_repo.update_status(deal_id, DealStatus.COMPLETED.value)
            if deal is None:
                return None

            asset = deal.commission_currency or deal.asset_in_type or "USDT"
            client_fee = deal.commission_amount or Decimal("0")
            if client_fee > 0:
                await commission_repo.create(
                    deal_id=deal_id,
                    commission_type=CommissionType.CLIENT_FEE.value,
                    asset=asset,
                    amount=client_fee,
                    status=CommissionStatus.CALCULATED.value,
                )

            manager_reward = (client_fee * Decimal("0.10")).quantize(Decimal("0.00000001"))
            if deal.manager_id and manager_reward > 0:
                await commission_repo.create(
                    deal_id=deal_id,
                    commission_type=CommissionType.MANAGER_REWARD.value,
                    asset=asset,
                    amount=manager_reward,
                    manager_id=deal.manager_id,
                    percentage=Decimal("10.0000"),
                    status=CommissionStatus.CALCULATED.value,
                )

            if deal.partner_id and client_fee > 0:
                partner_reward = (client_fee * Decimal("0.05")).quantize(Decimal("0.00000001"))
                await commission_repo.create(
                    deal_id=deal_id,
                    commission_type=CommissionType.PARTNER_REWARD.value,
                    asset=asset,
                    amount=partner_reward,
                    partner_id=deal.partner_id,
                    percentage=Decimal("5.0000"),
                    status=CommissionStatus.CALCULATED.value,
                )

            company_profit = await commission_repo.calculate_company_profit(deal_id)
            if company_profit > 0:
                await commission_repo.create(
                    deal_id=deal_id,
                    commission_type=CommissionType.COMPANY_PROFIT.value,
                    asset=asset,
                    amount=company_profit,
                    status=CommissionStatus.CALCULATED.value,
                )
                await ledger_repo.create_entry(
                    deal_id=deal_id,
                    account_type=LedgerAccountType.COMPANY.value,
                    asset=asset,
                    amount=company_profit,
                    direction=LedgerDirection.CREDIT.value,
                    description="Company profit on deal completion",
                )

            if deal.asset_out_amount and deal.asset_out_type:
                await ledger_repo.create_entry(
                    deal_id=deal_id,
                    account_type=LedgerAccountType.CLIENT.value,
                    account_id=deal.client_id,
                    asset=deal.asset_out_type,
                    amount=deal.asset_out_amount,
                    direction=LedgerDirection.DEBIT.value,
                    description="Client payout on deal completion",
                )

            await DealWorkflowService._audit(
                session,
                user_id=actor_id,
                action=AuditAction.STATUS_CHANGE.value,
                entity_id=str(deal_id),
                old_value={"status": old_status},
                new_value={"status": DealStatus.COMPLETED.value, "profit": str(company_profit)},
            )
            await DealWorkflowService._notify(
                session,
                notification_type=NotificationType.DEAL_COMPLETED.value,
                title="Deal completed",
                message=f"Deal {deal_id} completed. Profit: {company_profit} {asset}",
                user_id=deal.manager_id or deal.client_id,
                deal_id=deal_id,
            )
            await DealWorkflowService._notify(
                session,
                notification_type=NotificationType.COMMISSION_CALCULATED.value,
                title="Commissions calculated",
                message=f"Commissions calculated for deal {deal_id}",
                user_id=deal.manager_id,
                deal_id=deal_id,
            )
            await DealWorkflowService._publish_event(
                "deal.closed",
                deal_id,
                {"status": DealStatus.COMPLETED.value, "profit": str(company_profit)},
            )
            await DealWorkflowService._publish_event(
                "commission.accrued",
                deal_id,
                {"profit": str(company_profit), "asset": asset},
            )
            return deal
