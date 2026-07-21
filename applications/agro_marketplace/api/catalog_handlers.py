# Catalog / warehouse / inventory / harvest / search API handlers — Sprint 8.2.

from __future__ import annotations

from aiohttp import web

from applications.agro_marketplace import agro_marketplace
from applications.agro_marketplace.api.middleware import error_response, json_response
from applications.agro_marketplace.product_catalog.models import (
    AgriculturalProduct,
    AgroWarehouse,
    AvailabilityStatus,
    Crop,
    CropVariety,
    HarvestBatch,
    HarvestRecord,
    LaboratoryResult,
    Packaging,
    QualityCertificateRecord,
    QualityGrade,
    Season,
    StorageLocation,
    StorageLotRecord,
    UnitOfMeasure,
)
from applications.agro_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.agro_marketplace.shared.models import ProductCategory


# --- Catalog ---


async def catalog_list_handler(request: web.Request) -> web.Response:
    status = request.query.get("status")
    include_archived = request.query.get("include_archived", "false").lower() == "true"
    products = agro_marketplace.product_catalog.list_products(
        status=AvailabilityStatus(status) if status else None,
        include_archived=include_archived,
        category_id=request.query.get("category_id") or None,
        farmer_id=request.query.get("farmer_id") or None,
    )
    return json_response({"items": [p.to_dict() for p in products]})


