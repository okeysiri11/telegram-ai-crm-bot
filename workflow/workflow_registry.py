# WorkflowRegistry — in-memory registry of loaded workflow definitions.

from __future__ import annotations

import logging
from pathlib import Path

from workflow.models import WorkflowDefinition
from workflow.workflow_loader import WorkflowLoader
from workflow.workflow_validator import WorkflowValidator

logger = logging.getLogger(__name__)


class WorkflowRegistry:
    def __init__(self) -> None:
        self._workflows: dict[str, WorkflowDefinition] = {}
        self._by_vertical: dict[str, list[str]] = {}

    def register(self, definition: WorkflowDefinition) -> None:
        WorkflowValidator.validate_or_raise(definition)
        self._workflows[definition.id] = definition
        vertical = definition.vertical.upper()
        bucket = self._by_vertical.setdefault(vertical, [])
        if definition.id not in bucket:
            bucket.append(definition.id)
        logger.info(
            "workflow_registered id=%s vertical=%s steps=%s",
            definition.id,
            vertical,
            len(definition.steps),
        )

    def get(self, workflow_id: str) -> WorkflowDefinition | None:
        return self._workflows.get(workflow_id)

    def get_for_vertical(self, vertical: str) -> WorkflowDefinition | None:
        ids = self._by_vertical.get(vertical.upper(), [])
        if not ids:
            return None
        return self._workflows.get(ids[0])

    def list_all(self) -> list[WorkflowDefinition]:
        return list(self._workflows.values())

    def list_ids(self) -> list[str]:
        return list(self._workflows.keys())

    def load_from_directory(self, directory: Path | None = None) -> int:
        count = 0
        for definition in WorkflowLoader.load_directory(directory):
            self.register(definition)
            count += 1
        return count

    def clear(self) -> None:
        self._workflows.clear()
        self._by_vertical.clear()


workflow_registry = WorkflowRegistry()
