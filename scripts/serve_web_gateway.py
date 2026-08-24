#!/usr/bin/env python3
"""Same-origin public gateway for the existing Enterprise Web + local API.

Serves ``src/web/dist`` and proxies ``/api``, ``/management`` and health
routes to the running ADOS API (default 127.0.0.1:8080).

This is not a second frontend or backend.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

from aiohttp import ClientSession, ClientTimeout, TCPConnector, web

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.bind import client_max_size_bytes  # noqa: E402
from api.web_static import web_dist_dir  # noqa: E402

logger = logging.getLogger("web_gateway")
PROXY_ROOTS = (
    "/api",
    "/management",
    "/health",
    "/liveness",
    "/readiness",
    "/ready",
    "/metrics",
    "/system",
)


def _should_proxy(path: str) -> bool:
    return any(path == root or path.startswith(root + "/") for root in PROXY_ROOTS)


async def _proxy(request: web.Request) -> web.StreamResponse:
    target = request.app["proxy_target"].rstrip("/")
    url = f"{target}{request.path_qs}"
    session: ClientSession = request.app["session"]
    headers = {k: v for k, v in request.headers.items() if k.lower() not in {"host", "content-length"}}
    body = await request.read()
    async with session.request(
        request.method,
        url,
        headers=headers,
        data=body or None,
        allow_redirects=False,
    ) as upstream:
        out = web.StreamResponse(status=upstream.status, reason=upstream.reason)
        for key, value in upstream.headers.items():
            if key.lower() in {"transfer-encoding", "content-encoding", "content-length"}:
                continue
            out.headers[key] = value
        await out.prepare(request)
        async for chunk in upstream.content.iter_chunked(64 * 1024):
            await out.write(chunk)
        await out.write_eof()
        return out


def _spa(dist: Path):
    async def index(_request: web.Request) -> web.FileResponse:
        return web.FileResponse(dist / "index.html")

    return index


def build_app(dist: Path, proxy_target: str) -> web.Application:
    app = web.Application(client_max_size=client_max_size_bytes())
    app["proxy_target"] = proxy_target
    app.router.add_get("/", _spa(dist))
    assets = dist / "assets"
    if assets.is_dir():
        app.router.add_static("/assets", assets, append_version=False)

    async def catch_all(request: web.Request) -> web.StreamResponse:
        if _should_proxy(request.path):
            return await _proxy(request)
        if request.method in {"GET", "HEAD"}:
            return web.FileResponse(dist / "index.html")
        raise web.HTTPNotFound()

    app.router.add_route("*", "/{path:.*}", catch_all)

    async def on_start(_app: web.Application) -> None:
        _app["session"] = ClientSession(
            timeout=ClientTimeout(total=120),
            connector=TCPConnector(limit=64, force_close=True),
        )

    async def on_stop(_app: web.Application) -> None:
        session = _app.get("session")
        if session:
            await session.close()

    app.on_startup.append(on_start)
    app.on_cleanup.append(on_stop)
    return app


async def _run(host: str, port: int, dist: Path, proxy_target: str) -> None:
    app = build_app(dist, proxy_target)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    logger.info("web gateway http://%s:%s → %s (dist=%s)", host, port, proxy_target, dist)
    stop = asyncio.Event()
    try:
        await stop.wait()
    finally:
        await runner.cleanup()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser(description="ADOS same-origin web gateway")
    parser.add_argument("--host", default=os.environ.get("ADOS_GATEWAY_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("ADOS_GATEWAY_PORT", "4173")))
    parser.add_argument("--proxy", default=os.environ.get("ADOS_GATEWAY_PROXY", "http://127.0.0.1:8080"))
    parser.add_argument("--dist", default="")
    args = parser.parse_args()
    dist = Path(args.dist) if args.dist else web_dist_dir()
    if not (dist / "index.html").is_file():
        raise SystemExit(f"frontend production build missing: {dist}/index.html (run npm run build --prefix src/web)")
    try:
        asyncio.run(_run(args.host, args.port, dist, args.proxy.rstrip("/")))
    except KeyboardInterrupt:
        raise SystemExit(0)


if __name__ == "__main__":
    main()
