from __future__ import annotations

from typing import Any

from platform_workflows.adapters.python_definitions import list_template_metadata, register_builtin_workflows
from platform_workflows.workflow_registry import workflow_registry


def register_all() -> None:
    register_builtin_workflows(workflow_registry)


def list_templates() -> list[dict]:
    return list_template_metadata()
