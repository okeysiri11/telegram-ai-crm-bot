# Admin platform SDK routes — /api/v1/verticals

from __future__ import annotations

import logging

from aiohttp import web

logger = logging.getLogger(__name__)


async def verticals_list_handler(request: web.Request) -> web.Response:
    from platform_sdk.vertical_registry import vertical_registry

    items = []
    for entry in vertical_registry.list():
        code = entry["code"]
        try:
            cls = vertical_registry.get(code)
            items.append({**entry, **cls.vertical_metadata()})
        except Exception:
            items.append(entry)

    return web.json_response({"verticals": items, "count": len(items)})


def register_platform_sdk_routes(app: web.Application) -> None:
    app.router.add_get("/api/v1/verticals", verticals_list_handler)
    logger.info("platform_sdk_routes_registered")
