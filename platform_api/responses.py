# Typed API response envelope (frozen v1).

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from aiohttp import web
from pydantic import BaseModel, Field

from platform_api.contracts import API_CONTRACT_VERSION, PLATFORM_API_VERSION
from platform_api.errors import ErrorResponse


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_request_id() -> str:
    return str(uuid.uuid4())


class ApiEnvelope(BaseModel):
    """Standard success/error envelope for all v1 endpoints."""

    success: bool
    timestamp: str
    request_id: str
    api_version: str = PLATFORM_API_VERSION
    contract_version: str = API_CONTRACT_VERSION
    data: Any = None
    errors: list[str] = Field(default_factory=list)

    def to_json_response(self, *, status: int = 200) -> web.Response:
        return web.json_response(self.model_dump(), status=status)


def success_response(
    data: Any,
    *,
    request_id: str | None = None,
    status: int = 200,
) -> web.Response:
    envelope = ApiEnvelope(
        success=True,
        timestamp=utc_now_iso(),
        request_id=request_id or new_request_id(),
        data=data,
        errors=[],
    )
    return envelope.to_json_response(status=status)


def error_response(
    errors: list[str] | str,
    *,
    request_id: str | None = None,
    status: int = 400,
    data: Any = None,
) -> web.Response:
    err_list = [errors] if isinstance(errors, str) else list(errors)
    parsed = ErrorResponse.from_messages(err_list)
    envelope = ApiEnvelope(
        success=False,
        timestamp=utc_now_iso(),
        request_id=request_id or new_request_id(),
        data=data,
        errors=[e.message for e in parsed.errors],
    )
    return envelope.to_json_response(status=status)
