# SdkWorkflowLoader — load workflows by vertical workflow_name via SDK.

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from platform_sdk.exceptions import WorkflowNotFoundError
from workflow.models import WorkflowDefinition
from workflow.workflow_loader import WorkflowLoader
from workflow.workflow_registry import WorkflowRegistry, workflow_registry

logger = logging.getLogger(__name__)

DEFAULT_DEFINITIONS_DIR = Path(__file__).resolve().parents[1] / "workflow" / "definitions"


class SdkWorkflowLoader:
    """SDK workflow loader — vertical exposes workflow_name, SDK loads automatically."""

    def __init__(
        self,
        registry: WorkflowRegistry | None = None,
        definitions_dir: Path | None = None,
    ) -> None:
        self._registry = registry or workflow_registry
        self._definitions_dir = definitions_dir or DEFAULT_DEFINITIONS_DIR
        self._loaded = False

    def ensure_loaded(self) -> int:
        if self._loaded:
            return len(self._registry.list_ids())
        count = 0
        for definition in WorkflowLoader.load_directory(self._definitions_dir):
            if self._registry.get(definition.id) is None:
                self._registry.register(definition)
            count += 1
        self._loaded = True
        logger.info("sdk_workflows_loaded count=%s", count)
        return count

    def get_definition(self, workflow_name: str) -> WorkflowDefinition:
        self.ensure_loaded()
        definition = self._registry.get(workflow_name)
        if definition is None:
            raise WorkflowNotFoundError(workflow_name)
        return definition

    def get_for_vertical(self, vertical_code: str) -> WorkflowDefinition | None:
        self.ensure_loaded()
        return self._registry.get_for_vertical(vertical_code.upper())

    async def run_post_create(
        self,
        *,
        vertical_code: str,
        workflow_name: str,
        telegram_user: dict[str, Any],
        request: dict[str, Any],
        manager: dict[str, Any] | None = None,
        variables: dict[str, Any] | None = None,
    ) -> Any:
        self.ensure_loaded()
        if self._registry.get(workflow_name) is None and self._registry.get_for_vertical(vertical_code.upper()) is None:
            logger.debug("No workflow for vertical=%s name=%s", vertical_code, workflow_name)
            return None

        from workflow import workflow_engine

        return await workflow_engine.run_backend_workflow(
            vertical_code.upper(),
            telegram_user=telegram_user,
            request=request,
            manager=manager,
            variables=variables,
        )


sdk_workflow_loader = SdkWorkflowLoader()
