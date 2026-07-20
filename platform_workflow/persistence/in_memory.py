# In-memory persistence — swappable with repository adapters later.

from __future__ import annotations

from platform_workflow.models import Task, TaskResult, Workflow
from platform_workflow.persistence.base import (
    ExecutionHistoryRepository,
    TaskRepository,
    WorkflowRepository,
)


class InMemoryWorkflowRepository(WorkflowRepository):
    def __init__(self) -> None:
        self._workflows: dict[str, Workflow] = {}

    def reset(self) -> None:
        self._workflows.clear()

    async def save_workflow(self, workflow: Workflow) -> None:
        self._workflows[workflow.workflow_id] = workflow

    async def get_workflow(self, workflow_id: str) -> Workflow | None:
        return self._workflows.get(workflow_id)

    async def update_workflow(self, workflow: Workflow) -> None:
        self._workflows[workflow.workflow_id] = workflow

    async def list_workflows(self) -> list[Workflow]:
        return list(self._workflows.values())


class InMemoryTaskRepository(TaskRepository):
    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}

    def reset(self) -> None:
        self._tasks.clear()

    async def save_task(self, task: Task) -> None:
        self._tasks[task.task_id] = task

    async def get_task(self, task_id: str) -> Task | None:
        return self._tasks.get(task_id)

    async def update_task(self, task: Task) -> None:
        self._tasks[task.task_id] = task

    async def list_tasks_for_workflow(self, workflow_id: str) -> list[Task]:
        return [t for t in self._tasks.values() if t.workflow_id == workflow_id]


class InMemoryExecutionHistoryRepository(ExecutionHistoryRepository):
    def __init__(self) -> None:
        self._history: list[TaskResult] = []

    def reset(self) -> None:
        self._history.clear()

    async def record(self, result: TaskResult) -> None:
        self._history.append(result)

    async def history_for_workflow(self, workflow_id: str) -> list[TaskResult]:
        return [h for h in self._history if h.workflow_id == workflow_id]

    async def history_for_task(self, task_id: str) -> list[TaskResult]:
        return [h for h in self._history if h.task_id == task_id]
