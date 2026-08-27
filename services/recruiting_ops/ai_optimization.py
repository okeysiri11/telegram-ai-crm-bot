"""AI campaign optimization — advisory only. No live spend writes."""

from __future__ import annotations

from typing import Any

RECOMMENDATION_TYPES = (
    "increase_budget",
    "decrease_budget",
    "pause_campaign",
    "change_targeting",
    "change_creative",
    "change_source_allocation",
)

AI_LIVE_WRITE_ACCESS = False


def _txt(value: Any) -> str:
    return str(value or "").strip()


def _num(value: Any) -> float | None:
    try:
        if value is None or str(value).strip() == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def build_recommendation(body: dict[str, Any], *, metrics: dict[str, Any] | None = None) -> dict[str, Any]:
    rec = _txt(body.get("recommendation") or body.get("type"))
    if rec not in RECOMMENDATION_TYPES:
        return {"ok": False, "error": "validation", "message_ru": "Неизвестный тип рекомендации"}
    data = metrics or {}
    return {
        "ok": True,
        "item": {
            "recommendation": rec,
            "reason": _txt(body.get("reason")) or "Анализ воронки Recruiting без live-метрик провайдера.",
            "supporting_metrics": {
                "leads": data.get("leads"),
                "qualified": data.get("qualified"),
                "interviews": data.get("interviews"),
                "hires": data.get("hires"),
                "spend": data.get("spend"),
                "impressions": data.get("impressions"),
                "clicks": data.get("clicks"),
                "cpl": data.get("cpl"),
                "cost_per_qualified": data.get("cost_per_qualified"),
                "cost_per_interview": data.get("cost_per_interview"),
                "cost_per_hire": data.get("cost_per_hire"),
                "live_provider_metrics": bool(data.get("spend") is not None or data.get("impressions") is not None),
            },
            "confidence": _num(body.get("confidence")) if body.get("confidence") is not None else 0.4,
            "expected_impact": _txt(body.get("expected_impact")) or "Требует проверки человеком.",
            "risk": _txt(body.get("risk")) or "Изменение расхода без live-данных провайдера.",
            "provider": _txt(body.get("provider")).lower() or None,
            "campaign_id": _txt(body.get("campaign_id")) or None,
            "advisory_only": True,
            "live_write_access": AI_LIVE_WRITE_ACCESS,
            "status": "PENDING",
        },
    }


def apply_human_decision(item: dict[str, Any], decision: str) -> dict[str, Any]:
    value = _txt(decision).upper()
    if value not in {"APPROVE", "REJECT", "APPROVED", "REJECTED"}:
        return {"ok": False, "error": "validation", "message_ru": "Решение должно быть Approve или Reject"}
    status = "APPROVED" if value in {"APPROVE", "APPROVED"} else "REJECTED"
    return {
        "ok": True,
        "item": {
            **item,
            "status": status,
            "live_applied": False,
            "advisory_only": True,
            "live_write_access": False,
        },
    }
