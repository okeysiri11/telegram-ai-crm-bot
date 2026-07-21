# Internal API handlers — Agro Marketplace.

from __future__ import annotations

from aiohttp import web

from applications.agro_marketplace import agro_marketplace
from applications.agro_marketplace.api.middleware import json_response


async def pipeline_handler(_request: web.Request) -> web.Response:
    return json_response(
        {
            "orders": agro_marketplace.analytics.orders_by_status(),
            "metrics": agro_marketplace.analytics.dashboard_metrics(),
        }
    )


async def store_stats_handler(_request: web.Request) -> web.Response:
    store = agro_marketplace.store
    return json_response(
        {
            "farmers": store.farmers.count(),
            "products": store.products.count(),
            "orders": store.orders.count(),
            "warehouses": store.warehouses.count(),
            "export_shipments": store.export_shipments.count(),
            "notifications": store.notifications.count(),
        }
    )
