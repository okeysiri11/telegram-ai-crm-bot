"""API handlers — Enterprise Developer Platform (Sprint 20.6)."""

from __future__ import annotations

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
    return enterprise_hub.developer_platform


async def sdp_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "developer_platform_ready": health.get("developer_platform_ready"),
            "plugin_framework_ready": health.get("plugin_framework_ready"),
            "sdk_ready": health.get("sdk_ready"),
            "marketplace_ready": health.get("marketplace_ready"),
            "suite": _suite().status(),
        }
    )


async def sdp_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def sdp_plugins_handler(request: web.Request) -> web.Response:
    try:
        suite = _suite()
        if request.method == "GET":
            return json_response({"plugins": suite.registry.list_all(), **suite.registry.status()})
        body = await _read_json(request)
        return json_response(
            suite.plugins.install_from_manifest(
                plugin_id=body.get("plugin_id", ""),
                name=body.get("name", ""),
                version=body.get("version", "1.0.0"),
                kind=body.get("kind", "plugin"),
                author=body.get("author", "bidex"),
                description=body.get("description", ""),
                dependencies=body.get("dependencies") if isinstance(body.get("dependencies"), list) else None,
                permissions=body.get("permissions") if isinstance(body.get("permissions"), list) else None,
                activate=bool(body.get("activate", True)),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def sdp_lifecycle_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        action = (body.get("action") or "activate").lower()
        plugin_id = body.get("plugin_id", "")
        lc = _suite().lifecycle
        if action == "activate":
            return json_response(lc.activate(plugin_id=plugin_id), status=201)
        if action == "disable":
            return json_response(lc.disable(plugin_id=plugin_id), status=201)
        if action == "hot_reload":
            return json_response(lc.hot_reload(plugin_id=plugin_id), status=201)
        if action == "rollback":
            return json_response(lc.rollback(plugin_id=plugin_id, to_version=body.get("to_version", "")), status=201)
        raise ValidationError(f"unknown action: {action}")
    except Exception as exc:
        return _handle_error(exc)


async def sdp_extensions_handler(request: web.Request) -> web.Response:
    try:
        suite = _suite()
        if request.method == "GET":
            return json_response(suite.extensions.status())
        body = await _read_json(request)
        return json_response(
            suite.extensions.extend(
                plugin_id=body.get("plugin_id", ""),
                point=body.get("point", ""),
                label=body.get("label", ""),
                handler=body.get("handler", "default"),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def sdp_sdk_handler(request: web.Request) -> web.Response:
    try:
        suite = _suite()
        if request.method == "GET":
            return json_response(suite.sdk.describe())
        body = await _read_json(request)
        return json_response(
            suite.sdk.call(
                surface=body.get("surface", "crm"),
                method=body.get("method", ""),
                plugin_id=body.get("plugin_id", "system"),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def sdp_marketplace_handler(request: web.Request) -> web.Response:
    try:
        suite = _suite()
        if request.method == "GET":
            q = request.rel_url.query.get("q", "")
            tag = request.rel_url.query.get("tag")
            return json_response({"listings": suite.marketplace.search(query=q, tag=tag), **suite.marketplace.status()})
        body = await _read_json(request)
        action = (body.get("action") or "publish").lower()
        if action == "publish":
            return json_response(
                suite.publisher.publish(
                    package_id=body.get("package_id", ""),
                    name=body.get("name", ""),
                    version=body.get("version", "1.0.0"),
                    author=body.get("author", "bidex"),
                    description=body.get("description", ""),
                    tags=body.get("tags") if isinstance(body.get("tags"), list) else None,
                ),
                status=201,
            )
        if action == "install":
            return json_response(suite.installer.install_listing(listing_id=body.get("listing_id", "")), status=201)
        raise ValidationError(f"unknown action: {action}")
    except Exception as exc:
        return _handle_error(exc)


async def sdp_packages_handler(request: web.Request) -> web.Response:
    try:
        suite = _suite()
        if request.method == "GET":
            return json_response(suite.packages.status())
        body = await _read_json(request)
        action = (body.get("action") or "install").lower()
        if action == "install":
            return json_response(
                suite.packages.install(
                    package_id=body.get("package_id", ""),
                    name=body.get("name", ""),
                    version=body.get("version", "1.0.0"),
                ),
                status=201,
            )
        if action == "update":
            return json_response(
                suite.packages.update(package_id=body.get("package_id", ""), version=body.get("version", "")),
                status=201,
            )
        if action == "rollback":
            return json_response(suite.packages.rollback(package_id=body.get("package_id", "")), status=201)
        if action == "verify":
            return json_response(suite.packages.verify_integrity(package_id=body.get("package_id", "")), status=201)
        raise ValidationError(f"unknown action: {action}")
    except Exception as exc:
        return _handle_error(exc)


async def sdp_console_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().console())
    except Exception as exc:
        return _handle_error(exc)


async def sdp_analytics_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().analytics())
    except Exception as exc:
        return _handle_error(exc)


async def sdp_docs_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().generate_sdk_docs())
    except Exception as exc:
        return _handle_error(exc)
