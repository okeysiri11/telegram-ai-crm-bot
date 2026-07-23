"""API handlers — Enterprise Hub Foundation (Sprint 19.0)."""

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


async def health_handler(request: web.Request) -> web.Response:
    return json_response(enterprise_hub.health())


async def bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(enterprise_hub.bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def registry_handler(request: web.Request) -> web.Response:
    try:
        registry = enterprise_hub.registry
        if request.method == "GET":
            return json_response(registry.status())
        body = await _read_json(request)
        action = body.get("action", "platform")
        if action == "service":
            return json_response(
                registry.register_service(
                    name=body.get("name", ""),
                    platform=body.get("platform", ""),
                    endpoint=body.get("endpoint", ""),
                ),
                status=201,
            )
        if action == "module":
            return json_response(
                registry.register_module(
                    name=body.get("name", ""),
                    platform=body.get("platform", ""),
                    sprint=body.get("sprint", ""),
                ),
                status=201,
            )
        if action == "integration":
            return json_response(
                registry.register_integration(
                    source=body.get("source", ""),
                    target=body.get("target", ""),
                    protocol=body.get("protocol", "event_bus"),
                ),
                status=201,
            )
        if action == "organization":
            return json_response(
                registry.register_organization(
                    name=body.get("name", ""),
                    org_code=body.get("org_code", ""),
                    jurisdiction=body.get("jurisdiction", ""),
                ),
                status=201,
            )
        if action == "environment":
            return json_response(
                registry.register_environment(
                    name=body.get("name", ""),
                    env_type=body.get("env_type", "production"),
                    profile=body.get("profile", ""),
                ),
                status=201,
            )
        return json_response(
            registry.register_platform(
                name=body.get("name", ""),
                version=body.get("version", "1.0"),
                status=body.get("status", "connected"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def integration_handler(request: web.Request) -> web.Response:
    try:
        integration = enterprise_hub.integration
        if request.method == "GET":
            return json_response(integration.status())
        body = await _read_json(request)
        action = body.get("action", "gateway")
        if action == "discover":
            return json_response(
                integration.discover(
                    service_name=body.get("service_name", ""),
                    platform=body.get("platform", ""),
                ),
                status=201,
            )
        if action == "route":
            return json_response(
                integration.route_request(
                    path=body.get("path", ""),
                    method=body.get("method", "GET"),
                    target_platform=body.get("target_platform", ""),
                ),
                status=201,
            )
        if action == "aggregate":
            return json_response(
                integration.aggregate(
                    label=body.get("label", ""),
                    responses=body.get("responses") if isinstance(body.get("responses"), list) else None,
                ),
                status=201,
            )
        if action == "bus":
            return json_response(
                integration.publish_bus(
                    topic=body.get("topic", ""),
                    message=body.get("message") if isinstance(body.get("message"), dict) else None,
                    source=body.get("source", "hub"),
                ),
                status=201,
            )
        return json_response(
            integration.gateway(
                path=body.get("path", ""),
                method=body.get("method", "GET"),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else None,
                target_platform=body.get("target_platform", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def identity_handler(request: web.Request) -> web.Response:
    try:
        identity = enterprise_hub.identity
        if request.method == "GET":
            return json_response(identity.status())
        body = await _read_json(request)
        action = body.get("action", "identity")
        if action == "org_map":
            return json_response(
                identity.map_organization(
                    hub_org_id=body.get("hub_org_id", ""),
                    platform=body.get("platform", ""),
                    external_org_id=body.get("external_org_id", ""),
                ),
                status=201,
            )
        if action == "user":
            return json_response(
                identity.register_user(
                    username=body.get("username", ""),
                    identity_id=body.get("identity_id", ""),
                    platforms=body.get("platforms") if isinstance(body.get("platforms"), list) else None,
                ),
                status=201,
            )
        if action == "role_map":
            return json_response(
                identity.map_role(
                    hub_role=body.get("hub_role", ""),
                    platform=body.get("platform", ""),
                    platform_role=body.get("platform_role", ""),
                ),
                status=201,
            )
        if action == "permission_sync":
            return json_response(
                identity.sync_permissions(
                    platform=body.get("platform", ""),
                    permissions=body.get("permissions") if isinstance(body.get("permissions"), list) else None,
                ),
                status=201,
            )
        return json_response(
            identity.register_identity(
                subject=body.get("subject", ""),
                identity_type=body.get("identity_type", "user"),
                platforms=body.get("platforms") if isinstance(body.get("platforms"), list) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def configuration_handler(request: web.Request) -> web.Response:
    try:
        configuration = enterprise_hub.configuration
        if request.method == "GET":
            return json_response(configuration.status())
        body = await _read_json(request)
        action = body.get("action", "global")
        if action == "feature_flag":
            return json_response(
                configuration.set_feature_flag(
                    name=body.get("name", ""),
                    enabled=bool(body.get("enabled", False)),
                    scope=body.get("scope", "global"),
                ),
                status=201,
            )
        if action == "platform_setting":
            return json_response(
                configuration.set_platform_setting(
                    platform=body.get("platform", ""),
                    key=body.get("key", ""),
                    value=body.get("value"),
                ),
                status=201,
            )
        if action == "profile":
            return json_response(
                configuration.register_profile(
                    name=body.get("name", ""),
                    env_type=body.get("env_type", "production"),
                    settings=body.get("settings") if isinstance(body.get("settings"), dict) else None,
                ),
                status=201,
            )
        if action == "registry":
            return json_response(
                configuration.register_config(
                    name=body.get("name", ""),
                    category=body.get("category", "general"),
                    payload=body.get("payload") if isinstance(body.get("payload"), dict) else None,
                ),
                status=201,
            )
        return json_response(
            configuration.set_global(key=body.get("key", ""), value=body.get("value")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def events_handler(request: web.Request) -> web.Response:
    try:
        events = enterprise_hub.events
        if request.method == "GET":
            return json_response(events.status())
        body = await _read_json(request)
        action = body.get("action", "publish")
        if action == "register":
            return json_response(
                events.register_event_type(
                    name=body.get("name", ""),
                    kind=body.get("kind", "domain"),
                    schema=body.get("schema", ""),
                ),
                status=201,
            )
        if action == "replay":
            return json_response(events.replay(event_id=body.get("event_id", "")), status=201)
        return json_response(
            events.publish(
                event_type=body.get("event_type", ""),
                source=body.get("source", ""),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else None,
                fail=bool(body.get("fail", False)),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def dashboard_handler(request: web.Request) -> web.Response:
    try:
        dashboard = enterprise_hub.dashboard
        if request.method == "GET":
            dtype = request.rel_url.query.get("dashboard_type", "overview")
            return json_response(dashboard.render(dashboard_type=dtype))
        body = await _read_json(request)
        return json_response(
            dashboard.render(dashboard_type=body.get("dashboard_type", "overview")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def knowledge_handler(request: web.Request) -> web.Response:
    try:
        knowledge = enterprise_hub.knowledge
        if request.method == "GET":
            return json_response(knowledge.status())
        body = await _read_json(request)
        return json_response(
            knowledge.publish(
                base=body.get("base", "enterprise"),
                key=body.get("key", ""),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
