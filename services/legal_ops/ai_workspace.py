"""Legal Ops AI workspace — Sprint Lawyer 3.2.

Single service layer for AI-анализ and AI-юрист.
Uses platform_ai MockAIProvider when available; never invents external law sources.
No fake OCR — images without a vision pipeline are flagged honestly.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any

ANALYSIS_ACTIONS: list[dict[str, str]] = [
    {"id": "summarize", "label_ru": "Кратко объяснить"},
    {"id": "risks", "label_ru": "Найти юридические риски"},
    {"id": "deadlines", "label_ru": "Найти важные сроки"},
    {"id": "review_contract", "label_ru": "Проверить договор"},
    {"id": "obligations", "label_ru": "Выделить обязательства сторон"},
    {"id": "contradictions", "label_ru": "Найти противоречия"},
    {"id": "compare", "label_ru": "Сравнить документы"},
    {"id": "action_plan", "label_ru": "Подготовить план действий"},
    {"id": "client_questions", "label_ru": "Подготовить вопросы клиенту"},
]

LAWYER_MODES: list[dict[str, str]] = [
    {"id": "consult", "label_ru": "Консультация"},
    {"id": "draft_document", "label_ru": "Создать документ"},
    {"id": "review_document", "label_ru": "Проверить документ"},
    {"id": "position", "label_ru": "Подготовить позицию"},
    {"id": "case_plan", "label_ru": "План дела"},
    {"id": "compare", "label_ru": "Сравнить документы"},
    {"id": "research", "label_ru": "Исследование"},
]

DRAFT_KINDS: list[dict[str, str]] = [
    {"id": "contract", "label_ru": "Договор"},
    {"id": "addendum", "label_ru": "Дополнительное соглашение"},
    {"id": "claim", "label_ru": "Претензия"},
    {"id": "claim_response", "label_ru": "Ответ на претензию"},
    {"id": "application", "label_ru": "Заявление"},
    {"id": "request", "label_ru": "Запрос"},
    {"id": "letter", "label_ru": "Письмо"},
    {"id": "receipt", "label_ru": "Расписка"},
    {"id": "power_of_attorney", "label_ru": "Доверенность"},
    {"id": "lawsuit_draft", "label_ru": "Иск / процессуальный документ (проект)"},
    {"id": "custom", "label_ru": "Пользовательский документ"},
]

DOC_STATUSES = {
    "ai_draft": "AI Draft",
    "in_review": "На проверке",
    "approved": "Одобрено",
    "archived": "Архив",
}

UNVERIFIED = "Источник не подтвержден"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def empty_structured() -> dict[str, Any]:
    return {
        "summary": "",
        "facts": [],
        "key_terms": [],
        "risks": [],
        "deadlines": [],
        "obligations": [],
        "contradictions": [],
        "missing_data": [],
        "sources": [],
        "recommended_actions": [],
        "disclaimer": "AI-анализ. Не является юридической консультацией и не заменяет проверку юристом.",
    }


def _date_candidates(text: str) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for m in re.finditer(r"\b(\d{1,2}[./]\d{1,2}[./]\d{2,4}|\d{4}-\d{2}-\d{2})\b", text or ""):
        out.append({"date": m.group(1), "context": text[max(0, m.start() - 40) : m.end() + 40].strip()})
    return out[:12]


def build_structured_analysis(
    *,
    action: str,
    question: str,
    context_text: str,
    target_type: str,
    target_id: str | None,
    provider_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Deterministic structured analysis (mockable LLM layer can refine later)."""
    result = empty_structured()
    ctx = (context_text or "").strip()
    q = (question or "").strip()
    action_label = next((a["label_ru"] for a in ANALYSIS_ACTIONS if a["id"] == action), action)
    dates = _date_candidates(ctx + "\n" + q)

    result["summary"] = (
        f"{action_label}: по материалам «{target_type}» сформирован рабочий вывод для проверки юристом."
    )
    if ctx:
        result["facts"] = [f"Фрагмент контекста ({min(len(ctx), 240)} симв.): {ctx[:240]}…"] if len(ctx) > 240 else [f"Контекст: {ctx}"]
    else:
        result["facts"] = ["Контекст объекта пуст или недоступен."]
        result["missing_data"].append("Текст/содержание объекта для анализа")

    if action in {"risks", "review_contract", "summarize"}:
        result["risks"] = [
            "Неясность ответственности сторон — требует ручной проверки.",
            "Возможны скрытые сроки и штрафы — сверить с полным текстом.",
        ]
    if action in {"deadlines", "summarize", "action_plan", "review_contract"}:
        result["deadlines"] = dates or [{"date": "", "note": "Явных дат в предоставленном тексте не найдено."}]
    if action in {"obligations", "review_contract", "summarize"}:
        result["obligations"] = [
            "Обязательства сторон нужно подтвердить по полному тексту документа.",
            "Проверить порядок оплаты, поставки/услуг и расторжения.",
        ]
    if action in {"contradictions", "compare"}:
        result["contradictions"] = [
            "Автоматическое сравнение ограничено доступным контекстом; противоречия не подтверждены без второго источника.",
        ]
        result["missing_data"].append("Второй документ для сравнения" if action == "compare" else "")
    if action in {"key_terms", "review_contract", "summarize"} or True:
        result["key_terms"] = [
            "Предмет / стороны / сроки / ответственность — проверить в оригинале.",
        ]
    if action == "client_questions":
        result["recommended_actions"] = [
            "Уточнить у клиента цели и допустимые сроки.",
            "Запросить полный комплект приложений к договору/делу.",
            "Подтвердить полномочия подписанта.",
        ]
    elif action == "action_plan":
        result["recommended_actions"] = [
            "Зафиксировать найденные сроки в задачах/календаре.",
            "Назначить ответственного юриста.",
            "Подготовить перечень недостающих документов.",
        ]
    else:
        result["recommended_actions"] = [
            "Сохранить анализ в деле.",
            "При необходимости создать задачу или событие календаря.",
            "Передать спорные пункты AI-юристу для проекта документа.",
        ]

    result["missing_data"] = [x for x in result["missing_data"] if x]
    result["sources"] = [
        {
            "kind": "internal",
            "label_ru": "Внутренние данные Legal Ops",
            "target_type": target_type,
            "target_id": target_id,
            "verified": True if ctx else False,
            "note": None if ctx else UNVERIFIED,
        },
        {
            "kind": "external_legal",
            "label_ru": "Внешние юридические источники",
            "verified": False,
            "note": "В Sprint 3.2 внешние госреестры не подключены. " + UNVERIFIED,
        },
    ]
    result["provider"] = provider_meta or {"provider": "legal_ops_deterministic", "model": "rules-v1", "mocked": True}
    result["action"] = action
    result["question"] = q
    return result


