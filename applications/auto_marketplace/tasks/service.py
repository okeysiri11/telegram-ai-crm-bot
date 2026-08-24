# TaskService — CRM task management (durable via CRM persistence).

from __future__ import annotations

import time

from events.publisher import publish
from applications.auto_marketplace.crm.events import TaskCreatedEvent
from applications.auto_marketplace.crm.models import CRMTask, TaskPriority, TaskStatus
from applications.auto_marketplace.crm.persistence import CRMPersistence, get_crm_persistence
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class TaskService:
    def __init__(
        self,
        store: MarketplaceStore | None = None,
        persistence: CRMPersistence | None = None,
    ) -> None:
        self._store = store or marketplace_store
        self._persistence = persistence

    def _records(self) -> CRMPersistence:
        return self._persistence or get_crm_persistence()

    async def _record_activity(self, task: CRMTask, activity_type: str, *, subject: str, key: str) -> None:
        from applications.auto_marketplace.activities.service import activity_service
        from applications.auto_marketplace.crm.models import Interaction, InteractionType

        try:
            itype = InteractionType(activity_type)
        except ValueError:
            itype = InteractionType.NOTE
        await activity_service.record(
            Interaction(
                customer_id=task.customer_id,
                lead_id=task.lead_id,
                deal_id=task.deal_id,
                task_id=task.task_id,
                interaction_type=itype,
                subject=subject,
                body=task.title,
                agent_id=task.assigned_agent_id or task.created_by,
                idempotency_key=key,
            )
        )

    async def _assert_relations(self, task: CRMTask) -> None:
        records = self._records()
        if task.lead_id and await records.get_lead(task.lead_id) is None:
            raise NotFoundError("CRMLead", task.lead_id)
        if task.customer_id and await records.get_customer(task.customer_id) is None:
            raise NotFoundError("CustomerProfile", task.customer_id)
        if task.deal_id and await records.get_deal(task.deal_id) is None:
            raise NotFoundError("CRMDeal", task.deal_id)

    async def create(self, task: CRMTask) -> CRMTask:
        await self._assert_relations(task)
        task.updated_at = time.time()
        saved = await self._records().save_task(task)
        await publish(
            TaskCreatedEvent(
                task_id=saved.task_id,
                assigned_agent_id=saved.assigned_agent_id,
                customer_id=saved.customer_id,
            )
        )
        await self._record_activity(
            saved,
            "task_created",
            subject="Task created",
            key=f"task_created:{saved.task_id}",
        )
        return saved

    async def get(self, task_id: str) -> CRMTask:
        task = await self._records().get_task(task_id)
        if task is None:
            raise NotFoundError("CRMTask", task_id)
        return task

    async def list_tasks(
        self,
        *,
        agent_id: str | None = None,
        assigned_to: str | None = None,
        customer_id: str | None = None,
        lead_id: str | None = None,
        deal_id: str | None = None,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        overdue: bool = False,
        due: bool = False,
        now: float | None = None,
    ) -> list[CRMTask]:
        items = await self._records().list_tasks()
        assignee = assigned_to or agent_id
        if assignee:
            items = [t for t in items if t.assigned_agent_id == assignee]
        if customer_id:
            items = [t for t in items if t.customer_id == customer_id]
        if lead_id:
            items = [t for t in items if t.lead_id == lead_id]
        if deal_id:
            items = [t for t in items if t.deal_id == deal_id]
        if status:
            items = [t for t in items if t.status == status]
        if priority:
            items = [t for t in items if t.priority == priority]
        clock = now if now is not None else time.time()
        open_statuses = {TaskStatus.PENDING, TaskStatus.IN_PROGRESS}
        if overdue:
            items = [
                t
                for t in items
                if t.due_at is not None and t.due_at < clock and t.status in open_statuses
            ]
        elif due:
            items = [
                t
                for t in items
                if t.due_at is not None and t.due_at >= clock and t.status in open_statuses
            ]
        return sorted(items, key=lambda t: (t.due_at is None, t.due_at or 0, t.created_at))

    async def update(self, task_id: str, **updates: object) -> CRMTask:
        task = await self.get(task_id)
        for key, value in updates.items():
            if key == "assigned_to":
                key = "assigned_agent_id"
            if not hasattr(task, key) or value is None:
                continue
            if key == "status":
                if not isinstance(value, TaskStatus):
                    try:
                        value = TaskStatus(str(value))
                    except ValueError as exc:
                        raise ValidationError(f"invalid task status: {value!r}") from exc
            if key == "priority":
                if not isinstance(value, TaskPriority):
                    try:
                        value = TaskPriority(str(value))
                    except ValueError as exc:
                        raise ValidationError(f"invalid task priority: {value!r}") from exc
            setattr(task, key, value)
        await self._assert_relations(task)
        task.updated_at = time.time()
        return await self._records().save_task(task)

    async def complete(self, task_id: str) -> CRMTask:
        task = await self.get(task_id)
        if task.status == TaskStatus.COMPLETED:
            return task
        task.status = TaskStatus.COMPLETED
        task.completed_at = time.time()
        task.updated_at = task.completed_at
        saved = await self._records().save_task(task)
        await self._record_activity(
            saved,
            "task_completed",
            subject="Task completed",
            key=f"task_completed:{saved.task_id}",
        )
        return saved

    async def reopen(self, task_id: str) -> CRMTask:
        task = await self.get(task_id)
        task.status = TaskStatus.PENDING
        task.completed_at = None
        task.updated_at = time.time()
        return await self._records().save_task(task)

    async def delete(self, task_id: str) -> bool:
        await self.get(task_id)
        return await self._records().delete_task(task_id)


task_service = TaskService()
