# AI Workflow event bus integration.

from __future__ import annotations

from dataclasses import dataclass

from events.base_event import BaseEvent


@dataclass(kw_only=True)
class AIWorkflowStartedEvent(BaseEvent):
    workflow_id: str = ""
    execution_id: str = ""
    plugin_id: str = ""


@dataclass(kw_only=True)
class AIWorkflowCompletedEvent(BaseEvent):
    workflow_id: str = ""
    execution_id: str = ""
    plugin_id: str = ""
    latency_ms: float = 0.0
    cost_usd: float = 0.0


@dataclass(kw_only=True)
class AIWorkflowFailedEvent(BaseEvent):
    workflow_id: str = ""
    execution_id: str = ""
    plugin_id: str = ""
    error: str = ""


@dataclass(kw_only=True)
class AIWorkflowCancelledEvent(BaseEvent):
    workflow_id: str = ""
    execution_id: str = ""
    plugin_id: str = ""


@dataclass(kw_only=True)
class StepStartedEvent(BaseEvent):
    workflow_id: str = ""
    execution_id: str = ""
    step_id: str = ""


@dataclass(kw_only=True)
class StepCompletedEvent(BaseEvent):
    workflow_id: str = ""
    execution_id: str = ""
    step_id: str = ""
    latency_ms: float = 0.0


@dataclass(kw_only=True)
class StepFailedEvent(BaseEvent):
    workflow_id: str = ""
    execution_id: str = ""
    step_id: str = ""
    error: str = ""


async def publish_workflow_event(event: BaseEvent) -> None:
    from events.publisher import publish_workflow

    await publish_workflow(event, wait=True)
