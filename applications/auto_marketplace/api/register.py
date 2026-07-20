# Register Auto Marketplace API routes on aiohttp application.

from __future__ import annotations

from aiohttp import web

from applications.auto_marketplace.api import internal_handlers, rest_handlers, webhooks
from applications.auto_marketplace.api.middleware import auth_middleware
from applications.auto_marketplace.config import DEFAULT_CONFIG


def register_auto_marketplace_routes(app: web.Application) -> None:
    """Mount REST, internal, and webhook routes for Auto Marketplace."""
    config = DEFAULT_CONFIG
    prefix = config.api_prefix
    internal = config.internal_prefix
    webhooks_prefix = config.webhook_prefix

    app.middlewares.append(auth_middleware)

    # Public REST API
    app.router.add_get(f"{prefix}/health", rest_handlers.health_handler)
    app.router.add_get(f"{prefix}/vehicles", rest_handlers.list_vehicles_handler)
    app.router.add_post(f"{prefix}/vehicles", rest_handlers.create_vehicle_handler)
    app.router.add_get(f"{prefix}/vehicles/{{vehicle_id}}", rest_handlers.get_vehicle_handler)
    app.router.add_get(f"{prefix}/search", rest_handlers.search_vehicles_handler)
    app.router.add_get(f"{prefix}/dealers", rest_handlers.list_dealers_handler)
    app.router.add_post(f"{prefix}/dealers", rest_handlers.create_dealer_handler)
    app.router.add_post(f"{prefix}/customers", rest_handlers.create_customer_handler)
    app.router.add_post(f"{prefix}/leads", rest_handlers.create_lead_handler)
    app.router.add_get(f"{prefix}/customers/{{customer_id}}/recommendations", rest_handlers.recommendations_handler)
    app.router.add_get(f"{prefix}/analytics", rest_handlers.analytics_handler)
    app.router.add_get(f"{prefix}/dashboard", rest_handlers.dashboard_handler)
    app.router.add_get(f"{prefix}/mobile/feed", rest_handlers.mobile_feed_handler)

    # Internal API
    app.router.add_get(f"{internal}/health", internal_handlers.internal_health_handler)
    app.router.add_get(f"{internal}/pipeline", internal_handlers.internal_pipeline_handler)
    app.router.add_get(f"{internal}/inventory", internal_handlers.internal_inventory_handler)
    app.router.add_post(f"{internal}/deals", internal_handlers.internal_create_deal_handler)
    app.router.add_post(f"{internal}/payments", internal_handlers.internal_create_payment_handler)
    app.router.add_post(f"{internal}/payments/{{payment_id}}/capture", internal_handlers.internal_capture_payment_handler)
    app.router.add_post(f"{internal}/ai/pricing", internal_handlers.internal_ai_pricing_handler)
    app.router.add_post(f"{internal}/ai/plan", internal_handlers.internal_ai_plan_handler)

    # Webhooks
    app.router.add_post(f"{webhooks_prefix}/payments", webhooks.payment_webhook_handler)
    app.router.add_post(f"{webhooks_prefix}/delivery", webhooks.delivery_webhook_handler)
    app.router.add_post(f"{webhooks_prefix}/crm", webhooks.crm_webhook_handler)
