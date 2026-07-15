# AI Manager — conversational lead qualification and routing.

from __future__ import annotations

import json
import logging
import re
from typing import Any

from openrouter import _call_openrouter

logger = logging.getLogger(__name__)

AI_MANAGER_INTENTS = frozenset({
    "BUY_CAR",
    "SELL_CAR",
    "LEASING",
    "INSURANCE",
    "CREDIT",
    "LOGISTICS",
    "LEGAL",
    "SERVICE",
    "OTHER",
})

AI_MANAGER_SYSTEM = """
You are an automotive CRM AI assistant for a Telegram marketplace.
Analyze the user message and return ONLY valid JSON with keys:
lead_score (0-100 int), priority (LOW|MEDIUM|HIGH), department (string),
intent (one of: BUY_CAR, SELL_CAR, LEASING, INSURANCE, CREDIT, LOGISTICS, LEGAL, SERVICE, OTHER),
sentiment (positive|neutral|negative), urgency (low|medium|high),
missing_fields (array of strings), reply (short helpful Russian response to user).
Do not wrap JSON in markdown.
"""


class AiManagerEngineV1:
    @staticmethod
    async def qualify_message(
        user_message: str,
        *,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        context_block = json.dumps(context or {}, ensure_ascii=False)
        messages = [
            {"role": "system", "content": AI_MANAGER_SYSTEM.strip()},
            {
                "role": "user",
                "content": f"Context: {context_block}\n\nUser: {user_message}",
            },
        ]
        try:
            raw = await _call_openrouter(messages)
            parsed = AiManagerEngineV1._parse_json(raw)
            return AiManagerEngineV1._normalize(parsed, fallback_reply=raw[:500])
        except Exception:
            logger.warning("AI Manager qualification failed", exc_info=True)
            return AiManagerEngineV1._fallback(user_message)

    @staticmethod
    async def chat(
        user_message: str,
        *,
        history: list[dict[str, str]] | None = None,
        context: dict[str, Any] | None = None,
    ) -> str:
        result = await AiManagerEngineV1.qualify_message(user_message, context=context)
        return str(result.get("reply") or "Спасибо за сообщение. Менеджер свяжется с вами.")

    @staticmethod
    def _parse_json(raw: str) -> dict[str, Any]:
        text = raw.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        return json.loads(text)

    @staticmethod
    def _normalize(parsed: dict[str, Any], *, fallback_reply: str) -> dict[str, Any]:
        intent = str(parsed.get("intent", "OTHER")).upper()
        if intent not in AI_MANAGER_INTENTS:
            intent = "OTHER"
        priority = str(parsed.get("priority", "MEDIUM")).upper()
        if priority not in {"LOW", "MEDIUM", "HIGH"}:
            priority = "MEDIUM"
        try:
            lead_score = int(parsed.get("lead_score", 50))
        except (TypeError, ValueError):
            lead_score = 50
        lead_score = max(0, min(100, lead_score))
        return {
            "lead_score": lead_score,
            "priority": priority,
            "department": str(parsed.get("department") or "GENERAL"),
            "intent": intent,
            "sentiment": str(parsed.get("sentiment") or "neutral"),
            "urgency": str(parsed.get("urgency") or "medium"),
            "missing_fields": list(parsed.get("missing_fields") or []),
            "reply": str(parsed.get("reply") or fallback_reply),
        }

    @staticmethod
    def _fallback(user_message: str) -> dict[str, Any]:
        lowered = user_message.lower()
        intent = "OTHER"
        department = "GENERAL"
        if any(w in lowered for w in ("куп", "buy", "поиск")):
            intent, department = "BUY_CAR", "SALES"
        elif any(w in lowered for w in ("прод", "sell")):
            intent, department = "SELL_CAR", "SALES"
        elif "страх" in lowered or "insurance" in lowered:
            intent, department = "INSURANCE", "INSURANCE"
        elif "кредит" in lowered or "credit" in lowered:
            intent, department = "CREDIT", "CREDIT"
        elif "лизинг" in lowered or "leasing" in lowered:
            intent, department = "LEASING", "LEASING"
        elif "логист" in lowered:
            intent, department = "LOGISTICS", "LOGISTICS"
        elif "юрид" in lowered or "legal" in lowered:
            intent, department = "LEGAL", "LEGAL"
        elif "сервис" in lowered or "сто" in lowered:
            intent, department = "SERVICE", "SERVICE"
        return {
            "lead_score": 60,
            "priority": "MEDIUM",
            "department": department,
            "intent": intent,
            "sentiment": "neutral",
            "urgency": "medium",
            "missing_fields": [],
            "reply": "Спасибо! Я передал запрос менеджеру. Уточните марку, бюджет и город для более точного подбора.",
        }
