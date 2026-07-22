"""API handlers — Unified AI Ecosystem (Sprint 12.0)."""

from __future__ import annotations

from aiohttp import web

from applications.ecosystem import ai_ecosystem
from applications.ecosystem.api.middleware import json_response
from applications.ecosystem.shared.exceptions import NotFoundError, ValidationError


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


async def health_handler(request: web.Request) -> web.Response:
    return json_response(ai_ecosystem.health())


async def bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(ai_ecosystem.bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def registry_handler(request: web.Request) -> web.Response:
    return json_response(ai_ecosystem.manager.application_registry())


async def agents_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            return json_response({"agents": ai_ecosystem.ai.list_agents(), "status": ai_ecosystem.ai.status()})
        body = await _read_json(request)
        action = body.get("action", "collaborate")
        if action == "chief":
            return json_response(ai_ecosystem.ai.chief(query=body.get("query", ""), context=body.get("context")))
        if action == "register":
            return json_response(
                ai_ecosystem.ai.register_agent(
                    agent_id=body.get("agent_id", ""),
                    name=body.get("name", ""),
                    application=body.get("application", ""),
                    status=body.get("status", "active"),
                ),
                status=201,
            )
        return json_response(
            ai_ecosystem.ai.collaborate(query=body.get("query", ""), agents=body.get("agents"), context=body.get("context"))
        )
    except Exception as exc:
        return _handle_error(exc)


async def memory_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        action = body.get("action", "connect")
        if action == "put":
            return json_response(
                ai_ecosystem.memory.put(app_id=body.get("app_id", ""), key=body.get("key", ""), value=body.get("value"), engine=body.get("engine", "semantic_memory")),
                status=201,
            )
        if action == "connect_all":
            return json_response(ai_ecosystem.memory.connect_all(body.get("app_ids") or ai_ecosystem.config.registered_applications), status=201)
        return json_response(ai_ecosystem.memory.connect_application(app_id=body.get("app_id", ""), engines=body.get("engines")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def exchange_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            return json_response({"exchanges": ai_ecosystem.communication.list_exchanges(exchange_type=request.rel_url.query.get("type"))})
        body = await _read_json(request)
        return json_response(
            ai_ecosystem.communication.exchange(
                source_app=body.get("source_app", ""),
                target_app=body.get("target_app", ""),
                exchange_type=body.get("exchange_type", "events"),
                payload=body.get("payload"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def auth_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        action = body.get("action", "sso")
        if action == "org":
            return json_response(ai_ecosystem.identity.create_organization(name=body.get("name", "")), status=201)
        if action == "department":
            return json_response(ai_ecosystem.identity.create_department(org_id=body.get("org_id", ""), name=body.get("name", "")), status=201)
        if action == "team":
            return json_response(ai_ecosystem.identity.create_team(department_id=body.get("department_id", ""), name=body.get("name", "")), status=201)
        if action == "role":
            return json_response(ai_ecosystem.identity.grant_role(principal=body.get("principal", ""), role=body.get("role", "operator")), status=201)
        if action == "audit":
            return json_response({"audit": ai_ecosystem.identity.list_audit()})
        return json_response(
            ai_ecosystem.identity.sso_login(principal=body.get("principal", ""), provider=body.get("provider", "local"), role=body.get("role", "operator")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def dashboard_handler(request: web.Request) -> web.Response:
    return json_response(ai_ecosystem.dashboard.all_dashboards())


async def search_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        mode = body.get("mode", "global")
        query = body.get("query", "")
        if mode == "semantic":
            return json_response(ai_ecosystem.search.semantic_search(query=query))
        return json_response(ai_ecosystem.search.global_search(query=query))
    except Exception as exc:
        return _handle_error(exc)


async def settings_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            return json_response({"settings": ai_ecosystem.settings.list_settings()})
        body = await _read_json(request)
        return json_response(ai_ecosystem.settings.set(key=body.get("key", ""), value=body.get("value"), scope=body.get("scope", "global")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def notifications_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        if body.get("action") == "list":
            return json_response({"notifications": ai_ecosystem.notifications.list_for(body.get("recipient", ""))})
        return json_response(
            ai_ecosystem.notifications.notify(
                recipient=body.get("recipient", ""),
                title=body.get("title", ""),
                body=body.get("body", ""),
                app_id=body.get("app_id", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def events_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            return json_response({"events": ai_ecosystem.events.list_events(topic=request.rel_url.query.get("topic"))})
        body = await _read_json(request)
        return json_response(
            ai_ecosystem.events.publish(topic=body.get("topic", ""), source=body.get("source", "api"), payload=body.get("payload")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def gateway_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            return json_response(ai_ecosystem.gateway.catalog())
        body = await _read_json(request)
        return json_response(ai_ecosystem.gateway.route(app_id=body.get("app_id", ""), path=body.get("path", "/")))
    except Exception as exc:
        return _handle_error(exc)


async def knowledge_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            return json_response({"status": ai_ecosystem.knowledge.status(), "sources": ai_ecosystem.knowledge.discover_sources()})
        return json_response(ai_ecosystem.knowledge.build_graph(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def analytics_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        if body.get("action") == "kpis":
            return json_response(ai_ecosystem.analytics.kpis())
        return json_response(ai_ecosystem.analytics.report(report_type=body.get("report_type", "executive")), status=201)
    except Exception as exc:
        return _handle_error(exc)
