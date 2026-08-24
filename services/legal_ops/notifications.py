"""Legal Ops → ADOS notifications bridge — Lawyer 3.5.

Stores org-scoped notification rows for Lawyer inbox deep-links and
publishes GenericPlatformEvent. Does NOT create a second notification subsystem.
Never logs document contents or OAuth secrets.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

CHANGE_MESSAGES_RU = {
    "hearing": "Назначено новое судебное заседание",
    "document": "Обнаружен новый документ",
    "status": "Изменился статус дела",
    "enforcement": "Изменено исполнительное производство",
    "deadline": "Приближается срок",
    "other": "Обнаружено изменение",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def message_for_change(change_type: str | None) -> str:
    return CHANGE_MESSAGES_RU.get(str(change_type or "other"), CHANGE_MESSAGES_RU["other"])


def deeplink_for_change(organization_id: str, change: dict[str, Any]) -> str:
    cid = change.get("id") or ""
    case_id = change.get("case_id") or ""
    if case_id:
        return f"/workspace/legal?view=monitoring&change={cid}&case={case_id}"
    return f"/workspace/legal?view=monitoring&change={cid}"


async def emit_legal_change_notification(
    service: Any,
    *,
    organization_id: str,
    change: dict[str, Any],
    role: str | None = None,
) -> dict[str, Any] | None:
    """Create Lawyer notification row + platform event + best-effort NotificationCenter push."""
    org = organization_id or "default"
    title = message_for_change(change.get("change_type"))
    summary = str(change.get("summary") or change.get("title") or title)
    deeplink = deeplink_for_change(org, change)
    item = {
        "id": str(uuid.uuid4()),
        "organization_id": org,
        "tenant_id": org,
        "title": title,
        "message": summary,
        "change_type": change.get("change_type"),
        "change_id": change.get("id"),
        "case_id": change.get("case_id"),
        "client_id": change.get("client_id"),
        "watchlist_id": change.get("watchlist_id"),
        "deeplink": deeplink,
        "read_at": None,
        "created_at": _now(),
        "payload": {
            "provider": change.get("provider"),
            "source_label": change.get("source_label"),
        },
    }
    bag = service._bag(org)
    bag.setdefault("notifications", []).insert(0, item)
    try:
        await service._activity(
            organization_id=org,
            entity_type="notification",
            entity_id=item["id"],
            action="LEGAL_NOTIFICATION_CREATED",
            summary=title,
            role=role,
            payload={"change_id": change.get("id"), "deeplink": deeplink},
        )
    except Exception as exc:
        logger.debug("legal notification activity skipped: %s", exc)

    # Platform event bus (typed)
    try:
        from events.generic_events import GenericPlatformEvent
        from events.publisher import publish

        event = GenericPlatformEvent(
            name="LEGAL_MONITOR_CHANGE",
            source="legal_ops",
            module="legal",
            entity_type="monitor_change",
            entity_id=str(change.get("id") or ""),
            payload={
                "organization_id": org,
                "change_id": change.get("id"),
                "change_type": change.get("change_type"),
                "case_id": change.get("case_id"),
                "title": title,
                "deeplink": deeplink,
            },
        )
        await publish(event)
    except Exception as exc:
        logger.debug("legal monitor event publish skipped: %s", exc)

    # Reuse NotificationCenter (push stub / telegram if configured) — no secrets
    try:
        from services.notification_center import NotificationCenterV1

        body = f"{title}\n{summary}\nОткрыть: {deeplink}"
        await NotificationCenterV1.send(
            channel="push",
            to=org,
            subject=title,
            body=body[:500],
            metadata={"module": "legal", "change_id": change.get("id"), "deeplink": deeplink},
        )
    except Exception as exc:
        logger.debug("NotificationCenter push skipped: %s", exc)

    return item
