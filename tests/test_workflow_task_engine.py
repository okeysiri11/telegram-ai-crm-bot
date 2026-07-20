"""Tests — Platform Workflow & Task Engine (Sprint 3.2)."""

from __future__ import annotations

import asyncio
import time

import pytest

from events.event_bus import reset_subscribers, subscribe
from platform_workflow.agent_assignment import AgentAssignmentService
from platform_workflow.human_assignment import HumanAssignmentService
from platform_workflow.metrics import WorkflowMetrics
from platform_workflow.models import (
    ExecutionContext,
    HumanRole,
    Task,
    TaskPriority,
    TaskStatus,
    TaskType,
    WorkflowStatus,
    WorkflowStep,
)
from platform_workflow.persistence.in_memory import (
    InMemoryExecutionHistoryRepository,
    InMemoryTaskRepository,
    InMemoryWorkflowRepository,
)
from platform_workflow.task_queue import TaskQueue
from platform_workflow.telegram_interface import NullTelegramTaskInterface
from platform_workflow.workflow_engine import WorkflowEngine
from platform_workflow.workflow_events import (
    TaskAssignedEvent,
    TaskCompletedEvent,
    TaskCreatedEvent,
    WorkflowCompletedEvent,
)


@pytest.fixture
def engine() -> WorkflowEngine:
    from platform_agents.registry import AgentRegistry

    registry = AgentRegistry()
    eng = WorkflowEngine(
        workflow_repo=InMemoryWorkflowRepository(),
        task_repo=InMemoryTaskRepository(),
        history_repo=InMemoryExecutionHistoryRepository(),
        queue=TaskQueue(),
        agent_assignment=AgentAssignmentService(registry),
        human_assignment=HumanAssignmentService(),
        metrics=WorkflowMetrics(),
        agent_registry_instance=registry,
        telegram=NullTelegramTaskInterface(),
    )
    yield eng
    eng.reset()


@pytest.fixture(autouse=True)
def _reset_events():
    reset_subscribers()
    yield
    reset_subscribers()


@pytest.mark.asyncio
async def test_create_workflow(engine: WorkflowEngine):
    wf = await engine.create_workflow(
        "Auto Purchase",
        [
            WorkflowStep(step_id="s1", name="Find car", capability="buy_car", task_type=TaskType.AGENT),
        ],
    )
    assert wf.workflow_id
    assert wf.status == WorkflowStatus.DRAFT


@pytest.mark.asyncio
async def test_execute_agent_workflow(engine: WorkflowEngine):
    wf = await engine.create_workflow(
        "Legal Review",
        [
            WorkflowStep(step_id="s1", name="Contract", capability="legal_contract", task_type=TaskType.AGENT),
        ],
    )
    result = await engine.execute_workflow(wf.workflow_id)
    assert result.status == WorkflowStatus.COMPLETED
    status = await engine.get_workflow_status(wf.workflow_id)
    assert status["tasks"][0]["status"] == "completed"
    assert status["tasks"][0]["assignee_id"] == "legal_agent"


@pytest.mark.asyncio
async def test_execute_multi_step_workflow(engine: WorkflowEngine):
    wf = await engine.create_workflow(
        "Auto + Legal",
        [
            WorkflowStep(step_id="s1", name="Buy", capability="buy_car", task_type=TaskType.AGENT),
            WorkflowStep(step_id="s2", name="Contract", capability="legal_contract", task_type=TaskType.AGENT, depends_on=["s1"]),
        ],
    )
    result = await engine.execute_workflow(wf.workflow_id)
    assert result.status == WorkflowStatus.COMPLETED
    status = await engine.get_workflow_status(wf.workflow_id)
    assert len(status["tasks"]) == 2


@pytest.mark.asyncio
async def test_pause_and_resume_workflow(engine: WorkflowEngine):
    wf = await engine.create_workflow("Pause test", [WorkflowStep(step_id="s1", name="Step", capability="buy_car")])
    paused = await engine.pause_workflow(wf.workflow_id)
    assert paused.status == WorkflowStatus.PAUSED
    resumed = await engine.resume_workflow(wf.workflow_id)
    assert resumed.status != WorkflowStatus.PAUSED


@pytest.mark.asyncio
async def test_cancel_workflow(engine: WorkflowEngine):
    wf = await engine.create_workflow("Cancel test", [WorkflowStep(step_id="s1", name="Step", capability="buy_car")])
    await engine.cancel_workflow(wf.workflow_id)
    status = await engine.get_workflow_status(wf.workflow_id)
    assert status["status"] == "cancelled"


@pytest.mark.asyncio
async def test_task_queue_priority_fifo(engine: WorkflowEngine):
    queue = engine._queue
    t1 = Task(task_id="t1", workflow_id="w1", step_id="s1", task_type=TaskType.AGENT, priority=TaskPriority.HIGH)
    t2 = Task(task_id="t2", workflow_id="w1", step_id="s2", task_type=TaskType.AGENT, priority=TaskPriority.LOW)
    t3 = Task(task_id="t3", workflow_id="w1", step_id="s3", task_type=TaskType.AGENT, priority=TaskPriority.HIGH)
    await queue.enqueue(t2)
    await queue.enqueue(t1)
    await queue.enqueue(t3)
    first = await queue.dequeue_ready()
    assert first.task_id == "t1"
    second = await queue.dequeue_ready()
    assert second.task_id == "t3"


@pytest.mark.asyncio
async def test_task_queue_delayed(engine: WorkflowEngine):
    queue = engine._queue
    task = Task(task_id="delayed", workflow_id="w1", step_id="s1", task_type=TaskType.AGENT)
    await queue.enqueue_delayed(task, delay_seconds=0.1)
    assert await queue.dequeue_ready() is None
    await asyncio.sleep(0.15)
    ready = await queue.dequeue_ready()
    assert ready is not None
    assert ready.task_id == "delayed"