def build_draft_body(*, kind: str, prompt: str, context_text: str, client_name: str | None, case_title: str | None) -> str:
    kind_label = next((k["label_ru"] for k in DRAFT_KINDS if k["id"] == kind), kind)
    lines = [
        f"# {kind_label} (AI Draft)",
        "",
        "Статус: AI Draft — требует проверки юристом. Не является финальным юридическим документом.",
        "",
        f"Клиент: {client_name or '—'}",
        f"Дело: {case_title or '—'}",
        "",
        "## Запрос",
        prompt or "—",
        "",
        "## Проект текста",
        "",
    ]
    if kind == "claim":
        lines += [
            "Претензия",
            "",
            "Настоящим направляем претензию в связи с нарушением обязательств.",
            "Просим в срок 10 (десяти) календарных дней устранить нарушения / исполнить обязательства.",
            "",
            "Основание: материалы дела и предоставленный контекст (внутренние документы).",
        ]
    elif kind == "contract":
        lines += [
            "1. Предмет договора",
            "2. Права и обязанности сторон",
            "3. Сроки и порядок расчётов",
            "4. Ответственность",
            "5. Заключительные положения",
        ]
    else:
        lines += [
            f"Проект «{kind_label}» подготовлен по запросу пользователя.",
            "Заполните реквизиты сторон и приложите первичные документы перед согласованием.",
        ]
    if context_text:
        lines += ["", "## Контекст (фрагмент)", context_text[:1200]]
    lines += ["", "—", "Источник внешних норм права: " + UNVERIFIED]
    return "\n".join(lines)


def extract_plain_text_from_bytes(filename: str, mime_type: str | None, data: bytes) -> dict[str, Any]:
    """Honest extraction: text files OK; images need vision; no fake OCR."""
    name = (filename or "").lower()
    mime = (mime_type or "").lower()
    if mime.startswith("text/") or name.endswith(".txt") or name.endswith(".md"):
        try:
            return {"ok": True, "text": data.decode("utf-8", errors="replace"), "method": "text"}
        except Exception:
            return {"ok": False, "text": "", "method": "text", "message_ru": "Не удалось прочитать текст"}
    if "pdf" in mime or name.endswith(".pdf"):
        # Best-effort: extract readable ASCII fragments only — not a full PDF parser.
        raw = data.decode("latin-1", errors="ignore")
        chunks = re.findall(r"[\x20-\x7EА-Яа-яЁё]{4,}", raw)
        text = " ".join(chunks[:200]).strip()
        if text:
            return {"ok": True, "text": text[:8000], "method": "pdf_heuristic", "limited": True}
        return {
            "ok": False,
            "text": "",
            "method": "pdf_heuristic",
            "message_ru": "Текст PDF не извлечён. Загрузите текстовую версию или вставьте текст вручную.",
        }
    if mime.startswith("image/") or name.endswith((".jpg", ".jpeg", ".png", ".webp")):
        return {
            "ok": False,
            "text": "",
            "method": "vision_required",
            "needs_vision": True,
            "message_ru": "Для изображений требуется OCR/vision pipeline. Фиктивный OCR не выполняется.",
        }
    if name.endswith((".doc", ".docx")) or "word" in mime:
        return {
            "ok": False,
            "text": "",
            "method": "office",
            "message_ru": "Автоизвлечение DOC/DOCX в Legal Ops ограничено. Вставьте текст или используйте текстовую выгрузку.",
        }
    return {"ok": False, "text": "", "method": "unknown", "message_ru": "Формат не поддерживается для извлечения текста"}


async def maybe_llm_complete(prompt: str) -> dict[str, Any]:
    """Use platform_ai MockAIProvider when available; never call flaky live APIs in default mode."""
    try:
        from platform_ai.provider_base import AIRequest, MockAIProvider

        provider = MockAIProvider()
        req = AIRequest(prompt=prompt, messages=[{"role": "user", "content": prompt}])
        # MockAIProvider.complete may be sync or async depending on version
        complete = provider.complete
        resp = complete(req, model_id="mock")
        if hasattr(resp, "__await__"):
            resp = await resp  # type: ignore[misc]
        text = getattr(resp, "text", None) or getattr(resp, "content", None) or str(resp)
        return {"ok": True, "text": text, "provider": "mock", "model": "mock", "mocked": True}
    except Exception as exc:
        return {"ok": False, "text": "", "provider": "none", "error": str(exc), "mocked": True}
