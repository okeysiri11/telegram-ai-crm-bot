"""Quick commands catalog (RU)."""

from __future__ import annotations

QUICK_COMMANDS: tuple[tuple[str, str], ...] = (
    ("create_client", "Создать клиента"),
    ("create_deal", "Создать сделку"),
    ("create_ads", "Создать рекламу"),
    ("create_image", "Создать изображение"),
    ("create_video", "Создать видео"),
    ("create_voice", "Создать голос"),
    ("create_doc", "Создать документ"),
    ("create_pres", "Создать презентацию"),
    ("create_workflow", "Создать Workflow"),
    ("run_agent", "Запустить AI Agent"),
)


def quick_labels() -> list[str]:
    return [label for _, label in QUICK_COMMANDS]