async def catalog_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        product = await agro_marketplace.product_catalog.create(
            AgriculturalProduct(
                name=data.get("name", ""),
                sku=data.get("sku", ""),
                category_id=data.get("category_id", ""),
                crop_id=data.get("crop_id", ""),
                variety_id=data.get("variety_id", ""),
                farmer_id=data.get("farmer_id", ""),
                supplier_id=data.get("supplier_id", ""),
                region=data.get("region", ""),
                description=data.get("description", ""),
                attributes=dict(data.get("attributes", {})),
                tags=list(data.get("tags", [])),
                uom=UnitOfMeasure(data.get("uom", "ton")),
                quantity=float(data.get("quantity", 0)),
                price=float(data.get("price", 0)),
                currency=data.get("currency", "USD"),
                packaging_id=data.get("packaging_id", ""),
                season_id=data.get("season_id", ""),
                status=AvailabilityStatus(data.get("status", AvailabilityStatus.AVAILABLE.value)),
            )
        )
        return json_response(product.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def catalog_get_handler(request: web.Request) -> web.Response:
    try:
        product = agro_marketplace.product_catalog.get(request.match_info["product_id"])
        return json_response(product.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def catalog_update_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        product = await agro_marketplace.product_catalog.update(request.match_info["product_id"], **data)
        return json_response(product.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def catalog_archive_handler(request: web.Request) -> web.Response:
    try:
        product = await agro_marketplace.product_catalog.archive(request.match_info["product_id"])
        return json_response(product.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def catalog_restore_handler(request: web.Request) -> web.Response:
    try:
        product = await agro_marketplace.product_catalog.restore(request.match_info["product_id"])
        return json_response(product.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def catalog_bulk_import_handler(request: web.Request) -> web.Response:
    data = await request.json()
    items = data.get("items", data if isinstance(data, list) else [])
    products = [
        AgriculturalProduct(
            name=i.get("name", ""),
            sku=i.get("sku", ""),
            category_id=i.get("category_id", ""),
            crop_id=i.get("crop_id", ""),
            farmer_id=i.get("farmer_id", ""),
            region=i.get("region", ""),
            quantity=float(i.get("quantity", 0)),
            price=float(i.get("price", 0)),
            uom=UnitOfMeasure(i.get("uom", "ton")),
            attributes=dict(i.get("attributes", {})),
            status=AvailabilityStatus(i.get("status", AvailabilityStatus.AVAILABLE.value)),
        )
        for i in items
    ]
    created = await agro_marketplace.product_catalog.bulk_import(products)
    return json_response({"items": [p.to_dict() for p in created]}, status=201)


async def catalog_bulk_update_handler(request: web.Request) -> web.Response:
    data = await request.json()
    updates = data.get("items", data if isinstance(data, list) else [])
    try:
        updated = await agro_marketplace.product_catalog.bulk_update(updates)
        return json_response({"items": [p.to_dict() for p in updated]})
    except (ValidationError, NotFoundError) as exc:
        status = 404 if isinstance(exc, NotFoundError) else 400
        return error_response(str(exc), status=status)


async def catalog_duplicates_handler(request: web.Request) -> web.Response:
    try:
        dupes = agro_marketplace.product_catalog.find_duplicates(request.match_info["product_id"])
        return json_response({"items": [d.to_dict() for d in dupes]})
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def catalog_attributes_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        product = agro_marketplace.product_catalog.set_attributes(
            request.match_info["product_id"],
            dict(data.get("attributes", data)),
        )
        return json_response(product.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def catalog_categories_list_handler(_request: web.Request) -> web.Response:
    return json_response({"items": [c.to_dict() for c in agro_marketplace.product_catalog.list_categories()]})


async def catalog_categories_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    category = agro_marketplace.product_catalog.create_category(
        ProductCategory(name=data.get("name", ""), parent_id=data.get("parent_id", ""))
    )
    return json_response(category.to_dict(), status=201)


async def catalog_crops_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    crop = agro_marketplace.product_catalog.create_crop(
        Crop(
            name=data.get("name", ""),
            scientific_name=data.get("scientific_name", ""),
            category=data.get("category", ""),
            typical_uom=UnitOfMeasure(data.get("uom", "ton")),
        )
    )
    return json_response(crop.to_dict(), status=201)


async def catalog_crops_list_handler(_request: web.Request) -> web.Response:
    return json_response({"items": [c.to_dict() for c in agro_marketplace.product_catalog.list_crops()]})


async def catalog_variety_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        variety = agro_marketplace.product_catalog.create_variety(
            CropVariety(
                crop_id=data.get("crop_id", ""),
                name=data.get("name", ""),
                traits=list(data.get("traits", [])),
                maturity_days=int(data.get("maturity_days", 0)),
            )
        )
        return json_response(variety.to_dict(), status=201)
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def catalog_packaging_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    packaging = agro_marketplace.product_catalog.create_packaging(
        Packaging(
            name=data.get("name", ""),
            material=data.get("material", ""),
            capacity=float(data.get("capacity", 0)),
            uom=UnitOfMeasure(data.get("uom", "kg")),
        )
    )
    return json_response(packaging.to_dict(), status=201)


async def catalog_recommend_handler(request: web.Request) -> web.Response:
    try:
        items = await agro_marketplace.product_catalog.recommend(request.match_info["product_id"])
        return json_response({"items": items})
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


# --- Warehouse ---


async def warehouse_list_handler(request: web.Request) -> web.Response:
    items = agro_marketplace.warehouse_engine.list_warehouses(region=request.query.get("region") or None)
    return json_response({"items": [w.to_dict() for w in items]})


async def warehouse_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        warehouse = await agro_marketplace.warehouse_engine.create_warehouse(
            AgroWarehouse(
                name=data.get("name", ""),
                owner_id=data.get("owner_id", ""),
                region=data.get("region", ""),
                location=data.get("location", ""),
                capacity_tons=float(data.get("capacity_tons", 0)),
            )
        )
        return json_response(warehouse.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def warehouse_get_handler(request: web.Request) -> web.Response:
    try:
        warehouse = agro_marketplace.warehouse_engine.get_warehouse(request.match_info["warehouse_id"])
        return json_response(warehouse.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def warehouse_location_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        location = agro_marketplace.warehouse_engine.create_location(
            StorageLocation(
                warehouse_id=data.get("warehouse_id", request.match_info.get("warehouse_id", "")),
                code=data.get("code", ""),
                zone=data.get("zone", ""),
                capacity_tons=float(data.get("capacity_tons", 0)),
                temperature_c=data.get("temperature_c"),
            )
        )
        return json_response(location.to_dict(), status=201)
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def warehouse_locations_list_handler(request: web.Request) -> web.Response:
    warehouse_id = request.match_info.get("warehouse_id") or request.query.get("warehouse_id")
    items = agro_marketplace.warehouse_engine.list_locations(warehouse_id=warehouse_id or None)
    return json_response({"items": [loc.to_dict() for loc in items]})


async def storage_lot_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        lot = await agro_marketplace.storage.store_batch_lot(
            StorageLotRecord(
                warehouse_id=data.get("warehouse_id", ""),
                location_id=data.get("location_id", ""),
                product_id=data.get("product_id", ""),
                batch_id=data.get("batch_id", ""),
                harvest_id=data.get("harvest_id", ""),
                quantity_tons=float(data.get("quantity_tons", 0)),
                quality_grade=QualityGrade(data.get("quality_grade", "A")),
            )
        )
        return json_response(lot.to_dict(), status=201)
    except (NotFoundError, ValidationError) as exc:
        status = 404 if isinstance(exc, NotFoundError) else 400
        return error_response(str(exc), status=status)


# --- Inventory ---


async def inventory_list_handler(request: web.Request) -> web.Response:
    items = agro_marketplace.inventory.list_items(
        warehouse_id=request.query.get("warehouse_id") or None,
        product_id=request.query.get("product_id") or None,
    )
    return json_response({"items": [i.to_dict() for i in items]})


async def inventory_availability_handler(request: web.Request) -> web.Response:
    return json_response(
        agro_marketplace.inventory.availability(
            product_id=request.query.get("product_id", ""),
            warehouse_id=request.query.get("warehouse_id", ""),
        )
    )


async def inventory_incoming_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        item = await agro_marketplace.inventory.incoming_harvest(
            product_id=data.get("product_id", ""),
            warehouse_id=data.get("warehouse_id", ""),
            quantity=float(data.get("quantity", 0)),
            location_id=data.get("location_id", ""),
            lot_id=data.get("lot_id", ""),
            batch_id=data.get("batch_id", ""),
            uom=UnitOfMeasure(data.get("uom", "ton")),
            reference=data.get("reference", ""),
        )
        return json_response(item.to_dict(), status=201)
    except (NotFoundError, ValidationError) as exc:
        status = 404 if isinstance(exc, NotFoundError) else 400
        return error_response(str(exc), status=status)


async def inventory_outgoing_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        movement = await agro_marketplace.inventory.prepare_shipment(
            product_id=data.get("product_id", ""),
            warehouse_id=data.get("warehouse_id", ""),
            quantity=float(data.get("quantity", 0)),
            reference=data.get("reference", ""),
            location_id=data.get("location_id", ""),
        )
        return json_response(movement.to_dict(), status=201)
    except (NotFoundError, ValidationError) as exc:
        status = 404 if isinstance(exc, NotFoundError) else 400
        return error_response(str(exc), status=status)


async def inventory_transfer_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        movement = await agro_marketplace.inventory.transfer(
            product_id=data.get("product_id", ""),
            from_warehouse_id=data.get("from_warehouse_id", ""),
            to_warehouse_id=data.get("to_warehouse_id", ""),
            quantity=float(data.get("quantity", 0)),
            from_location_id=data.get("from_location_id", ""),
            to_location_id=data.get("to_location_id", ""),
        )
        return json_response(movement.to_dict(), status=201)
    except (NotFoundError, ValidationError) as exc:
        status = 404 if isinstance(exc, NotFoundError) else 400
        return error_response(str(exc), status=status)


async def inventory_movements_handler(_request: web.Request) -> web.Response:
    return json_response({"items": [m.to_dict() for m in agro_marketplace.inventory.list_movements()]})


# --- Harvest ---


async def harvest_register_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        harvest = await agro_marketplace.harvest.register_harvest(
            HarvestRecord(
                farm_id=data.get("farm_id", ""),
                field_id=data.get("field_id", ""),
                crop_id=data.get("crop_id", ""),
                variety_id=data.get("variety_id", ""),
                season_id=data.get("season_id", ""),
                farmer_id=data.get("farmer_id", ""),
                region=data.get("region", ""),
                quantity=float(data.get("quantity", 0)),
                uom=UnitOfMeasure(data.get("uom", "ton")),
                yield_per_hectare=float(data.get("yield_per_hectare", 0)),
                moisture_pct=float(data.get("moisture_pct", 0)),
                protein_pct=float(data.get("protein_pct", 0)),
                foreign_material_pct=float(data.get("foreign_material_pct", 0)),
                notes=data.get("notes", ""),
            )
        )
        return json_response(harvest.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def harvest_list_handler(request: web.Request) -> web.Response:
    items = agro_marketplace.harvest.list_harvests(
        farm_id=request.query.get("farm_id") or None,
        season_id=request.query.get("season_id") or None,
        region=request.query.get("region") or None,
        crop_id=request.query.get("crop_id") or None,
    )
    return json_response({"items": [h.to_dict() for h in items]})


async def harvest_batch_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        batch = agro_marketplace.harvest.create_batch(
            HarvestBatch(
                harvest_id=data.get("harvest_id", ""),
                batch_code=data.get("batch_code", ""),
                quantity=float(data.get("quantity", 0)),
                quality_grade=QualityGrade(data.get("quality_grade", "A")),
                warehouse_id=data.get("warehouse_id", ""),
                location_id=data.get("location_id", ""),
            )
        )
        return json_response(batch.to_dict(), status=201)
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def harvest_season_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        season = agro_marketplace.harvest.create_season(
            Season(
                name=data.get("name", ""),
                year=int(data.get("year", 0)),
                region=data.get("region", ""),
                start_date=float(data.get("start_date", 0)),
                end_date=float(data.get("end_date", 0)),
            )
        )
        return json_response(season.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def harvest_grade_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        harvest = agro_marketplace.harvest.grade_quality(
            request.match_info["harvest_id"],
            grade=data.get("grade", "A"),
            moisture_pct=data.get("moisture_pct"),
            protein_pct=data.get("protein_pct"),
            foreign_material_pct=data.get("foreign_material_pct"),
        )
        return json_response(harvest.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def lab_result_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        result = agro_marketplace.quality.record_lab_result(
            LaboratoryResult(
                harvest_id=data.get("harvest_id", ""),
                batch_id=data.get("batch_id", ""),
                lab_name=data.get("lab_name", ""),
                moisture_pct=float(data.get("moisture_pct", 0)),
                protein_pct=float(data.get("protein_pct", 0)),
                foreign_material_pct=float(data.get("foreign_material_pct", 0)),
                toxins_ppm=float(data.get("toxins_ppm", 0)),
                notes=data.get("notes", ""),
            )
        )
        return json_response(result.to_dict(), status=201)
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def certificate_issue_handler(request: web.Request) -> web.Response:
    data = await request.json()
    cert = agro_marketplace.certification.issue(
        QualityCertificateRecord(
            product_id=data.get("product_id", ""),
            harvest_id=data.get("harvest_id", ""),
            batch_id=data.get("batch_id", ""),
            issuer=data.get("issuer", ""),
            grade=QualityGrade(data.get("grade", "A")),
        )
    )
    return json_response(cert.to_dict(), status=201)


async def certificate_verify_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
    except Exception:
        data = {}
    try:
        cert = await agro_marketplace.certification.verify(
            request.match_info["certificate_id"],
            grade=data.get("grade") if isinstance(data, dict) else None,
        )
        return json_response(cert.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


# --- Search ---


async def search_products_handler(request: web.Request) -> web.Response:
    items = agro_marketplace.search.search_products(
        query=request.query.get("q", ""),
        region=request.query.get("region", ""),
        category_id=request.query.get("category_id", ""),
        crop_id=request.query.get("crop_id", ""),
    )
    return json_response({"items": items})


async def search_crops_handler(request: web.Request) -> web.Response:
    return json_response({"items": agro_marketplace.search.search_crops(query=request.query.get("q", ""))})


async def search_region_handler(request: web.Request) -> web.Response:
    region = request.match_info.get("region") or request.query.get("region", "")
    return json_response(agro_marketplace.search.search_by_region(region))


async def search_harvests_handler(request: web.Request) -> web.Response:
    items = agro_marketplace.search.search_harvests(
        query=request.query.get("q", ""),
        season_id=request.query.get("season_id", ""),
        crop_id=request.query.get("crop_id", ""),
    )
    return json_response({"items": items})


async def search_warehouses_handler(request: web.Request) -> web.Response:
    items = agro_marketplace.search.search_warehouses(
        query=request.query.get("q", ""),
        region=request.query.get("region", ""),
    )
    return json_response({"items": items})


async def search_suppliers_handler(request: web.Request) -> web.Response:
    return json_response({"items": agro_marketplace.search.search_suppliers(query=request.query.get("q", ""))})


async def search_semantic_handler(request: web.Request) -> web.Response:
    query = request.query.get("q", "")
    if request.method == "POST":
        data = await request.json()
        query = data.get("q", query)
    items = await agro_marketplace.search.semantic_search(query)
    return json_response({"items": items})


async def pricing_estimate_handler(request: web.Request) -> web.Response:
    product_id = request.match_info["product_id"]
    result = await agro_marketplace.pricing.estimate_price(product_id)
    status = 404 if result.get("error") else 200
    return json_response(result, status=status)
