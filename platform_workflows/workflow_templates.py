"""Epic 45.3 — Workflow Library + AI Templates."""
from __future__ import annotations
from typing import Any

VERTICALS = (
    "beauty", "auto", "construction", "legal", "crypto", "travel", "agro",
    "manufacturing", "medical", "education", "marketplace", "company",
    "owner", "marketing", "sales", "hr", "finance",
)

AI_TEMPLATES: list[dict[str, Any]] = [
    {"id": "ad_campaign", "title_ru": "Создать рекламную кампанию", "goal": "ads", "vertical": "marketing"},
    {"id": "reels", "title_ru": "Создать Reels", "goal": "video", "vertical": "marketing"},
    {"id": "banner", "title_ru": "Создать баннер", "goal": "image", "vertical": "marketing"},
    {"id": "presentation", "title_ru": "Создать презентацию", "goal": "presentation", "vertical": "company"},
    {"id": "commercial_offer", "title_ru": "Создать коммерческое предложение", "goal": "presentation", "vertical": "sales"},
    {"id": "contract", "title_ru": "Подготовить договор", "goal": "legal", "vertical": "legal"},
    {"id": "client_reply", "title_ru": "Ответить клиенту", "goal": "client_reply", "vertical": "crm"},
    {"id": "competitors", "title_ru": "Проанализировать конкурентов", "goal": "competitors", "vertical": "marketing"},
    {"id": "content_plan", "title_ru": "Создать контент-план", "goal": "content_plan", "vertical": "marketing"},
    {"id": "publish_series", "title_ru": "Создать серию публикаций", "goal": "content_plan", "vertical": "marketing"},
    {"id": "report", "title_ru": "Подготовить отчёт", "goal": "report", "vertical": "owner"},
    {"id": "beauty_promo", "title_ru": "Beauty: создать акцию", "goal": "beauty_promo", "vertical": "beauty"},
]

BLOCK_TYPES = (
    "start", "ai", "condition", "generation", "crm", "erp", "telegram",
    "email", "webhook", "approval", "memory", "finish",
)

def library() -> dict[str, Any]:
    return {
        "verticals": list(VERTICALS),
        "templates": list(AI_TEMPLATES),
        "blocks": list(BLOCK_TYPES),
    }

def get_template(template_id: str) -> dict[str, Any] | None:
    for t in AI_TEMPLATES:
        if t["id"] == template_id:
            return dict(t)
    return None

def templates_for_vertical(vertical: str) -> list[dict[str, Any]]:
    return [t for t in AI_TEMPLATES if t.get("vertical") == vertical or vertical in ("company", "owner")]
