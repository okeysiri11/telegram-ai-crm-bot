from __future__ import annotations

from typing import Any

from platform_workflows.exceptions import WorkflowValidationError
from platform_ai.workflows.models import WorkflowDefinition


class WorkflowBuilder:
    def from_dict(self, data: dict[str, Any]) -> WorkflowDefinition:
        from typing import Any

        definition = WorkflowDefinition.from_dict(data)
        return definition

    def from_json(self, text: str) -> WorkflowDefinition:
        import json

        return self.from_dict(json.loads(text))

    def from_yaml(self, text: str) -> WorkflowDefinition:
        import yaml

        return self.from_dict(yaml.safe_load(text))

    def from_file(self, path: str) -> WorkflowDefinition:
        from pathlib import Path

        p = Path(path)
        text = p.read_text(encoding="utf-8")
        if p.suffix in (".yaml", ".yml"):
            return self.from_yaml(text)
        return self.from_json(text)

    def validate(self, definition: WorkflowDefinition) -> None:
        from platform_workflows.workflow_validator import WorkflowValidator

        WorkflowValidator.validate_or_raise(definition.to_unified())


workflow_builder = WorkflowBuilder()
