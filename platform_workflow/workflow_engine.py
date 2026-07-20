# Workflow Engine — universal workflow and task execution.

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from events.publisher import publish
from platform_agents.registry import AgentRegistry, agent_registry
from platform_agents.agents.builtin import register_builtin_agents
from platform_workflow.agent_assignment import AgentAssignmentService, agent_assignment_service
from platform_workflow.config import DEFAULT_WORKFLOW_CONFIG, WorkflowEngineConfig
from platform_workflow.exceptions import (
    AgentAssignmentError,
    InvalidWorkflowStateError,
    TaskNotFoundError,
    WorkflowNotFoundError,
)
from platform_workflow.human_assignment import HumanAssignmentService, human_assignment_service
from platform_workflow.metrics import WorkflowMetrics, workflow_metrics
from platform_workflow.models import (
    ExecutionContext,
    HumanRole,
    Task,
    TaskPriority,
    TaskResult,
    TaskStatus,
    TaskType,
    Workflow,
    WorkflowStatus,
    WorkflowStep,
)
from platform_workflow.persistence.in_memory import (
    InMemoryExecutionHistoryRepository,
    InMemoryTaskRepository,
    InMemoryWorkflowRepository,
)
from platform_workflow.task_queue import TaskQueue, task_queue
from platform_workflow.telegram_interface import NullTelegramTaskInterface, TelegramTaskInterface
from platform_workflow.workflow_events import (
    TaskAssignedEvent,
    TaskCompletedEvent,
    TaskCreatedEvent,
    TaskFailedEvent,
    TaskStartedEvent,
    WorkflowCompletedEvent,
    WorkflowFailedEvent,
)

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """Enterprise workflow & task engine — agents and humans collaborate in one workflow."""

    def __init__(
        self,
        *,
        workflow_repo: InMemoryWorkflowRepository | None = None,
        task_repo: InMemoryTaskRepository | None = None,
        history_repo: InMemoryExecutionHistoryRepository | None = None,
        queue: TaskQueue | None = None,
        agent_assignment: AgentAssignmentService | None = None,
        human_assignment: HumanAssignmentService | None = None,
        metrics: WorkflowMetrics | None = None,
        agent_registry_instance: AgentRegistry | None = None,
        telegram: TelegramTaskInterface | None = None,
        config: WorkflowEngineConfig | None = None,
    ) -> None:
        self._workflows = workflow_repo or InMemoryWorkflowRepository()
        self._tasks = task_repo or InMemoryTaskRepository()
        self._history = history_repo or InMemoryExecutionHistoryRepository()
        self._queue = queue or task_queue
        self._agent_registry = agent_registry_instance or agent_registry
        self._agent_assignment = agent_assignment or AgentAssignmentService(self._agent_registry)
        self._human_assignment = human_assignment or human_assignment_service
        self._metrics = metrics or workflow_metrics
        self._telegram = telegram or NullTelegramTaskInterface()
        self._config = config or DEFAULT_WORKFLOW_CONFIG
        self._paused: set[str] = set()
        self._cancelled: set[str] = set()
        self._agents_initialized = False

    def reset(self) -> None:
        self._workflows.reset()
        self._tasks.reset()
        self._history.reset()
        self._queue.reset()
        self._human_assignment.reset()
        self._metrics.reset()
        self._paused.clear()
        self._cancelled.clear()
        self._agents_initialized = False
        self._agent_registry.reset()

    def _ensure_agents(self) -> None:
        if not self._agents_initialized:
            register_builtin_agents(self._agent_registry)
            self._agents_initialized = True

    async def create_workflow(
        self,
        name: str,
        steps: list[WorkflowStep],
        *,
        description: str = "",
        context: ExecutionContext | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Workflow:
        workflow = Workflow.create(name, steps, description=description, context=context, metadata=metadata)
        await self._workflows.save_workflow(workflow)
        logger.info("workflow_created id=%s name=%s steps=%d", workflow.workflow_id, name, len(steps))
        return workflow

    CreateWorkflow = create_workflow

    async def execute_workflow(
        self,
        workflow_id: str,
        *,
        input_payload: dict[str, Any] | None = None,
    ) -> Workflow:
        self._ensure_agents()
        workflow = await self._get_workflow(workflow_id)
        if workflow.status in (WorkflowStatus.COMPLETED, WorkflowStatus.CANCELLED):
            raise InvalidWorkflowStateError(workflow_id, workflow.status.value)

        workflow.status = WorkflowStatus.RUNNING
        workflow.updated_at = time.time()
        await self._workflows.update_workflow(workflow)
        self._cancelled.discard(workflow_id)
        self._paused.discard(workflow_id)

        ordered_steps = self._order_steps(workflow.steps)
        payload = input_payload or {}

        for step in ordered_steps:
            if workflow_id in self._cancelled:
                workflow.status = WorkflowStatus.CANCELLED
                await self._workflows.update_workflow(workflow)
                return workflow

            while workflow_id in self._paused:
                await asyncio.sleep(0.01)

            task = Task.from_step(workflow, step)
            task.payload.update(payload)
            await self._tasks.save_task(task)
            await publish(
                TaskCreatedEvent(
                    task_id=task.task_id,
                    workflow_id=workflow_id,
                    task_type=task.task_type.value,
                    capability=task.capability,
                )
            )

            await self._assign_task(task, workflow)
            if task.status == TaskStatus.FAILED:
                workflow.status = WorkflowStatus.FAILED
                workflow.updated_at = time.time()
                await self._workflows.update_workflow(workflow)
                await publish(
                    WorkflowFailedEvent(
                        workflow_id=workflow_id,
                        name=workflow.name,
                        error=task.error or "assignment failed",
                        failed_task_id=task.task_id,
                    )
                )
                return workflow

            await self._queue.enqueue(task)
            self._metrics.set_queue_length(self._queue.length())

            result = await self._execute_task(task, workflow)
            await self._history.record(result)
            self._metrics.record(result)

            if result.status == TaskStatus.WAITING:
                workflow.status = WorkflowStatus.RUNNING
                workflow.updated_at = time.time()
                await self._workflows.update_workflow(workflow)
                return workflow

            if not result.success:
                workflow.status = WorkflowStatus.FAILED
                workflow.updated_at = time.time()
                await self._workflows.update_workflow(workflow)
                await publish(
                    WorkflowFailedEvent(
                        workflow_id=workflow_id,
                        name=workflow.name,
                        error=result.error or "task failed",
                        failed_task_id=task.task_id,
                    )
                )
                return workflow

            payload.update(result.output)

        workflow.status = WorkflowStatus.COMPLETED
        workflow.updated_at = time.time()
        await self._workflows.update_workflow(workflow)
        tasks = await self._tasks.list_tasks_for_workflow(workflow_id)
        await publish(
            WorkflowCompletedEvent(
                workflow_id=workflow_id,
                name=workflow.name,
                task_count=len(tasks),
            )
        )
        return workflow

    ExecuteWorkflow = execute_workflow

    async def pause_workflow(self, workflow_id: str) -> Workflow:
        workflow = await self._get_workflow(workflow_id)
        self._paused.add(workflow_id)
        workflow.status = WorkflowStatus.PAUSED
        workflow.updated_at = time.time()
        await self._workflows.update_workflow(workflow)
        return workflow

    PauseWorkflow = pause_workflow

    async def resume_workflow(self, workflow_id: str) -> Workflow:
        workflow = await self._get_workflow(workflow_id)
        self._paused.discard(workflow_id)
        if workflow.status == WorkflowStatus.PAUSED:
            workflow.status = WorkflowStatus.RUNNING
            workflow.updated_at = time.time()
            await self._workflows.update_workflow(workflow)
        return workflow

    ResumeWorkflow = resume_workflow

    async def cancel_workflow(self, workflow_id: str) -> Workflow:
        workflow = await self._get_workflow(workflow_id)
        self._cancelled.add(workflow_id)
        self._paused.discard(workflow_id)
        workflow.status = WorkflowStatus.CANCELLED
        workflow.updated_at = time.time()
        await self._workflows.update_workflow(workflow)

        tasks = await self._tasks.list_tasks_for_workflow(workflow_id)
        for task in tasks:
            if task.status not in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
                task.status = TaskStatus.CANCELLED
                task.updated_at = time.time()
                await self._tasks.update_task(task)
        return workflow

    CancelWorkflow = cancel_workflow

    async def retry_workflow(self, workflow_id: str) -> Workflow:
        workflow = await self._get_workflow(workflow_id)
        if workflow.status not in (WorkflowStatus.FAILED, WorkflowStatus.CANCELLED):
            raise InvalidWorkflowStateError(workflow_id, workflow.status.value)

        failed_tasks = [
            t
            for t in await self._tasks.list_tasks_for_workflow(workflow_id)
            if t.status == TaskStatus.FAILED
        ]
        for task in failed_tasks:
            task.status = TaskStatus.QUEUED
            task.retry_count = 0
            task.error = None
            task.updated_at = time.time()
            await self._tasks.update_task(task)
            await self._queue.enqueue(task)

        workflow.status = WorkflowStatus.RUNNING
        workflow.updated_at = time.time()
        await self._workflows.update_workflow(workflow)
        self._cancelled.discard(workflow_id)

        for task in failed_tasks:
            result = await self._execute_task(task, workflow)
            await self._history.record(result)
            self._metrics.record(result)
            if not result.success:
                workflow.status = WorkflowStatus.FAILED
                await self._workflows.update_workflow(workflow)
                return workflow

        workflow.status = WorkflowStatus.COMPLETED
        await self._workflows.update_workflow(workflow)
        await publish(
            WorkflowCompletedEvent(workflow_id=workflow_id, name=workflow.name, task_count=len(failed_tasks))
        )
        return workflow

    RetryWorkflow = retry_workflow

    async def get_workflow_status(self, workflow_id: str) -> dict[str, Any]:
        workflow = await self._get_workflow(workflow_id)
        tasks = await self._tasks.list_tasks_for_workflow(workflow_id)
        history = await self._history.history_for_workflow(workflow_id)
        return {
            "workflow_id": workflow_id,
            "name": workflow.name,
            "status": workflow.status.value,
            "tasks": [
                {
                    "task_id": t.task_id,
                    "step_id": t.step_id,
                    "status": t.status.value,
                    "assignee_id": t.assignee_id,
                    "assignee_type": t.assignee_type,
                }
                for t in tasks
            ],
            "history_count": len(history),
            "metrics": self._metrics.summary(),
        }

    GetWorkflowStatus = get_workflow_status

    async def continue_workflow(self, workflow_id: str) -> Workflow:
        """Resume workflow after human task completion."""
        workflow = await self._get_workflow(workflow_id)
        tasks = await self._tasks.list_tasks_for_workflow(workflow_id)
        completed_step_ids = {t.step_id for t in tasks if t.status == TaskStatus.COMPLETED}
        ordered_steps = self._order_steps(workflow.steps)
        payload: dict[str, Any] = {}
        for t in tasks:
            if t.status == TaskStatus.COMPLETED:
                payload.update(t.result)

        for step in ordered_steps:
            if step.step_id in completed_step_ids:
                continue
            if workflow_id in self._cancelled:
                workflow.status = WorkflowStatus.CANCELLED
                await self._workflows.update_workflow(workflow)
                return workflow

            task = Task.from_step(workflow, step)
            task.payload.update(payload)
            await self._tasks.save_task(task)
            await publish(
                TaskCreatedEvent(
                    task_id=task.task_id,
                    workflow_id=workflow_id,
                    task_type=task.task_type.value,
                    capability=task.capability,
                )
            )
            await self._assign_task(task, workflow)
            result = await self._execute_task(task, workflow)
            await self._history.record(result)
            self._metrics.record(result)

            if result.status == TaskStatus.WAITING:
                workflow.status = WorkflowStatus.RUNNING
                await self._workflows.update_workflow(workflow)
                return workflow
            if not result.success:
                workflow.status = WorkflowStatus.FAILED
                await self._workflows.update_workflow(workflow)
                await publish(
                    WorkflowFailedEvent(
                        workflow_id=workflow_id,
                        name=workflow.name,
                        error=result.error or "task failed",
                        failed_task_id=task.task_id,
                    )
                )
                return workflow
            payload.update(result.output)
            completed_step_ids.add(step.step_id)

        workflow.status = WorkflowStatus.COMPLETED
        workflow.updated_at = time.time()
        await self._workflows.update_workflow(workflow)
        await publish(
            WorkflowCompletedEvent(
                workflow_id=workflow_id,
                name=workflow.name,
                task_count=len(await self._tasks.list_tasks_for_workflow(workflow_id)),
            )
        )
        return workflow

    async def complete_human_task(self, task_id: str, output: dict[str, Any] | None = None) -> TaskResult:
        task = await self._get_task(task_id)
        if task.status != TaskStatus.WAITING:
            raise InvalidWorkflowStateError(task.workflow_id, task.status.value)

        started = time.monotonic()
        task.status = TaskStatus.COMPLETED
        task.result = output or {}
        task.completed_at = time.time()
        task.updated_at = time.time()
        await self._tasks.update_task(task)

        result = TaskResult(
            task_id=task.task_id,
            workflow_id=task.workflow_id,
            success=True,
            status=TaskStatus.COMPLETED,
            output=task.result,
            execution_time_ms=round((time.monotonic() - started) * 1000, 2),
            assignee_id=task.assignee_id,
        )
        await self._history.record(result)
        self._metrics.record(result)
        await publish(TaskCompletedEvent(task_id=task.task_id, workflow_id=task.workflow_id, execution_time_ms=result.execution_time_ms))
        return result

    async def _assign_task(self, task: Task, workflow: Workflow) -> None:
        try:
            if task.task_type == TaskType.AGENT and task.capability:
                agent_id, _ = self._agent_assignment.assign_with_fallback(task.capability)
                task.assignee_id = agent_id
                task.assignee_type = "agent"
            elif task.task_type == TaskType.HUMAN and task.human_role:
                task.assignee_id = self._human_assignment.assign(task.human_role, workflow.context.as_dict())
                task.assignee_type = "human"
            elif task.assignee_id:
                task.assignee_type = task.assignee_type or "human"
            else:
                task.assignee_type = "system"
                task.assignee_id = "system"
        except AgentAssignmentError as exc:
            task.status = TaskStatus.FAILED
            task.error = str(exc)
            task.updated_at = time.time()
            await self._tasks.update_task(task)
            await publish(
                TaskFailedEvent(
                    task_id=task.task_id,
                    workflow_id=task.workflow_id,
                    error=str(exc),
                )
            )
            return

        task.status = TaskStatus.ASSIGNED
        task.updated_at = time.time()
        await self._tasks.update_task(task)
        await publish(
            TaskAssignedEvent(
                task_id=task.task_id,
                workflow_id=task.workflow_id,
                assignee_id=task.assignee_id or "",
                assignee_type=task.assignee_type or "",
            )
        )

    async def _execute_task(self, task: Task, workflow: Workflow) -> TaskResult:
        if task.workflow_id in self._cancelled:
            task.status = TaskStatus.CANCELLED
            await self._tasks.update_task(task)
            return TaskResult(
                task_id=task.task_id,
                workflow_id=task.workflow_id,
                success=False,
                status=TaskStatus.CANCELLED,
                error="workflow cancelled",
            )

        started = time.monotonic()
        task.status = TaskStatus.RUNNING
        task.updated_at = time.time()
        await self._tasks.update_task(task)
        await publish(
            TaskStartedEvent(
                task_id=task.task_id,
                workflow_id=task.workflow_id,
                assignee_id=task.assignee_id,
            )
        )

        try:
            if task.task_type == TaskType.AGENT and task.capability and task.assignee_id:
                result = await self._execute_agent_task(task)
            elif task.task_type == TaskType.HUMAN:
                result = await self._execute_human_task(task, workflow)
            else:
                result = TaskResult(
                    task_id=task.task_id,
                    workflow_id=task.workflow_id,
                    success=True,
                    status=TaskStatus.COMPLETED,
                    output={"system": True},
                    assignee_id=task.assignee_id,
                )
                task.status = TaskStatus.COMPLETED
                task.result = result.output

            result.execution_time_ms = round((time.monotonic() - started) * 1000, 2)
            result.retries = task.retry_count
            task.updated_at = time.time()
            await self._tasks.update_task(task)

            if result.success:
                await publish(
                    TaskCompletedEvent(
                        task_id=task.task_id,
                        workflow_id=task.workflow_id,
                        execution_time_ms=result.execution_time_ms,
                    )
                )
            else:
                await publish(
                    TaskFailedEvent(
                        task_id=task.task_id,
                        workflow_id=task.workflow_id,
                        error=result.error or "unknown",
                        retries=task.retry_count,
                    )
                )
            return result

        except Exception as exc:
            task.retry_count += 1
            if task.retry_count <= task.max_retries:
                delay = min(
                    self._config.retry_base_delay_seconds * (2 ** (task.retry_count - 1)),
                    self._config.retry_max_delay_seconds,
                )
                await self._queue.requeue_for_retry(task, delay)
                return await self._execute_task(task, workflow)

            task.status = TaskStatus.FAILED
            task.error = str(exc)
            task.updated_at = time.time()
            await self._tasks.update_task(task)
            result = TaskResult(
                task_id=task.task_id,
                workflow_id=task.workflow_id,
                success=False,
                status=TaskStatus.FAILED,
                error=str(exc),
                execution_time_ms=round((time.monotonic() - started) * 1000, 2),
                assignee_id=task.assignee_id,
                retries=task.retry_count,
            )
            await publish(
                TaskFailedEvent(
                    task_id=task.task_id,
                    workflow_id=task.workflow_id,
                    error=str(exc),
                    retries=task.retry_count,
                )
            )
            return result

    async def _execute_agent_task(self, task: Task) -> TaskResult:
        agent = self._agent_registry.get(task.assignee_id or "")
        exec_result = await agent.execute(task.capability or "", task.payload)
        task.status = TaskStatus.COMPLETED if exec_result.success else TaskStatus.FAILED
        task.result = exec_result.output
        task.completed_at = time.time() if exec_result.success else None
        return TaskResult(
            task_id=task.task_id,
            workflow_id=task.workflow_id,
            success=exec_result.success,
            status=task.status,
            output=exec_result.output,
            error=exec_result.error,
            assignee_id=task.assignee_id,
        )

    async def _execute_human_task(self, task: Task, workflow: Workflow) -> TaskResult:
        task.status = TaskStatus.WAITING
        await self._tasks.update_task(task)

        message = f"Human task assigned: {task.metadata.get('step_name', task.step_id)}"
        await self._human_assignment.notify(task.assignee_id or "", task.task_id, message)

        tg_user = workflow.context.telegram_user_id
        if tg_user:
            await self._telegram.send_task_notification(tg_user, task.task_id, message)

        return TaskResult(
            task_id=task.task_id,
            workflow_id=task.workflow_id,
            success=True,
            status=TaskStatus.WAITING,
            output={"waiting_for_human": True, "assignee_id": task.assignee_id},
            assignee_id=task.assignee_id,
        )

    async def _get_workflow(self, workflow_id: str) -> Workflow:
        workflow = await self._workflows.get_workflow(workflow_id)
        if workflow is None:
            raise WorkflowNotFoundError(workflow_id)
        return workflow

    async def _get_task(self, task_id: str) -> Task:
        task = await self._tasks.get_task(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)
        return task

    def _order_steps(self, steps: list[WorkflowStep]) -> list[WorkflowStep]:
        if not any(s.depends_on for s in steps):
            return list(steps)
        ordered: list[WorkflowStep] = []
        remaining = {s.step_id: s for s in steps}
        while remaining:
            progress = False
            for step_id, step in list(remaining.items()):
                if all(dep in {s.step_id for s in ordered} or dep not in remaining for dep in step.depends_on):
                    ordered.append(step)
                    del remaining[step_id]
                    progress = True
            if not progress:
                ordered.extend(remaining.values())
                break
        return ordered


workflow_engine = WorkflowEngine()
