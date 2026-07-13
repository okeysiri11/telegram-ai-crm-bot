# Sales Pipeline Automation Engine v1 — stages, reminders, inactivity, follow-ups.

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from aiogram import Bot
from sqlalchemy import select

from config import BOT_TOKEN, MANAGER_ID, OWNER_ID
from database.models.audit_log import AuditAction
from database.models.lead_automation_engine import AutomationLead
from database.models.sales_pipeline_automation_engine import (
    STAGE_LABELS,
    PipelineStage,
)
from database.session import get_session
from repositories.audit_repository import AuditRepository
from repositories.lead_automation_repository import LeadAutomationRepository
from repositories.sales_pipeline_automation_repository import (
    FollowUpTaskRepository,
    InactivityAlertRepository,
    PipelineLeadRepository,
    PipelineReminderRepository,
    StageTransitionRepository,
)
from repositories.user_role_repository import UserRoleRepository

logger = logging.getLogger(__name__)

PIPELINE_ROLES = frozenset({"OWNER", "ADMIN", "MANAGER"})
INACTIVITY_DAYS_THRESHOLD = 3
STAGE_FOLLOW_UP_HOURS: dict[str, int] = {
    PipelineStage.NEW_LEAD.value: 24,
    PipelineStage.CONTACTED.value: 48,
    PipelineStage.INTERESTED.value: 72,
    PipelineStage.INSPECTION_SCHEDULED.value: 24,
    PipelineStage.NEGOTIATION.value: 48,
    PipelineStage.RESERVED.value: 24,
}


class SalesPipelineAutomationError(Exception):
    pass


