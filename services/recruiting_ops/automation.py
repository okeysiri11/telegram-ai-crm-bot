"""Recruiting campaign automation foundation.

Spend-changing / destructive actions default to APPROVAL_REQUIRED.
"""

from __future__ import annotations

from typing import Any

RULE_TYPES = (
    "pause_if_cpl_exceeded",
    "notify_provider_degraded",
    "notify_spend_without_leads",
    "flag_falling_conversion",
    "reactivate_waiting_provider",
)

APPROVAL_REQUIRED_TYPES = {
    "pause_if_cpl_exceeded",
}


def _txt(value: Any) -> str:
    return str(value or "").strip()


def _num(value: Any) -> float | None:
    try:
        if value is None or str(value).strip() == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_rule(body: dict[str, Any]) -> dict[str, Any]:
    rule_type = _txt(body.get("rule_type") or body.get("type"))
    if rule_type not in RULE_TYPES:
        return {"ok": False, "error": "validation", "message_ru": "Неизвестный тип правила"}
    approval = body.get("approval_required")
    if approval is None:
        approval = True
    return {
        "ok": True,
        "item": {
            "rule_type": rule_type,
            "name": _txt(body.get("name")) or rule_type,
            "enabled": bool(body.get("enabled", True)),
            "approval_required": bool(approval),
            "threshold": _num(body.get("threshold")),
            "provider": _txt(body.get("provider")).lower() or None,
            "campaign_id": _txt(body.get("campaign_id")) or None,
            "reason": _txt(body.get("reason")) or None,
        },
    }


def evaluate_rule(rule: dict[str, Any], *, metrics: dict[str, Any], provider_health: dict[str, Any] | None = None) -> dict[str, Any]:
    rule_type = _txt(rule.get("rule_type"))
    triggered = False
    reason = ""
    if rule_type == "pause_if_cpl_exceeded":
        cpl = _num(metrics.get("cpl"))
        threshold = _num(rule.get("threshold"))
        triggered = cpl is not None and threshold is not None and cpl > threshold
        reason = f"CPL {cpl} превышает порог {threshold}" if triggered else "CPL в пределах порога"
    elif rule_type == "notify_provider_degraded":
        status = _txt((provider_health or {}).get("connection_status") or (provider_health or {}).get("status"))
        triggered = status in {"DEGRADED", "ERROR"}
        reason = f"Провайдер {status}" if triggered else "Провайдер в норме"
    elif rule_type == "notify_spend_without_leads":
        spend = _num(metrics.get("spend")) or 0
        leads = int(metrics.get("leads") or 0)
        triggered = spend > 0 and leads == 0
        reason = "Есть расход без лидов" if triggered else "Расход согласован с лидами или отсутствует"
    elif rule_type == "flag_falling_conversion":
        conv = _num(metrics.get("conversion"))
        prev = _num(metrics.get("previous_conversion"))
        triggered = conv is not None and prev is not None and prev > 0 and conv < prev
        reason = "Конверсия снижается" if triggered else "Конверсия не падает"
    elif rule_type == "reactivate_waiting_provider":
        triggered = _txt((provider_health or {}).get("connection_status")) == "CONNECTED"
        reason = "Провайдер подключен, WAITING_PROVIDER можно активировать" if triggered else "Провайдер не CONNECTED"
    result = "TRIGGERED" if triggered else "SKIPPED"
    if triggered and rule.get("approval_required"):
        result = "APPROVAL_REQUIRED"
    return {
        "triggered": triggered,
        "result": result,
        "reason": reason,
        "input_metrics": {k: metrics.get(k) for k in ("cpl", "spend", "leads", "conversion", "previous_conversion")},
        "approval_required": bool(rule.get("approval_required")),
        "auto_applied": False,
    }
