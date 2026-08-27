"""LIVE campaign writes require explicit human approval. No autonomous spend changes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from services.recruiting_ops.provider_contract import adapter_result
from services.recruiting_ops.provider_live import live_list_campaigns, live_write_campaign

WRITE_ACTIONS = ("pause", "resume", "budget")
PENDING = "ACTION_PENDING_APPROVAL"
APPROVED = "APPROVED"
REJECTED = "REJECTED"
APPLIED = "APPLIED"
FAILED = "FAILED"


def _txt(value: Any) -> str:
    return str(value or "").strip()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def propose_write(body: dict[str, Any]) -> dict[str, Any]:
    action = _txt(body.get("action") or body.get("recommendation")).lower()
    if action not in WRITE_ACTIONS:
        return {"ok": False, "error": "validation", "message_ru": "Допустимы pause, resume или budget."}
    return {
        "ok": True,
        "item": {
            "action": action,
            "provider": _txt(body.get("provider")).lower() or None,
            "campaign_id": _txt(body.get("campaign_id") or body.get("external_id")) or None,
            "budget": body.get("budget"),
            "status": PENDING,
            "approval_required": True,
            "reason": _txt(body.get("reason")) or "Изменение live-кампании.",
            "created_at": _now(),
            "live_applied": False,
        },
    }


def apply_approved_write(item: dict[str, Any], *, decision: str) -> dict[str, Any]:
    value = _txt(decision).upper()
    if value in {"REJECT", "REJECTED"}:
        return {"ok": True, "item": {**item, "status": REJECTED, "live_applied": False, "decided_at": _now()}}
    if value not in {"APPROVE", "APPROVED"}:
        return {"ok": False, "error": "validation", "message_ru": "Нужно Approve или Reject."}
    if _txt(item.get("status")).upper() not in {PENDING, APPROVED}:
        return {"ok": False, "error": "validation", "message_ru": "Нет ожидающего согласования."}
    result = live_write_campaign(
        _txt(item.get("provider")),
        _txt(item.get("action")),
        campaign_id=_txt(item.get("campaign_id")),
        budget=item.get("budget"),
    )
    readback = None
    if result.get("ok"):
        listed = live_list_campaigns(_txt(item.get("provider")))
        readback = next((row for row in listed.get("items") or [] if str(row.get("id")) == str(item.get("campaign_id"))), None)
    return {
        "ok": bool(result.get("ok")),
        "item": {
            **item,
            "status": APPLIED if result.get("ok") else FAILED,
            "live_applied": bool(result.get("ok")),
            "decided_at": _now(),
            "provider_result": {k: result.get(k) for k in ("ok", "error", "error_code", "status", "message_ru") if k in result},
            "readback": readback,
        },
        "adapter": result,
    }


def reject_unapproved() -> dict[str, Any]:
    return adapter_result(ok=False, error="APPROVAL_REQUIRED", message_ru="Live-изменение кампании без согласования запрещено.")
