# WorkflowLoader — load workflow definitions from YAML and JSON files.

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import yaml

from workflow.models import StepDefinition, StepType, WorkflowDefinition

logger = logging.getLogger(__name__)

DEFAULT_DEFINITIONS_DIR = Path(__file__).resolve().parent / "definitions"


def _parse_step(raw: dict[str, Any]) -> StepDefinition:
    step_id = str(raw.get("id") or raw.get("name") or "").strip()
    if not step_id:
        raise ValueError("Workflow step requires id")

    step_type_raw = str(raw.get("type") or "complete").strip().lower()
    try:
        step_type = StepType(step_type_raw)
    except ValueError as exc:
        raise ValueError(f"Unknown step type: {step_type_raw}") from exc

    config = {k: v for k, v in raw.items() if k not in {"id", "type", "next", "next_step"}}
    next_step = raw.get("next_step") or raw.get("next")
    if next_step is not None:
        next_step = str(next_step)

    return StepDefinition(id=step_id, type=step_type, config=config, next_step=next_step)


def parse_workflow_document(data: dict[str, Any]) -> WorkflowDefinition:
    root = data.get("workflow") if "workflow" in data else data
    if not isinstance(root, dict):
        raise ValueError("Workflow document must be a mapping")

    workflow_id = str(root.get("id") or "").strip()
    if not workflow_id:
        raise ValueError("Workflow requires id")

    vertical = str(root.get("vertical") or root.get("segment") or "OTHER").strip().upper()
    description = str(root.get("description") or "")
    metadata = dict(root.get("metadata") or {})

    raw_steps = root.get("steps") or []
    if not isinstance(raw_steps, list) or not raw_steps:
        raise ValueError(f"Workflow {workflow_id} requires at least one step")

    steps = [_parse_step(item) for item in raw_steps if isinstance(item, dict)]

    # Auto-link linear steps when next_step omitted
    for idx, step in enumerate(steps):
        if step.next_step is None and idx + 1 < len(steps):
            steps[idx] = StepDefinition(
                id=step.id,
                type=step.type,
                config=step.config,
                next_step=steps[idx + 1].id,
            )

    return WorkflowDefinition(
        id=workflow_id,
        vertical=vertical,
        description=description,
        steps=steps,
        metadata=metadata,
    )


class WorkflowLoader:
    @staticmethod
    def load_file(path: Path) -> WorkflowDefinition:
        text = path.read_text(encoding="utf-8")
        if path.suffix.lower() in {".yaml", ".yml"}:
            data = yaml.safe_load(text)
        elif path.suffix.lower() == ".json":
            data = json.loads(text)
        else:
            raise ValueError(f"Unsupported workflow file: {path}")

        if not isinstance(data, dict):
            raise ValueError(f"Invalid workflow document in {path}")
        return parse_workflow_document(data)

    @staticmethod
    def load_directory(directory: Path | None = None) -> list[WorkflowDefinition]:
        base = directory or DEFAULT_DEFINITIONS_DIR
        if not base.exists():
            logger.warning("Workflow definitions directory missing: %s", base)
            return []

        workflows: list[WorkflowDefinition] = []
        for path in sorted(base.glob("*")):
            if path.suffix.lower() not in {".yaml", ".yml", ".json"}:
                continue
            try:
                workflows.append(WorkflowLoader.load_file(path))
                logger.info("workflow_loaded id=%s path=%s", workflows[-1].id, path.name)
            except Exception:
                logger.exception("workflow_load_failed path=%s", path)
        return workflows
