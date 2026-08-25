"""Serve the existing Enterprise Web production build from the API process.

This is not a second frontend. It exposes ``src/web/dist`` of the same app
so a single HTTPS origin can reach UI + ``/api`` + ``/management``.
"""

from __future__ import annotations

import os
from pathlib import Path

from aiohttp import web

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIST = ROOT / "src" / "web" / "dist"

_API_PREFIXES = (
    "/api/",
    "/management/",
    "/health",
    "/liveness",
    "/readiness",
    "/ready",
    "/metrics",
    "/system/",
    "/swagger",
    "/docs",
    "/redoc",
)


def web_dist_dir() -> Path:
    raw = (os.environ.get("ADOS_WEB_DIST") or "").strip()
    return Path(raw) if raw else DEFAULT_DIST


def serve_web_enabled() -> bool:
    flag = (os.environ.get("ADOS_SERVE_WEB") or "").strip().lower()
    if flag not in {"1", "true", "yes", "on"}:
        return False
    return (web_dist_dir() / "index.html").is_file()


def _is_api_path(path: str) -> bool:
    if path in {"/health", "/liveness", "/readiness", "/ready", "/metrics"}:
        return True
    return any(path == p.rstrip("/") or path.startswith(p) for p in _API_PREFIXES)


_SPA_CITY_PATHS = frozenset({"/city", "/city/"})


def prefers_html(request: web.Request) -> bool:
    """Browser navigations send text/html first; API clients send JSON."""
    accept = request.headers.get("Accept") or ""
    html_idx = accept.find("text/html")
    if html_idx < 0:
        return False
    json_idx = accept.find("application/json")
    return json_idx < 0 or html_idx < json_idx


def register_web_static(app: web.Application) -> None:
    dist = web_dist_dir()
    if not serve_web_enabled() or not (dist / "index.html").is_file():
        return
    assets = dist / "assets"
    if assets.is_dir():
        app.router.add_static("/assets", assets, append_version=False)

    async def spa_index(_request: web.Request) -> web.FileResponse:
        return web.FileResponse(dist / "index.html")

    app.router.add_get("/", spa_index)

    @web.middleware
    async def spa_city_html(request: web.Request, handler):
        # GET /city is also an authenticated city-runtime API. Browsers that
        # navigate there must receive the SPA; JSON clients keep the API.
        if (
            request.method in {"GET", "HEAD"}
            and request.path in _SPA_CITY_PATHS
            and prefers_html(request)
        ):
            return web.FileResponse(dist / "index.html")
        return await handler(request)

    @web.middleware
    async def spa_fallback(request: web.Request, handler):
        try:
            return await handler(request)
        except web.HTTPNotFound:
            if request.method in {"GET", "HEAD"} and not _is_api_path(request.path):
                return web.FileResponse(dist / "index.html")
            raise

    app.middlewares.append(spa_city_html)
    app.middlewares.append(spa_fallback)
