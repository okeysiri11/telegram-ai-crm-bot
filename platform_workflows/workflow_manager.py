"""Epic 45.3 — Universal Automation façade.

User → AI Command Center → Planner → Workflow Builder → Orchestrator
→ Hercules Runtime → Providers → Validator → Memory → Channels
"""

from __future__ import annotations

from typing import Any

from platform_workflows.approval_engine import approval_engine
from platform_workflows.planner import ai_planner
from platform_workflows.scheduler import workflow_scheduler
from platform_workflows.ua_engine import UniversalWorkflowEngine, universal_workflow_engine
from platform_workflows.ua_store import ua_store
from platform_workflows.workflow_builder import workflow_builder
from platform_workflows.workflow_history import workflow_history
from platform_workflows.workflow_permissions import WorkflowPrincipal, can_manage, can_run
from platform_workflows.workflow_templates import library, templates_for_vertical

VERSION = "45.3.0"


class WorkflowManager:
    VERSION = VERSION

    def __init__(self, engine: UniversalWorkflowEngine | None = None) -> None:
        self.engine = engine or universal_workflow_engine

    def principal(self, owner_id: str, *, role: str = "owner", company_id: str = "default") -> WorkflowPrincipal:
        return WorkflowPrincipal(owner_id=owner_id, role=role, company_id=company_id)

    def status(self, owner_id: str) -> dict[str, Any]:
        wfs = [w for w in ua_store.workflows.values() if w.owner_id == owner_id]
        runs = [r for r in ua_store.runs.values() if r.owner_id == owner_id]
        active = [r.to_dict() for r in runs if r.status in ("running", "awaiting_approval", "pending")]
        return {
            "version": self.VERSION,
            "owner_id": owner_id,
            "workflows": len(wfs),
            "active_runs": len(active),
            "jobs": len([j for j in ua_store.jobs.values() if j.owner_id == owner_id]),
            "pipeline": [
                "ai_command_center",
                "planner",
                "workflow_builder",
                "orchestrator",
                "hercules",
                "validator",
                "memory",
            ],
            "via_hercules_only": True,
            "active": active[:20],
        }

    def list_workflows(self, owner_id: str) -> list[dict[str, Any]]:
        return [w.to_dict() for w in ua_store.workflows.values() if w.owner_id == owner_id]

    def templates(self, *, vertical: str | None = None) -> dict[str, Any]:
        lib = library()
        if vertical:
            lib = {**lib, "templates": templates_for_vertical(vertical)}
        return lib

    def create(
        self,
        owner_id: str,
        *,
        goal: str | None = None,
        title: str | None = None,
        blocks: list[dict[str, Any]] | None = None,
        template_id: str | None = None,
        vertical: str = "company",
        channel: str = "web",
        role: str = "owner",
    ) -> dict[str, Any]:
        p = self.principal(owner_id, role=role)
        if not can_manage(p) and not can_run(p):
            return {"error": "forbidden"}
        if blocks:
            return workflow_builder.create_custom(owner_id, title or "Custom Workflow", blocks, channel=channel, vertical=vertical)
        return workflow_builder.build_from_goal(
            owner_id, goal or title or "Новая задача", vertical=vertical, channel=channel, template_id=template_id
        )

    def clone(self, owner_id: str, workflow_id: str) -> dict[str, Any]:
        cloned = workflow_builder.clone(owner_id, workflow_id)
        return cloned or {"error": "not_found"}

    def run(self, owner_id: str, workflow_id: str | None = None, *, goal: str | None = None, channel: str = "web", template_id: str | None = None, vertical: str = "company") -> dict[str, Any]:
        p = self.principal(owner_id)
        if not can_run(p):
            return {"error": "forbidden"}
        if not workflow_id:
            created = self.create(owner_id, goal=goal or "Задача", template_id=template_id, vertical=vertical, channel=channel)
            if created.get("error"):
                return created
            workflow_id = created["id"]
        return self.engine.start(owner_id, workflow_id, channel=channel)

    def run_goal(self, owner_id: str, goal_text: str, *, channel: str = "web", vertical: str = "company") -> dict[str, Any]:
        plan = ai_planner.plan(goal_text, vertical=vertical)
        created = self.create(owner_id, goal=goal_text, vertical=vertical, channel=channel)
        run = self.engine.start(owner_id, created["id"], channel=channel)
        return {"plan": plan, "workflow": created, "run": run}

    def approve(self, owner_id: str, run_id: str) -> dict[str, Any]:
        return self.engine.continue_after_approval(run_id, owner_id)

    def cancel(self, owner_id: str, run_id: str) -> dict[str, Any]:
        return self.engine.cancel(run_id, owner_id)

    def remove(self, owner_id: str, workflow_id: str) -> dict[str, Any]:
        wf = ua_store.workflows.get(workflow_id)
        if not wf or wf.owner_id != owner_id:
            return {"error": "not_found"}
        del ua_store.workflows[workflow_id]
        return {"removed": True, "id": workflow_id}

    def schedule(self, owner_id: str, workflow_id: str, schedule: str, **meta: Any) -> dict[str, Any]:
        return workflow_scheduler.schedule(owner_id, workflow_id, schedule, meta=meta or None)

    def jobs(self, owner_id: str) -> list[dict[str, Any]]:
        return workflow_scheduler.list_jobs(owner_id)

    def tick(self) -> list[dict[str, Any]]:
        return workflow_scheduler.tick(lambda oid, wid: self.engine.start(oid, wid, channel="scheduler"))

    def history(self, owner_id: str) -> list[dict[str, Any]]:
        return workflow_history.list_for(owner_id)

    def run_status(self, run_id: str) -> dict[str, Any] | None:
        return self.engine.status(run_id)

    def monitor(self, run_id: str) -> dict[str, Any] | None:
        return self.engine.monitor(run_id)

    def dashboard(self, owner_id: str) -> dict[str, Any]:
        st = self.status(owner_id)
        runs = [r.to_dict() for r in ua_store.runs.values() if r.owner_id == owner_id]
        costs = sum(r.get("cost", 0) for r in runs)
        errors = [r for r in runs if r.get("status") == "failed"]
        return {
            "title": "Owner Dashboard · Автоматизация",
            "active_workflows": st["active"],
            "hercules_queue": [r for r in st["active"] if r.get("via_hercules")],
            "background_jobs": self.jobs(owner_id),
            "cost_total": costs,
            "models_used": sorted({m for r in runs for m in r.get("models") or []}),
            "errors": errors[:20],
            "history": self.history(owner_id)[:20],
            "performance": {"runs": len(runs), "completed": sum(1 for r in runs if r.get("status") == "completed")},
        }

    def telegram_menu(self, owner_id: str) -> dict[str, Any]:
        return {
            "title": "⚡ Автоматизация",
            "status": self.status(owner_id),
            "buttons": [
                "Создать Workflow",
                "Мои Workflow",
                "Библиотека",
                "Активные процессы",
                "Запланированные",
                "История",
                "Фоновые задачи",
                "Монитор",
                "Настройки",
            ],
        }

    def match_voice(self, text: str) -> str | None:
        import re
        raw = (text or "").strip().lower()
        mapping = [
            (r"создай\s+workflow|создать\s+workflow", "create"),
            (r"сделай\s+реклам|создай\s+реклам", "ads"),
            (r"подготовь\s+презентац|создай\s+презентац", "presentation"),
            (r"создай\s+договор|подготовь\s+договор", "legal"),
            (r"запусти\s+анализ|анализ\s+конкурент", "competitors"),
            (r"создай\s+видео", "video"),
            (r"сделай\s+публикац", "content_plan"),
            (r"продолж\w*\s+workflow", "continue"),
            (r"останов\w*\s+workflow", "stop"),
        ]
        for pat, intent in mapping:
            if re.search(pat, raw, re.I):
                return intent
        return None

    async def run_from_command(self, owner_id: str, text: str, *, channel: str = "web") -> dict[str, Any]:
        intent = self.match_voice(text)
        if intent == "stop":
            active = [r for r in ua_store.runs.values() if r.owner_id == owner_id and r.status in ("running", "awaiting_approval")]
            if not active:
                return {"type": "voice", "reply_ru": "Нет активных Workflow."}
            return {"type": "voice", "reply_ru": "Workflow остановлен.", "run": self.cancel(owner_id, active[-1].id)}
        if intent == "continue":
            waiting = [r for r in ua_store.runs.values() if r.owner_id == owner_id and r.status == "awaiting_approval"]
            if waiting:
                return {"type": "voice", "reply_ru": "Продолжаем Workflow.", "run": self.approve(owner_id, waiting[-1].id)}
            return {"type": "voice", "reply_ru": "Нет Workflow, ожидающих подтверждения."}
        goal = text
        vertical = "company"
        if intent == "ads":
            goal, vertical = "Создай рекламу", "marketing"
        elif intent == "presentation":
            goal = "Создай презентацию"
        elif intent == "legal":
            goal, vertical = "Подготовь договор", "legal"
        elif intent == "competitors":
            goal = "Проанализируй конкурентов"
        elif intent == "video":
            goal = "Создай видео"
        elif intent == "content_plan":
            goal = "Создай серию публикаций"
        elif intent == "create":
            goal = text
        result = self.run_goal(owner_id, goal, channel=channel, vertical=vertical)
        return {
            "type": "workflow_run",
            "reply_ru": f"Workflow запущен через Hercules. Статус: {result['run'].get('status')}",
            **result,
        }


workflow_manager = WorkflowManager()
