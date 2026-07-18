# WorkflowLoader — YAML, JSON, and Python workflow definitions.

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import yaml

from platform_workflows.models import StepDefinition, StepType, WorkflowDefinition

logger = logging.getLogger(__name__)

DEFAULT_DEFINITIONS_DIR = Path(__file__).resolve().parents[1] / "workflow" / "definitions"


def _parse_step(raw: dict[str, Any]) -> StepDefinition:
    step_id = str(raw.get("id") or raw.get("step_id") or raw.get("name") or "").strip()
    if not step_id:
        raise ValueError("Workflow step requires id")
    return StepDefinition.from_dict(raw, step_id=step_id)


def parse_workflow_document(data: dict[str, Any]) -> WorkflowDefinition:
    root = data.get("workflow") if "workflow" in data else data
    if not isinstance(root, dict):
        raise ValueError("Workflow document must be a mapping")

    workflow_id = str(root.get("id") or root.get("workflow_id") or "").strip()
    if not workflow_id:
        raise ValueError("Workflow requires id")

    vertical = str(root.get("vertical") or root.get("segment") or root.get("category") or "OTHER").strip().upper()
    description = str(root.get("description") or root.get("name") or "")
    metadata = dict(root.get("metadata") or {})
    entry_step = root.get("entry_step")

    raw_steps = root.get("steps") or []
    steps: dict[str, StepDefinition] = {}

    if isinstance(raw_steps, dict):
        for sid, item in raw_steps.items():
            if isinstance(item, dict):
                steps[sid] = StepDefinition.from_dict(item, step_id=sid)
    elif isinstance(raw_steps, list):
        parsed = [_parse_step(item) for item in raw_steps if isinstance(item, dict)]
        for idx, step in enumerate(parsed):
            if step.next_step is None and idx + 1 < len(parsed):
                parsed[idx] = StepDefinition(
                    id=step.id,
                    type=step.type,
                    config=step.config,
                    next_step=parsed[idx + 1].id,
                    on_true=step.on_true,
                    on_false=step.on_false,
                    fallback=step.fallback,
                    branches=step.branches,
                    retries=step.retries,
                    timeout_seconds=step.timeout_seconds,
                )
        steps = {s.id: s for s in parsed}
        if entry_step is None and parsed:
            entry_step = parsed[0].id
    else:
        raise ValueError(f"Workflow {workflow_id} requires steps")

    if not steps:
        raise ValueError(f"Workflow {workflow_id} requires at least one step")

    if entry_step is None:
        entry_step = next(iter(steps.keys()))

    return WorkflowDefinition(
        id=workflow_id,
        vertical=vertical,
        description=description,
        steps=steps,
        entry_step=str(entry_step),
        metadata=metadata,
        version=str(root.get("version") or "1.0.0"),
        category=str(root.get("category") or "general"),
        tags=list(root.get("tags") or []),
        enabled=bool(root.get("enabled", True)),
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

    @staticmethod
    def from_dict(data: dict[str, Any]) -> WorkflowDefinition:
        return parse_workflow_document(data)
