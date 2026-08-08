"""Epic 45.3 — workflow logger."""
from __future__ import annotations
from typing import Any
from platform_workflows.ua_store import ua_store

class WorkflowLogger:
    def log(self, run_id: str, message: str) -> None:
        run = ua_store.runs.get(run_id)
        if run:
            run.logs.append(message)
            ua_store.runs[run_id] = run
    def dump(self, run_id: str) -> list[str]:
        run = ua_store.runs.get(run_id)
        return list(run.logs) if run else []

workflow_logger = WorkflowLogger()
