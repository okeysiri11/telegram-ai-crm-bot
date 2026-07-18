# AI Workflow execution context — shared memory and external references.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class WorkflowContext:
    """Shared execution context passed through all workflow steps."""

    workflow_id: str
    execution_id: str
    plugin_id: str | None = None
    user_id: str | None = None
    input: dict[str, Any] = field(default_factory=dict)
    memory: dict[str, Any] = field(default_factory=dict)
    step_results: dict[str, Any] = field(default_factory=dict)
    conversation: dict[str, Any] = field(default_factory=dict)
    files: list[dict[str, Any]] = field(default_factory=list)
    history: list[dict[str, Any]] = field(default_factory=list)
    configuration: dict[str, Any] = field(default_factory=dict)
    external_apis: dict[str, Any] = field(default_factory=dict)

    def resolve(self, ref: Any) -> Any:
        """Resolve $input.x, $memory.x, $steps.step_id paths."""
        if not isinstance(ref, str) or not ref.startswith("$"):
            return ref
        path = ref[1:].split(".")
        root = path[0]
        if root == "input":
            return _dig(self.input, path[1:])
        if root == "memory":
            return _dig(self.memory, path[1:])
        if root == "steps":
            return _dig(self.step_results, path[1:])
        if root == "config":
            return _dig(self.configuration, path[1:])
        return ref

    def resolve_mapping(self, mapping: dict[str, Any]) -> dict[str, Any]:
        return {k: self.resolve(v) for k, v in mapping.items()}

    def set_memory(self, key: str, value: Any) -> None:
        self.memory[key] = value

    def get_step_output(self, step_id: str) -> dict[str, Any]:
        result = self.step_results.get(step_id, {})
        if isinstance(result, dict):
            return result.get("output", result)
        return {}


def _dig(obj: Any, path: list[str]) -> Any:
    cur = obj
    for part in path:
        if cur is None:
            return None
        if isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return None
    return cur
