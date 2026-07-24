"""API handlers — Extension SDK (Sprint 25.0)."""

from __future__ import annotations

import uuid

from aiohttp import web

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.middleware import json_response
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError


async def _read_json(request: web.Request) -> dict:
    try:
        data = await request.json()
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _handle_error(exc: Exception) -> web.Response:
    if isinstance(exc, NotFoundError):
        return json_response({"error": str(exc)}, status=404)
    if isinstance(exc, ValidationError):
        return json_response({"error": str(exc)}, status=400)
    return json_response({"error": str(exc)}, status=500)


def _suite():
    return enterprise_hub.extension_sdk


async def ees_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "extension_sdk_ready": health.get("extension_sdk_ready"),
            "marketplace_foundation_ready": health.get("marketplace_foundation_ready"),
            "extension_permissions_ready": health.get("extension_permissions_ready"),
            "extension_lifecycle_ready": health.get("extension_lifecycle_ready"),
            "suite": _suite().status(),
        }
    )


async def ees_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ees_register_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().register(
                extension_id=body.get("extension_id") or f"ext_{uuid.uuid4().hex[:8]}",
                name=body.get("name", ""),
                version=body.get("version", "1.0.0"),
                author=body.get("author", ""),
                publisher=body.get("publisher", ""),
                industry=body.get("industry", "general"),
                extension_type=body.get("extension_type", "industry_module"),
                dependencies=body.get("dependencies"),
                required_permissions=body.get("required_permissions"),
                compatibility=body.get("compatibility"),
                signature=body.get("signature"),
                status=body.get("status", "draft"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ees_extensions_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().list_extensions())
    except Exception as exc:
        return _handle_error(exc)


async def ees_scaffold_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().scaffold(
                extension_type=body.get("extension_type", "industry_module"),
                name=body.get("name", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ees_permissions_request_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().request_permissions(
                extension_id=body.get("extension_id", ""),
                scopes=body.get("scopes") or body.get("required_permissions") or [],
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ees_permissions_decide_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().decide_permissions(
                extension_id=body.get("extension_id", ""),
                actor=body.get("actor", ""),
                action=body.get("action", ""),
                scopes=body.get("scopes") or [],
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ees_verify_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().verify(
                extension_id=body.get("extension_id", ""),
                fail_check=body.get("fail_check"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ees_lifecycle_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().transition(
                extension_id=body.get("extension_id", ""),
                to_status=body.get("to_status", body.get("status", "")),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ees_install_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().install(
                extension_id=body.get("extension_id", ""),
                allow_unsigned=bool(body.get("allow_unsigned", False)),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ees_update_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().update(
                extension_id=body.get("extension_id", ""),
                to_version=body.get("to_version", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ees_uninstall_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(_suite().uninstall(extension_id=body.get("extension_id", "")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ees_rollback_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().rollback(
                extension_id=body.get("extension_id", ""),
                to_version=body.get("to_version", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ees_marketplace_list_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().marketplace_list(
                extension_id=body.get("extension_id", ""),
                category=body.get("category", "templates"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ees_marketplace_catalog_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().marketplace_catalog())
    except Exception as exc:
        return _handle_error(exc)


async def ees_public_api_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().public_call(method=body.get("method", ""), payload=body.get("payload")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
