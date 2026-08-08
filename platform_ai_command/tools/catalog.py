"""Tool catalog — unified AI tools for Command Center."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AiTool:
    id: str
    name_ru: str
    category: str
    modality: str
    hercules_backend: str = "pipeline"


TOOLS: tuple[AiTool, ...] = (
    AiTool("generate_image", "Генерация изображения", "creative", "image"),
    AiTool("generate_video", "Генерация видео", "creative", "video"),
    AiTool("generate_voice", "Генерация голоса", "creative", "voice"),
    AiTool("write_text", "Написание текста", "creative", "text"),
    AiTool("translate", "Перевод", "language", "text"),
    AiTool("ocr", "OCR", "document", "text"),
    AiTool("search", "Поиск", "knowledge", "text"),
    AiTool("analyze_document", "Анализ документов", "document", "document"),
    AiTool("create_presentation", "Создание презентаций", "document", "presentation"),
    AiTool("create_table", "Создание таблиц", "document", "text"),
    AiTool("crm_action", "Работа с CRM", "business", "text"),
    AiTool("erp_action", "Работа с ERP", "business", "text"),
    AiTool("knowledge_action", "Работа с Knowledge", "knowledge", "text"),
    AiTool("publish", "Публикация", "marketing", "ads"),
    AiTool("workflow", "Workflow", "automation", "workflow"),
)


def get_tool(tool_id: str) -> AiTool | None:
    for t in TOOLS:
        if t.id == tool_id:
            return t
    return None


def list_tools(*, category: str | None = None) -> list[AiTool]:
    if not category:
        return list(TOOLS)
    return [t for t in TOOLS if t.category == category]


def tool_ids() -> list[str]:
    return [t.id for t in TOOLS]
