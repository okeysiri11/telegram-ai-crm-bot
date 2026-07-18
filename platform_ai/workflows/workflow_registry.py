# Workflow registry — dynamic registration with versioning and tags.

from __future__ import annotations

import logging
from typing import Any

from platform_ai.workflows.exceptions import WorkflowNotFoundError
from platform_ai.workflows.models import WorkflowDefinition, WorkflowRecord, WorkflowState

logger = logging.getLogger(__name__)


class WorkflowRegistry:
    def __init__(self) -> None:
        self._definitions: dict[str, WorkflowDefinition] = {}
        self._records: dict[str, WorkflowRecord] = {}
        self._versions: dict[str, list[str]] = {}

    def reset(self) -> None:
        self._definitions.clear()
        self._records.clear()
        self._versions.clear()

    def register(self, definition: WorkflowDefinition) -> WorkflowRecord:
        wf_id = definition.workflow_id
        self._definitions[wf_id] = definition
        record = WorkflowRecord(definition=definition, state=WorkflowState.REGISTERED)
        self._records[wf_id] = record
        versions = self._versions.setdefault(wf_id, [])
        if definition.version not in versions:
            versions.append(definition.version)
        logger.info("workflow_registered id=%s version=%s", wf_id, definition.version)
        return record

    def get(self, workflow_id: str) -> WorkflowDefinition:
        if workflow_id not in self._definitions:
            raise WorkflowNotFoundError(workflow_id)
        return self._definitions[workflow_id]

    def get_record(self, workflow_id: str) -> WorkflowRecord:
        if workflow_id not in self._records:
            raise WorkflowNotFoundError(workflow_id)
        return self._records[workflow_id]

    def list_records(self) -> list[WorkflowRecord]:
        return list(self._records.values())

    def list_by_tag(self, tag: str) -> list[WorkflowRecord]:
        return [r for r in self._records.values() if tag in r.definition.tags]

    def set_state(self, workflow_id: str, state: WorkflowState) -> None:
        self.get_record(workflow_id).state = state

    def summary(self) -> dict[str, Any]:
        by_category: dict[str, int] = {}
        for r in self._records.values():
            cat = r.definition.category
            by_category[cat] = by_category.get(cat, 0) + 1
        return {
            "total": len(self._records),
            "by_category": by_category,
            "workflows": [r.to_dict() for r in self._records.values()],
        }


workflow_registry = WorkflowRegistry()
