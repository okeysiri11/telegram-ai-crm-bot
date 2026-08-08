"""Vertical AI Framework — config-driven industry assistants over UnifiedAiPipeline."""

from __future__ import annotations

from typing import Any

from platform_ai.pipeline import UnifiedAiPipeline, unified_ai_pipeline
from platform_ai.pipeline_models import AiChannel, AiTaskRecord, AiTaskRequest
from platform_vertical_ai.agents import agent_catalog, resolve_agent_task
from platform_vertical_ai.models import VerticalConfig, VerticalMenuItem
from platform_vertical_ai.registry import VerticalRegistry, vertical_registry
from platform_vertical_ai.wizard import (
    WizardDraft,
    build_vertical_prompt,
    calendar_plan,
    chain_plan,
    marketing_suggestions,
    wizard_steps_as_studio,
)

VERSION = "43.4"


class VerticalAiFramework:
    """
    Universal vertical layer.

    New verticals = register VerticalConfig. No business-logic copy.
    All generation uses the same UnifiedAiPipeline runtime.
    """

    VERSION = VERSION

    def __init__(
        self,
        registry: VerticalRegistry | None = None,
        pipeline: UnifiedAiPipeline | None = None,
    ) -> None:
        self.registry = registry or vertical_registry
        self.pipeline = pipeline or unified_ai_pipeline

    def list_verticals(self) -> list[VerticalConfig]:
        return self.registry.list_all()

    def get(self, vertical_id: str) -> VerticalConfig:
        return self.registry.require(vertical_id)

    def welcome(self, vertical_id: str) -> str:
        cfg = self.get(vertical_id)
        lines = [
            f"{cfg.icon} {cfg.name_ru}",
            "",
            cfg.description_ru,
            "",
            "Выберите задачу или напишите идею своими словами.",
        ]
        if cfg.complete:
            lines.append("")
            lines.append("Эталонная вертикаль Framework — готовые сценарии и мастер создания.")
        return "\n".join(lines)

    def menu_items(self, vertical_id: str) -> list[VerticalMenuItem]:
        return list(self.get(vertical_id).menu)

    def menu_labels(self, vertical_id: str) -> list[str]:
        return self.get(vertical_id).menu_labels()

    def resolve_menu(self, vertical_id: str, label: str) -> VerticalMenuItem | None:
        return self.get(vertical_id).find_menu(label)

    def wizard_steps(self, vertical_id: str) -> list[dict[str, Any]]:
        return wizard_steps_as_studio(self.get(vertical_id))

    def start_wizard(self, vertical_id: str, *, menu_action: str | None = None) -> WizardDraft:
        return WizardDraft(vertical_id=vertical_id, menu_action=menu_action)

    def preview_chain(self, vertical_id: str, answers: dict[str, str]) -> str:
        cfg = self.get(vertical_id)
        steps = chain_plan(cfg, answers)
        lines = ["Цепочка генерации:", ""]
        for s in steps:
            lines.append(f"• {s['title']}: {s['detail'][:80]}")
        lines.append("")
        lines.append("Могу запустить сейчас.")
        return "\n".join(lines)

    def agents_overview(self, vertical_id: str) -> str:
        cfg = self.get(vertical_id)
        catalog = agent_catalog(cfg)
        lines = [f"Агенты {cfg.name_ru}:", ""]
        for a in cfg.agents:
            products = ", ".join(catalog.get(a.id, [])[:5])
            lines.append(f"• {a.name_ru} — {products}")
        return "\n".join(lines)

    def prompt_library_text(self, vertical_id: str) -> str:
        cfg = self.get(vertical_id)
        if not cfg.prompt_library:
            return "Библиотека промптов пуста."
        lines = [f"📚 Промпты · {cfg.name_ru}", ""]
        by_cat: dict[str, list[str]] = {}
        for p in cfg.prompt_library:
            by_cat.setdefault(p.category, []).append(f"  · {p.title}")
        for cat, items in by_cat.items():
            lines.append(cat)
            lines.extend(items)
            lines.append("")
        return "\n".join(lines)

    def calendar_text(self, vertical_id: str, days: int = 30, *, service: str = "") -> str:
        cfg = self.get(vertical_id)
        if days not in cfg.calendar_periods:
            days = cfg.calendar_periods[0] if cfg.calendar_periods else 7
        plan = calendar_plan(cfg, days, service=service)
        lines = [f"📅 Контент-план на {days} дней · {cfg.name_ru}", ""]
        for row in plan[:14]:  # preview first 2 weeks in chat
            lines.append(f"День {row['day']}: {row['type']} — {row['theme']} ({row['hook']})")
        if days > 14:
            lines.append("")
            lines.append(f"… и ещё {days - 14} дней в полном плане.")
        return "\n".join(lines)

    def marketing_text(self, vertical_id: str) -> str:
        cfg = self.get(vertical_id)
        lines = [f"📢 Маркетинг · {cfg.name_ru}", ""]
        for offer in marketing_suggestions(cfg):
            lines.append(f"• {offer}")
        return "\n".join(lines)

    def settings_text(self, vertical_id: str) -> str:
        cfg = self.get(vertical_id)
        return (
            f"⚙ Настройки · {cfg.name_ru}\n\n"
            f"Язык: Русский\n"
            f"Иконка: {cfg.icon}\n"
            f"Полная вертикаль: {'да' if cfg.complete else 'каркас Framework'}\n"
            "Наследует: чат, студию, CRM, историю, избранное, агентов, Telegram."
        )

    def history_text(self, owner_id: str, vertical_id: str) -> str:
        tasks = [
            t
            for t in self.pipeline.list_for_owner(owner_id, limit=20)
            if (t.vertical == vertical_id) or (getattr(t, "studio_id", None) == vertical_id)
        ]
        if not tasks:
            return f"📱 История · {self.get(vertical_id).name_ru}\n\nПока пусто. Создайте первый пост или Reels."
        lines = [f"📱 История · {self.get(vertical_id).name_ru}", ""]
        for t in tasks[:12]:
            lines.append(f"• {t.modality} · {t.status} · ≈{t.cost_estimate:.3f}")
            lines.append(f"  {(t.prompt or '')[:70]}")
        return "\n".join(lines)

    def favorites_text(self, owner_id: str, vertical_id: str) -> str:
        favs = [
            t
            for t in self.pipeline.favorites(owner_id)
            if t.vertical == vertical_id or getattr(t, "studio_id", None) == vertical_id
        ]
        if not favs:
            return f"⭐ Избранное · {self.get(vertical_id).name_ru}\n\nПусто."
        lines = [f"⭐ Избранное · {self.get(vertical_id).name_ru}", ""]
        for t in favs:
            lines.append(f"• {(t.prompt or '')[:80]}")
        return "\n".join(lines)

    def modality_for_menu(self, item: VerticalMenuItem) -> str:
        if item.modality:
            return item.modality
        if item.action in ("history", "favorites", "settings", "calendar", "marketing", "wizard"):
            return "text"
        return "ads"

    async def run_menu_generation(
        self,
        owner_id: str,
        vertical_id: str,
        *,
        menu_id: str,
        answers: dict[str, str],
    ) -> AiTaskRecord:
        cfg = self.get(vertical_id)
        item = next((m for m in cfg.menu if m.id == menu_id), None)
        modality = self.modality_for_menu(item) if item else "ads"
        intent = item.label if item else menu_id
        if item and item.agent:
            product = answers.get("service") or answers.get("what") or intent
            task_spec = resolve_agent_task(cfg, item.agent, product, answers)
            prompt = task_spec["prompt"]
            modality = task_spec["modality"]
        else:
            prompt = build_vertical_prompt(cfg, answers, intent=intent)
        req = AiTaskRequest(
            owner_id=owner_id,
            modality=modality if modality != "calendar" else "text",
            prompt=prompt,
            channel=AiChannel.TELEGRAM.value,
            meta=dict(answers),
            studio_id=vertical_id,
            vertical=vertical_id,
            optimize_prompt=True,
        )
        return await self.pipeline.run(req)

    async def run_chain(
        self,
        owner_id: str,
        vertical_id: str,
        answers: dict[str, str],
    ) -> dict[str, Any]:
        """Run key chain steps sequentially through the shared runtime."""
        cfg = self.get(vertical_id)
        prompt = build_vertical_prompt(cfg, answers)
        results: dict[str, Any] = {"vertical_id": vertical_id, "prompt": prompt, "steps": {}}
        modality_map = {
            "prompt": "prompt",
            "image": "image",
            "video": "video",
            "voice": "voice",
            "music": "voice",
            "reels": "video",
            "caption": "text",
            "hashtags": "text",
            "publish_ready": "ads",
        }
        # Keep UX snappy: execute prompt + image + caption as primary; rest planned
        execute = ("prompt", "image", "caption", "hashtags")
        for step in cfg.chain_steps:
            mod = modality_map.get(step, "text")
            if step not in execute:
                results["steps"][step] = {"status": "planned", "title": step}
                continue
            task = await self.pipeline.run(
                AiTaskRequest(
                    owner_id=owner_id,
                    modality=mod,
                    prompt=f"{prompt} | этап: {step}",
                    channel=AiChannel.TELEGRAM.value,
                    meta=dict(answers),
                    studio_id=vertical_id,
                    vertical=vertical_id,
                    optimize_prompt=step == "prompt",
                )
            )
            results["steps"][step] = {
                "status": task.status,
                "task_id": task.id,
                "content": (task.result or {}).get("content", "")[:500],
            }
        results["chain_preview"] = chain_plan(cfg, answers)
        return results

    def new_vertical_checklist(self) -> list[str]:
        """What to fill to add a vertical without copying code."""
        return [
            "Название",
            "Иконка",
            "Цвет",
            "Меню",
            "AI агенты",
            "Документы",
            "CRM сущности",
            "Шаблоны / сценарии",
            "Knowledge",
            "Prompt Library",
            "Dashboard виджеты",
            "Wizard вопросы",
        ]


vertical_ai_framework = VerticalAiFramework()
