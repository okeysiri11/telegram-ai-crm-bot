"""Corporate chat & internal service bus messaging."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class CorporateChat:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def send(
        self,
        *,
        from_party: str,
        to_party: str,
        message: str,
        party_type: str = "employee",
    ) -> dict[str, Any]:
        if not from_party or not to_party or not message:
            raise ValidationError("from_party, to_party, and message required")
        pt = party_type.lower().strip()
        if pt not in ("employee", "ai_agent", "service", "module"):
            raise ValidationError("party_type must be employee, ai_agent, service, or module")
        cid = _id("comm_chat")
        return self.store.comm_chat.save(
            cid,
            {
                "chat_id": cid,
                "from_party": from_party,
                "to_party": to_party,
                "message": message,
                "party_type": pt,
                "at": _now(),
            },
        )

    def ai_to_ai(self, *, from_agent: str, to_agent: str, message: str) -> dict[str, Any]:
        return self.send(
            from_party=from_agent,
            to_party=to_agent,
            message=message,
            party_type="ai_agent",
        )

    def service_bus(self, *, from_service: str, to_service: str, message: str) -> dict[str, Any]:
        return self.send(
            from_party=from_service,
            to_party=to_service,
            message=message,
            party_type="service",
        )

    def status(self) -> dict[str, Any]:
        return {"messages": self.store.comm_chat.count()}
