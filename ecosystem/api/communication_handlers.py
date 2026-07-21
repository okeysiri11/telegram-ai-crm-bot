# Communication API handlers — Sprint 7.2.

from __future__ import annotations

from aiohttp import web

from ecosystem import ecosystem
from ecosystem.api.middleware import error_response, json_response
from ecosystem.communication.models import EventCategory, MessagePriority, MessageType, SyncScope
from ecosystem.shared.exceptions import EcosystemError, NotFoundError, ValidationError


def _handle_error(exc: Exception) -> web.Response:
    if isinstance(exc, ValidationError):
        return error_response(str(exc), status=400)
    if isinstance(exc, NotFoundError):
        return error_response(str(exc), status=404)
    if isinstance(exc, EcosystemError):
        return error_response(str(exc), status=400)
    raise exc


async def communication_metrics_handler(_request: web.Request) -> web.Response:
    return json_response(ecosystem.engine.communication.metrics())


async def publish_event_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        category = EventCategory(data.get("category", "application"))
        event = await ecosystem.engine.communication.bus.publish(
            data["event_name"],
            data.get("payload", {}),
            category=category,
            source_application=data.get("source_application", ""),
            metadata=data.get("metadata"),
        )
        return json_response(event.to_dict(), status=201)
    except (KeyError, ValueError, EcosystemError) as exc:
        return _handle_error(exc if isinstance(exc, EcosystemError) else ValidationError(str(exc)))


async def list_events_handler(request: web.Request) -> web.Response:
    category_raw = request.query.get("category")
    category = EventCategory(category_raw) if category_raw else None
    source = request.query.get("source_application", "")
    events = ecosystem.engine.communication.bus.list_events(category=category, source_application=source)
    return json_response({"events": [e.to_dict() for e in events]})


async def replay_events_handler(request: web.Request) -> web.Response:
    since = float(request.query.get("since", "0") or 0)
    events = ecosystem.engine.communication.store.replay(since=since)
    return json_response({"events": [e.to_dict() for e in events], "stats": ecosystem.engine.communication.store.stats()})


async def send_message_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        message_type = MessageType(data.get("message_type", "direct"))
        priority = MessagePriority(data.get("priority", "normal"))
        envelope = await ecosystem.engine.communication.router.send(
            message_type=message_type,
            source_application=data["source_application"],
            target_application=data.get("target_application", ""),
            payload=data.get("payload", {}),
            topic=data.get("topic", ""),
            priority=priority,
            correlation_id=data.get("correlation_id", ""),
            headers=data.get("headers"),
        )
        return json_response(envelope.to_dict(), status=201)
    except (KeyError, ValueError, EcosystemError) as exc:
        return _handle_error(exc if isinstance(exc, EcosystemError) else ValidationError(str(exc)))


async def request_response_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        envelope = await ecosystem.engine.communication.router.request(
            data["source_application"],
            data["target_application"],
            data.get("payload", {}),
            topic=data.get("topic", "request"),
        )
        return json_response(envelope.to_dict(), status=201)
    except (KeyError, EcosystemError) as exc:
        return _handle_error(exc if isinstance(exc, EcosystemError) else ValidationError(str(exc)))


async def broadcast_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        envelope = await ecosystem.engine.communication.router.broadcast(
            data["source_application"],
            data.get("payload", {}),
            topic=data.get("topic", "broadcast"),
        )
        return json_response(envelope.to_dict(), status=201)
    except (KeyError, EcosystemError) as exc:
        return _handle_error(exc if isinstance(exc, EcosystemError) else ValidationError(str(exc)))


async def command_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        envelope = await ecosystem.engine.communication.router.command(
            data["source_application"],
            data["target_application"],
            data["command_name"],
            data.get("payload", {}),
        )
        return json_response(envelope.to_dict(), status=201)
    except (KeyError, EcosystemError) as exc:
        return _handle_error(exc if isinstance(exc, EcosystemError) else ValidationError(str(exc)))


async def query_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        envelope = await ecosystem.engine.communication.router.query(
            data["source_application"],
            data["target_application"],
            data["query_name"],
            data.get("payload", {}),
        )
        return json_response(envelope.to_dict(), status=201)
    except (KeyError, EcosystemError) as exc:
        return _handle_error(exc if isinstance(exc, EcosystemError) else ValidationError(str(exc)))


