# Webhook endpoints — external integrations.

from __future__ import annotations

import logging

from aiohttp import web

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.middleware import json_response

logger = logging.getLogger(__name__)


async def payment_webhook_handler(request: web.Request) -> web.Response:
    payload = await request.json()
    payment_id = payload.get("payment_id", "")
    event = payload.get("event", "unknown")
    logger.info("auto_marketplace_webhook event=%s payment_id=%s", event, payment_id)
    if event == "payment.captured" and payment_id:
        payment = auto_marketplace.payments.capture_payment(payment_id)
        return json_response({"processed": True, "payment": payment.to_dict()})
    return json_response({"processed": True, "event": event})


async def delivery_webhook_handler(request: web.Request) -> web.Response:
    payload = await request.json()
    delivery_id = payload.get("delivery_id", "")
    status = payload.get("status", "")
    if delivery_id and status == "delivered":
        delivery = auto_marketplace.delivery.mark_delivered(delivery_id)
        return json_response({"processed": True, "delivery": delivery.to_dict()})
    return json_response({"processed": True})


async def crm_webhook_handler(request: web.Request) -> web.Response:
    payload = await request.json()
    decision = await auto_marketplace.platform.decide_next_action(payload)
    return json_response({"processed": True, "decision": decision})
