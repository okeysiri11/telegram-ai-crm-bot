from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"

from applications.enterprise_hub.api_standardization.models import WS_CHANNELS


class WebSocketStandard:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def channels(self) -> dict[str, Any]:
        cid = _id("eas_ws")
        record = {
            "standard_id": cid,
            "channels": [
                {"name": ch, "path": f"/ws/v1/{ch}", "auth_required": True} for ch in WS_CHANNELS
            ],
            "protocol": "websocket",
            "built_at": _now(),
        }
        self.store.eas_ws_standards.save(cid, record)
        return record
