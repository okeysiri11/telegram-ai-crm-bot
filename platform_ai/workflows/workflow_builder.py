# Workflow builder — construct definitions from JSON/YAML dicts.

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from platform_ai.workflows.exceptions import WorkflowValidationError
from platform_ai.workflows.models import WorkflowDefinition, WorkflowStep


class WorkflowBuilder:
    def from_dict(self, data: dict[str, Any]) -> WorkflowDefinition:
        if "steps" in data and isinstance(data["steps"], dict):
            steps = {k: WorkflowStep.from_dict({**v, "step_id": k}) for k, v in data["steps"].items()}
            return WorkflowDefinition(
                workflow_id=data["workflow_id"],
                name=data.get("name", data["workflow_id"]),
                entry_step=data["entry_step"],
                steps=steps,
                version=data.get("version", "1.0.0"),
                description=data.get("description", ""),
                tags=data.get("tags", []),
                category=data.get("category", "general"),
                enabled=data.get("enabled", True),
            )
        return WorkflowDefinition.from_dict(data)

    def from_json(self, text: str) -> WorkflowDefinition:
        return self.from_dict(json.loads(text))

    def from_yaml(self, text: str) -> WorkflowDefinition:
        try:
            import yaml
        except ImportError as exc:
            raise WorkflowValidationError("PyYAML required for YAML definitions") from exc
        return self.from_dict(yaml.safe_load(text))

    def from_file(self, path: str | Path) -> WorkflowDefinition:
        p = Path(path)
        text = p.read_text(encoding="utf-8")
        if p.suffix in (".yaml", ".yml"):
            return self.from_yaml(text)
        return self.from_json(text)

    def validate(self, definition: WorkflowDefinition) -> None:
        if definition.entry_step not in definition.steps:
            raise WorkflowValidationError(f"Entry step not found: {definition.entry_step}")
        for step_id, step in definition.steps.items():
            for ref in (step.next, step.on_true, step.on_false, step.fallback, *step.branches):
                if ref and ref != "end" and ref not in definition.steps:
                    raise WorkflowValidationError(f"Step {step_id} references unknown step: {ref}")
            if step.step_type == "skill" and "skill_id" not in step.config:
                raise WorkflowValidationError(f"Skill step {step_id} missing skill_id")


workflow_builder = WorkflowBuilder()
