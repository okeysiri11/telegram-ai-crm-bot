# Register Agro Marketplace API routes on aiohttp application.

from __future__ import annotations

from aiohttp import web

from applications.agro_marketplace.api import catalog_handlers, crm_handlers, internal_handlers, rest_handlers, webhooks
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

    # Sprint 8.2 — Product Catalog API
    catalog = f"{prefix}/catalog"
    app.router.add_get(f"{catalog}/products", catalog_handlers.catalog_list_handler)
    app.router.add_post(f"{catalog}/products", catalog_handlers.catalog_create_handler)
    app.router.add_get(f"{catalog}/products/{{product_id}}", catalog_handlers.catalog_get_handler)
    app.router.add_patch(f"{catalog}/products/{{product_id}}", catalog_handlers.catalog_update_handler)
    app.router.add_post(f"{catalog}/products/{{product_id}}/archive", catalog_handlers.catalog_archive_handler)
    app.router.add_post(f"{catalog}/products/{{product_id}}/restore", catalog_handlers.catalog_restore_handler)
    app.router.add_post(f"{catalog}/products/bulk/import", catalog_handlers.catalog_bulk_import_handler)
    app.router.add_post(f"{catalog}/products/bulk/update", catalog_handlers.catalog_bulk_update_handler)
    app.router.add_get(f"{catalog}/products/{{product_id}}/duplicates", catalog_handlers.catalog_duplicates_handler)
    app.router.add_post(f"{catalog}/products/{{product_id}}/attributes", catalog_handlers.catalog_attributes_handler)
    app.router.add_get(f"{catalog}/products/{{product_id}}/recommendations", catalog_handlers.catalog_recommend_handler)
    app.router.add_get(f"{catalog}/categories", catalog_handlers.catalog_categories_list_handler)
    app.router.add_post(f"{catalog}/categories", catalog_handlers.catalog_categories_create_handler)
    app.router.add_get(f"{catalog}/crops", catalog_handlers.catalog_crops_list_handler)
    app.router.add_post(f"{catalog}/crops", catalog_handlers.catalog_crops_create_handler)
    app.router.add_post(f"{catalog}/varieties", catalog_handlers.catalog_variety_create_handler)
    app.router.add_post(f"{catalog}/packaging", catalog_handlers.catalog_packaging_create_handler)
    app.router.add_get(f"{catalog}/pricing/{{product_id}}/estimate", catalog_handlers.pricing_estimate_handler)

    # Sprint 8.2 — Warehouse API
    wh = f"{prefix}/warehouse"
    app.router.add_get(f"{wh}/warehouses", catalog_handlers.warehouse_list_handler)
    app.router.add_post(f"{wh}/warehouses", catalog_handlers.warehouse_create_handler)
    app.router.add_get(f"{wh}/warehouses/{{warehouse_id}}", catalog_handlers.warehouse_get_handler)
    app.router.add_post(
        f"{wh}/warehouses/{{warehouse_id}}/locations",
        catalog_handlers.warehouse_location_create_handler,
    )
    app.router.add_get(
        f"{wh}/warehouses/{{warehouse_id}}/locations",
        catalog_handlers.warehouse_locations_list_handler,
    )
    app.router.add_post(f"{wh}/lots", catalog_handlers.storage_lot_create_handler)

    # Sprint 8.2 — Inventory API
    inv = f"{prefix}/inventory"
    app.router.add_get(f"{inv}/items", catalog_handlers.inventory_list_handler)
    app.router.add_get(f"{inv}/availability", catalog_handlers.inventory_availability_handler)
    app.router.add_post(f"{inv}/incoming", catalog_handlers.inventory_incoming_handler)
    app.router.add_post(f"{inv}/outgoing", catalog_handlers.inventory_outgoing_handler)
    app.router.add_post(f"{inv}/transfer", catalog_handlers.inventory_transfer_handler)
    app.router.add_get(f"{inv}/movements", catalog_handlers.inventory_movements_handler)

    # Sprint 8.2 — Harvest API
    hv = f"{prefix}/harvest"
    app.router.add_get(f"{hv}/records", catalog_handlers.harvest_list_handler)
    app.router.add_post(f"{hv}/records", catalog_handlers.harvest_register_handler)
    app.router.add_post(f"{hv}/batches", catalog_handlers.harvest_batch_create_handler)
    app.router.add_post(f"{hv}/seasons", catalog_handlers.harvest_season_create_handler)
    app.router.add_post(f"{hv}/records/{{harvest_id}}/grade", catalog_handlers.harvest_grade_handler)
    app.router.add_post(f"{hv}/lab-results", catalog_handlers.lab_result_create_handler)
    app.router.add_post(f"{hv}/certificates", catalog_handlers.certificate_issue_handler)
    app.router.add_post(f"{hv}/certificates/{{certificate_id}}/verify", catalog_handlers.certificate_verify_handler)

    # Sprint 8.2 — Search API
    search = f"{prefix}/search"
    app.router.add_get(f"{search}/products", catalog_handlers.search_products_handler)
    app.router.add_get(f"{search}/crops", catalog_handlers.search_crops_handler)
    app.router.add_get(f"{search}/regions/{{region}}", catalog_handlers.search_region_handler)
    app.router.add_get(f"{search}/harvests", catalog_handlers.search_harvests_handler)
    app.router.add_get(f"{search}/warehouses", catalog_handlers.search_warehouses_handler)
    app.router.add_get(f"{search}/suppliers", catalog_handlers.search_suppliers_handler)
    app.router.add_get(f"{search}/semantic", catalog_handlers.search_semantic_handler)
    app.router.add_post(f"{search}/semantic", catalog_handlers.search_semantic_handler)

    # Sprint 8.3 — CRM API
    crm = f"{prefix}/crm"
    app.router.add_get(f"{crm}/metrics", crm_handlers.crm_metrics_handler)
    app.router.add_get(f"{crm}/farmers", crm_handlers.crm_list_farmers_handler)
    app.router.add_post(f"{crm}/farmers", crm_handlers.crm_register_farmer_handler)
    app.router.add_get(f"{crm}/buyers", crm_handlers.crm_list_buyers_handler)
    app.router.add_post(f"{crm}/buyers", crm_handlers.crm_register_buyer_handler)
    app.router.add_get(f"{crm}/suppliers", crm_handlers.crm_list_suppliers_handler)
    app.router.add_post(f"{crm}/suppliers", crm_handlers.crm_register_supplier_handler)
    app.router.add_get(f"{crm}/exporters", crm_handlers.crm_list_exporters_handler)
    app.router.add_post(f"{crm}/exporters", crm_handlers.crm_register_exporter_handler)
    app.router.add_get(f"{crm}/leads", crm_handlers.crm_list_leads_handler)
    app.router.add_post(f"{crm}/leads", crm_handlers.crm_create_lead_handler)
    app.router.add_post(f"{crm}/leads/{{lead_id}}/assign", crm_handlers.crm_assign_lead_handler)
    app.router.add_post(f"{crm}/leads/{{lead_id}}/qualify", crm_handlers.crm_qualify_lead_handler)
    app.router.add_post(f"{crm}/contacts", crm_handlers.crm_contact_handler)
    app.router.add_get(f"{crm}/profiles/{{profile_id}}/timeline", crm_handlers.crm_timeline_handler)
    app.router.add_get(f"{crm}/tasks", crm_handlers.crm_list_tasks_handler)
    app.router.add_post(f"{crm}/tasks", crm_handlers.crm_create_task_handler)

    # Sprint 8.3 — Marketplace API
    mp = f"{prefix}/marketplace"
    app.router.add_get(f"{mp}/metrics", crm_handlers.marketplace_metrics_handler)
    app.router.add_get(f"{mp}/listings", crm_handlers.marketplace_listings_handler)
    app.router.add_post(f"{mp}/listings", crm_handlers.marketplace_listing_create_handler)
    app.router.add_get(f"{mp}/requests", crm_handlers.marketplace_requests_handler)
    app.router.add_post(f"{mp}/requests", crm_handlers.marketplace_request_create_handler)
    app.router.add_get(f"{mp}/offers", crm_handlers.marketplace_offers_handler)
    app.router.add_post(f"{mp}/offers", crm_handlers.marketplace_offer_publish_handler)
    app.router.add_post(f"{mp}/match", crm_handlers.marketplace_match_handler)
    app.router.add_get(f"{mp}/opportunities", crm_handlers.marketplace_opportunities_handler)
    app.router.add_post(f"{mp}/deals", crm_handlers.marketplace_deal_create_handler)
    app.router.add_post(f"{mp}/deals/{{deal_id}}/complete", crm_handlers.marketplace_deal_complete_handler)
    app.router.add_get(
        f"{mp}/offers/{{offer_id}}/buyer-recommendations",
        crm_handlers.recommend_buyers_handler,
    )
    app.router.add_get(
        f"{mp}/requests/{{request_id}}/supplier-recommendations",
        crm_handlers.recommend_suppliers_handler,
    )

    # Sprint 8.3 — Trading API
    tr = f"{prefix}/trading"
    app.router.add_get(f"{tr}/rfqs", crm_handlers.trading_rfq_list_handler)
    app.router.add_post(f"{tr}/rfqs", crm_handlers.trading_rfq_create_handler)
    app.router.add_post(f"{tr}/rfqs/{{rfq_id}}/respond", crm_handlers.trading_rfq_respond_handler)
    app.router.add_post(f"{tr}/sessions", crm_handlers.trading_session_create_handler)
    app.router.add_get(f"{tr}/history", crm_handlers.trading_history_handler)
    app.router.add_get(
        f"{tr}/offers/{{offer_id}}/price-recommendation",
        crm_handlers.trading_price_recommend_handler,
    )
    app.router.add_post(f"{tr}/contracts", crm_handlers.trading_contract_prepare_handler)
    app.router.add_post(f"{tr}/contracts/{{contract_id}}/sign", crm_handlers.trading_contract_sign_handler)

    # Sprint 8.3 — Negotiation API
    nego = f"{prefix}/negotiations"
    app.router.add_get(f"{nego}", crm_handlers.negotiation_list_handler)
    app.router.add_post(f"{nego}", crm_handlers.negotiation_start_handler)
    app.router.add_post(f"{nego}/{{negotiation_id}}/counter", crm_handlers.negotiation_counter_handler)
    app.router.add_post(f"{nego}/{{negotiation_id}}/agree", crm_handlers.negotiation_agree_handler)
    app.router.add_post(f"{nego}/{{negotiation_id}}/assist", crm_handlers.negotiation_assist_handler)

    # Sprint 8.3 — Marketplace Order API
    morders = f"{prefix}/marketplace/orders"
    app.router.add_get(f"{morders}", crm_handlers.order_list_handler)
    app.router.add_post(f"{morders}", crm_handlers.order_create_handler)
    app.router.add_post(f"{morders}/{{order_id}}/confirm", crm_handlers.order_confirm_handler)

    # Internal API
    app.router.add_get(f"{internal}/pipeline", internal_handlers.pipeline_handler)
    app.router.add_get(f"{internal}/stats", internal_handlers.store_stats_handler)

    # Webhook API
    app.router.add_post(f"{webhooks_prefix}/orders", webhooks.order_webhook_handler)
    app.router.add_post(f"{webhooks_prefix}/shipments", webhooks.shipment_webhook_handler)
