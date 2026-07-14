# Universal Deal Engine v1 — lead conversion, dashboard, partner attachment.

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select

from database.models.deal_engine_v1 import (
    DEAL_ENGINE_V1_SUPPORTED_VERTICALS,
    DEAL_ENGINE_V1_TERMINAL_STATUSES,
    DealEngineV1Deal,
    DealEngineV1Status,
)
from database.models.lead_engine import LeadEngineLead, LeadEngineStatus
from database.models.users import User
from database.session import get_session
from repositories.deal_engine_v1_repository import DealEngineV1Repository
from repositories.lead_engine_repository import LeadEngineRepository


class DealEngineV1Error(Exception):
    pass


logger = logging.getLogger(__name__)


class DealEngineV1:
    @staticmethod
    async def create_from_lead(
        lead_id: uuid.UUID,
        *,
        title: str | None = None,
        description: str | None = None,
        amount: Decimal | float | str = Decimal("0"),
        currency: str = "USD",
        partner_id: uuid.UUID | None = None,
        manager_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        async with get_session() as session:
            lead_repo = LeadEngineRepository(session)
            deal_repo = DealEngineV1Repository(session)

            lead = await lead_repo.get_by_id(lead_id)
            if lead is None:
                raise DealEngineV1Error(f"Lead {lead_id} not found")

            existing = await deal_repo.get_by_lead_id(lead_id)
            if existing is not None:
                raise DealEngineV1Error(f"Deal already exists for lead {lead_id}")

            client_id = await DealEngineV1._resolve_client_id(session, lead)
            resolved_manager = manager_id or lead.assigned_manager_id
            deal_title = title or DealEngineV1._default_title(lead)

            row = await deal_repo.create(
                lead_id=lead.id,
                vertical=lead.vertical,
                client_id=client_id,
                manager_id=resolved_manager,
                partner_id=partner_id,
                title=deal_title,
                description=description,
                amount=Decimal(str(amount)),
                currency=currency.upper(),
                status=DealEngineV1Status.NEW.value,
            )

            if lead.status not in {LeadEngineStatus.WON.value, LeadEngineStatus.LOST.value}:
                await lead_repo.update(lead.id, status=LeadEngineStatus.WON.value)

        from services.pg_sla_tracking_v1 import SlaTrackingV1

        await SlaTrackingV1.on_deal_linked(lead.id, row.id)
        return DealEngineV1._snapshot(row)

    @staticmethod
    async def create_deal(
        *,
        vertical: str,
        client_id: uuid.UUID,
        title: str,
        manager_id: uuid.UUID | None = None,
        partner_id: uuid.UUID | None = None,
        description: str | None = None,
        amount: Decimal | float | str = Decimal("0"),
        currency: str = "USD",
        lead_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        vertical_key = vertical.strip().lower()
        if vertical_key not in DEAL_ENGINE_V1_SUPPORTED_VERTICALS:
            raise DealEngineV1Error(f"Unsupported vertical: {vertical}")

        async with get_session() as session:
            row = await DealEngineV1Repository(session).create(
                lead_id=lead_id,
                vertical=vertical_key,
                client_id=client_id,
                manager_id=manager_id,
                partner_id=partner_id,
                title=title,
                description=description,
                amount=Decimal(str(amount)),
                currency=currency.upper(),
                status=DealEngineV1Status.NEW.value,
            )
        return DealEngineV1._snapshot(row)

    @staticmethod
    async def update_status(deal_id: uuid.UUID, status: str) -> dict[str, Any] | None:
        if status not in {s.value for s in DealEngineV1Status}:
            raise DealEngineV1Error(f"Unsupported status: {status}")

        updates: dict[str, Any] = {"status": status}
        if status in DEAL_ENGINE_V1_TERMINAL_STATUSES:
            updates["closed_at"] = datetime.now(timezone.utc)

        async with get_session() as session:
            row = await DealEngineV1Repository(session).update(deal_id, **updates)
        if row is None:
            return None
        snapshot = DealEngineV1._snapshot(row)
        if status == DealEngineV1Status.COMPLETED.value:
            from services.pg_revenue_engine_v1 import RevenueEngineV1

            try:
                revenue = await RevenueEngineV1.create_from_completed_deal(deal_id)
                if revenue:
                    snapshot["revenue_entry_id"] = revenue["id"]
            except Exception:
                logger.exception("Revenue entry creation failed for deal %s", deal_id)
        if status in DEAL_ENGINE_V1_TERMINAL_STATUSES:
            from services.pg_sla_tracking_v1 import SlaTrackingV1

            lead_uuid = uuid.UUID(snapshot["lead_id"]) if snapshot.get("lead_id") else None
            await SlaTrackingV1.on_deal_closed(
                deal_id=deal_id,
                lead_id=lead_uuid,
                closed_at=datetime.fromisoformat(snapshot["closed_at"])
                if snapshot.get("closed_at")
                else None,
            )
        return snapshot

    @staticmethod
    async def attach_partner(deal_id: uuid.UUID, partner_id: uuid.UUID | None) -> dict[str, Any] | None:
        async with get_session() as session:
            row = await DealEngineV1Repository(session).attach_partner(deal_id, partner_id)
        if row is None:
            return None
        return DealEngineV1._snapshot(row)

    @staticmethod
    async def get_owner_dashboard() -> dict[str, Any]:
        today = DealEngineV1Repository.start_of_today()
        week = DealEngineV1Repository.start_of_week()

        async with get_session() as session:
            repo = DealEngineV1Repository(session)
            total = await repo.count_since()
            today_count = await repo.count_since(today)
            week_count = await repo.count_since(week)
            completed = await repo.count_by_status(DealEngineV1Status.COMPLETED.value)
            cancelled = await repo.count_by_status(DealEngineV1Status.CANCELLED.value)
            in_progress = await repo.count_by_status(DealEngineV1Status.IN_PROGRESS.value)
            payment_pending = await repo.count_by_status(DealEngineV1Status.PAYMENT_PENDING.value)
            by_vertical = await repo.group_count(DealEngineV1Deal.vertical, since=week)
            by_status = await repo.group_count(DealEngineV1Deal.status, since=week)
            auto_volume = await repo.sum_amount(
                vertical="auto",
                since=week,
                statuses=frozenset({DealEngineV1Status.COMPLETED.value, DealEngineV1Status.PAYMENT_RECEIVED.value}),
            )
            agro_volume = await repo.sum_amount(
                vertical="agro",
                since=week,
                statuses=frozenset({DealEngineV1Status.COMPLETED.value, DealEngineV1Status.PAYMENT_RECEIVED.value}),
            )
            recent = await repo.list_recent(limit=10)

        closed = completed + cancelled
        completion_rate = round((completed / closed) * 100, 1) if closed else 0.0

        return {
            "total": total,
            "today": today_count,
            "week": week_count,
            "completed": completed,
            "cancelled": cancelled,
            "in_progress": in_progress,
            "payment_pending": payment_pending,
            "completion_rate": completion_rate,
            "by_vertical": by_vertical,
            "by_status": by_status,
            "auto_volume_week": auto_volume,
            "agro_volume_week": agro_volume,
            "recent": [DealEngineV1._snapshot(row) for row in recent],
        }

    @staticmethod
    def format_owner_dashboard(data: dict[str, Any]) -> str:
        lines = [
            "🤝 Deal Engine Dashboard",
            "",
            f"📈 Deals today: {data['today']}",
            f"📈 Deals this week: {data['week']}",
            f"📈 Total deals: {data['total']}",
            f"📈 Completion rate: {data['completion_rate']}%",
            "",
            "📈 By vertical (week):",
        ]
        if data["by_vertical"]:
            for vertical, count in data["by_vertical"]:
                volume = data.get("auto_volume_week") if vertical == "auto" else data.get("agro_volume_week")
                vol_line = f" | vol {volume}" if vertical in {"auto", "agro"} and volume else ""
                lines.append(f"  • {vertical or '—'}: {count}{vol_line}")
        else:
            lines.append("  • —")

        lines.append("")
        lines.append("📈 By status (week):")
        if data["by_status"]:
            for status, count in data["by_status"]:
                lines.append(f"  • {status}: {count}")
        else:
            lines.append("  • —")

        lines.append("")
        lines.append(
            f"Pipeline: ⚙ {data['in_progress']} in progress | "
            f"💳 {data['payment_pending']} payment pending | "
            f"✅ {data['completed']} completed | ❌ {data['cancelled']} cancelled"
        )

        recent = data.get("recent") or []
        if recent:
            lines.append("")
            lines.append("Recent deals:")
            for deal in recent[:5]:
                lines.append(
                    f"  • {deal.get('title', '—')} | {deal.get('vertical')} | "
                    f"{deal.get('amount')} {deal.get('currency')} | {deal.get('status')}"
                )
        return "\n".join(lines)

    @staticmethod
    def format_deal_list(deals: list[dict[str, Any]]) -> str:
        if not deals:
            return "📋 Deals\n\nСписок пуст."
        lines = ["📋 Deals", ""]
        for deal in deals:
            partner = deal.get("partner_id") or "—"
            lines.append(
                f"• {deal['id'][:8]}… | {deal['vertical']} | {deal['status']}\n"
                f"  {deal.get('title')} | {deal.get('amount')} {deal.get('currency')}\n"
                f"  partner: {partner[:8] + '…' if partner != '—' else '—'}"
            )
        return "\n".join(lines)

    @staticmethod
    async def _resolve_client_id(session, lead: LeadEngineLead) -> uuid.UUID:
        result = await session.execute(
            select(User).where(User.telegram_id == lead.telegram_user_id)
        )
        user = result.scalar_one_or_none()
        if user is None:
            raise DealEngineV1Error(
                f"No user record for telegram_id={lead.telegram_user_id}. "
                "Ensure user exists before converting lead."
            )
        return user.id

    @staticmethod
    def _default_title(lead: LeadEngineLead) -> str:
        name = lead.full_name or lead.telegram_username or str(lead.telegram_user_id)
        return f"{lead.vertical.upper()} deal — {name}"

    @staticmethod
    def _snapshot(row: DealEngineV1Deal) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "lead_id": str(row.lead_id) if row.lead_id else None,
            "vertical": row.vertical,
            "client_id": str(row.client_id),
            "manager_id": str(row.manager_id) if row.manager_id else None,
            "partner_id": str(row.partner_id) if row.partner_id else None,
            "title": row.title,
            "description": row.description,
            "amount": str(row.amount),
            "currency": row.currency,
            "status": row.status,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
            "closed_at": row.closed_at.isoformat() if row.closed_at else None,
        }
