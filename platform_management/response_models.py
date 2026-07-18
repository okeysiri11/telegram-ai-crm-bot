# Standard Management API response envelope — delegates to frozen platform_api contracts.

from __future__ import annotations

from typing import Any

from aiohttp import web

from platform_api.responses import (
    ApiEnvelope,
    error_response as _error_response,
    new_request_id,
    success_response as _success_response,
    utc_now_iso,
)

__all__ = [
    "ApiEnvelope",
    "error_response",
    "new_request_id",
    "success_response",
    "utc_now_iso",
]


def success_response(
    data: Any,
    *,
    request_id: str | None = None,
    status: int = 200,
) -> web.Response:
    return _success_response(data, request_id=request_id, status=status)


def error_response(
    errors: list[str] | str,
    *,
    request_id: str | None = None,
    status: int = 400,
    data: Any = None,
) -> web.Response:
    return _error_response(errors, request_id=request_id, status=status, data=data)
