# Deal Pipeline Engine v2 — stage validation, tasks, SLA, manager assignment.

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from config import MANAGER_ID, OWNER_ID
from database.models.ai_sales_agent import SalesLeadStatus
from database.models.audit_log import AuditAction
from database.models.deal_pipeline_engine import (
    DEFAULT_STAGE_ORDER,
    DEFAULT_STAGE_SLA_HOURS,
    DealPipelineStageCode,
    DealStatus,
    DealTaskStatus,
)
from database.models.notification import NotificationChannel, NotificationType
from database.session import get_session
from repositories.audit_repository import AuditRepository
from repositories.deal_pipeline_repository import (
    DEFAULT_ALLOWED_TRANSITIONS,
    DealCommentRepository,
    DealStageHistoryRepository,
    DealStageRepository,
    DealTaskRepository,
    PipelineDealRepository,
)
from repositories.notification_repository import NotificationRepository
from repositories.user_role_repository import UserRoleRepository
from services.pg_ai_sales_agent_engine import AiSalesAgentV1
from services.pg_partner_tenant_engine import PartnerTenantEngineV1

DEAL_PIPELINE_ROLES = frozenset({"OWNER", "ADMIN", "MANAGER"})
MODEL_VERSION = "deal-pipeline-engine-v2.0.0"

STAGE_LABELS: dict[str, str] = {
    DealPipelineStageCode.NEW_LEAD.value: "New Lead",
    DealPipelineStageCode.CONTACTED.value: "Contacted",
    DealPipelineStageCode.QUALIFIED.value: "Qualified",
    DealPipelineStageCode.VIEWING.value: "Viewing",
    DealPipelineStageCode.NEGOTIATION.value: "Negotiation",
    DealPipelineStageCode.RESERVED.value: "Reserved",
    DealPipelineStageCode.DOCUMENTS.value: "Documents",
    DealPipelineStageCode.PAYMENT.value: "Payment",
    DealPipelineStageCode.DELIVERED.value: "Delivered",
    DealPipelineStageCode.LOST.value: "Lost",
}

AUTO_TASKS_BY_STAGE: dict[str, str] = {
    DealPipelineStageCode.CONTACTED.value: "Follow up after initial contact",
    DealPipelineStageCode.QUALIFIED.value: "Schedule vehicle viewing",
    DealPipelineStageCode.VIEWING.value: "Collect feedback after viewing",
    DealPipelineStageCode.NEGOTIATION.value: "Prepare offer terms",
    DealPipelineStageCode.RESERVED.value: "Prepare reservation documents",
    DealPipelineStageCode.DOCUMENTS.value: "Verify document package",
    DealPipelineStageCode.PAYMENT.value: "Confirm payment received",
}

SALES_AGENT_STAGE_MAP: dict[str, str] = {
    DealPipelineStageCode.NEW_LEAD.value: SalesLeadStatus.NEW.value,
    DealPipelineStageCode.QUALIFIED.value: SalesLeadStatus.QUALIFIED.value,
    DealPipelineStageCode.NEGOTIATION.value: SalesLeadStatus.NEGOTIATION.value,
    DealPipelineStageCode.RESERVED.value: SalesLeadStatus.RESERVED.value,
    DealPipelineStageCode.DELIVERED.value: SalesLeadStatus.SOLD.value,
    DealPipelineStageCode.LOST.value: SalesLeadStatus.LOST.value,
}


class DealPipelineEngineError(Exception):
    pass


