"""API handlers — Enterprise Documentation Platform (Sprint 21.6)."""

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
    return enterprise_hub.documentation_platform


async def edo_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "documentation_platform_ready": health.get("documentation_platform_ready"),
            "docs_registry_ready": health.get("docs_registry_ready"),
            "docs_search_ready": health.get("docs_search_ready"),
            "docs_publishing_ready": health.get("docs_publishing_ready"),
            "suite": _suite().status(),
        }
    )


async def edo_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def edo_docs_handler(request: web.Request) -> web.Response:
    try:
        suite = _suite()
        if request.method == "GET":
            items = suite.store.edo_docs.list_all()
            return json_response({"docs": len(items), "items": items})
        body = await _read_json(request)
        created = suite.register_doc(
            title=body.get("title", ""),
            category=body.get("category", "modules"),
            content=body.get("content", ""),
            version=body.get("version", enterprise_hub.config.application_version),
            channel=body.get("channel", "release_candidate"),
            module=body.get("module"),
            kind=body.get("kind"),
        )
        return json_response(created, status=201)
    except Exception as exc:
        return _handle_error(exc)


async def edo_search_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request) if request.method == "POST" else {}
        q = body.get("query") or request.rel_url.query.get("query", "")
        return json_response(
            _suite().search(
                query=q,
                category=body.get("category") or request.rel_url.query.get("category"),
                module=body.get("module") or request.rel_url.query.get("module"),
                version=body.get("version") or request.rel_url.query.get("version"),
                doc_type=body.get("type") or request.rel_url.query.get("type"),
            )
        )
    except Exception as exc:
        return _handle_error(exc)


async def edo_generate_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(_suite().generate(body.get("kind", "architecture")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def edo_publish_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        formats = body.get("formats") if isinstance(body.get("formats"), list) else None
        return json_response(_suite().publish(formats=formats), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def edo_quality_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().quality())
    except Exception as exc:
        return _handle_error(exc)


async def edo_dashboard_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().dashboard())
    except Exception as exc:
        return _handle_error(exc)