@pytest.mark.asyncio
async def test_task_queue_scheduled(engine: WorkflowEngine):
    queue = engine._queue
    task = Task(task_id="scheduled", workflow_id="w1", step_id="s1", task_type=TaskType.AGENT)
    run_at = time.monotonic() + 0.1
    await queue.enqueue_scheduled(task, scheduled_at=run_at)
    assert await queue.dequeue_ready() is None
    await asyncio.sleep(0.15)
    ready = await queue.dequeue_ready()
    assert ready.task_id == "scheduled"


@pytest.mark.asyncio
async def test_agent_assignment_by_capability(engine: WorkflowEngine):
    engine._ensure_agents()
    agent_id = engine._agent_assignment.assign("buy_car")
    assert agent_id == "auto_agent"


@pytest.mark.asyncio
async def test_agent_assignment_fallback(engine: WorkflowEngine):
    engine._ensure_agents()
    agent_id, cap = engine._agent_assignment.assign_with_fallback(
        "unknown_cap", fallback_capabilities=["buy_car"]
    )
    assert cap == "buy_car"
    assert agent_id == "auto_agent"


@pytest.mark.asyncio
async def test_human_assignment(engine: WorkflowEngine):
    assignee = engine._human_assignment.assign(HumanRole.MANAGER)
    assert assignee == "manager_default"
    await engine._human_assignment.notify(assignee, "task-1", "Please review")
    assert len(engine._human_assignment.notifications()) == 1


@pytest.mark.asyncio
async def test_human_task_workflow(engine: WorkflowEngine):
    wf = await engine.create_workflow(
        "Human approval",
        [
            WorkflowStep(
                step_id="s1",
                name="Manager approval",
                task_type=TaskType.HUMAN,
                human_role=HumanRole.MANAGER,
            ),
        ],
        context=ExecutionContext(telegram_user_id="12345"),
    )
    partial = await engine.execute_workflow(wf.workflow_id)
    assert partial.status == WorkflowStatus.RUNNING
    status = await engine.get_workflow_status(wf.workflow_id)
    task_id = status["tasks"][0]["task_id"]
    assert status["tasks"][0]["status"] == "waiting"

    await engine.complete_human_task(task_id, {"approved": True})
    completed = await engine.continue_workflow(wf.workflow_id)
    assert completed.status == WorkflowStatus.COMPLETED


@pytest.mark.asyncio
async def test_workflow_events(engine: WorkflowEngine):
    events: list[str] = []

    async def _capture(event):
        events.append(type(event).__name__)

    subscribe(TaskCreatedEvent, _capture)
    subscribe(TaskAssignedEvent, _capture)
    subscribe(TaskCompletedEvent, _capture)
    subscribe(WorkflowCompletedEvent, _capture)

    wf = await engine.create_workflow(
        "Events test",
        [WorkflowStep(step_id="s1", name="Step", capability="buy_car", task_type=TaskType.AGENT)],
    )
    await engine.execute_workflow(wf.workflow_id)
    await asyncio.sleep(0.05)
    assert "TaskCreatedEvent" in events
    assert "TaskAssignedEvent" in events
    assert "TaskCompletedEvent" in events
    assert "WorkflowCompletedEvent" in events


@pytest.mark.asyncio
async def test_persistence(engine: WorkflowEngine):
    wf = await engine.create_workflow(
        "Persist",
        [WorkflowStep(step_id="s1", name="Step", capability="buy_car")],
    )
    await engine.execute_workflow(wf.workflow_id)
    loaded = await engine._workflows.get_workflow(wf.workflow_id)
    assert loaded is not None
    tasks = await engine._tasks.list_tasks_for_workflow(wf.workflow_id)
    assert len(tasks) == 1
    history = await engine._history.history_for_workflow(wf.workflow_id)
    assert len(history) >= 1


@pytest.mark.asyncio
async def test_metrics(engine: WorkflowEngine):
    wf = await engine.create_workflow(
        "Metrics",
        [WorkflowStep(step_id="s1", name="Step", capability="buy_car")],
    )
    await engine.execute_workflow(wf.workflow_id)
    summary = engine._metrics.summary()
    assert summary["executions"] >= 1
    assert summary["success_rate"] == 1.0


@pytest.mark.asyncio
async def test_retry_workflow(engine: WorkflowEngine):
    wf = await engine.create_workflow(
        "Retry",
        [WorkflowStep(step_id="s1", name="Bad", capability="nonexistent_capability", task_type=TaskType.AGENT, max_retries=0)],
    )
    result = await engine.execute_workflow(wf.workflow_id)
    assert result.status == WorkflowStatus.FAILED


@pytest.mark.asyncio
async def test_get_workflow_status(engine: WorkflowEngine):
    wf = await engine.create_workflow("Status", [WorkflowStep(step_id="s1", name="Step", capability="buy_car")])
    await engine.execute_workflow(wf.workflow_id)
    status = await engine.get_workflow_status(wf.workflow_id)
    assert status["workflow_id"] == wf.workflow_id
    assert status["status"] == "completed"
    assert "metrics" in status


@pytest.mark.asyncio
async def test_telegram_interface(engine: WorkflowEngine):
    tg = engine._telegram
    assert await tg.send_task_notification("123", "t1", "Hello")
    assert (await tg.approve_task("123", "t1"))["approved"] is True
    assert (await tg.reject_task("123", "t1"))["rejected"] is True
    assert (await tg.complete_task("123", "t1"))["completed"] is True
    assert (await tg.request_clarification("123", "t1", "Why?"))["clarification_requested"] is True
