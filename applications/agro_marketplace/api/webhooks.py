# Webhook API handlers — Agro Marketplace.

from __future__ import annotations

from aiohttp import web

from applications.agro_marketplace import agro_marketplace
from applications.agro_marketplace.api.middleware import json_response


async def order_webhook_handler(request: web.Request) -> web.Response:
    data = await request.json()
    agro_marketplace.notifications.notify(
        recipient_id=data.get("recipient_id", "system"),
        title="Order webhook",
        body=str(data),
        channel="webhook",
    )
    return json_response({"received": True, "event": data.get("event", "order")})


async def shipment_webhook_handler(request: web.Request) -> web.Response:
    data = await request.json()
    agro_marketplace.notifications.notify(
        recipient_id=data.get("recipient_id", "system"),
        title="Shipment webhook",
        body=str(data),
        channel="webhook",
    )
    return json_response({"received": True, "event": data.get("event", "shipment")})
