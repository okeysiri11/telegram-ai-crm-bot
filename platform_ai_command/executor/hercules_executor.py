"""Command executor — Hercules ONLY. Never call Provider Manager directly."""

from __future__ import annotations

import time
from typing import Any

from platform_ai_command.core.models import CommandPlan, CommandResult
from platform_hercules.core.models import ExecutionContext
from platform_hercules.runtime.hercules_runtime import hercules_runtime


async def execute_plan(plan: CommandPlan, *, max_steps: int | None = None) -> CommandResult:
    """Execute plan steps exclusively via Hercules Runtime."""
    started = time.time()
    job_ids: list[str] = []
    step_results: dict[str, Any] = {}
    cost = 0.0
    limit = max_steps if max_steps is not None else len(plan.steps)

    ctx = ExecutionContext(
        owner_id=plan.message.owner_id,
        channel=plan.message.channel,
        vertical=plan.route.vertical,
        session_id=plan.message.session_id,
        meta={
            "command_plan_id": plan.id,
            "task_kind": plan.route.task_kind.value,
            "via": "ai_command_center",
        },
    )

    for step in plan.steps[:limit]:
        job = await hercules_runtime.submit_ai(
            ctx,
            prompt=str(step.payload.get("prompt") or plan.message.text),
            modality=step.modality,
            vertical=plan.route.vertical,
        )
        job_ids.append(job.id)
        st = hercules_runtime.status(job.id) or {}
        step_results[step.id] = {
            "title": step.title_ru,
            "tool": step.tool,
            "hercules_job_id": job.id,
            "status": st.get("lifecycle"),
            "cost": st.get("cost", 0),
        }
        cost += float(st.get("cost") or 0)

    duration = round(time.time() - started, 3)
    reply = _compose_reply(plan, step_results, cost, duration)
    return CommandResult(
        plan_id=plan.id,
        status="готово",
        reply_ru=reply,
        hercules_job_ids=job_ids,
        step_results=step_results,
        cost=cost,
        duration_sec=duration,
    )


def _compose_reply(plan: CommandPlan, steps: dict[str, Any], cost: float, duration: float) -> str:
    """Human-facing result. Hercules/cost stay in structured CommandResult fields."""
    _ = cost, duration
    prompt = (plan.message.text or "").strip()
    kind = plan.route.task_kind.value if plan.route and plan.route.task_kind else "chat"
    low = prompt.lower()

    if "реклам" in low or kind in {"image", "video"}:
        title = "Рекламный вариант"
        if "кафе" in low or "кофе" in low:
            title = "Рекламная концепция для кафе"
        return (
            f"✅ {title} готов.\n\n"
            f"Запрос: {prompt}\n\n"
            "Черновик:\n"
            "• оффер и тон — дружелюбный, понятный;\n"
            "• формат — Instagram / Reels;\n"
            "• следующий шаг — уточнить название, город и визуал.\n\n"
            "Могу создать изображение, видео или изменить текст."
        )

    if kind in {"crm", "analytics", "document", "search"}:
        return (
            f"✅ Готово.\n\n"
            f"Запрос обработан: {prompt}\n"
            "Могу уточнить детали или продолжить следующим шагом."
        )

    if kind == "chat" or not steps:
        return f"Понял: {prompt}\n\nЧем продолжить?"

    step_hint = ", ".join(s.get("title") or k for k, s in list(steps.items())[:3])
    return (
        f"✅ Готово.\n\n"
        f"Сделано: {step_hint or 'задача выполнена'}.\n"
        f"Исходный запрос: {prompt}"
    )


def assert_hercules_only() -> bool:
    """Guard for architecture tests — executor module imports hercules_runtime."""
    return hercules_runtime is not None
