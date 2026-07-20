# Internal API — service-to-service endpoints.

from __future__ import annotations

from aiohttp import web

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.middleware import json_response
from applications.auto_marketplace.shared.models import Deal, Payment


async def internal_health_handler(_request: web.Request) -> web.Response:
    return json_response({"status": "ok", "layer": "internal"})


async def internal_pipeline_handler(_request: web.Request) -> web.Response:
    return json_response(auto_marketplace.analytics.sales_pipeline())


async def internal_inventory_handler(_request: web.Request) -> web.Response:
    return json_response(auto_marketplace.inventory.stock_summary())


async def internal_create_deal_handler(request: web.Request) -> web.Response:
    data = await request.json()
    deal = Deal(
        customer_id=data.get("customer_id", ""),
        dealer_id=data.get("dealer_id", ""),
        vehicle_id=data.get("vehicle_id", ""),
    )
    created = auto_marketplace.crm.create_deal(deal)
    workflow_id = await auto_marketplace.platform.start_deal_workflow(created.deal_id, created.to_dict())
    return json_response({**created.to_dict(), "workflow_id": workflow_id}, status=201)


async def internal_ai_pricing_handler(request: web.Request) -> web.Response:
    data = await request.json()
    reasoning = await auto_marketplace.platform.reason_about_pricing(data)
    return json_response(reasoning)


async def internal_ai_plan_handler(request: web.Request) -> web.Response:
    data = await request.json()
    plan = await auto_marketplace.platform.plan_purchase_journey(
        data.get("customer_id", ""),
        data.get("preferences", {}),
    )
    return json_response(plan)


async def internal_capture_payment_handler(request: web.Request) -> web.Response:
    payment_id = request.match_info["payment_id"]
    payment = auto_marketplace.payments.capture_payment(payment_id)
    return json_response(payment.to_dict())


async def internal_create_payment_handler(request: web.Request) -> web.Response:
    data = await request.json()
    payment = Payment(
        deal_id=data.get("deal_id", ""),
        customer_id=data.get("customer_id", ""),
        amount=float(data.get("amount", 0)),
        currency=data.get("currency", "USD"),
        provider=data.get("provider", "internal"),
    )
    created = auto_marketplace.payments.create_payment(payment)
    return json_response(created.to_dict(), status=201)
