# Catalog, inventory, search, and media API handlers — Sprint 6.2.

from __future__ import annotations

from aiohttp import web

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.middleware import error_response, json_response
from applications.auto_marketplace.filters.criteria import VehicleSearchCriteria
from applications.auto_marketplace.media.models import MediaType, VehicleMedia
from applications.auto_marketplace.shared.exceptions import AutoMarketplaceError, NotFoundError, ValidationError
from applications.auto_marketplace.specifications.models import FuelType, InventoryVehicleStatus, Transmission
from applications.auto_marketplace.vehicle_catalog.models import CatalogVehicle
from applications.auto_marketplace.vehicle_catalog.vin_validator import validate_vin


def _catalog_vehicle_from_payload(data: dict) -> CatalogVehicle:
    fuel = data.get("fuel_type")
    trans = data.get("transmission")
    return CatalogVehicle(
        vin=data.get("vin", ""),
        dealer_id=data.get("dealer_id", ""),
        brand=data.get("brand", data.get("make", "")),
        model=data.get("model", ""),
        year=int(data.get("year", 0)),
        mileage_km=int(data.get("mileage_km", 0)),
        price=float(data.get("price", 0)),
        currency=data.get("currency", "USD"),
        description=data.get("description", ""),
        fuel_type=FuelType(fuel) if fuel else FuelType.GASOLINE,
        transmission=Transmission(trans) if trans else Transmission.AUTOMATIC,
        warehouse_id=data.get("warehouse_id", ""),
    )


async def catalog_list_handler(_request: web.Request) -> web.Response:
    status = _request.query.get("status")
    dealer_id = _request.query.get("dealer_id")
    st = InventoryVehicleStatus(status) if status else None
    items = auto_marketplace.vehicle_catalog.list_vehicles(status=st, dealer_id=dealer_id)
    return json_response({"items": [v.to_dict() for v in items]})


async def catalog_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    vehicle = _catalog_vehicle_from_payload(data)
    created = await auto_marketplace.vehicle_catalog.create(vehicle)
    return json_response(created.to_dict(), status=201)


async def catalog_get_handler(request: web.Request) -> web.Response:
    vehicle = auto_marketplace.vehicle_catalog.get(request.match_info["vehicle_id"])
    return json_response(vehicle.to_dict())


async def catalog_update_handler(request: web.Request) -> web.Response:
    data = await request.json()
    updated = await auto_marketplace.vehicle_catalog.update(request.match_info["vehicle_id"], **data)
    return json_response(updated.to_dict())


async def catalog_archive_handler(request: web.Request) -> web.Response:
    vehicle = await auto_marketplace.vehicle_catalog.archive(request.match_info["vehicle_id"])
    return json_response(vehicle.to_dict())


async def catalog_restore_handler(request: web.Request) -> web.Response:
    vehicle = await auto_marketplace.vehicle_catalog.restore(request.match_info["vehicle_id"])
    return json_response(vehicle.to_dict())


async def catalog_bulk_import_handler(request: web.Request) -> web.Response:
    data = await request.json()
    vehicles = [_catalog_vehicle_from_payload(item) for item in data.get("items", [])]
    result = await auto_marketplace.vehicle_catalog.bulk_import(vehicles)
    return json_response(result, status=201)


async def catalog_bulk_update_handler(request: web.Request) -> web.Response:
    data = await request.json()
    result = await auto_marketplace.vehicle_catalog.bulk_update(data.get("items", []))
    return json_response(result)


async def catalog_vin_validate_handler(request: web.Request) -> web.Response:
    data = await request.json()
    ok, message = validate_vin(data.get("vin", ""))
    return json_response({"valid": ok, "message": message})


async def catalog_duplicates_handler(request: web.Request) -> web.Response:
    dupes = auto_marketplace.vehicle_catalog.duplicate_check(request.match_info["vehicle_id"])
    return json_response({"duplicates": [d.to_dict() for d in dupes]})


async def inventory_availability_handler(request: web.Request) -> web.Response:
    return json_response(
        auto_marketplace.inventory_engine.availability(
            dealer_id=request.query.get("dealer_id"),
            warehouse_id=request.query.get("warehouse_id"),
        )
    )


