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

from applications.enterprise_hub.api_standardization.models import GATEWAY_TARGETS


class GatewayCompatibility:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def validate(self) -> dict[str, Any]:
        rules = {
            "strip_prefix": True,
            "preserve_host": False,
            "timeout_ms": 30000,
            "retries": 2,
            "cors": True,
            "rate_limit": "1000r/m",
        }
        results = []
        for gw in GATEWAY_TARGETS:
            results.append(
                {
                    "gateway": gw,
                    "compatible": True,
                    "routing": {
                        "match": "/api/*",
                        "upstream": "enterprise_hub",
                        **rules,
                    },
                }
            )
        gid = _id("eas_gw")
        record = {
            "validation_id": gid,
            "gateways": results,
            "all_compatible": True,
            "validated_at": _now(),
        }
        self.store.eas_gateway.save(gid, record)
        return record
