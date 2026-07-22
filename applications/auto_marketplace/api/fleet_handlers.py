# Sprint 10.7 REST handlers — fleet, rental, leasing (fleet), drivers, dispatch, operations.

from __future__ import annotations

from aiohttp import web

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.middleware import error_response, json_response
from applications.auto_marketplace.fleet.models import (
    FleetDispatchJob,
    FleetDriver,
    FleetLeaseKind,
    FleetRegistry,
    FleetVehicle,
    MobilityBooking,
    RentalContract,
    RentalKind,
    SubscriptionPlan,
    TelematicsReading,
    TravelRequest,
)
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError


def _rental_kind(value: str) -> RentalKind:
    try:
        return RentalKind(value or "short_term")
    except ValueError as exc:
        raise ValidationError(f"invalid rental kind: {value}") from exc


def _lease_kind(value: str) -> FleetLeaseKind:
    try:
        return FleetLeaseKind(value or "operational")
    except ValueError as exc:
        raise ValidationError(f"invalid lease kind: {value}") from exc


async def fleet_health_handler(_request: web.Request) -> web.Response:
    return json_response(
        {
            "fleet_engine": auto_marketplace.config.fleet_engine,
            "application_version": auto_marketplace.config.application_version,
            "metrics": auto_marketplace.fleet_ops.metrics(),
        }
    )


