"""Epic 45.3 — AI Planner: goal → step plan."""
from __future__ import annotations
import re
from typing import Any

GOAL_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"реклам|акци|баннер|reels|stories|кампани", re.I), "ads"),
    (re.compile(r"презентац", re.I), "presentation"),
    (re.compile(r"договор|контракт", re.I), "legal"),
    (re.compile(r"видео", re.I), "video"),
    (re.compile(r"изображ|картин|баннер", re.I), "image"),
    (re.compile(r"отчет|отчёт", re.I), "report"),
    (re.compile(r"контент.?план|публикац", re.I), "content_plan"),
    (re.compile(r"клиент|ответ", re.I), "client_reply"),
    (re.compile(r"конкурент|анализ", re.I), "competitors"),
    (re.compile(r"workflow|автоматиз", re.I), "workflow"),
]

PLANS: dict[str, list[dict[str, Any]]] = {
    "ads": [
        {"id": "analyze", "title": "Анализ задачи", "kind": "ai", "parallel_group": None},
        {"id": "context", "title": "Поиск контекста", "kind": "memory", "parallel_group": None},
        {"id": "plan", "title": "Создание плана", "kind": "ai", "parallel_group": None},
        {"id": "copy", "title": "Генерация текста", "kind": "generation", "parallel_group": "creative"},
        {"id": "image", "title": "Генерация изображений", "kind": "generation", "parallel_group": "creative"},
        {"id": "video", "title": "Генерация видео", "kind": "generation", "parallel_group": "creative"},
        {"id": "voice", "title": "Озвучка", "kind": "generation", "parallel_group": "creative"},
        {"id": "qa", "title": "Финальная проверка", "kind": "ai", "parallel_group": None},
        {"id": "save", "title": "Сохранение проекта", "kind": "memory", "parallel_group": None},
        {"id": "deliver", "title": "Готовый результат", "kind": "finish", "parallel_group": None},
    ],
    "beauty_promo": [
        {"id": "offer", "title": "AI пишет оффер", "kind": "generation", "parallel_group": None},
        {"id": "banner", "title": "Создаёт баннер", "kind": "generation", "parallel_group": "creative"},
        {"id": "video", "title": "Делает видео", "kind": "generation", "parallel_group": "creative"},
        {"id": "voice", "title": "Генерирует голос", "kind": "generation", "parallel_group": "creative"},
        {"id": "reels", "title": "Создаёт Reels", "kind": "generation", "parallel_group": "pack"},
        {"id": "stories", "title": "Создаёт Stories", "kind": "generation", "parallel_group": "pack"},
        {"id": "desc", "title": "Делает описание", "kind": "generation", "parallel_group": "pack"},
        {"id": "tags", "title": "Создаёт хэштеги", "kind": "generation", "parallel_group": "pack"},
        {"id": "save", "title": "Сохраняет проект", "kind": "memory", "parallel_group": None},
        {"id": "send", "title": "Отправляет владельцу", "kind": "telegram", "parallel_group": None},
    ],
    "presentation": [
        {"id": "outline", "title": "Структура презентации", "kind": "ai"},
        {"id": "slides", "title": "Генерация слайдов", "kind": "generation"},
        {"id": "save", "title": "Сохранение", "kind": "memory"},
        {"id": "finish", "title": "Готово", "kind": "finish"},
    ],
    "legal": [
        {"id": "draft", "title": "Черновик договора", "kind": "generation"},
        {"id": "review", "title": "Проверка", "kind": "approval"},
        {"id": "save", "title": "Сохранение", "kind": "memory"},
        {"id": "finish", "title": "Готово", "kind": "finish"},
    ],
    "video": [
        {"id": "script", "title": "Сценарий", "kind": "generation", "parallel_group": "prep"},
        {"id": "visual", "title": "Визуал", "kind": "generation", "parallel_group": "prep"},
        {"id": "render", "title": "Рендер видео", "kind": "generation"},
        {"id": "finish", "title": "Готово", "kind": "finish"},
    ],
    "image": [
        {"id": "gen", "title": "Генерация изображения", "kind": "generation"},
        {"id": "finish", "title": "Готово", "kind": "finish"},
    ],
    "report": [
        {"id": "collect", "title": "Сбор данных", "kind": "ai"},
        {"id": "write", "title": "Подготовка отчёта", "kind": "generation"},
        {"id": "finish", "title": "Готово", "kind": "finish"},
    ],
    "content_plan": [
        {"id": "plan", "title": "Контент-план", "kind": "generation"},
        {"id": "series", "title": "Серия публикаций", "kind": "generation"},
        {"id": "finish", "title": "Готово", "kind": "finish"},
    ],
    "client_reply": [
        {"id": "crm", "title": "Контекст CRM", "kind": "crm"},
        {"id": "reply", "title": "Ответ клиенту", "kind": "generation"},
        {"id": "finish", "title": "Готово", "kind": "finish"},
    ],
    "competitors": [
        {"id": "scan", "title": "Анализ конкурентов", "kind": "ai", "parallel_group": "research"},
        {"id": "copy", "title": "Сводка", "kind": "generation", "parallel_group": "research"},
        {"id": "finish", "title": "Готово", "kind": "finish"},
    ],
    "workflow": [
        {"id": "build", "title": "Построение Workflow", "kind": "ai"},
        {"id": "finish", "title": "Готово", "kind": "finish"},
    ],
    "generic": [
        {"id": "analyze", "title": "Анализ", "kind": "ai"},
        {"id": "execute", "title": "Выполнение", "kind": "generation"},
        {"id": "save", "title": "Сохранение", "kind": "memory"},
        {"id": "finish", "title": "Готово", "kind": "finish"},
    ],
}

class AIPlanner:
    def detect_goal(self, text: str) -> str:
        raw = text or ""
        if re.search(r"салон|beauty|маникюр|акци", raw, re.I) and re.search(r"реклам|акци|создай", raw, re.I):
            return "beauty_promo"
        for pat, goal in GOAL_PATTERNS:
            if pat.search(raw):
                return goal
        return "generic"
    def plan(self, goal_text: str, *, vertical: str | None = None) -> dict[str, Any]:
        goal = self.detect_goal(goal_text)
        if vertical == "beauty" and goal in ("ads", "generic"):
            goal = "beauty_promo"
        steps = [dict(s) for s in PLANS.get(goal, PLANS["generic"])]
        return {
            "goal": goal,
            "goal_text": goal_text,
            "steps": steps,
            "step_count": len(steps),
            "parallel_groups": sorted({s["parallel_group"] for s in steps if s.get("parallel_group")}),
            "pipeline": ["planner", "workflow_builder", "orchestrator", "hercules", "validator", "memory"],
        }

ai_planner = AIPlanner()
