"""API handlers — Enterprise Communications & Notifications (Sprint 19.4)."""

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
    return enterprise_hub.communications


async def comm_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "enterprise_communications_ready": health.get("enterprise_communications_ready"),
            "notification_center_ready": health.get("notification_center_ready"),
            "multi_channel_delivery_ready": health.get("multi_channel_delivery_ready"),
            "corporate_chat_ready": health.get("corporate_chat_ready"),
            "suite": _suite().status(),
        }
    )


async def comm_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def comm_center_handler(request: web.Request) -> web.Response:
    try:
        center = _suite().center
        if request.method == "GET":
            return json_response(center.status())
        body = await _read_json(request)
        return json_response(
            center.publish(
                source=body.get("source", ""),
                event=body.get("event", ""),
                recipient=body.get("recipient", ""),
                subject=body.get("subject", ""),
                body=body.get("body", ""),
                channel=body.get("channel", ""),
                priority=body.get("priority", ""),
                template=body.get("template", ""),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def comm_router_handler(request: web.Request) -> web.Response:
    try:
        router = _suite().router
        if request.method == "GET":
            return json_response(router.status())
        body = await _read_json(request)
        action = body.get("action", "route")
        if action == "smart":
            return json_response(
                router.smart_route(
                    source=body.get("source", ""),
                    event=body.get("event", ""),
                    recipient=body.get("recipient", ""),
                    subject=body.get("subject", ""),
                    body=body.get("body", ""),
                    payload=body.get("payload") if isinstance(body.get("payload"), dict) else None,
                ),
                status=201,
            )
        return json_response(
            router.route(
                event_id=body.get("event_id", ""),
                fallback=bool(body.get("fallback", True)),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def comm_queue_handler(request: web.Request) -> web.Response:
    try:
        queue = _suite().queue
        if request.method == "GET":
            return json_response(queue.status())
        body = await _read_json(request)
        action = body.get("action", "enqueue")
        if action == "batch":
            return json_response({"items": queue.dequeue_batch(limit=int(body.get("limit", 10) or 10))}, status=201)
        if action == "status":
            return json_response(
                queue.set_status(queue_id=body.get("queue_id", ""), status=body.get("status", "pending")),
                status=201,
            )
        return json_response(
            queue.enqueue(
                event_id=body.get("event_id", ""),
                recipient=body.get("recipient", ""),
                channel=body.get("channel", "email"),
                priority=body.get("priority", "medium"),
                mode=body.get("mode", "fifo"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def comm_delivery_handler(request: web.Request) -> web.Response:
    try:
        delivery = _suite().delivery
        if request.method == "GET":
            return json_response(delivery.status())
        body = await _read_json(request)
        action = body.get("action", "track")
        if action == "delivered":
            return json_response(
                delivery.mark_delivered(
                    delivery_id=body.get("delivery_id", ""),
                    latency_ms=float(body.get("latency_ms", 0) or 0),
                ),
                status=201,
            )
        if action == "read":
            return json_response(delivery.mark_read(delivery_id=body.get("delivery_id", "")), status=201)
        if action == "retry":
            return json_response(
                delivery.retry(delivery_id=body.get("delivery_id", ""), error=body.get("error", "")),
                status=201,
            )
        return json_response(
            delivery.track(
                message_id=body.get("message_id", ""),
                recipient=body.get("recipient", ""),
                channel=body.get("channel", "email"),
                status=body.get("status", "pending"),
                latency_ms=float(body.get("latency_ms", 0) or 0),
                error=body.get("error", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def comm_priority_handler(request: web.Request) -> web.Response:
    try:
        priority = _suite().priority
        if request.method == "GET":
            return json_response(priority.status())
        body = await _read_json(request)
        return json_response(
            priority.classify(
                subject=body.get("subject", ""),
                event=body.get("event", ""),
                hint=body.get("hint", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def comm_templates_handler(request: web.Request) -> web.Response:
    try:
        templates = _suite().templates
        if request.method == "GET":
            return json_response(templates.status())
        body = await _read_json(request)
        action = body.get("action", "register")
        if action == "render":
            return json_response(
                templates.render(
                    template_id=body.get("template_id", ""),
                    kind=body.get("kind", ""),
                    variables=body.get("variables") if isinstance(body.get("variables"), dict) else None,
                    fmt=body.get("format", ""),
                ),
                status=201,
            )
        return json_response(
            templates.register(
                kind=body.get("kind", "crm"),
                name=body.get("name", ""),
                body=body.get("body", ""),
                fmt=body.get("format", "plain"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def comm_chat_handler(request: web.Request) -> web.Response:
    try:
        chat = _suite().chat
        if request.method == "GET":
            return json_response(chat.status())
        body = await _read_json(request)
        action = body.get("action", "send")
        if action == "ai_to_ai":
            return json_response(
                chat.ai_to_ai(
                    from_agent=body.get("from_agent", ""),
                    to_agent=body.get("to_agent", ""),
                    message=body.get("message", ""),
                ),
                status=201,
            )
        if action == "service_bus":
            return json_response(
                chat.service_bus(
                    from_service=body.get("from_service", ""),
                    to_service=body.get("to_service", ""),
                    message=body.get("message", ""),
                ),
                status=201,
            )
        return json_response(
            chat.send(
                from_party=body.get("from_party", ""),
                to_party=body.get("to_party", ""),
                message=body.get("message", ""),
                party_type=body.get("party_type", "employee"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def comm_audit_handler(request: web.Request) -> web.Response:
    try:
        audit = _suite().audit
        if request.method == "GET":
            return json_response(audit.status())
        body = await _read_json(request)
        return json_response(
            audit.record(
                sender=body.get("sender", ""),
                recipient=body.get("recipient", ""),
                route_id=body.get("route_id", ""),
                template=body.get("template", ""),
                status=body.get("status", ""),
                delivery_confirmed=bool(body.get("delivery_confirmed", False)),
                read_confirmed=bool(body.get("read_confirmed", False)),
                retries=int(body.get("retries", 0) or 0),
                detail=body.get("detail", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def comm_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dashboard = _suite().dashboard
        if request.method == "GET":
            return json_response(dashboard.status())
        body = await _read_json(request)
        return json_response(
            dashboard.render(dashboard_type=body.get("dashboard_type", "delivery")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
