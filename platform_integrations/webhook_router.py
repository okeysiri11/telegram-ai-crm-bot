# Inbound webhook HTTP router.

from __future__ import annotations

import json
import logging

from aiohttp import web

from platform_integrations.integration_service import integration_service
from platform_integrations.webhook_manager import webhook_manager

logger = logging.getLogger(__name__)


async def inbound_webhook_handler(request: web.Request) -> web.Response:
    webhook_id = request.match_info["webhook_id"]
    body = await request.read()

    try:
        payload = json.loads(body.decode()) if body else {}
    except json.JSONDecodeError:
        payload = {"raw": body.decode(errors="replace")}

    try:
        result = await integration_service.process_webhook(
            webhook_id,
            body=body,
            signature=request.headers.get("X-Webhook-Signature"),
            nonce=request.headers.get("X-Webhook-Nonce"),
            timestamp=request.headers.get("X-Webhook-Timestamp"),
            payload=payload,
        )
        return web.json_response({"success": True, "data": result})
    except Exception as exc:
        logger.warning("webhook_processing_failed id=%s error=%s", webhook_id, exc)
        return web.json_response({"success": False, "error": str(exc)}, status=400)


def register_webhook_routes(app: web.Application) -> None:
    app.router.add_post("/integrations/inbound/{webhook_id}", inbound_webhook_handler)
    logger.info("integration_webhook_routes_registered")