async def fleet_create_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        fleet = auto_marketplace.fleet_ops.fleet.create_fleet(
            FleetRegistry(name=data.get("name", ""), owner_id=data.get("owner_id", ""), corporate=bool(data.get("corporate")))
        )
        return json_response(fleet.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def fleet_vehicles_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            items = auto_marketplace.fleet_ops.fleet.list_vehicles(fleet_id=request.query.get("fleet_id", ""))
            return json_response({"items": [v.to_dict() for v in items]})
        data = await request.json()
        vehicle = auto_marketplace.fleet_ops.fleet.register_vehicle(
            FleetVehicle(
                fleet_id=data.get("fleet_id", ""),
                vehicle_id=data.get("vehicle_id", ""),
                vin=data.get("vin", ""),
                label=data.get("label", ""),
                department=data.get("department", ""),
                mileage_km=int(data.get("mileage_km", 0) or 0),
            )
        )
        return json_response(vehicle.to_dict(), status=201)
    except (NotFoundError, ValidationError) as exc:
        return error_response(str(exc), status=404 if isinstance(exc, NotFoundError) else 400)


async def fleet_assign_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        vehicle = auto_marketplace.fleet_ops.fleet.assign_driver(
            request.match_info["fleet_vehicle_id"], data.get("driver_id", "")
        )
        return json_response(vehicle.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def fleet_analytics_handler(request: web.Request) -> web.Response:
    return json_response(auto_marketplace.fleet_ops.fleet.analytics(request.query.get("fleet_id", "")))


async def rental_health_handler(_request: web.Request) -> web.Response:
    return json_response(
        {
            "rental_engine": auto_marketplace.config.rental_engine,
            "metrics": auto_marketplace.fleet_ops.rental.metrics(),
        }
    )


async def rental_availability_handler(request: web.Request) -> web.Response:
    return json_response({"items": auto_marketplace.fleet_ops.rental.availability(request.query.get("fleet_id", ""))})


async def rental_price_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        return json_response(
            auto_marketplace.fleet_ops.rental.price(
                kind=_rental_kind(data.get("kind", "short_term")),
                days=int(data.get("days", 1) or 1),
                base_daily=float(data.get("base_daily", 45) or 45),
            )
        )
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def rental_reserve_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        rental = auto_marketplace.fleet_ops.rental.reserve(
            RentalContract(
                fleet_vehicle_id=data.get("fleet_vehicle_id", ""),
                customer_id=data.get("customer_id", ""),
                kind=_rental_kind(data.get("kind", "short_term")),
                starts_at=float(data.get("starts_at", 0) or 0),
                ends_at=float(data.get("ends_at", 0) or 0),
                daily_rate=float(data.get("daily_rate", 45) or 45),
            )
        )
        return json_response(rental.to_dict(), status=201)
    except (NotFoundError, ValidationError) as exc:
        return error_response(str(exc), status=404 if isinstance(exc, NotFoundError) else 400)


async def rental_return_handler(request: web.Request) -> web.Response:
    try:
        try:
            data = await request.json()
        except Exception:
            data = {}
        rental = auto_marketplace.fleet_ops.rental.return_vehicle(
            request.match_info["rental_id"],
            damage=(data or {}).get("damage", ""),
            damage_cost=float((data or {}).get("damage_cost", 0) or 0),
        )
        return json_response(rental.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def fleet_leasing_quote_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        contract = auto_marketplace.fleet_ops.leasing.quote(
            fleet_vehicle_id=data.get("fleet_vehicle_id", ""),
            customer_id=data.get("customer_id", ""),
            vehicle_price=float(data.get("vehicle_price", 0) or 0),
            kind=_lease_kind(data.get("kind", "operational")),
            term_months=int(data.get("term_months", 36) or 36),
            residual_pct=float(data.get("residual_pct", 0.4) or 0.4),
            insurance_policy=data.get("insurance_policy", ""),
        )
        return json_response(contract.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def fleet_leasing_approve_handler(request: web.Request) -> web.Response:
    try:
        contract = auto_marketplace.fleet_ops.leasing.approve(request.match_info["lease_id"])
        return json_response(contract.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def drivers_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            return json_response({"items": [d.to_dict() for d in auto_marketplace.fleet_ops.drivers.list_drivers()]})
        data = await request.json()
        driver = auto_marketplace.fleet_ops.drivers.register(
            FleetDriver(name=data.get("name", ""), license_id=data.get("license_id", ""))
        )
        return json_response(driver.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def drivers_rate_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        driver = auto_marketplace.fleet_ops.drivers.rate(request.match_info["driver_id"], float(data.get("score", 0) or 0))
        return json_response(driver.to_dict())
    except (NotFoundError, ValidationError) as exc:
        return error_response(str(exc), status=404 if isinstance(exc, NotFoundError) else 400)


async def dispatch_health_handler(_request: web.Request) -> web.Response:
    return json_response({"metrics": auto_marketplace.fleet_ops.dispatch.metrics()})


async def dispatch_jobs_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            items = auto_marketplace.fleet_ops.dispatch.list_jobs(status=request.query.get("status", ""))
            return json_response({"items": [j.to_dict() for j in items]})
        data = await request.json()
        job = auto_marketplace.fleet_ops.dispatch.create_job(
            FleetDispatchJob(
                task=data.get("task", ""),
                fleet_vehicle_id=data.get("fleet_vehicle_id", ""),
                driver_id=data.get("driver_id", ""),
                route=list(data.get("route") or []),
                priority=int(data.get("priority", 0) or 0),
                emergency=bool(data.get("emergency")),
            )
        )
        return json_response(job.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def dispatch_assign_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        job = auto_marketplace.fleet_ops.dispatch.assign(
            request.match_info["job_id"],
            fleet_vehicle_id=data.get("fleet_vehicle_id", ""),
            driver_id=data.get("driver_id", ""),
        )
        return json_response(job.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def dispatch_optimize_handler(_request: web.Request) -> web.Response:
    items = auto_marketplace.fleet_ops.dispatch.optimize_queue()
    return json_response({"items": [j.to_dict() for j in items]})


async def dispatch_emergency_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        job = auto_marketplace.fleet_ops.dispatch.emergency(
            task=data.get("task", "emergency"),
            fleet_vehicle_id=data.get("fleet_vehicle_id", ""),
            driver_id=data.get("driver_id", ""),
        )
        return json_response(job.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def operations_health_handler(_request: web.Request) -> web.Response:
    return json_response(
        {
            "operations_engine": auto_marketplace.config.operations_engine,
            "overview": auto_marketplace.fleet_ops.operations.overview(),
        }
    )


async def operations_executive_handler(request: web.Request) -> web.Response:
    return json_response(auto_marketplace.fleet_ops.executive.kpis(request.query.get("fleet_id", "")))


async def operations_map_handler(request: web.Request) -> web.Response:
    return json_response({"items": auto_marketplace.fleet_ops.executive.live_map(request.query.get("fleet_id", ""))})


async def operations_assistant_handler(request: web.Request) -> web.Response:
    data = await request.json()
    return json_response(
        auto_marketplace.fleet_ops.executive.assistant(data.get("question", ""), data.get("fleet_id", ""))
    )


async def operations_ai_handler(request: web.Request) -> web.Response:
    data = await request.json()
    action = data.get("action", "forecast")
    ai = auto_marketplace.fleet_ops.ai_operations
    if action == "maintenance":
        return json_response(ai.predictive_maintenance(data.get("fleet_vehicle_id", "")))
    if action == "optimize":
        return json_response(ai.fleet_optimization(data.get("fleet_id", "")))
    if action == "forecast":
        return json_response(ai.demand_forecast(int(data.get("days", 7) or 7)))
    if action == "pricing":
        return json_response(
            ai.pricing_optimization(
                base_daily=float(data.get("base_daily", 45) or 45),
                utilization_pct=float(data.get("utilization_pct", 50) or 50),
            )
        )
    if action == "utilization":
        return json_response(ai.utilization_prediction(data.get("fleet_id", "")))
    if action == "risk":
        return json_response(ai.risk_scoring(data.get("fleet_vehicle_id", "")))
    if action == "drivers":
        return json_response({"items": ai.driver_recommendations()})
    return error_response("unknown action", status=400)


async def operations_telematics_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        reading = auto_marketplace.fleet_ops.telematics.ingest(
            TelematicsReading(
                fleet_vehicle_id=data.get("fleet_vehicle_id", ""),
                lat=float(data.get("lat", 0) or 0),
                lon=float(data.get("lon", 0) or 0),
                speed_kmh=float(data.get("speed_kmh", 0) or 0),
                fuel_l_per_100km=float(data.get("fuel_l_per_100km", 0) or 0),
                mileage_km=int(data.get("mileage_km", 0) or 0),
                battery_pct=float(data["battery_pct"]) if data.get("battery_pct") is not None else None,
                obd_codes=list(data.get("obd_codes") or []),
                behavior_score=float(data.get("behavior_score", 80) or 80),
            )
        )
        return json_response(reading.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def operations_corporate_book_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        booking = auto_marketplace.fleet_ops.corporate.book_pool(
            MobilityBooking(
                company_id=data.get("company_id", ""),
                employee_id=data.get("employee_id", ""),
                fleet_vehicle_id=data.get("fleet_vehicle_id", ""),
                department=data.get("department", ""),
                purpose=data.get("purpose", ""),
                starts_at=float(data.get("starts_at", 0) or 0),
                ends_at=float(data.get("ends_at", 0) or 0),
            )
        )
        return json_response(booking.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def operations_travel_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        item = auto_marketplace.fleet_ops.corporate.create_travel_request(
            TravelRequest(
                company_id=data.get("company_id", ""),
                employee_id=data.get("employee_id", ""),
                department=data.get("department", ""),
                destination=data.get("destination", ""),
                starts_at=float(data.get("starts_at", 0) or 0),
                ends_at=float(data.get("ends_at", 0) or 0),
            )
        )
        return json_response(item.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def operations_subscription_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        plan = auto_marketplace.fleet_ops.subscriptions.create_plan(
            SubscriptionPlan(
                name=data.get("name", ""),
                monthly_fee=float(data.get("monthly_fee", 0) or 0),
                mileage_limit_km=int(data.get("mileage_limit_km", 1500) or 1500),
                includes=list(data.get("includes") or []),
            )
        )
        return json_response(plan.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)
