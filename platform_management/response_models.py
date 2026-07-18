# Standard Management API response envelope.

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from aiohttp import web


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_request_id() -> str:
    return str(uuid.uuid4())


def success_response(
    data: Any,
    *,
    request_id: str | None = None,
    status: int = 200,
) -> web.Response:
    payload = {
        "success": True,
        "timestamp": utc_now_iso(),
        "request_id": request_id or new_request_id(),
        "data": data,
        "errors": [],
    }
    return web.json_response(payload, status=status)


def error_response(
    errors: list[str] | str,
    *,
    request_id: str | None = None,
    status: int = 400,
    data: Any = None,
) -> web.Response:
    err_list = [errors] if isinstance(errors, str) else list(errors)
    payload = {
        "success": False,
        "timestamp": utc_now_iso(),
        "request_id": request_id or new_request_id(),
        "data": data,
        "errors": err_list,
    }
    return web.json_response(payload, status=status)
