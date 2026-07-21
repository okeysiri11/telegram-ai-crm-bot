# Portal / Mobile / Partner / Notification API — Sprint 8.7.

from __future__ import annotations

from aiohttp import web

from applications.agro_marketplace import agro_marketplace
from applications.agro_marketplace.api.middleware import error_response, json_response
from applications.agro_marketplace.portal.models import (
    CalendarEvent,
    Message,
    MessageThread,
    PartnerConnection,
    PartnerType,
    PortalKind,
    PortalUser,
    SharedDocument,
    WebhookSubscription,
)
from applications.agro_marketplace.shared.exceptions import NotFoundError, ValidationError


async def portal_health_handler(_request: web.Request) -> web.Response:
    return json_response(
        {
            "portal_engine": agro_marketplace.config.portal_engine,
            "application_version": agro_marketplace.config.application_version,
            "portal": agro_marketplace.portal_engine.metrics(),
            "notifications": agro_marketplace.notification_center.metrics(),
        }
    )


async def portal_register_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        user = await agro_marketplace.portal_engine.register_user(
            PortalUser(
                email=data.get("email", ""),
                display_name=data.get("display_name", ""),
                role=data.get("role", "farmer"),
                phone=data.get("phone", ""),
                organization_id=data.get("organization_id", ""),
            )
        )
        return json_response(user.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def portal_build_handler(request: web.Request) -> web.Response:
    kind = request.match_info["kind"]
    user_id = request.query.get("user_id", "")
    try:
        view = await agro_marketplace.portal_engine.build_portal(PortalKind(kind), user_id=user_id)
        return json_response(view.to_dict())
    except ValueError:
        return error_response(f"unknown portal kind: {kind}", status=400)


async def portal_assistant_handler(request: web.Request) -> web.Response:
    data = await request.json()
    result = await agro_marketplace.portal_engine.assistant(
        data.get("message", ""),
        role=data.get("role", "farmer"),
        user_id=data.get("user_id", ""),
    )
    return json_response(result)


async def mobile_auth_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        result = await agro_marketplace.mobile_engine.authenticate(
            email=data.get("email", ""),
            display_name=data.get("display_name", ""),
            role=data.get("role", "farmer"),
            device_id=data.get("device_id", ""),
            platform=data.get("platform", "ios"),
            access_token=data.get("access_token", ""),
        )
        return json_response(result, status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def mobile_profile_handler(request: web.Request) -> web.Response:
    try:
        user = agro_marketplace.mobile_engine.profile(request.match_info["user_id"])
        return json_response(user.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def mobile_home_handler(request: web.Request) -> web.Response:
    try:
        return json_response(agro_marketplace.mobile_engine.home(request.match_info["user_id"]))
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def mobile_assistant_handler(request: web.Request) -> web.Response:
    data = await request.json()
    result = await agro_marketplace.mobile_engine.assistant(
        data.get("message", ""),
        user_id=data.get("user_id", ""),
        role=data.get("role", "farmer"),
    )
    return json_response(result)


async def mobile_products_handler(_request: web.Request) -> web.Response:
    items = agro_marketplace.product_catalog.list_products()
    return json_response({"items": [p.to_dict() for p in items]})


async def mobile_orders_handler(_request: web.Request) -> web.Response:
    items = agro_marketplace.orders.list_orders()
    return json_response({"items": [o.to_dict() for o in items]})


async def mobile_notifications_handler(request: web.Request) -> web.Response:
    user_id = request.match_info["user_id"]
    return json_response(
        {"items": [n.to_dict() for n in agro_marketplace.notification_center.inbox(user_id)]}
    )


async def mobile_analytics_handler(_request: web.Request) -> web.Response:
    return json_response(agro_marketplace.analytics.dashboard_metrics())


async def mobile_documents_handler(request: web.Request) -> web.Response:
    user_id = request.query.get("user_id")
    items = agro_marketplace.portal_engine.documents.list_shared(user_id=user_id)
    return json_response({"items": [d.to_dict() for d in items]})


async def mobile_messaging_threads_handler(request: web.Request) -> web.Response:
    user_id = request.query.get("user_id")
    items = agro_marketplace.portal_engine.messaging.list_threads(user_id=user_id)
    return json_response({"items": [t.to_dict() for t in items]})


async def partner_connect_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        connection = await agro_marketplace.partner_api.connect(
            PartnerConnection(
                partner_type=PartnerType(data.get("partner_type", "bank")),
                partner_name=data.get("partner_name", ""),
                credentials_ref=data.get("credentials_ref", ""),
                config=dict(data.get("config", {})),
            )
        )
        return json_response(connection.to_dict(), status=201)
    except (ValidationError, ValueError) as exc:
        return error_response(str(exc), status=400)


async def partner_list_handler(request: web.Request) -> web.Response:
    ptype = request.query.get("type")
    try:
        partner_type = PartnerType(ptype) if ptype else None
    except ValueError:
        return error_response(f"unknown partner type: {ptype}", status=400)
    items = agro_marketplace.partner_api.list_connections(partner_type=partner_type)
    return json_response({"items": [c.to_dict() for c in items]})


async def partner_invoke_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        result = agro_marketplace.partner_api.invoke(
            data.get("partner_type", "bank"),
            data.get("action", "default"),
            **dict(data.get("params", {})),
        )
        return json_response(result)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def notifications_send_handler(request: web.Request) -> web.Response:
    data = await request.json()
    note = await agro_marketplace.notification_center.send(
        data.get("recipient_id", ""),
        data.get("title", ""),
        data.get("body", ""),
        channel=data.get("channel", "in_app"),
    )
    return json_response(note.to_dict(), status=201)


async def notifications_inbox_handler(request: web.Request) -> web.Response:
    items = agro_marketplace.notification_center.inbox(request.match_info["user_id"])
    return json_response({"items": [n.to_dict() for n in items]})


async def notifications_ai_alert_handler(request: web.Request) -> web.Response:
    data = await request.json()
    note = await agro_marketplace.notification_center.ai_alert(
        data.get("recipient_id", ""),
        data.get("signal", "attention"),
    )
    return json_response(note.to_dict(), status=201)


async def webhook_subscribe_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        sub = agro_marketplace.webhooks_registry.subscribe(
            WebhookSubscription(
                target_url=data.get("target_url", ""),
                event_types=list(data.get("event_types", [])),
                secret=data.get("secret", ""),
                partner_id=data.get("partner_id", ""),
            )
        )
        return json_response(sub.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def webhook_trigger_handler(request: web.Request) -> web.Response:
    data = await request.json()
    deliveries = await agro_marketplace.webhooks_registry.trigger(
        data.get("event_type", "custom"),
        dict(data.get("payload", {})),
    )
    return json_response({"deliveries": deliveries})


async def messaging_thread_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        thread = agro_marketplace.portal_engine.messaging.create_thread(
            MessageThread(
                participants=list(data.get("participants", [])),
                subject=data.get("subject", ""),
            )
        )
        return json_response(thread.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def messaging_send_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        msg = agro_marketplace.portal_engine.messaging.send(
            Message(
                thread_id=request.match_info["thread_id"],
                sender_id=data.get("sender_id", ""),
                body=data.get("body", ""),
            )
        )
        return json_response(msg.to_dict(), status=201)
    except (NotFoundError, ValidationError) as exc:
        status = 404 if isinstance(exc, NotFoundError) else 400
        return error_response(str(exc), status=status)


async def calendar_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        event = agro_marketplace.portal_engine.calendar.create(
            CalendarEvent(
                user_id=data.get("user_id", ""),
                title=data.get("title", ""),
                starts_at=float(data.get("starts_at", 0)),
                ends_at=float(data.get("ends_at", 0)),
                event_type=data.get("event_type", "general"),
                related_id=data.get("related_id", ""),
            )
        )
        return json_response(event.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def documents_share_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        share = await agro_marketplace.portal_engine.documents.share(
            SharedDocument(
                document_id=data.get("document_id", ""),
                owner_id=data.get("owner_id", ""),
                recipient_id=data.get("recipient_id", ""),
                title=data.get("title", ""),
            )
        )
        return json_response(share.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)
