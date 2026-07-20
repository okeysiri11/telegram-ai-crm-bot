# TaskService — CRM task management.

from __future__ import annotations

from events.publisher import publish
from applications.auto_marketplace.crm.events import TaskCreatedEvent
from applications.auto_marketplace.crm.models import CRMTask, TaskStatus
from applications.auto_marketplace.shared.exceptions import NotFoundError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class TaskService:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    async def create(self, task: CRMTask) -> CRMTask:
        saved = self._store.crm_tasks.save(task.task_id, task)
        await publish(
            TaskCreatedEvent(
                task_id=saved.task_id,
                assigned_agent_id=saved.assigned_agent_id,
                customer_id=saved.customer_id,
            )
        )
        return saved

    def get(self, task_id: str) -> CRMTask:
        task = self._store.crm_tasks.get(task_id)
        if task is None:
            raise NotFoundError("CRMTask", task_id)
        return task

    def list_tasks(
        self,
        *,
        agent_id: str | None = None,
        customer_id: str | None = None,
        status: TaskStatus | None = None,
    ) -> list[CRMTask]:
        items = self._store.crm_tasks.list_all()
        if agent_id:
            items = [t for t in items if t.assigned_agent_id == agent_id]
        if customer_id:
            items = [t for t in items if t.customer_id == customer_id]
        if status:
            items = [t for t in items if t.status == status]
        return items

    def complete(self, task_id: str) -> CRMTask:
        task = self.get(task_id)
        task.status = TaskStatus.COMPLETED
        return self._store.crm_tasks.save(task_id, task)


task_service = TaskService()
