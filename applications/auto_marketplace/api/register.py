# Register Auto Marketplace API routes on aiohttp application.

from __future__ import annotations

from aiohttp import web

from applications.auto_marketplace.api import catalog_handlers, internal_handlers, rest_handlers, webhooks
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

    # Sprint 6.2 — Vehicle Catalog & Inventory Engine
    catalog = f"{prefix}/catalog"
    app.router.add_get(f"{catalog}/vehicles", catalog_handlers.catalog_list_handler)
    app.router.add_post(f"{catalog}/vehicles", catalog_handlers.catalog_create_handler)
    app.router.add_get(f"{catalog}/vehicles/{{vehicle_id}}", catalog_handlers.catalog_get_handler)
    app.router.add_patch(f"{catalog}/vehicles/{{vehicle_id}}", catalog_handlers.catalog_update_handler)
    app.router.add_post(f"{catalog}/vehicles/{{vehicle_id}}/archive", catalog_handlers.catalog_archive_handler)
    app.router.add_post(f"{catalog}/vehicles/{{vehicle_id}}/restore", catalog_handlers.catalog_restore_handler)
    app.router.add_post(f"{catalog}/vehicles/bulk/import", catalog_handlers.catalog_bulk_import_handler)
    app.router.add_post(f"{catalog}/vehicles/bulk/update", catalog_handlers.catalog_bulk_update_handler)
    app.router.add_post(f"{catalog}/vin/validate", catalog_handlers.catalog_vin_validate_handler)
    app.router.add_get(f"{catalog}/vehicles/{{vehicle_id}}/duplicates", catalog_handlers.catalog_duplicates_handler)

    inv = f"{prefix}/inventory"
    app.router.add_get(f"{inv}/availability", catalog_handlers.inventory_availability_handler)
    app.router.add_get(f"{inv}/dealers/{{dealer_id}}", catalog_handlers.inventory_dealer_handler)
    app.router.add_post(f"{inv}/vehicles/{{vehicle_id}}/reserve", catalog_handlers.inventory_reserve_handler)
    app.router.add_post(f"{inv}/vehicles/{{vehicle_id}}/sold", catalog_handlers.inventory_sold_handler)
    app.router.add_post(f"{inv}/vehicles/{{vehicle_id}}/incoming", catalog_handlers.inventory_incoming_handler)

    app.router.add_get(f"{prefix}/catalog/search", catalog_handlers.search_catalog_handler)

    app.router.add_get(f"{prefix}/vehicles/{{vehicle_id}}/media", catalog_handlers.media_list_handler)
    app.router.add_post(f"{prefix}/vehicles/{{vehicle_id}}/media", catalog_handlers.media_upload_handler)
    app.router.add_post(f"{prefix}/vehicles/{{vehicle_id}}/media/reorder", catalog_handlers.media_reorder_handler)
    app.router.add_post(f"{prefix}/media/{{media_id}}/optimize", catalog_handlers.media_optimize_handler)

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