async def acknowledge_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        confirmation = ecosystem.engine.communication.router.acknowledge(data["message_id"], data["application_id"])
        return json_response(confirmation.to_dict())
    except (KeyError, EcosystemError) as exc:
        return _handle_error(exc if isinstance(exc, EcosystemError) else ValidationError(str(exc)))


async def dead_letters_handler(_request: web.Request) -> web.Response:
    letters = ecosystem.engine.communication.router.dead_letters()
    return json_response({"dead_letters": [e.to_dict() for e in letters]})


async def subscribe_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        sub = ecosystem.engine.communication.subscriptions.subscribe(
            data["application_id"],
            data["topic"],
            event_filter=data.get("event_filter", ""),
        )
        return json_response(sub.to_dict(), status=201)
    except (KeyError, EcosystemError) as exc:
        return _handle_error(exc if isinstance(exc, EcosystemError) else ValidationError(str(exc)))


async def list_subscriptions_handler(request: web.Request) -> web.Response:
    app_id = request.query.get("application_id", "")
    if app_id:
        subs = ecosystem.engine.communication.subscriptions.list_for_application(app_id)
    else:
        subs = ecosystem.engine.communication.subscriptions.list_all()
    return json_response({"subscriptions": [s.to_dict() for s in subs]})


async def register_application_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        result = await ecosystem.engine.communication.bridge.connect_application(
            data["application_id"],
            version=data.get("version", "1.0.0"),
            capabilities=data.get("capabilities"),
            endpoints=data.get("endpoints"),
            dependencies=data.get("dependencies"),
        )
        return json_response(result, status=201)
    except (KeyError, EcosystemError) as exc:
        return _handle_error(exc if isinstance(exc, EcosystemError) else ValidationError(str(exc)))


async def list_registry_handler(_request: web.Request) -> web.Response:
    apps = ecosystem.engine.communication.registry.list_applications()
    return json_response({"applications": [a.to_dict() for a in apps]})


async def registry_health_handler(_request: web.Request) -> web.Response:
    return json_response(ecosystem.engine.communication.registry.health_report())


async def dependency_graph_handler(_request: web.Request) -> web.Response:
    return json_response(ecosystem.engine.communication.registry.dependency_graph())


async def discover_capability_handler(request: web.Request) -> web.Response:
    capability = request.match_info["capability"]
    apps = ecosystem.engine.communication.registry.discover_capability(capability)
    return json_response({"capability": capability, "applications": [a.to_dict() for a in apps]})


async def sync_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        scope = SyncScope(data.get("scope", "context"))
        record = await ecosystem.engine.communication.sync.synchronize(
            scope,
            data.get("data", {}),
            source_application=data["source_application"],
            target_applications=data.get("target_applications"),
        )
        return json_response(record.to_dict(), status=201)
    except (KeyError, ValueError, EcosystemError) as exc:
        return _handle_error(exc if isinstance(exc, EcosystemError) else ValidationError(str(exc)))


async def sync_history_handler(request: web.Request) -> web.Response:
    source = request.query.get("source_application", "")
    history = ecosystem.engine.communication.sync.history(source_application=source)
    return json_response({"history": [h.to_dict() for h in history]})


async def share_context_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        context = await ecosystem.engine.communication.bridge.share_context(
            data["user_id"],
            data["application_id"],
            data.get("data", {}),
            shared_with=data.get("shared_with"),
        )
        return json_response(context.to_dict(), status=201)
    except (KeyError, EcosystemError) as exc:
        return _handle_error(exc if isinstance(exc, EcosystemError) else ValidationError(str(exc)))


async def delegate_agent_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        result = await ecosystem.engine.communication.bridge.delegate_task(
            data["source_application"],
            data["task_type"],
            data.get("payload", {}),
            target_agent=data.get("target_agent", ""),
        )
        return json_response(result)
    except (KeyError, EcosystemError) as exc:
        return _handle_error(exc if isinstance(exc, EcosystemError) else ValidationError(str(exc)))
