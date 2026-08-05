"""AI Skills & SDK service façade — Sprint 36.8."""

from __future__ import annotations

from typing import Any

from platform_ai.skills_sdk_engine import SkillsSdkEngine, skills_sdk_engine
from platform_ai.skills_sdk_models import SdkKind, SkillVisibility


class SkillsSdkService:
    def __init__(self, engine: SkillsSdkEngine | None = None) -> None:
        self.engine = engine or skills_sdk_engine

    def reset(self) -> None:
        self.engine.reset()

    def ensure_ready(self) -> None:
        self.engine.ensure_seed()

    def status(self) -> dict[str, Any]:
        self.ensure_ready()
        return {
            "service": "skills_sdk",
            "canonical": "platform_ai",
            "sprint": "36.8",
            "visibilities": [v.value for v in SkillVisibility],
            "sdks": [k.value for k in SdkKind],
            "statistics": self.engine.statistics(),
            "integrations": [
                "ai_runtime",
                "multi_agent_runtime",
                "project_memory",
                "context_engine",
                "workflow",
                "voice_runtime",
            ],
        }

    def register(self, body: dict[str, Any]) -> dict[str, Any]:
        return self.engine.register(body).to_dict()

    def list_skills(self, **kwargs: Any) -> list[dict[str, Any]]:
        return [s.to_dict() for s in self.engine.list_skills(**kwargs)]

    def get_skill(self, skill_id: str) -> dict[str, Any]:
        return self.engine.get_skill(skill_id).to_dict()

    def list_versions(self, skill_id: str) -> list[dict[str, Any]]:
        return [v.to_dict() for v in self.engine.list_versions(skill_id)]

    def publish_version(self, skill_id: str, body: dict[str, Any]) -> dict[str, Any]:
        return self.engine.publish_version(skill_id, body).to_dict()

    def install(self, skill_id: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.engine.install(skill_id, body).to_dict()

    def uninstall(self, skill_id: str) -> dict[str, Any]:
        return self.engine.uninstall(skill_id).to_dict()

    def enable(self, skill_id: str) -> dict[str, Any]:
        return self.engine.enable(skill_id).to_dict()

    def disable(self, skill_id: str) -> dict[str, Any]:
        return self.engine.disable(skill_id).to_dict()

    def list_installed(self) -> list[dict[str, Any]]:
        return [i.to_dict() for i in self.engine.list_installed()]

    async def execute(self, body: dict[str, Any]) -> dict[str, Any]:
        return (await self.engine.execute(body)).to_dict()

    def marketplace(self, *, repository: str | None = None) -> list[dict[str, Any]]:
        return self.engine.marketplace_list(repository=repository)

    def rate(self, skill_id: str, body: dict[str, Any]) -> dict[str, Any]:
        return self.engine.rate(skill_id, float(body.get("score") or 0), comment=str(body.get("comment") or "")).to_dict()

    def updates(self, skill_id: str) -> dict[str, Any]:
        return self.engine.check_updates(skill_id)

    def templates(self, *, kind: str | None = None) -> list[dict[str, Any]]:
        return [t.to_dict() for t in self.engine.list_templates(kind=kind)]

    def get_template(self, template_id: str) -> dict[str, Any]:
        return self.engine.get_template(template_id).to_dict()

    def sdk_manifest(self) -> dict[str, Any]:
        return self.engine.sdk_manifest()

    def statistics(self) -> dict[str, Any]:
        return self.engine.statistics()

    def list_executions(self) -> list[dict[str, Any]]:
        return [e.to_dict() for e in self.engine.list_executions()]

    # --- Integrations ---

    async def for_ai_runtime(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        body = body or {}
        skill_id = str(body.get("skill_id") or "skill.summarize_report")
        exe = await self.execute({**body, "skill_id": skill_id, "agent_id": body.get("agent_id") or "ai_runtime"})
        return {"consumer": "ai_runtime", "execution": exe}

    async def for_multi_agent(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        body = body or {}
        skill_id = str(body.get("skill_id") or "skill.crm_enrich")
        self.install(skill_id, {"principal": "multi_agent"})
        exe = await self.execute({**body, "skill_id": skill_id, "agent_id": "agent_worker"})
        return {"consumer": "multi_agent_runtime", "execution": exe}

    async def for_project_memory(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        body = body or {}
        try:
            from platform_memory.project_memory_service import project_memory_service

            await project_memory_service.remember(
                {
                    "kind": "agent",
                    "layer": "working",
                    "title": "Skill execution note",
                    "content": f"Skill {body.get('skill_id') or 'skill.summarize_report'} available",
                    "agent_id": "skills_sdk",
                    "project_id": body.get("project_id") or "proj_ados",
                }
            )
        except Exception:
            pass
        exe = await self.execute(
            {"skill_id": body.get("skill_id") or "skill.summarize_report", "input": body.get("input") or {}}
        )
        return {"consumer": "project_memory", "execution": exe}

    async def for_context_engine(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        body = body or {}
        ctx = None
        try:
            from platform_memory.service import context_engine_service

            ctx = await context_engine_service.for_ai_runtime(
                {"query": body.get("query") or "skills", "use_project_memory": False}
            )
        except Exception as exc:  # noqa: BLE001
            ctx = {"error": str(exc)}
        exe = await self.execute(
            {
                "skill_id": body.get("skill_id") or "skill.summarize_report",
                "input": {"context": ctx},
            }
        )
        return {"consumer": "context_engine", "context": ctx, "execution": exe}

    async def for_workflow(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        body = body or {}
        exe = await self.execute(
            {"skill_id": body.get("skill_id") or "skill.local_draft", "input": body.get("input") or {}}
        )
        return {"consumer": "workflow", "execution": exe}

    async def for_voice(self, body: dict[str, Any] | None = None) -> dict[str, Any]:
        body = body or {}
        parsed = None
        try:
            from platform_ai.voice_service import voice_runtime_service

            parsed = voice_runtime_service.parse(str(body.get("transcript") or "generate report about skills"))
        except Exception as exc:  # noqa: BLE001
            parsed = {"error": str(exc)}
        exe = await self.execute(
            {
                "skill_id": body.get("skill_id") or "skill.summarize_report",
                "input": {"voice": parsed},
                "agent_id": "voice_runtime",
            }
        )
        return {"consumer": "voice_runtime", "voice": parsed, "execution": exe}


skills_sdk_service = SkillsSdkService()
