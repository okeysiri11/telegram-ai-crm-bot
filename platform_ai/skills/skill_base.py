# Abstract AI Skill base class.

from __future__ import annotations

from abc import ABC
from typing import Any, ClassVar

from platform_ai.models import TaskType
from platform_ai.skills.models import SkillCategory, SkillExecutionResult, SkillHealthResult, SkillMetadata
from platform_ai.skills.skill_context import SkillContext


class AISkill(ABC):
    """Reusable business capability powered by AI — never calls providers directly."""

    skill_id: ClassVar[str] = ""
    name: ClassVar[str] = ""
    version: ClassVar[str] = "1.0.0"
    description: ClassVar[str] = ""
    category: ClassVar[str] = SkillCategory.ANALYSIS.value
    tags: ClassVar[list[str]] = []
    capabilities: ClassVar[list[str]] = []
    permissions: ClassVar[list[str]] = []
    cache_ttl: ClassVar[float] = 3600.0
    task_type: ClassVar[TaskType] = TaskType.CHAT
    template_id: ClassVar[str | None] = None
    preferred_models: ClassVar[list[str]] = []

    @classmethod
    def metadata(cls) -> SkillMetadata:
        return SkillMetadata(
            skill_id=cls.skill_id,
            name=cls.name,
            version=cls.version,
            description=cls.description,
            category=cls.category,
            tags=list(cls.tags),
            capabilities=list(cls.capabilities),
            permissions=list(cls.permissions),
            cache_ttl=cls.cache_ttl,
        )

    async def execute(self, ctx: SkillContext) -> SkillExecutionResult:
        """Override for custom execution; default path uses skill_executor + ai_service."""
        raise NotImplementedError(f"Skill {self.skill_id} must be executed via skill_executor")

    def validate(self, ctx: SkillContext) -> None:
        """Validate input against required_context."""
        missing = [k for k in self.required_context() if k not in ctx.input and k not in ctx.request]
        if missing:
            from platform_ai.skills.exceptions import SkillValidationError

            raise SkillValidationError(f"Missing required context: {', '.join(missing)}")

    def estimate_cost(self, ctx: SkillContext) -> float:
        prompt_len = sum(len(str(v)) for v in ctx.input.values())
        return round(prompt_len / 4000 * 0.002, 6)

    def supported_models(self) -> list[str]:
        return list(self.preferred_models) or ["*"]

    def required_context(self) -> list[str]:
        return []

    async def health(self) -> SkillHealthResult:
        return SkillHealthResult(skill_id=self.skill_id, status="healthy")

    def build_prompt(self, ctx: SkillContext) -> str:
        """Override to customize prompt construction."""
        import json

        return f"Skill: {self.skill_id}\nInput: {json.dumps(ctx.input, ensure_ascii=False)}"

    def parse_json_output(self, raw: str, fallback: dict[str, Any] | None = None) -> dict[str, Any]:
        from platform_ai.provider_base import ProviderResponse
        from platform_ai.response_parser import response_parser

        parsed = response_parser.parse_json(ProviderResponse(content=raw))
        if fallback and parsed.keys() == {"raw"}:
            return {**fallback, "raw": raw}
        return parsed

    def parse_output(self, raw: str, ctx: SkillContext) -> dict[str, Any]:
        """Override to parse AI response into structured output."""
        return {"result": raw.strip()}
