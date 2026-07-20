# Persistence interfaces — no SQL in workflow services.

from __future__ import annotations

from abc import ABC, abstractmethod

from platform_workflow.models import Task, TaskResult, Workflow


class WorkflowRepository(ABC):
    @abstractmethod
    async def save_workflow(self, workflow: Workflow) -> None: ...

    @abstractmethod
    async def get_workflow(self, workflow_id: str) -> Workflow | None: ...

    @abstractmethod
    async def update_workflow(self, workflow: Workflow) -> None: ...

    @abstractmethod
    async def list_workflows(self) -> list[Workflow]: ...


class TaskRepository(ABC):
    @abstractmethod
    async def save_task(self, task: Task) -> None: ...

    @abstractmethod
    async def get_task(self, task_id: str) -> Task | None: ...

    @abstractmethod
    async def update_task(self, task: Task) -> None: ...

    @abstractmethod
    async def list_tasks_for_workflow(self, workflow_id: str) -> list[Task]: ...


class ExecutionHistoryRepository(ABC):
    @abstractmethod
    async def record(self, result: TaskResult) -> None: ...

    @abstractmethod
    async def history_for_workflow(self, workflow_id: str) -> list[TaskResult]: ...

    @abstractmethod
    async def history_for_task(self, task_id: str) -> list[TaskResult]: ...
