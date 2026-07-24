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

def success_response(
    data: Any,
    *,
    meta: dict[str, Any] | None = None,
    pagination: dict[str, Any] | None = None,
    request_id: str | None = None,
) -> dict[str, Any]:
    return {
        "success": True,
        "data": data,
        "meta": meta or {},
        "pagination": pagination,
        "request_id": request_id or _id("req"),
        "timestamp": _now(),
    }


def error_response(
    *,
    error_code: str,
    message: str,
    details: dict[str, Any] | None = None,
    trace_id: str | None = None,
) -> dict[str, Any]:
    if not error_code or not message:
        raise ValidationError("error_code and message are required")
    return {
        "success": False,
        "error_code": error_code,
        "message": message,
        "details": details or {},
        "trace_id": trace_id or _id("trace"),
        "timestamp": _now(),
    }
