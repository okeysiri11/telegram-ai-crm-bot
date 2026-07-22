# Sprint 10.1 foundation REST handlers — catalog, vehicles, search, dealers, buyers, CRM.

from __future__ import annotations

from aiohttp import web

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.middleware import error_response, json_response
from applications.auto_marketplace.foundation.models import (
    Appointment,
    Buyer,
    BuyerRequest,
    CatalogCategory,
    InspectionReport,
    Negotiation,
    VehicleBrand,
    VehicleModel,
)
from applications.auto_marketplace.shared.exceptions import AutoMarketplaceError, NotFoundError, ValidationError
from applications.auto_marketplace.shared.models import (
    Dealer,
    Lead,
    Reservation,
    Vehicle,
    VehicleSpecification,
    VehicleStatus,
)


async def catalog_root_handler(_request: web.Request) -> web.Response:
    return json_response(
        {
            "application_version": auto_marketplace.config.application_version,
            "catalog_engine": auto_marketplace.config.catalog_engine,
            "overview": auto_marketplace.catalog.overview(),
            "categories": auto_marketplace.catalog.categories(),
        }
    )


async def vehicles_taxonomy_brands_handler(request: web.Request) -> web.Response:
    if request.method == "GET":
        return json_response({"items": [b.to_dict() for b in auto_marketplace.vehicles.list_brands()]})
    data = await request.json()
    try:
        brand = auto_marketplace.vehicles.register_brand(
            VehicleBrand(name=data.get("name", ""), country=data.get("country", ""))
        )
        return json_response(brand.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def vehicles_taxonomy_models_handler(request: web.Request) -> web.Response:
    if request.method == "GET":
        brand_id = request.rel_url.query.get("brand_id")
        return json_response(
            {"items": [m.to_dict() for m in auto_marketplace.vehicles.list_models(brand_id=brand_id)]}
        )
    data = await request.json()
    try:
        category = CatalogCategory(data.get("category", CatalogCategory.CARS.value))
        model = auto_marketplace.vehicles.register_model(
            VehicleModel(
                brand_id=data.get("brand_id", ""),
                name=data.get("name", ""),
                category=category,
            )
        )
        return json_response(model.to_dict(), status=201)
    except (ValidationError, ValueError) as exc:
        return error_response(str(exc), status=400)


async def vehicles_vin_handler(request: web.Request) -> web.Response:
    data = await request.json()
    parsed = auto_marketplace.vehicles.parse_vin(data.get("vin", ""))
    return json_response(parsed.to_dict())


async def search_filters_handler(_request: web.Request) -> web.Response:
    return json_response({"filters": auto_marketplace.search.filter_keys()})


async def search_advanced_handler(request: web.Request) -> web.Response:
    q = request.rel_url.query
    year = q.get("year")
    mileage_max = q.get("mileage") or q.get("mileage_max")
    min_price = q.get("min_price") or q.get("price_min")
    max_price = q.get("max_price") or q.get("price_max") or q.get("price")
    results = auto_marketplace.search.search_vehicles(
        query=q.get("q", ""),
        brand=q.get("brand", "") or q.get("make", ""),
        model=q.get("model", ""),
        year=int(year) if year else None,
        mileage_max=int(mileage_max) if mileage_max else None,
        fuel=q.get("fuel", ""),
        transmission=q.get("transmission", ""),
        body=q.get("body", ""),
        region=q.get("region", ""),
        vin=q.get("vin", ""),
        condition=q.get("condition", ""),
        min_price=float(min_price) if min_price else None,
        max_price=float(max_price) if max_price else None,
    )
    return json_response({"items": results, "filters": auto_marketplace.search.filter_keys()})


async def buyers_list_handler(_request: web.Request) -> web.Response:
    return json_response({"items": [b.to_dict() for b in auto_marketplace.buyers.list_buyers()]})


async def buyers_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        buyer = auto_marketplace.buyers.register(
            Buyer(
                first_name=data.get("first_name", ""),
                last_name=data.get("last_name", ""),
                email=data.get("email", ""),
                phone=data.get("phone", ""),
                region=data.get("region", ""),
                preferences=dict(data.get("preferences") or {}),
            )
        )
        return json_response(buyer.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def buyers_get_handler(request: web.Request) -> web.Response:
    try:
        buyer = auto_marketplace.buyers.get(request.match_info["buyer_id"])
        return json_response(buyer.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def crm_root_handler(_request: web.Request) -> web.Response:
    return json_response(
        {
            "application_version": auto_marketplace.config.application_version,
            "crm_foundation": auto_marketplace.config.crm_foundation,
            "metrics": auto_marketplace.crm.metrics(),
        }
    )


async def crm_requests_handler(request: web.Request) -> web.Response:
    if request.method == "GET":
        buyer_id = request.rel_url.query.get("buyer_id", "")
        return json_response(
            {"items": [r.to_dict() for r in auto_marketplace.crm.list_requests(buyer_id=buyer_id)]}
        )
    data = await request.json()
    try:
        created = auto_marketplace.crm.create_request(
            BuyerRequest(
                buyer_id=data.get("buyer_id", ""),
                vehicle_id=data.get("vehicle_id", ""),
                message=data.get("message", ""),
            )
        )
        return json_response(created.to_dict(), status=201)
    except (ValidationError, AutoMarketplaceError) as exc:
        return error_response(str(exc), status=400)


async def crm_appointments_handler(request: web.Request) -> web.Response:
    if request.method == "GET":
        return json_response(
            {
                "items": [
                    a.to_dict()
                    for a in auto_marketplace.crm.list_appointments(
                        buyer_id=request.rel_url.query.get("buyer_id", ""),
                        dealer_id=request.rel_url.query.get("dealer_id", ""),
                    )
                ]
            }
        )
    data = await request.json()
    try:
        created = auto_marketplace.crm.schedule_appointment(
            Appointment(
                buyer_id=data.get("buyer_id", ""),
                dealer_id=data.get("dealer_id", ""),
                vehicle_id=data.get("vehicle_id", ""),
                scheduled_at=float(data.get("scheduled_at", 0) or 0),
                notes=data.get("notes", ""),
            )
        )
        return json_response(created.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def crm_negotiations_handler(request: web.Request) -> web.Response:
    if request.method == "GET":
        return json_response(
            {
                "items": [
                    n.to_dict()
                    for n in auto_marketplace.crm.list_negotiations(
                        buyer_id=request.rel_url.query.get("buyer_id", "")
                    )
                ]
            }
        )
    data = await request.json()
    try:
        created = auto_marketplace.crm.start_negotiation(
            Negotiation(
                buyer_id=data.get("buyer_id", ""),
                dealer_id=data.get("dealer_id", ""),
                vehicle_id=data.get("vehicle_id", ""),
                offer_price=float(data.get("offer_price", 0) or 0),
                currency=data.get("currency", "USD"),
            )
        )
        return json_response(created.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def crm_reservations_handler(request: web.Request) -> web.Response:
    if request.method == "GET":
        return json_response(
            {
                "items": [
                    r.to_dict()
                    for r in auto_marketplace.crm.list_reservations(
                        customer_id=request.rel_url.query.get("customer_id", ""),
                        active_only=request.rel_url.query.get("active_only", "true") != "false",
                    )
                ]
            }
        )
    data = await request.json()
    try:
        created = auto_marketplace.crm.reserve_vehicle(
            Reservation(
                vehicle_id=data.get("vehicle_id", ""),
                customer_id=data.get("customer_id", "") or data.get("buyer_id", ""),
                dealer_id=data.get("dealer_id", ""),
                deposit_amount=float(data.get("deposit_amount", 0) or 0),
            )
        )
        return json_response(created.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def crm_history_handler(request: web.Request) -> web.Response:
    customer_id = request.match_info["customer_id"]
    return json_response(auto_marketplace.crm.customer_history(customer_id))


async def crm_leads_foundation_handler(request: web.Request) -> web.Response:
    if request.method == "GET":
        return json_response({"items": [l.to_dict() for l in auto_marketplace.crm.list_leads()]})
    data = await request.json()
    lead = auto_marketplace.crm.create_lead(
        Lead(
            customer_id=data.get("customer_id", "") or data.get("buyer_id", ""),
            vehicle_id=data.get("vehicle_id", ""),
            dealer_id=data.get("dealer_id", ""),
            source=data.get("source", "web"),
            notes=data.get("notes", ""),
        )
    )
    return json_response(lead.to_dict(), status=201)


async def inspection_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        report = auto_marketplace.inspection.create_report(
            InspectionReport(
                vehicle_id=data.get("vehicle_id", ""),
                inspector=data.get("inspector", ""),
                score=float(data.get("score", 0) or 0),
                findings=list(data.get("findings") or []),
                report_url=data.get("report_url", ""),
            )
        )
        return json_response(report.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def dealers_list_foundation_handler(_request: web.Request) -> web.Response:
    return json_response({"items": [d.to_dict() for d in auto_marketplace.dealers.list_dealers()]})


async def dealers_create_foundation_handler(request: web.Request) -> web.Response:
    data = await request.json()
    dealer = auto_marketplace.dealers.create_dealer(
        Dealer(
            name=data.get("name", ""),
            email=data.get("email", ""),
            phone=data.get("phone", ""),
            verified=bool(data.get("verified", False)),
        )
    )
    return json_response(dealer.to_dict(), status=201)


async def vehicles_create_foundation_handler(request: web.Request) -> web.Response:
    data = await request.json()
    spec_data = data.get("specification", {})
    vehicle = Vehicle(
        dealer_id=data.get("dealer_id", ""),
        specification=VehicleSpecification(
            make=spec_data.get("make", ""),
            model=spec_data.get("model", ""),
            year=int(spec_data.get("year", 0)),
            mileage_km=int(spec_data.get("mileage_km", 0)),
            fuel_type=spec_data.get("fuel_type", ""),
            transmission=spec_data.get("transmission", ""),
            body_type=spec_data.get("body_type", ""),
            vin=spec_data.get("vin", ""),
        ),
        price=float(data.get("price", 0)),
        currency=data.get("currency", "USD"),
        description=data.get("description", ""),
        status=VehicleStatus(data.get("status", VehicleStatus.LISTED.value)),
        features=list(data.get("features") or []),
    )
    created = auto_marketplace.catalog.create_vehicle(
        vehicle, category=data.get("category", CatalogCategory.CARS.value)
    )
    if data.get("price") is not None:
        auto_marketplace.pricing.record_price(
            created.vehicle_id, float(data.get("price", 0)), currency=created.currency, reason="list"
        )
    return json_response(created.to_dict(), status=201)
