# Skill context — assembled execution context for skills.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SkillContext:
    """Context passed to skill execution — no direct provider access."""

    skill_id: str
    plugin_id: str | None = None
    user_id: str | None = None
    request_id: str | None = None
    workflow: dict[str, Any] = field(default_factory=dict)
    request: dict[str, Any] = field(default_factory=dict)
    configuration: dict[str, Any] = field(default_factory=dict)
    conversation: dict[str, Any] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)
    files: list[dict[str, Any]] = field(default_factory=list)
    input: dict[str, Any] = field(default_factory=dict)

    def to_prompt_context(self) -> dict[str, Any]:
        return {
            "plugin_id": self.plugin_id,
            "user_id": self.user_id,
            "request_id": self.request_id,
            "workflow": self.workflow,
            "request": self.request,
            "configuration": self.configuration,
            "conversation": self.conversation,
            "history": self.history,
            "files": self.files,
            "input": self.input,
        }

    @classmethod
    def from_execution(
        cls,
        skill_id: str,
        *,
        plugin_id: str | None = None,
        user_id: str | None = None,
        request_id: str | None = None,
        input_data: dict[str, Any] | None = None,
        extra: dict[str, Any] | None = None,
    ) -> SkillContext:
        extra = extra or {}
        return cls(
            skill_id=skill_id,
            plugin_id=plugin_id,
            user_id=user_id,
            request_id=request_id,
            workflow=extra.get("workflow", {}),
            request=extra.get("request", {}),
            configuration=extra.get("configuration", {}),
            conversation=extra.get("conversation", {}),
            history=extra.get("history", []),
            files=extra.get("files", []),
            input=dict(input_data or {}),
        )
