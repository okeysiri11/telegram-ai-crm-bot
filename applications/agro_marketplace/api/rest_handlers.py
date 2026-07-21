# REST API handlers — Agro Marketplace public API v1.

from __future__ import annotations

from aiohttp import web

from applications.agro_marketplace import agro_marketplace
from applications.agro_marketplace.api.middleware import error_response, json_response
from applications.agro_marketplace.shared.exceptions import AgroMarketplaceError, NotFoundError, ValidationError
from applications.agro_marketplace.shared.models import (
    Buyer,
    Delivery,
    ExportShipment,
    Farm,
    Farmer,
    Field,
    Harvest,
    MarketplaceListing,
    Offer,
    Order,
    Product,
    ProductCategory,
    Supplier,
    Warehouse,
)


async def health_handler(_request: web.Request) -> web.Response:
    return json_response(agro_marketplace.health())


async def list_farmers_handler(_request: web.Request) -> web.Response:
    farmers = agro_marketplace.farmers.list_farmers()
    return json_response({"items": [f.to_dict() for f in farmers]})


async def register_farmer_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        farmer = await agro_marketplace.farmers.register_farmer(
            Farmer(
                name=data.get("name", ""),
                email=data.get("email", ""),
                phone=data.get("phone", ""),
                country=data.get("country", ""),
                region=data.get("region", ""),
                certifications=list(data.get("certifications", [])),
            )
        )
        return json_response(farmer.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def create_farm_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        farm = agro_marketplace.farmers.create_farm(
            Farm(
                farmer_id=data.get("farmer_id", ""),
                name=data.get("name", ""),
                location=data.get("location", ""),
                size_hectares=float(data.get("size_hectares", 0)),
            )
        )
        return json_response(farm.to_dict(), status=201)
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def add_field_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        field = agro_marketplace.farmers.add_field(
            Field(
                farm_id=data.get("farm_id", ""),
                name=data.get("name", ""),
                crop_type=data.get("crop_type", ""),
                area_hectares=float(data.get("area_hectares", 0)),
                soil_type=data.get("soil_type", ""),
            )
        )
        return json_response(field.to_dict(), status=201)
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def list_buyers_handler(_request: web.Request) -> web.Response:
    buyers = agro_marketplace.buyers.list_buyers()
    return json_response({"items": [b.to_dict() for b in buyers]})


async def create_buyer_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        buyer = agro_marketplace.buyers.create_buyer(
            Buyer(
                name=data.get("name", ""),
                email=data.get("email", ""),
                buyer_type=data.get("buyer_type", "processor"),
                country=data.get("country", ""),
            )
        )
        return json_response(buyer.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def list_suppliers_handler(_request: web.Request) -> web.Response:
    suppliers = agro_marketplace.suppliers.list_suppliers()
    return json_response({"items": [s.to_dict() for s in suppliers]})


async def create_supplier_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        supplier = agro_marketplace.suppliers.create_supplier(
            Supplier(
                name=data.get("name", ""),
                email=data.get("email", ""),
                category=data.get("category", "inputs"),
                country=data.get("country", ""),
            )
        )
        return json_response(supplier.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def list_products_handler(request: web.Request) -> web.Response:
    products = agro_marketplace.products.list_products()
    return json_response({"items": [p.to_dict() for p in products]})


async def create_product_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        product = await agro_marketplace.products.create_product(
            Product(
                name=data.get("name", ""),
                category_id=data.get("category_id", ""),
                crop_id=data.get("crop_id", ""),
                farmer_id=data.get("farmer_id", ""),
                unit=data.get("unit", "ton"),
                quantity=float(data.get("quantity", 0)),
                price=float(data.get("price", 0)),
                currency=data.get("currency", "USD"),
            )
        )
        return json_response(product.to_dict(), status=201)
    except (ValidationError, AgroMarketplaceError) as exc:
        return error_response(str(exc), status=400)


async def add_harvest_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        harvest = await agro_marketplace.products.add_harvest(
            Harvest(
                farm_id=data.get("farm_id", ""),
                field_id=data.get("field_id", ""),
                crop_id=data.get("crop_id", ""),
                quantity_tons=float(data.get("quantity_tons", 0)),
                quality_grade=data.get("quality_grade", "A"),
            )
        )
        return json_response(harvest.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def list_categories_handler(_request: web.Request) -> web.Response:
    categories = agro_marketplace.catalog.list_categories()
    return json_response({"items": [c.to_dict() for c in categories]})


async def create_category_handler(request: web.Request) -> web.Response:
    data = await request.json()
    category = agro_marketplace.catalog.create_category(
        ProductCategory(name=data.get("name", ""), parent_id=data.get("parent_id", ""))
    )
    return json_response(category.to_dict(), status=201)


async def catalog_search_handler(request: web.Request) -> web.Response:
    results = agro_marketplace.catalog.search(
        query=request.query.get("q", ""),
        category_id=request.query.get("category_id", ""),
    )
    return json_response({"items": results})


async def create_listing_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        listing = agro_marketplace.catalog.create_listing(
            MarketplaceListing(
                product_id=data.get("product_id", ""),
                title=data.get("title", ""),
                description=data.get("description", ""),
            )
        )
        return json_response(listing.to_dict(), status=201)
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def list_listings_handler(_request: web.Request) -> web.Response:
    listings = agro_marketplace.catalog.list_listings()
    return json_response({"items": [l.to_dict() for l in listings]})


async def create_order_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        order = await agro_marketplace.orders.create_order(
            Order(
                buyer_id=data.get("buyer_id", ""),
                farmer_id=data.get("farmer_id", ""),
                product_id=data.get("product_id", ""),
                quantity=float(data.get("quantity", 0)),
                unit_price=float(data.get("unit_price", 0)),
                currency=data.get("currency", "USD"),
            )
        )
        return json_response(order.to_dict(), status=201)
    except (NotFoundError, ValidationError) as exc:
        status = 404 if isinstance(exc, NotFoundError) else 400
        return error_response(str(exc), status=status)


async def list_orders_handler(_request: web.Request) -> web.Response:
    orders = agro_marketplace.orders.list_orders()
    return json_response({"items": [o.to_dict() for o in orders]})


async def create_offer_handler(request: web.Request) -> web.Response:
    data = await request.json()
    offer = agro_marketplace.orders.create_offer(
        Offer(
            product_id=data.get("product_id", ""),
            buyer_id=data.get("buyer_id", ""),
            price=float(data.get("price", 0)),
            quantity=float(data.get("quantity", 0)),
        )
    )
    return json_response(offer.to_dict(), status=201)


async def create_warehouse_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        warehouse = agro_marketplace.warehouse.create_warehouse(
            Warehouse(
                name=data.get("name", ""),
                owner_id=data.get("owner_id", ""),
                location=data.get("location", ""),
                capacity_tons=float(data.get("capacity_tons", 0)),
            )
        )
        return json_response(warehouse.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def list_warehouses_handler(_request: web.Request) -> web.Response:
    warehouses = agro_marketplace.warehouse.list_warehouses()
    return json_response({"items": [w.to_dict() for w in warehouses]})


async def pricing_quote_handler(request: web.Request) -> web.Response:
    product_id = request.query.get("product_id", "")
    quantity = float(request.query.get("quantity", "1"))
    return json_response(agro_marketplace.pricing.quote(product_id, quantity))


async def create_delivery_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        delivery = await agro_marketplace.logistics.create_delivery(
            Delivery(
                order_id=data.get("order_id", ""),
                carrier=data.get("carrier", ""),
                origin=data.get("origin", ""),
                destination=data.get("destination", ""),
            )
        )
        return json_response(delivery.to_dict(), status=201)
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def complete_delivery_handler(request: web.Request) -> web.Response:
    delivery_id = request.match_info["delivery_id"]
    try:
        delivery = await agro_marketplace.logistics.complete_delivery(delivery_id)
        return json_response(delivery.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def create_export_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        shipment = await agro_marketplace.export.create_shipment(
            ExportShipment(
                order_id=data.get("order_id", ""),
                exporter_id=data.get("exporter_id", ""),
                destination_country=data.get("destination_country", ""),
            )
        )
        return json_response(shipment.to_dict(), status=201)
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def start_export_handler(request: web.Request) -> web.Response:
    shipment_id = request.match_info["shipment_id"]
    try:
        shipment = await agro_marketplace.export.start_export(shipment_id)
        return json_response(shipment.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def analytics_handler(_request: web.Request) -> web.Response:
    return json_response(agro_marketplace.analytics.dashboard_metrics())


async def dashboard_handler(_request: web.Request) -> web.Response:
    return json_response(agro_marketplace.dashboard.overview())


async def recommendations_handler(request: web.Request) -> web.Response:
    buyer_id = request.match_info["buyer_id"]
    budget = request.query.get("budget")
    items = agro_marketplace.pricing.recommend_for_buyer(
        buyer_id,
        budget=float(budget) if budget else None,
    )
    return json_response({"items": items})


async def assistant_handler(request: web.Request) -> web.Response:
    data = await request.json()
    result = await agro_marketplace.ecosystem.ask_assistant(
        data.get("message", ""),
        user_id=data.get("user_id", ""),
        context=data.get("context"),
    )
    return json_response(result)


async def roles_handler(_request: web.Request) -> web.Response:
    return json_response({"roles": agro_marketplace.permissions.roles()})
