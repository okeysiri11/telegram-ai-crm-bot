# Admin configuration REST routes — /api/v1/configuration/*

from __future__ import annotations

import logging

from aiohttp import web

logger = logging.getLogger(__name__)


async def _body_actor(request: web.Request) -> tuple[dict, int | None]:
    try:
        body = await request.json()
    except Exception:
        body = {}
    actor = body.get("actor_telegram_id")
    if actor is not None:
        try:
            return body, int(actor)
        except (TypeError, ValueError):
            return body, None
    return body, None


async def configuration_list_handler(request: web.Request) -> web.Response:
    from platform_configuration.config_provider import config_provider
    from platform_configuration.config_schema import ConfigSection
    from platform_configuration.config_service import (
        ConfigurationPermissionError,
        configuration_service,
    )

    actor_raw = request.query.get("actor_telegram_id")
    actor_id = int(actor_raw) if actor_raw else None
    try:
        await configuration_service._check_read_permission(actor_telegram_id=actor_id)
    except ConfigurationPermissionError as exc:
        return web.json_response({"error": str(exc)}, status=403)

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
    from platform_configuration.config_service import (
        ConfigurationPermissionError,
        configuration_service,
    )

    key = request.match_info["key"]
    actor_raw = request.query.get("actor_telegram_id")
    actor_id = int(actor_raw) if actor_raw else None
    try:
        value = await configuration_service.get(key, actor_telegram_id=actor_id)
    except ConfigurationPermissionError as exc:
        return web.json_response({"error": str(exc)}, status=403)
    return web.json_response({"key": key, "value": value})


async def configuration_set_handler(request: web.Request) -> web.Response:
    from platform_configuration.config_service import (
        ConfigurationPermissionError,
        configuration_service,
    )
    from platform_configuration.config_validator import ConfigValidationError

    key = request.match_info["key"]
    body, actor_from_body = await _body_actor(request)

    value = body.get("value")
    changed_by = body.get("changed_by")
    reason = body.get("reason")
    actor_telegram_id = actor_from_body

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


async def configuration_delete_handler(request: web.Request) -> web.Response:
    from platform_configuration.config_service import (
        ConfigurationPermissionError,
        configuration_service,
    )

    key = request.match_info["key"]
    body, actor_from_body = await _body_actor(request)
    try:
        result = await configuration_service.delete(
            key,
            changed_by=body.get("changed_by"),
            reason=body.get("reason"),
            actor_telegram_id=actor_from_body,
        )
    except ConfigurationPermissionError as exc:
        return web.json_response({"error": str(exc)}, status=403)

    if result is None:
        return web.json_response({"error": "Key not found"}, status=404)
    return web.json_response(result)


async def configuration_rollback_handler(request: web.Request) -> web.Response:
    from platform_configuration.config_service import (
        ConfigurationPermissionError,
        configuration_service,
    )

    key = request.match_info["key"]
    body, actor_from_body = await _body_actor(request)
    version = body.get("version")
    if version is None:
        return web.json_response({"error": "version is required"}, status=400)
    try:
        version_int = int(version)
    except (TypeError, ValueError):
        return web.json_response({"error": "version must be an integer"}, status=400)

    try:
        result = await configuration_service.rollback(
            key,
            version_int,
            changed_by=body.get("changed_by"),
            reason=body.get("reason"),
            actor_telegram_id=actor_from_body,
        )
    except ConfigurationPermissionError as exc:
        return web.json_response({"error": str(exc)}, status=403)

    if result is None:
        return web.json_response({"error": "Version not found"}, status=404)
    return web.json_response(result)


async def configuration_history_handler(request: web.Request) -> web.Response:
    from platform_configuration.config_service import (
        ConfigurationPermissionError,
        configuration_service,
    )

    key = request.match_info["key"]
    actor_raw = request.query.get("actor_telegram_id")
    actor_id = int(actor_raw) if actor_raw else None
    limit_raw = request.query.get("limit", "50")
    try:
        limit = int(limit_raw)
    except ValueError:
        limit = 50

    try:
        await configuration_service._check_read_permission(actor_telegram_id=actor_id)
        history = await configuration_service.get_history(key, limit=limit)
    except ConfigurationPermissionError as exc:
        return web.json_response({"error": str(exc)}, status=403)

    return web.json_response({"key": key, "history": history})


async def configuration_validate_handler(request: web.Request) -> web.Response:
    from platform_configuration.config_service import configuration_service
    from platform_configuration.config_validator import ConfigValidationError

    body, _ = await _body_actor(request)
    payload = body.get("payload")
    try:
        result = await configuration_service.validate(payload)
    except ConfigValidationError as exc:
        return web.json_response({"valid": False, "error": str(exc)}, status=400)
    return web.json_response(result)


async def configuration_import_handler(request: web.Request) -> web.Response:
    from platform_configuration.config_service import (
        ConfigurationPermissionError,
        configuration_service,
    )
    from platform_configuration.config_validator import ConfigValidationError

    body, actor_from_body = await _body_actor(request)
    payload = body.get("payload") or body
    try:
        result = await configuration_service.import_config(
            payload,
            changed_by=body.get("changed_by"),
            reason=body.get("reason"),
            actor_telegram_id=actor_from_body,
        )
    except ConfigurationPermissionError as exc:
        return web.json_response({"error": str(exc)}, status=403)
    except ConfigValidationError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    return web.json_response(result)


async def configuration_export_handler(request: web.Request) -> web.Response:
    from platform_configuration.config_service import (
        ConfigurationPermissionError,
        configuration_service,
    )

    actor_raw = request.query.get("actor_telegram_id")
    actor_id = int(actor_raw) if actor_raw else None
    try:
        await configuration_service._check_read_permission(actor_telegram_id=actor_id)
        payload = await configuration_service.export()
    except ConfigurationPermissionError as exc:
        return web.json_response({"error": str(exc)}, status=403)
    return web.json_response(payload)


def register_configuration_admin_routes(app: web.Application) -> None:
    app.router.add_get("/api/v1/configuration", configuration_list_handler)
    app.router.add_get("/api/v1/configuration/export", configuration_export_handler)
    app.router.add_post("/api/v1/configuration/validate", configuration_validate_handler)
    app.router.add_post("/api/v1/configuration/import", configuration_import_handler)
    app.router.add_get("/api/v1/configuration/{key:.+}/history", configuration_history_handler)
    app.router.add_post("/api/v1/configuration/{key:.+}/rollback", configuration_rollback_handler)
    app.router.add_get("/api/v1/configuration/{key:.+}", configuration_get_handler)
    app.router.add_put("/api/v1/configuration/{key:.+}", configuration_set_handler)
    app.router.add_delete("/api/v1/configuration/{key:.+}", configuration_delete_handler)
    logger.info("configuration_admin_routes_registered")
