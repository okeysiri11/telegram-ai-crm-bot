"""API handlers — Automotive ERP (Sprint 13.6)."""

from __future__ import annotations

from aiohttp import web

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.middleware import json_response
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError


async def _read_json(request: web.Request) -> dict:
    try:
        data = await request.json()
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _handle_error(exc: Exception) -> web.Response:
    if isinstance(exc, NotFoundError):
        return json_response({"error": str(exc)}, status=404)
    if isinstance(exc, ValidationError):
        return json_response({"error": str(exc)}, status=400)
    return json_response({"error": str(exc)}, status=500)


def _suite():
    return auto_marketplace.automotive_erp


async def ae_health_handler(request: web.Request) -> web.Response:
    health = auto_marketplace.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "automotive_erp_ready": health.get("automotive_erp_ready"),
            "fleet_management_ready": health.get("fleet_management_ready"),
            "predictive_maintenance_ready": health.get("predictive_maintenance_ready"),
            "enterprise_service_platform_ready": health.get("enterprise_service_platform_ready"),
            "suite": _suite().status(),
        }
    )


async def ae_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ae_service_handler(request: web.Request) -> web.Response:
    try:
        service = _suite().service
        if request.method == "GET":
            return json_response(service.status())
        body = await _read_json(request)
        action = body.get("action", "service_order")
        if action == "mechanic":
            return json_response(
                service.register_mechanic(name=body.get("name", ""), specialty=body.get("specialty", "general")),
                status=201,
            )
        if action == "repair_order":
            return json_response(
                service.create_repair_order(
                    service_order_id=body.get("service_order_id", ""),
                    tasks=body.get("tasks"),
                    parts=body.get("parts"),
                ),
                status=201,
            )
        if action == "schedule":
            return json_response(
                service.schedule(
                    body.get("service_order_id", ""),
                    mechanic_id=body.get("mechanic_id", ""),
                    starts_at=body.get("starts_at", ""),
                ),
                status=201,
            )
        if action == "qc":
            return json_response(
                service.quality_control(
                    body.get("service_order_id", ""),
                    passed=bool(body.get("passed", True)),
                    notes=body.get("notes", ""),
                ),
                status=201,
            )
        return json_response(
            service.create_service_order(
                vin=body.get("vin", ""),
                customer=body.get("customer", ""),
                description=body.get("description", ""),
                warranty=bool(body.get("warranty", False)),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ae_fleet_handler(request: web.Request) -> web.Response:
    try:
        fleet = _suite().fleet
        if request.method == "GET":
            fid = request.rel_url.query.get("fleet_id")
            if fid:
                return json_response(fleet.dashboard(fid))
            return json_response(fleet.status())
        body = await _read_json(request)
        action = body.get("action", "fleet")
        if action == "vehicle":
            return json_response(
                fleet.add_vehicle(
                    fleet_id=body.get("fleet_id", ""),
                    vin=body.get("vin", ""),
                    label=body.get("label", ""),
                ),
                status=201,
            )
        if action == "driver":
            return json_response(
                fleet.register_driver(name=body.get("name", ""), license_id=body.get("license_id", "")),
                status=201,
            )
        if action == "assign":
            return json_response(
                fleet.assign_vehicle(
                    fleet_vehicle_id=body.get("fleet_vehicle_id", ""),
                    driver_id=body.get("driver_id", ""),
                ),
                status=201,
            )
        if action == "trip":
            return json_response(
                fleet.log_trip(
                    fleet_vehicle_id=body.get("fleet_vehicle_id", ""),
                    distance_km=float(body.get("distance_km", 0) or 0),
                    fuel_liters=float(body.get("fuel_liters", 0) or 0),
                ),
                status=201,
            )
        if action == "maintenance":
            return json_response(
                fleet.schedule_maintenance(
                    fleet_vehicle_id=body.get("fleet_vehicle_id", ""),
                    due_at=body.get("due_at", ""),
                    tasks=body.get("tasks"),
                ),
                status=201,
            )
        return json_response(
            fleet.create_fleet(name=body.get("name", ""), operator=body.get("operator", "")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ae_parts_handler(request: web.Request) -> web.Response:
    try:
        parts = _suite().parts
        if request.method == "GET":
            return json_response(parts.status())
        body = await _read_json(request)
        action = body.get("action", "part")
        if action == "supplier":
            return json_response(
                parts.register_supplier(name=body.get("name", ""), contact=body.get("contact", "")),
                status=201,
            )
        if action == "purchase_order":
            return json_response(
                parts.create_purchase_order(supplier_id=body.get("supplier_id", ""), items=body.get("items")),
                status=201,
            )
        if action == "reserve":
            return json_response(
                parts.reserve(part_id=body.get("part_id", ""), qty=int(body.get("qty", 1) or 1), ref=body.get("ref", "")),
                status=201,
            )
        if action == "serial":
            return json_response(
                parts.track_serial(part_id=body.get("part_id", ""), serial=body.get("serial", "")),
                status=201,
            )
        if action == "forecast":
            return json_response(parts.forecast(warehouse=body.get("warehouse", "main")), status=201)
        return json_response(
            parts.add_part(
                sku=body.get("sku", ""),
                name=body.get("name", ""),
                warehouse=body.get("warehouse", "main"),
                qty=int(body.get("qty", 0) or 0),
                unit_cost=float(body.get("unit_cost", 0) or 0),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ae_maintenance_handler(request: web.Request) -> web.Response:
    try:
        mai = _suite().maintenance_ai
        if request.method == "GET":
            return json_response(mai.status())
        body = await _read_json(request)
        return json_response(
            mai.predict(
                vin=body.get("vin", ""),
                mileage=int(body.get("mileage", 50000) or 50000),
                health_score=float(body.get("health_score", 80) or 80),
                recent_failures=int(body.get("recent_failures", 0) or 0),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ae_enterprise_handler(request: web.Request) -> web.Response:
    try:
        enterprise = _suite().enterprise
        if request.method == "GET":
            return json_response(enterprise.status())
        body = await _read_json(request)
        action = body.get("action", "invoice")
        if action == "contract":
            return json_response(
                enterprise.create_contract(
                    party=body.get("party", ""),
                    contract_type=body.get("contract_type", "service"),
                    terms=body.get("terms"),
                ),
                status=201,
            )
        if action == "procurement":
            return json_response(
                enterprise.procurement_request(title=body.get("title", ""), budget=float(body.get("budget", 0) or 0)),
                status=201,
            )
        if action == "portal":
            return json_response(
                enterprise.portal_access(portal=body.get("portal", "customer"), principal=body.get("principal", "")),
                status=201,
            )
        return json_response(
            enterprise.create_invoice(
                customer=body.get("customer", ""),
                amount=float(body.get("amount", 0) or 0),
                ref=body.get("ref", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ae_analytics_handler(request: web.Request) -> web.Response:
    try:
        analytics = _suite().analytics
        if request.method == "GET":
            return json_response(analytics.report(report_type=request.rel_url.query.get("type", "fleet")))
        body = await _read_json(request)
        return json_response(analytics.report(report_type=body.get("report_type", "fleet")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ae_integrations_handler(request: web.Request) -> web.Response:
    try:
        integrations = _suite().integrations
        if request.method == "GET":
            return json_response({"connections": integrations.list_connections(), **integrations.status()})
        body = await _read_json(request)
        return json_response(
            integrations.connect(target=body.get("target", ""), endpoint=body.get("endpoint", "")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
