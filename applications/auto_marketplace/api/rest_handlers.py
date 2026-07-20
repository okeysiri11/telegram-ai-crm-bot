# REST API handlers — public Auto Marketplace API v1.

from __future__ import annotations

from aiohttp import web

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.middleware import error_response, json_response
from applications.auto_marketplace.shared.exceptions import AutoMarketplaceError, NotFoundError
from applications.auto_marketplace.shared.models import (
    Customer,
    Dealer,
    Lead,
    Vehicle,
    VehicleSpecification,
    VehicleStatus,
)


async def health_handler(_request: web.Request) -> web.Response:
    return json_response(auto_marketplace.health())


async def list_vehicles_handler(_request: web.Request) -> web.Response:
    status = _request.query.get("status")
    vehicle_status = VehicleStatus(status) if status else None
    vehicles = auto_marketplace.catalog.list_vehicles(status=vehicle_status)
    return json_response({"items": [v.to_dict() for v in vehicles]})


async def get_vehicle_handler(request: web.Request) -> web.Response:
    vehicle_id = request.match_info["vehicle_id"]
    try:
        vehicle = auto_marketplace.catalog.get_vehicle(vehicle_id)
        return json_response(vehicle.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def create_vehicle_handler(request: web.Request) -> web.Response:
    data = await request.json()
    spec_data = data.get("specification", {})
    vehicle = Vehicle(
        dealer_id=data.get("dealer_id", ""),
        specification=VehicleSpecification(
            make=spec_data.get("make", ""),
            model=spec_data.get("model", ""),
            year=int(spec_data.get("year", 0)),
            mileage_km=int(spec_data.get("mileage_km", 0)),
            vin=spec_data.get("vin", ""),
        ),
        price=float(data.get("price", 0)),
        currency=data.get("currency", "USD"),
        description=data.get("description", ""),
        status=VehicleStatus(data.get("status", VehicleStatus.LISTED.value)),
    )
    created = auto_marketplace.catalog.create_vehicle(vehicle)
    return json_response(created.to_dict(), status=201)


async def search_vehicles_handler(request: web.Request) -> web.Response:
    query = request.query.get("q", "")
    make = request.query.get("make", "")
    max_price = request.query.get("max_price")
    results = auto_marketplace.search.search_vehicles(
        query=query,
        make=make,
        max_price=float(max_price) if max_price else None,
    )
    return json_response({"items": results})


async def list_dealers_handler(_request: web.Request) -> web.Response:
    dealers = auto_marketplace.dealers.list_dealers()
    return json_response({"items": [d.to_dict() for d in dealers]})


async def create_dealer_handler(request: web.Request) -> web.Response:
    data = await request.json()
    dealer = Dealer(
        name=data.get("name", ""),
        email=data.get("email", ""),
        phone=data.get("phone", ""),
        verified=bool(data.get("verified", False)),
    )
    created = auto_marketplace.dealers.create_dealer(dealer)
    return json_response(created.to_dict(), status=201)


async def create_customer_handler(request: web.Request) -> web.Response:
    data = await request.json()
    customer = Customer(
        first_name=data.get("first_name", ""),
        last_name=data.get("last_name", ""),
        email=data.get("email", ""),
        phone=data.get("phone", ""),
        preferences=data.get("preferences", {}),
    )
    created = auto_marketplace.customers.create_customer(customer)
    await auto_marketplace.platform.store_customer_context(created.customer_id, created.to_dict())
    return json_response(created.to_dict(), status=201)


async def create_lead_handler(request: web.Request) -> web.Response:
    data = await request.json()
    lead = Lead(
        customer_id=data.get("customer_id", ""),
        vehicle_id=data.get("vehicle_id", ""),
        dealer_id=data.get("dealer_id", ""),
        source=data.get("source", "api"),
        notes=data.get("notes", ""),
    )
    created = auto_marketplace.crm.create_lead(lead)
    customer = auto_marketplace.customers.get_customer(created.customer_id)
    auto_marketplace.notifications.notify_lead_created(created.lead_id, customer.email)
    orchestration = await auto_marketplace.platform.orchestrate_vehicle_inquiry(
        created.vehicle_id,
        created.customer_id,
    )
    return json_response({**created.to_dict(), "orchestration": orchestration}, status=201)


async def recommendations_handler(request: web.Request) -> web.Response:
    customer_id = request.match_info["customer_id"]
    items = auto_marketplace.recommendations.recommend_for_customer(customer_id)
    return json_response({"items": items})


async def analytics_handler(_request: web.Request) -> web.Response:
    return json_response(auto_marketplace.analytics.dashboard_metrics())


async def dashboard_handler(_request: web.Request) -> web.Response:
    from applications.auto_marketplace.dashboard import dashboard_service

    return json_response(dashboard_service.overview())


async def mobile_feed_handler(_request: web.Request) -> web.Response:
    from applications.auto_marketplace.mobile import mobile_api

    return json_response(mobile_api.home_feed())


async def error_middleware(_request: web.Request, handler):
    try:
        return await handler(_request)
    except NotFoundError as exc:
        return error_response(str(exc), status=404)
    except AutoMarketplaceError as exc:
        return error_response(str(exc), status=400)
