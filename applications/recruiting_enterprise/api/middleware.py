"""API helpers for Recruiting Ops."""

from __future__ import annotations

from aiohttp import web


def json_response(data, *, status: int = 200, retry_after: int | None = None) -> web.Response:
    headers = {"Retry-After": str(retry_after)} if retry_after is not None else None
    return web.json_response(data, status=status, headers=headers)