class SalesPipelineAutomationEngineV1:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in PIPELINE_ROLES for role in roles)

    @staticmethod
    def _pipeline_snapshot(lead) -> dict[str, Any]:
        return {
            "id": str(lead.id),
            "automation_lead_id": str(lead.automation_lead_id),
            "car_id": str(lead.car_id) if lead.car_id else None,
            "stage": lead.stage,
            "stage_label": STAGE_LABELS.get(lead.stage, lead.stage),
            "assigned_manager_id": lead.assigned_manager_id,
            "last_activity_at": lead.last_activity_at.isoformat()
            if lead.last_activity_at
            else None,
            "next_follow_up_at": lead.next_follow_up_at.isoformat()
            if lead.next_follow_up_at
            else None,
            "metadata": lead.metadata_ or {},
            "created_at": lead.created_at.isoformat(),
            "updated_at": lead.updated_at.isoformat(),
        }

    @staticmethod
    async def sync_from_automation_leads(*, limit: int = 100) -> dict[str, Any]:
        created = 0
        async with get_session() as session:
            lead_repo = LeadAutomationRepository(session)
            pipeline_repo = PipelineLeadRepository(session)
            transition_repo = StageTransitionRepository(session)

            result = await session.execute(
                select(AutomationLead)
                .where(AutomationLead.is_duplicate.is_(False))
                .order_by(AutomationLead.created_at.desc())
                .limit(limit)
            )
            automation_leads = list(result.scalars().all())

            for auto_lead in automation_leads:
                existing = await pipeline_repo.get_by_automation_lead(auto_lead.id)
                if existing is not None:
                    continue
                pipeline_lead = await pipeline_repo.create(
                    automation_lead_id=auto_lead.id,
                    car_id=auto_lead.car_id,
                    assigned_manager_id=auto_lead.assigned_manager_id,
                )
                await transition_repo.record(
                    pipeline_lead_id=pipeline_lead.id,
                    from_stage=None,
                    to_stage=PipelineStage.NEW_LEAD.value,
                    notes="Auto-sync from lead automation",
                )
                await SalesPipelineAutomationEngineV1._schedule_stage_follow_up(
                    session,
                    pipeline_lead,
                )
                created += 1

        return {"synced": created, "scanned": len(automation_leads)}

    @staticmethod
    async def transition_stage(
        actor_id: int,
        pipeline_lead_id: uuid.UUID,
        *,
        to_stage: str,
        notes: str | None = None,
    ) -> dict[str, Any]:
        if not await SalesPipelineAutomationEngineV1.user_can_access(actor_id):
            raise SalesPipelineAutomationError("Access denied")
        if to_stage not in STAGE_LABELS:
            raise SalesPipelineAutomationError(f"Invalid stage: {to_stage}")

        async with get_session() as session:
            pipeline_repo = PipelineLeadRepository(session)
            transition_repo = StageTransitionRepository(session)
            lead = await pipeline_repo.get_by_id(pipeline_lead_id)
            if lead is None:
                raise SalesPipelineAutomationError(f"Pipeline lead not found: {pipeline_lead_id}")

            from_stage = lead.stage
            now = datetime.now(timezone.utc)
            await pipeline_repo.update(
                lead,
                stage=to_stage,
                last_activity_at=now,
            )
            await transition_repo.record(
                pipeline_lead_id=lead.id,
                from_stage=from_stage,
                to_stage=to_stage,
                changed_by=actor_id,
                notes=notes,
            )
            await SalesPipelineAutomationEngineV1._schedule_stage_follow_up(session, lead)
            if to_stage == PipelineStage.CONTACTED.value:
                await FollowUpTaskRepository(session).create(
                    pipeline_lead_id=lead.id,
                    title="Follow up after contact",
                    description=notes,
                    due_at=now + timedelta(hours=24),
                    assigned_to=lead.assigned_manager_id or MANAGER_ID,
                )
            await AuditRepository(session).create_log(
                user_id=actor_id,
                entity_type="pipeline_lead",
                entity_id=str(lead.id),
                action=AuditAction.UPDATE.value,
                old_value={"stage": from_stage},
                new_value={"stage": to_stage},
            )
            await session.refresh(lead)
            return SalesPipelineAutomationEngineV1._pipeline_snapshot(lead)

    @staticmethod
    async def _schedule_stage_follow_up(session, lead) -> None:
        hours = STAGE_FOLLOW_UP_HOURS.get(lead.stage, 48)
        due_at = datetime.now(timezone.utc) + timedelta(hours=hours)
        await PipelineReminderRepository(session).create(
            pipeline_lead_id=lead.id,
            reminder_type=f"stage_{lead.stage}",
            message=f"Follow up: lead in stage {STAGE_LABELS.get(lead.stage, lead.stage)}",
            due_at=due_at,
        )
        await PipelineLeadRepository(session).update(lead, next_follow_up_at=due_at)

    @staticmethod
    async def list_pipeline(
        actor_id: int,
        *,
        stage: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        if not await SalesPipelineAutomationEngineV1.user_can_access(actor_id):
            raise SalesPipelineAutomationError("Access denied")

        async with get_session() as session:
            repo = PipelineLeadRepository(session)
            if stage:
                leads = await repo.list_by_stage(stage, limit=limit)
            else:
                leads = []
                for stage_value in PipelineStage:
                    leads.extend(await repo.list_by_stage(stage_value.value, limit=limit))
                leads = leads[:limit]
            return [SalesPipelineAutomationEngineV1._pipeline_snapshot(l) for l in leads]

    @staticmethod
    async def process_reminders(*, limit: int = 50) -> dict[str, Any]:
        sent = 0
        results: list[dict[str, Any]] = []

        async with get_session() as session:
            reminder_repo = PipelineReminderRepository(session)
            pipeline_repo = PipelineLeadRepository(session)
            due = await reminder_repo.list_due(limit=limit)

            for reminder in due:
                lead = await pipeline_repo.get_by_id(reminder.pipeline_lead_id)
                manager_id = lead.assigned_manager_id if lead else MANAGER_ID
                await SalesPipelineAutomationEngineV1._notify_manager(
                    manager_id=manager_id or MANAGER_ID,
                    message=reminder.message,
                )
                await reminder_repo.mark_sent(reminder)
                if lead:
                    await FollowUpTaskRepository(session).create(
                        pipeline_lead_id=lead.id,
                        title=f"Reminder: {reminder.reminder_type}",
                        description=reminder.message,
                        assigned_to=manager_id,
                    )
                sent += 1
                results.append({
                    "reminder_id": str(reminder.id),
                    "pipeline_lead_id": str(reminder.pipeline_lead_id),
                    "type": reminder.reminder_type,
                })

        return {"sent": sent, "results": results}

    @staticmethod
    async def check_inactivity(*, inactive_days: int = INACTIVITY_DAYS_THRESHOLD) -> dict[str, Any]:
        alerts_created = 0
        cutoff = datetime.now(timezone.utc) - timedelta(days=inactive_days)

        async with get_session() as session:
            pipeline_repo = PipelineLeadRepository(session)
            alert_repo = InactivityAlertRepository(session)
            inactive_leads = await pipeline_repo.list_inactive(before=cutoff)

            for lead in inactive_leads:
                if await alert_repo.has_open_alert(lead.id):
                    continue
                days = inactive_days
                if lead.last_activity_at:
                    delta = datetime.now(timezone.utc) - lead.last_activity_at
                    days = max(inactive_days, delta.days)

                message = (
                    f"Inactivity alert: pipeline lead {lead.id} "
                    f"inactive {days} days in stage {STAGE_LABELS.get(lead.stage, lead.stage)}"
                )
                await alert_repo.create(
                    pipeline_lead_id=lead.id,
                    inactive_days=days,
                    message=message,
                )
                await SalesPipelineAutomationEngineV1._notify_manager(
                    manager_id=lead.assigned_manager_id or MANAGER_ID,
                    message=message,
                )
                alerts_created += 1

        return {"alerts_created": alerts_created, "inactive_scanned": len(inactive_leads)}

    @staticmethod
    async def run_automation_cycle(
        *,
        reminder_limit: int = 50,
        inactive_days: int = INACTIVITY_DAYS_THRESHOLD,
    ) -> dict[str, Any]:
        sync = await SalesPipelineAutomationEngineV1.sync_from_automation_leads()
        reminders = await SalesPipelineAutomationEngineV1.process_reminders(limit=reminder_limit)
        inactivity = await SalesPipelineAutomationEngineV1.check_inactivity(
            inactive_days=inactive_days,
        )
        return {"sync": sync, "reminders": reminders, "inactivity": inactivity}

    @staticmethod
    async def _notify_manager(*, manager_id: int, message: str) -> None:
        if not BOT_TOKEN:
            return
        bot = Bot(token=BOT_TOKEN)
        try:
            await bot.send_message(
                chat_id=manager_id,
                text=f"📋 Sales Pipeline\n\n{message[:3500]}",
            )
        except Exception:
            logger.exception("Pipeline notify failed for manager %s", manager_id)
        finally:
            await bot.session.close()