class DealPipelineEngineV2:
    @staticmethod
    async def user_can_access(user_id: int) -> bool:
        if user_id == OWNER_ID:
            return True
        async with get_session() as session:
            roles = await UserRoleRepository(session).get_user_roles(user_id)
            return any(role.code in DEAL_PIPELINE_ROLES for role in roles)

    @staticmethod
    async def _require_access(actor_id: int, tenant_id: uuid.UUID):
        if not await DealPipelineEngineV2.user_can_access(actor_id):
            raise DealPipelineEngineError("Deal pipeline access denied")
        return await PartnerTenantEngineV1.resolve_context(actor_id, tenant_id)

    @staticmethod
    def _deal_snapshot(row) -> dict[str, Any]:
        return {
            "id": str(row.id),
            "tenant_id": str(row.tenant_id),
            "title": row.title,
            "current_stage": row.current_stage,
            "stage_label": STAGE_LABELS.get(row.current_stage, row.current_stage),
            "status": row.status,
            "sales_lead_id": str(row.sales_lead_id) if row.sales_lead_id else None,
            "car_id": str(row.car_id) if row.car_id else None,
            "assigned_manager_id": row.assigned_manager_id,
            "deal_value": str(row.deal_value) if row.deal_value is not None else None,
            "currency": row.currency,
            "sla_due_at": row.sla_due_at.isoformat() if row.sla_due_at else None,
            "last_activity_at": row.last_activity_at.isoformat() if row.last_activity_at else None,
            "customer_name": row.customer_name,
            "created_at": row.created_at.isoformat(),
        }

    @staticmethod
    async def _get_deal_or_raise(session, deal_id: uuid.UUID, tenant_id: uuid.UUID):
        row = await PipelineDealRepository(session).get_by_id(deal_id)
        if row is None or row.tenant_id != tenant_id:
            raise DealPipelineEngineError(f"Deal not found: {deal_id}")
        return row

    @staticmethod
    async def validate_stage_transition(
        tenant_id: uuid.UUID,
        from_stage: str,
        to_stage: str,
    ) -> dict[str, Any]:
        async with get_session() as session:
            stage_row = await DealStageRepository(session).get_by_code(tenant_id, from_stage)
            allowed = (
                stage_row.allowed_next_stages
                if stage_row
                else DEFAULT_ALLOWED_TRANSITIONS.get(from_stage, [])
            )
        valid = to_stage in allowed
        return {
            "from_stage": from_stage,
            "to_stage": to_stage,
            "valid": valid,
            "allowed_next_stages": allowed,
        }

    @staticmethod
    async def _bootstrap_stages_in_session(
        session,
        *,
        tenant_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> list[dict[str, Any]]:
        created: list[dict[str, Any]] = []
        repo = DealStageRepository(session)
        for code in DealPipelineStageCode:
            existing = await repo.get_by_code(tenant_id, code.value)
            if existing:
                created.append({
                    "stage_code": existing.stage_code,
                    "label": existing.label,
                    "sla_hours": existing.sla_hours,
                })
                continue
            row = await repo.create(
                tenant_id=tenant_id,
                company_id=company_id,
                stage_code=code.value,
                label=STAGE_LABELS[code.value],
                sort_order=DEFAULT_STAGE_ORDER[code.value],
                sla_hours=DEFAULT_STAGE_SLA_HOURS[code.value],
                allowed_next_stages=DEFAULT_ALLOWED_TRANSITIONS.get(code.value, []),
                is_terminal=code.value in {
                    DealPipelineStageCode.DELIVERED.value,
                    DealPipelineStageCode.LOST.value,
                },
            )
            created.append({
                "stage_code": row.stage_code,
                "label": row.label,
                "sla_hours": row.sla_hours,
            })
        return created

    @staticmethod
    async def bootstrap_stages(actor_id: int, tenant_id: uuid.UUID) -> list[dict[str, Any]]:
        ctx = await DealPipelineEngineV2._require_access(actor_id, tenant_id)
        async with get_session() as session:
            return await DealPipelineEngineV2._bootstrap_stages_in_session(
                session,
                tenant_id=tenant_id,
                company_id=ctx.company_id,
            )

    @staticmethod
    async def create_deal(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        title: str,
        customer_name: str | None = None,
        sales_lead_id: uuid.UUID | None = None,
        car_id: uuid.UUID | None = None,
        assigned_manager_id: int | None = None,
        deal_value: Decimal | float | int | None = None,
    ) -> dict[str, Any]:
        ctx = await DealPipelineEngineV2._require_access(actor_id, tenant_id)
        now = datetime.now(timezone.utc)
        stage = DealPipelineStageCode.NEW_LEAD.value
        sla_hours = DEFAULT_STAGE_SLA_HOURS[stage]

        async with get_session() as session:
            stages = await DealStageRepository(session).list_by_tenant(tenant_id)
            if not stages:
                await DealPipelineEngineV2._bootstrap_stages_in_session(
                    session,
                    tenant_id=tenant_id,
                    company_id=ctx.company_id,
                )
            stage_row = await DealStageRepository(session).get_by_code(tenant_id, stage)
            if stage_row:
                sla_hours = stage_row.sla_hours

            manager = assigned_manager_id or MANAGER_ID
            deal = await PipelineDealRepository(session).create(
                tenant_id=tenant_id,
                company_id=ctx.company_id,
                title=title,
                customer_name=customer_name,
                sales_lead_id=sales_lead_id,
                car_id=car_id,
                assigned_manager_id=manager,
                deal_value=Decimal(str(deal_value)) if deal_value is not None else None,
                sla_due_at=now + timedelta(hours=sla_hours) if sla_hours else None,
                last_activity_at=now,
                created_by=actor_id,
            )
            await DealStageHistoryRepository(session).create(
                deal_id=deal.id,
                tenant_id=tenant_id,
                from_stage=None,
                to_stage=stage,
                changed_by=actor_id,
                notes="Deal created",
            )
            await DealTaskRepository(session).create(
                deal_id=deal.id,
                tenant_id=tenant_id,
                title="Initial contact",
                task_type="stage_NEW_LEAD",
                assigned_to=manager,
                due_at=now + timedelta(hours=sla_hours) if sla_hours else None,
                auto_created=True,
                created_by=actor_id,
            )
            await AuditRepository(session).create_log(
                user_id=actor_id,
                company_id=ctx.company_id,
                tenant_id=tenant_id,
                entity_type="pipeline_deal",
                entity_id=str(deal.id),
                action=AuditAction.CREATE.value,
                new_value={"title": title, "stage": stage, "manager_id": manager},
            )
            await session.refresh(deal)
            return DealPipelineEngineV2._deal_snapshot(deal)

    @staticmethod
    async def assign_manager(
        actor_id: int,
        tenant_id: uuid.UUID,
        deal_id: uuid.UUID,
        manager_id: int,
    ) -> dict[str, Any]:
        ctx = await DealPipelineEngineV2._require_access(actor_id, tenant_id)
        async with get_session() as session:
            deal = await DealPipelineEngineV2._get_deal_or_raise(session, deal_id, tenant_id)
            updated = await PipelineDealRepository(session).update_fields(
                deal_id, assigned_manager_id=manager_id
            )
            await NotificationRepository(session).create(
                user_id=manager_id,
                notification_type=NotificationType.DEAL_ASSIGNED.value,
                channel=NotificationChannel.INTERNAL.value,
                title=f"Deal assigned: {deal.title}",
                message=f"You have been assigned deal {deal_id} at stage {deal.current_stage}.",
            )
            await AuditRepository(session).create_log(
                user_id=actor_id,
                company_id=ctx.company_id,
                tenant_id=tenant_id,
                entity_type="pipeline_deal",
                entity_id=str(deal_id),
                action=AuditAction.UPDATE.value,
                new_value={"assigned_manager_id": manager_id},
            )
            await session.refresh(updated)
            return DealPipelineEngineV2._deal_snapshot(updated)

    @staticmethod
    async def transition_stage(
        actor_id: int,
        tenant_id: uuid.UUID,
        deal_id: uuid.UUID,
        to_stage: str,
        *,
        notes: str | None = None,
    ) -> dict[str, Any]:
        ctx = await DealPipelineEngineV2._require_access(actor_id, tenant_id)
        now = datetime.now(timezone.utc)

        async with get_session() as session:
            deal = await DealPipelineEngineV2._get_deal_or_raise(session, deal_id, tenant_id)
            from_stage = deal.current_stage
            stage_row = await DealStageRepository(session).get_by_code(tenant_id, from_stage)
            allowed = (
                stage_row.allowed_next_stages
                if stage_row
                else DEFAULT_ALLOWED_TRANSITIONS.get(from_stage, [])
            )
            validation = {
                "from_stage": from_stage,
                "to_stage": to_stage,
                "valid": to_stage in allowed,
                "allowed_next_stages": allowed,
            }
            if not validation["valid"]:
                await DealStageHistoryRepository(session).create(
                    deal_id=deal_id,
                    tenant_id=tenant_id,
                    from_stage=from_stage,
                    to_stage=to_stage,
                    changed_by=actor_id,
                    validation_passed=False,
                    notes=notes or "Transition rejected",
                )
                raise DealPipelineEngineError(
                    f"Invalid transition {from_stage} -> {to_stage}. "
                    f"Allowed: {validation['allowed_next_stages']}"
                )

            to_stage_row = await DealStageRepository(session).get_by_code(tenant_id, to_stage)
            sla_hours = (
                to_stage_row.sla_hours
                if to_stage_row
                else DEFAULT_STAGE_SLA_HOURS.get(to_stage, 48)
            )
            sla_due = now + timedelta(hours=sla_hours) if sla_hours else None

            new_status = DealStatus.ACTIVE.value
            if to_stage == DealPipelineStageCode.DELIVERED.value:
                new_status = DealStatus.WON.value
            elif to_stage == DealPipelineStageCode.LOST.value:
                new_status = DealStatus.LOST.value

            updated = await PipelineDealRepository(session).update_fields(
                deal_id,
                current_stage=to_stage,
                status=new_status,
                sla_due_at=sla_due,
                last_activity_at=now,
            )
            await DealStageHistoryRepository(session).create(
                deal_id=deal_id,
                tenant_id=tenant_id,
                from_stage=from_stage,
                to_stage=to_stage,
                changed_by=actor_id,
                notes=notes,
            )

            task_title = AUTO_TASKS_BY_STAGE.get(to_stage)
            created_task = None
            if task_title:
                created_task = await DealTaskRepository(session).create(
                    deal_id=deal_id,
                    tenant_id=tenant_id,
                    title=task_title,
                    task_type=f"stage_{to_stage}",
                    description=notes,
                    assigned_to=deal.assigned_manager_id or MANAGER_ID,
                    due_at=sla_due,
                    auto_created=True,
                    created_by=actor_id,
                )

            if deal.sales_lead_id and to_stage in SALES_AGENT_STAGE_MAP:
                try:
                    await AiSalesAgentV1.update_lead_status(
                        actor_id,
                        tenant_id,
                        deal.sales_lead_id,
                        SALES_AGENT_STAGE_MAP[to_stage],
                    )
                except Exception:
                    pass

            await AuditRepository(session).create_log(
                user_id=actor_id,
                company_id=ctx.company_id,
                tenant_id=tenant_id,
                entity_type="pipeline_deal",
                entity_id=str(deal_id),
                action=AuditAction.STATUS_CHANGE.value,
                old_value={"stage": from_stage},
                new_value={"stage": to_stage, "status": new_status},
            )
            await session.refresh(updated)
            return {
                "deal": DealPipelineEngineV2._deal_snapshot(updated),
                "transition": validation,
                "auto_task_id": str(created_task.id) if created_task else None,
            }

    @staticmethod
    async def add_comment(
        actor_id: int,
        tenant_id: uuid.UUID,
        deal_id: uuid.UUID,
        body: str,
        *,
        is_internal: bool = True,
    ) -> dict[str, Any]:
        await DealPipelineEngineV2._require_access(actor_id, tenant_id)
        async with get_session() as session:
            await DealPipelineEngineV2._get_deal_or_raise(session, deal_id, tenant_id)
            row = await DealCommentRepository(session).create(
                deal_id=deal_id,
                tenant_id=tenant_id,
                body=body,
                author_id=actor_id,
                is_internal=is_internal,
            )
            await PipelineDealRepository(session).update_fields(
                deal_id, last_activity_at=datetime.now(timezone.utc)
            )
            await session.refresh(row)
            return {
                "id": str(row.id),
                "deal_id": str(deal_id),
                "body": row.body,
                "author_id": row.author_id,
                "created_at": row.created_at.isoformat(),
            }

    @staticmethod
    async def detect_overdue(
        actor_id: int,
        tenant_id: uuid.UUID,
    ) -> dict[str, Any]:
        ctx = await DealPipelineEngineV2._require_access(actor_id, tenant_id)
        now = datetime.now(timezone.utc)
        overdue_deals: list[dict[str, Any]] = []
        overdue_tasks: list[dict[str, Any]] = []

        async with get_session() as session:
            deals = await PipelineDealRepository(session).list_overdue_sla(tenant_id, before=now)
            tasks = await DealTaskRepository(session).list_overdue(tenant_id, before=now)

            for deal in deals:
                overdue_deals.append(DealPipelineEngineV2._deal_snapshot(deal))
                manager = deal.assigned_manager_id or MANAGER_ID
                await NotificationRepository(session).create(
                    user_id=manager,
                    notification_type=NotificationType.SYSTEM_ALERT.value,
                    channel=NotificationChannel.INTERNAL.value,
                    title=f"SLA overdue: {deal.title}",
                    message=f"Deal {deal.id} in stage {deal.current_stage} exceeded SLA.",
                )

            for task in tasks:
                await DealTaskRepository(session).update_fields(
                    task.id, status=DealTaskStatus.OVERDUE.value
                )
                overdue_tasks.append({
                    "id": str(task.id),
                    "deal_id": str(task.deal_id),
                    "title": task.title,
                    "due_at": task.due_at.isoformat() if task.due_at else None,
                })

            if overdue_deals or overdue_tasks:
                await AuditRepository(session).create_log(
                    user_id=actor_id,
                    company_id=ctx.company_id,
                    tenant_id=tenant_id,
                    entity_type="deal_pipeline",
                    entity_id=str(tenant_id),
                    action=AuditAction.STATUS_CHANGE.value,
                    new_value={
                        "overdue_deals": len(overdue_deals),
                        "overdue_tasks": len(overdue_tasks),
                    },
                )

        return {
            "overdue_deals": overdue_deals,
            "overdue_tasks": overdue_tasks,
            "deal_count": len(overdue_deals),
            "task_count": len(overdue_tasks),
        }

    @staticmethod
    async def get_deal(
        actor_id: int,
        tenant_id: uuid.UUID,
        deal_id: uuid.UUID,
    ) -> dict[str, Any]:
        await DealPipelineEngineV2._require_access(actor_id, tenant_id)
        async with get_session() as session:
            deal = await DealPipelineEngineV2._get_deal_or_raise(session, deal_id, tenant_id)
            history = await DealStageHistoryRepository(session).list_by_deal(deal_id)
            tasks = await DealTaskRepository(session).list_by_deal(deal_id)
            comments = await DealCommentRepository(session).list_by_deal(deal_id)
            return {
                "deal": DealPipelineEngineV2._deal_snapshot(deal),
                "history": [
                    {
                        "id": str(h.id),
                        "from_stage": h.from_stage,
                        "to_stage": h.to_stage,
                        "validation_passed": h.validation_passed,
                        "changed_by": h.changed_by,
                        "notes": h.notes,
                        "created_at": h.created_at.isoformat(),
                    }
                    for h in history
                ],
                "tasks": [
                    {
                        "id": str(t.id),
                        "title": t.title,
                        "status": t.status,
                        "due_at": t.due_at.isoformat() if t.due_at else None,
                        "auto_created": t.auto_created,
                    }
                    for t in tasks
                ],
                "comments": [
                    {
                        "id": str(c.id),
                        "body": c.body,
                        "author_id": c.author_id,
                        "created_at": c.created_at.isoformat(),
                    }
                    for c in comments
                ],
            }

    @staticmethod
    async def list_deals(
        actor_id: int,
        tenant_id: uuid.UUID,
        *,
        stage: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        await DealPipelineEngineV2._require_access(actor_id, tenant_id)
        async with get_session() as session:
            rows = await PipelineDealRepository(session).list_by_tenant(
                tenant_id, stage=stage, limit=limit
            )
            return [DealPipelineEngineV2._deal_snapshot(r) for r in rows]

    @staticmethod
    async def get_pipeline_dashboard(
        actor_id: int,
        tenant_id: uuid.UUID,
    ) -> dict[str, Any]:
        await DealPipelineEngineV2._require_access(actor_id, tenant_id)
        stages = await DealPipelineEngineV2.bootstrap_stages(actor_id, tenant_id)
        deals = await DealPipelineEngineV2.list_deals(actor_id, tenant_id, limit=200)
        by_stage: dict[str, int] = {}
        for deal in deals:
            by_stage[deal["current_stage"]] = by_stage.get(deal["current_stage"], 0) + 1

        return {
            "tenant_id": str(tenant_id),
            "stages": stages,
            "default_stages": [s.value for s in DealPipelineStageCode],
            "deal_count": len(deals),
            "deals_by_stage": by_stage,
            "capabilities": [
                "stage_transition_validation",
                "automatic_task_creation",
                "manager_assignment",
                "sla_timers",
                "overdue_detection",
            ],
            "integrations": ["notification_engine", "audit_log_engine", "ai_sales_agent"],
        }
