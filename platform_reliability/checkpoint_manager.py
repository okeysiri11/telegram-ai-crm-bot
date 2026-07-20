# CheckpointManager — workflow/task checkpoints and restore.

from __future__ import annotations

import logging
from typing import Any

from platform_reliability.config import DEFAULT_RELIABILITY_CONFIG, ReliabilityConfig
from platform_reliability.exceptions import CheckpointNotFoundError
from platform_reliability.models import Checkpoint, RecoveryContext

logger = logging.getLogger(__name__)


class CheckpointManager:
    def __init__(self, *, config: ReliabilityConfig | None = None) -> None:
        self._config = config or DEFAULT_RELIABILITY_CONFIG
        self._checkpoints: dict[str, Checkpoint] = {}
        self._workflow_index: dict[str, list[str]] = {}

    def reset(self) -> None:
        self._checkpoints.clear()
        self._workflow_index.clear()

    def save(
        self,
        *,
        workflow_id: str | None = None,
        task_id: str | None = None,
        agent_id: str | None = None,
        step_index: int = 0,
        snapshot: dict[str, Any] | None = None,
    ) -> Checkpoint:
        cp = Checkpoint(
            workflow_id=workflow_id,
            task_id=task_id,
            agent_id=agent_id,
            step_index=step_index,
            snapshot=dict(snapshot or {}),
        )
        self._checkpoints[cp.checkpoint_id] = cp
        if workflow_id:
            self._workflow_index.setdefault(workflow_id, []).append(cp.checkpoint_id)
        if len(self._checkpoints) > self._config.checkpoint_retention_limit:
            oldest = min(self._checkpoints, key=lambda k: self._checkpoints[k].created_at)
            del self._checkpoints[oldest]
        return cp

    def get(self, checkpoint_id: str) -> Checkpoint:
        if checkpoint_id not in self._checkpoints:
            raise CheckpointNotFoundError(checkpoint_id)
        return self._checkpoints[checkpoint_id]

    def latest_for_workflow(self, workflow_id: str) -> Checkpoint | None:
        ids = self._workflow_index.get(workflow_id, [])
        if not ids:
            return None
        cps = [self._checkpoints[i] for i in ids if i in self._checkpoints]
        return max(cps, key=lambda c: c.created_at) if cps else None

    def restore(self, checkpoint_id: str) -> dict[str, Any]:
        cp = self.get(checkpoint_id)
        return dict(cp.snapshot)

    def rollback(self, workflow_id: str) -> Checkpoint | None:
        cp = self.latest_for_workflow(workflow_id)
        if cp:
            logger.info("rollback workflow=%s checkpoint=%s", workflow_id, cp.checkpoint_id)
        return cp

    def apply_to_context(self, ctx: RecoveryContext, checkpoint_id: str) -> RecoveryContext:
        snapshot = self.restore(checkpoint_id)
        ctx.checkpoint_id = checkpoint_id
        ctx.shared_context = snapshot.get("shared_context", {})
        ctx.planning_state = snapshot.get("planning_state", {})
        ctx.decision_state = snapshot.get("decision_state", {})
        ctx.metadata["restored_from"] = checkpoint_id
        return ctx

    def list_checkpoints(self, *, workflow_id: str | None = None) -> list[Checkpoint]:
        if workflow_id:
            ids = self._workflow_index.get(workflow_id, [])
            return [self._checkpoints[i] for i in ids if i in self._checkpoints]
        return list(self._checkpoints.values())


checkpoint_manager = CheckpointManager()
