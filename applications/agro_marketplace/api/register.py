# Register Agro Marketplace API routes on aiohttp application.

from __future__ import annotations

from aiohttp import web

from applications.agro_marketplace.api import internal_handlers, rest_handlers, webhooks
from applications.agro_marketplace.api.middleware import auth_middleware
from applications.agro_marketplace.config import DEFAULT_CONFIG


def register_agro_marketplace_routes(app: web.Application) -> None:
    """Mount REST, internal, and webhook routes for Agro Marketplace."""
    config = DEFAULT_CONFIG
    prefix = config.api_prefix
    internal = config.internal_prefix
    webhooks_prefix = config.webhook_prefix

    app.middlewares.append(auth_middleware)

    # Versioned REST API
    app.router.add_get(f"{prefix}/health", rest_handlers.health_handler)
    app.router.add_get(f"{prefix}/roles", rest_handlers.roles_handler)

    app.router.add_get(f"{prefix}/farmers", rest_handlers.list_farmers_handler)
    app.router.add_post(f"{prefix}/farmers", rest_handlers.register_farmer_handler)
    app.router.add_post(f"{prefix}/farms", rest_handlers.create_farm_handler)
    app.router.add_post(f"{prefix}/fields", rest_handlers.add_field_handler)

    app.router.add_get(f"{prefix}/buyers", rest_handlers.list_buyers_handler)
    app.router.add_post(f"{prefix}/buyers", rest_handlers.create_buyer_handler)

    app.router.add_get(f"{prefix}/suppliers", rest_handlers.list_suppliers_handler)
    app.router.add_post(f"{prefix}/suppliers", rest_handlers.create_supplier_handler)

    app.router.add_get(f"{prefix}/products", rest_handlers.list_products_handler)
    app.router.add_post(f"{prefix}/products", rest_handlers.create_product_handler)
    app.router.add_post(f"{prefix}/harvests", rest_handlers.add_harvest_handler)

    app.router.add_get(f"{prefix}/categories", rest_handlers.list_categories_handler)
    app.router.add_post(f"{prefix}/categories", rest_handlers.create_category_handler)
    app.router.add_get(f"{prefix}/catalog/search", rest_handlers.catalog_search_handler)
    app.router.add_get(f"{prefix}/listings", rest_handlers.list_listings_handler)
    app.router.add_post(f"{prefix}/listings", rest_handlers.create_listing_handler)

    app.router.add_get(f"{prefix}/orders", rest_handlers.list_orders_handler)
    app.router.add_post(f"{prefix}/orders", rest_handlers.create_order_handler)
    app.router.add_post(f"{prefix}/offers", rest_handlers.create_offer_handler)

    app.router.add_get(f"{prefix}/warehouses", rest_handlers.list_warehouses_handler)
    app.router.add_post(f"{prefix}/warehouses", rest_handlers.create_warehouse_handler)

    app.router.add_get(f"{prefix}/pricing/quote", rest_handlers.pricing_quote_handler)
    app.router.add_post(f"{prefix}/deliveries", rest_handlers.create_delivery_handler)
    app.router.add_post(
        f"{prefix}/deliveries/{{delivery_id}}/complete",
        rest_handlers.complete_delivery_handler,
    )

    app.router.add_post(f"{prefix}/export/shipments", rest_handlers.create_export_handler)
    app.router.add_post(
        f"{prefix}/export/shipments/{{shipment_id}}/start",
        rest_handlers.start_export_handler,
    )

    app.router.add_get(f"{prefix}/analytics", rest_handlers.analytics_handler)
    app.router.add_get(f"{prefix}/dashboard", rest_handlers.dashboard_handler)
    app.router.add_get(
        f"{prefix}/buyers/{{buyer_id}}/recommendations",
        rest_handlers.recommendations_handler,
    )
    app.router.add_post(f"{prefix}/assistant", rest_handlers.assistant_handler)

    # Internal API
    app.router.add_get(f"{internal}/pipeline", internal_handlers.pipeline_handler)
    app.router.add_get(f"{internal}/stats", internal_handlers.store_stats_handler)

    # Webhook API
    app.router.add_post(f"{webhooks_prefix}/orders", webhooks.order_webhook_handler)
    app.router.add_post(f"{webhooks_prefix}/shipments", webhooks.shipment_webhook_handler)
