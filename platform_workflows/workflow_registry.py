# WorkflowRegistry — single in-memory registry for all workflow definitions.

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable

from platform_workflows.models import WorkflowDefinition
from platform_workflows.workflow_loader import WorkflowLoader
from platform_workflows.workflow_validator import WorkflowValidator

logger = logging.getLogger(__name__)


class WorkflowRegistry:
    def __init__(self) -> None:
        self._workflows: dict[str, WorkflowDefinition] = {}
        self._by_vertical: dict[str, list[str]] = {}
        self._records: dict[str, dict[str, Any]] = {}

    def register(self, definition: WorkflowDefinition, *, source: str = "manual") -> None:
        WorkflowValidator.validate_or_raise(definition)
        self._workflows[definition.id] = definition
        vertical = definition.vertical.upper()
        bucket = self._by_vertical.setdefault(vertical, [])
        if definition.id not in bucket:
            bucket.append(definition.id)
        self._records[definition.id] = {
            "definition": definition.to_dict(),
            "source": source,
            "state": "registered",
        }
        logger.info(
            "workflow_registered id=%s vertical=%s steps=%s source=%s",
            definition.id,
            vertical,
            len(definition.steps),
            source,
        )

    def register_from_callable(self, builder: Callable[[], WorkflowDefinition]) -> WorkflowDefinition:
        definition = builder()
        self.register(definition, source="python")
        return definition

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

    def list_records(self) -> list[dict[str, Any]]:
        return list(self._records.values())

    def summary(self) -> dict[str, Any]:
        return {
            "total": len(self._workflows),
            "by_vertical": {v: len(ids) for v, ids in self._by_vertical.items()},
            "workflow_ids": self.list_ids(),
        }

    def load_from_directory(self, directory: Path | None = None) -> int:
        count = 0
        for definition in WorkflowLoader.load_directory(directory):
            self.register(definition, source="yaml")
            count += 1
        return count

    def clear(self) -> None:
        self._workflows.clear()
        self._by_vertical.clear()
        self._records.clear()


workflow_registry = WorkflowRegistry()
