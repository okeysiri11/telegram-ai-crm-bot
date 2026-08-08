"""Sprint 43.3 — product UX helpers (hide tech jargon from users)."""

from __future__ import annotations

import re
from typing import Any

# Words/phrases that must never appear in user-facing Telegram copy.
TECH_LEAK_PATTERNS = re.compile(
    r"\b(provider|pipeline|runtime|vault|fallback|sandbox|openai|anthropic|gemini|"
    r"flux|replicate|runway|veo|pika|kling|luma|hailuo|elevenlabs|cartesia|"
    r"fal\.ai|stability|ideogram|recraft|bfl|deepseek|mistral|openrouter|"
    r"provider.?manager|api.?key|ados_ai_live|media_url|job_id)\b",
    re.I,
)

PROGRESS_STEPS_RU: tuple[tuple[str, str], ...] = (
    ("prepare", "Подготовка…"),
    ("queue", "В очереди…"),
    ("generate", "Генерация…"),
    ("process", "Обработка…"),
    ("done", "Готово"),
)


def sanitize_user_text(text: str) -> str:
    """Strip or rewrite technical leaks for end-user messages."""
    if not text:
        return text
    cleaned = TECH_LEAK_PATTERNS.sub("система", text)
    replacements = {
        "Provider Layer": "платформа",
        "Provider Manager": "платформа",
        "AI Runtime": "AI",
        "UnifiedAiPipeline": "AI",
        "sandbox": "черновик",
        "live": "готово",
        "mode:": "статус:",
    }
    for a, b in replacements.items():
        cleaned = cleaned.replace(a, b)
    return cleaned


def progress_message(step: str, *, eta_sec: int | None = None) -> str:
    label = dict(PROGRESS_STEPS_RU).get(step, "Работаем…")
    if eta_sec is not None and step != "done":
        return f"{label}\nОсталось примерно {eta_sec} сек."
    return label


def format_result_for_user(task: Any) -> str:
    """Human-readable result without provider ids / modes."""
    body = ""
    if getattr(task, "result", None):
        body = str(task.result.get("content") or task.result.get("error") or "")
    if getattr(task, "error", None) and not body:
        body = str(task.error)
    body = sanitize_user_text(body)
    # Drop sandbox markers
    body = re.sub(r"\[sandbox-[^\]]+\]\s*", "", body)
    body = re.sub(r"— Результат подготовлен через.*", "", body).strip()
    cost = 0.0
    if getattr(task, "result", None):
        cb = task.result.get("cost_breakdown") or {}
        cost = float(cb.get("total") or getattr(task, "cost_estimate", 0) or 0)
    lines = [
        "✅ Готово",
        "",
        body[:1200] if body else "Результат сохранён в истории.",
    ]
    if cost > 0:
        lines.append("")
        lines.append(f"Стоимость: ≈ {cost:.3f} у.е.")
    if getattr(task, "duration_sec", None):
        try:
            lines.append(f"Время: {task.duration_sec()} сек.")
        except Exception:
            pass
    return "\n".join(lines)


def format_history_line(task: Any) -> str:
    prompt = sanitize_user_text((getattr(task, "prompt", "") or "")[:80])
    status = getattr(task, "status", "")
    status_map = {
        "создана": "Создана",
        "в_очереди": "В очереди",
        "подготавливается": "Подготовка",
        "генерируется": "Генерация",
        "обрабатывается": "Обработка",
        "готово": "Готово",
        "ошибка": "Ошибка",
        "отменена": "Отменена",
        "повтор": "Повтор",
    }
    st = status_map.get(status, status)
    cost = getattr(task, "cost_estimate", 0) or 0
    return f"• {st} · {getattr(task, 'modality', '')} · ≈{cost:.3f} у.е.\n  {prompt}"


STATUS_USER_RU = {
    "создана": "Создана",
    "в_очереди": "В очереди",
    "подготавливается": "Подготовка",
    "генерируется": "Генерация",
    "обрабатывается": "Обработка",
    "готово": "Готово",
    "ошибка": "Ошибка",
}
