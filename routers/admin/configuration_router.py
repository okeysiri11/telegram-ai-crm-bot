# Admin configuration REST routes — /api/v1/configuration/*

from __future__ import annotations

import logging

from aiohttp import web

logger = logging.getLogger(__name__)


async def configuration_list_handler(request: web.Request) -> web.Response:
    from platform_configuration.config_provider import config_provider
    from platform_configuration.config_schema import ConfigSection

    section = request.query.get("section")
    if section:
        try:
            sec = ConfigSection(section)
        except ValueError:
            return web.json_response({"error": f"Unknown section: {section}"}, status=400)
        data = config_provider.get_section(sec)
    else:
        data = config_provider.snapshot()
    return web.json_response({"section": section, "configuration": data})


async def configuration_get_handler(request: web.Request) -> web.Response:
    from platform_configuration.config_service import configuration_service

    key = request.match_info["key"]
    value = await configuration_service.get(key)
    return web.json_response({"key": key, "value": value})


async def configuration_set_handler(request: web.Request) -> web.Response:
    from platform_configuration.config_service import (
        ConfigurationPermissionError,
        configuration_service,
    )
    from platform_configuration.config_validator import ConfigValidationError

    key = request.match_info["key"]
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    value = body.get("value")
    changed_by = body.get("changed_by")
    reason = body.get("reason")
    actor_telegram_id = body.get("actor_telegram_id")

    try:
        result = await configuration_service.set(
            key,
            value,
            changed_by=changed_by,
            reason=reason,
            actor_telegram_id=actor_telegram_id,
        )
    except ConfigurationPermissionError as exc:
        return web.json_response({"error": str(exc)}, status=403)
    except ConfigValidationError as exc:
        return web.json_response({"error": str(exc)}, status=400)

    return web.json_response(result)


async def configuration_export_handler(request: web.Request) -> web.Response:
    from platform_configuration.config_service import configuration_service

    payload = await configuration_service.export()
    return web.json_response(payload)


def register_configuration_admin_routes(app: web.Application) -> None:
    app.router.add_get("/api/v1/configuration", configuration_list_handler)
    app.router.add_get("/api/v1/configuration/export", configuration_export_handler)
    app.router.add_get("/api/v1/configuration/{key:.+}", configuration_get_handler)
    app.router.add_put("/api/v1/configuration/{key:.+}", configuration_set_handler)
    logger.info("configuration_admin_routes_registered")
