"""API helpers for Recruiting Ops."""

from __future__ import annotations

from aiohttp import web


def json_response(data, *, status: int = 200) -> web.Response:
    return web.json_response(data, status=status)
