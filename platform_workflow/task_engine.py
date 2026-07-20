# Task Engine — alias facade for workflow task operations.

from __future__ import annotations

from platform_workflow.workflow_engine import WorkflowEngine, workflow_engine

TaskEngine = WorkflowEngine
task_engine = workflow_engine

__all__ = ["TaskEngine", "task_engine"]