async def inventory_dealer_handler(request: web.Request) -> web.Response:
    dealer_id = request.match_info["dealer_id"]
    items = auto_marketplace.inventory_engine.dealer_inventory(dealer_id)
    return json_response({"items": [v.to_dict() for v in items]})


async def inventory_reserve_handler(request: web.Request) -> web.Response:
    data = await request.json()
    vehicle = await auto_marketplace.inventory_engine.reserve(
        request.match_info["vehicle_id"],
        reservation_id=data.get("reservation_id", ""),
        customer_id=data.get("customer_id", ""),
    )
    return json_response(vehicle.to_dict())


async def inventory_sold_handler(request: web.Request) -> web.Response:
    data = await request.json()
    vehicle = await auto_marketplace.inventory_engine.mark_sold(
        request.match_info["vehicle_id"],
        deal_id=data.get("deal_id", ""),
        final_price=float(data.get("final_price", 0)),
    )
    return json_response(vehicle.to_dict())


async def inventory_incoming_handler(request: web.Request) -> web.Response:
    data = await request.json()
    vehicle = await auto_marketplace.inventory_engine.mark_incoming(
        request.match_info["vehicle_id"],
        warehouse_id=data.get("warehouse_id", ""),
    )
    return json_response(vehicle.to_dict())


async def search_catalog_handler(request: web.Request) -> web.Response:
    q = request.query
    fuel = q.get("fuel_type")
    trans = q.get("transmission")
    criteria = VehicleSearchCriteria(
        query=q.get("q", ""),
        vin=q.get("vin", ""),
        brand=q.get("brand", q.get("make", "")),
        model=q.get("model", ""),
        year_min=int(q["year_min"]) if q.get("year_min") else None,
        year_max=int(q["year_max"]) if q.get("year_max") else None,
        mileage_max=int(q["mileage_max"]) if q.get("mileage_max") else None,
        price_min=float(q["price_min"]) if q.get("price_min") else None,
        price_max=float(q["price_max"]) if q.get("price_max") else None,
        fuel_type=FuelType(fuel) if fuel else None,
        transmission=Transmission(trans) if trans else None,
        city=q.get("city", ""),
        dealer_id=q.get("dealer_id", ""),
        semantic=q.get("semantic", "").lower() in {"1", "true", "yes"},
        limit=int(q.get("limit", 50)),
    )
    items = await auto_marketplace.search_engine.search(criteria)
    return json_response({"items": items})


async def media_list_handler(request: web.Request) -> web.Response:
    items = auto_marketplace.media.list_for_vehicle(request.match_info["vehicle_id"])
    return json_response({"items": [m.to_dict() for m in items]})


async def media_upload_handler(request: web.Request) -> web.Response:
    data = await request.json()
    media = VehicleMedia(
        vehicle_id=request.match_info["vehicle_id"],
        media_type=MediaType(data.get("media_type", "photo")),
        url=data.get("url", ""),
        caption=data.get("caption", ""),
        sort_order=int(data.get("sort_order", 0)),
        file_size_bytes=int(data.get("file_size_bytes", 0)),
    )
    saved = await auto_marketplace.media.upload(media)
    return json_response(saved.to_dict(), status=201)


async def media_reorder_handler(request: web.Request) -> web.Response:
    data = await request.json()
    items = await auto_marketplace.media.reorder(
        request.match_info["vehicle_id"],
        data.get("media_ids", []),
    )
    return json_response({"items": [m.to_dict() for m in items]})


async def media_optimize_handler(request: web.Request) -> web.Response:
    media = auto_marketplace.media.optimize(request.match_info["media_id"])
    return json_response(media.to_dict())


async def catalog_error_middleware(request: web.Request, handler):
    try:
        return await handler(request)
    except NotFoundError as exc:
        return error_response(str(exc), status=404)
    except ValidationError as exc:
        return error_response(str(exc), status=422)
    except AutoMarketplaceError as exc:
        return error_response(str(exc), status=400)
