# Register Agro Marketplace API routes on aiohttp application.

from __future__ import annotations

from aiohttp import web

from applications.agro_marketplace.api import (
    ai_handlers,
    bi_handlers,
    catalog_handlers,
    crm_handlers,
    export_handlers,
    internal_handlers,
    ops_handlers,
    portal_handlers,
    rest_handlers,
    webhooks,
)
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

    # Sprint 8.4 — AI / Recommendations / Forecast / Knowledge / Assistant
    ai = f"{prefix}/ai"
    app.router.add_get(f"{ai}/health", ai_handlers.ai_health_handler)
    app.router.add_get(f"{ai}/agents", ai_handlers.ai_agents_list_handler)
    app.router.add_post(f"{ai}/agents/{{agent_type}}/invoke", ai_handlers.ai_agent_invoke_handler)
    app.router.add_post(f"{ai}/agents/invoke", ai_handlers.ai_agent_invoke_handler)
    app.router.add_post(f"{ai}/assistant", ai_handlers.assistant_ask_handler)
    app.router.add_get(f"{ai}/pricing/{{product_id}}/estimate", ai_handlers.pricing_ai_estimate_handler)
    app.router.add_get(f"{ai}/crops/{{crop}}/advise", ai_handlers.crop_ai_advise_handler)
    app.router.add_get(f"{ai}/market/snapshot", ai_handlers.market_ai_snapshot_handler)
    app.router.add_post(f"{ai}/market/snapshot", ai_handlers.market_ai_snapshot_handler)

    rec = f"{prefix}/recommendations"
    app.router.add_get(f"{rec}/products", ai_handlers.recommendations_products_handler)
    app.router.add_get(f"{rec}/buyers/{{offer_id}}", ai_handlers.recommendations_buyers_handler)
    app.router.add_get(f"{rec}/suppliers/{{request_id}}", ai_handlers.recommendations_suppliers_handler)
    app.router.add_get(f"{rec}/contracts/{{order_id}}", ai_handlers.recommendations_contracts_handler)
    app.router.add_get(f"{rec}/opportunities", ai_handlers.recommendations_opportunities_handler)
    app.router.add_get(f"{rec}/inventory", ai_handlers.recommendations_inventory_handler)
    app.router.add_get(f"{rec}/warehouse", ai_handlers.recommendations_warehouse_handler)

    fc = f"{prefix}/forecast"
    app.router.add_get(f"{fc}", ai_handlers.forecast_list_handler)
    app.router.add_get(f"{fc}/price", ai_handlers.forecast_price_handler)
    app.router.add_post(f"{fc}/price", ai_handlers.forecast_price_handler)
    app.router.add_get(f"{fc}/demand", ai_handlers.forecast_demand_handler)
    app.router.add_post(f"{fc}/demand", ai_handlers.forecast_demand_handler)
    app.router.add_get(f"{fc}/supply", ai_handlers.forecast_supply_handler)
    app.router.add_post(f"{fc}/supply", ai_handlers.forecast_supply_handler)
    app.router.add_get(f"{fc}/harvest", ai_handlers.forecast_harvest_handler)
    app.router.add_post(f"{fc}/harvest", ai_handlers.forecast_harvest_handler)
    app.router.add_get(f"{fc}/season", ai_handlers.forecast_season_handler)
    app.router.add_post(f"{fc}/season", ai_handlers.forecast_season_handler)
    app.router.add_get(f"{fc}/risk", ai_handlers.forecast_risk_handler)
    app.router.add_post(f"{fc}/risk", ai_handlers.forecast_risk_handler)

    kn = f"{prefix}/knowledge"
    app.router.add_get(f"{kn}/search", ai_handlers.knowledge_search_handler)
    app.router.add_get(f"{kn}/taxonomy", ai_handlers.knowledge_taxonomy_handler)
    app.router.add_get(f"{kn}/seasonality", ai_handlers.knowledge_seasonality_handler)
    app.router.add_get(f"{kn}/export-regulations", ai_handlers.knowledge_export_handler)
    app.router.add_post(f"{kn}/articles", ai_handlers.knowledge_add_handler)

    wf = f"{prefix}/ai/workflow"
    app.router.add_post(f"{wf}/leads/{{lead_id}}/qualify", ai_handlers.workflow_qualify_lead_handler)
    app.router.add_post(f"{wf}/offers/auto-match", ai_handlers.workflow_auto_match_handler)
    app.router.add_post(f"{wf}/negotiations/{{negotiation_id}}/assist", ai_handlers.workflow_negotiation_handler)
    app.router.add_post(f"{wf}/opportunities", ai_handlers.workflow_opportunities_handler)
    app.router.add_post(f"{wf}/executive-report", ai_handlers.workflow_executive_report_handler)
    app.router.add_get(f"{wf}/tasks", ai_handlers.workflow_tasks_handler)

    # Sprint 8.5 — Export / Logistics / Shipping / Tracking / Documents
    ex = f"{prefix}/export"
    app.router.add_get(f"{ex}/health", export_handlers.export_health_handler)
    app.router.add_get(f"{ex}/shipments", export_handlers.export_list_shipments_handler)
    app.router.add_post(f"{ex}/shipments", export_handlers.export_create_shipment_handler)
    app.router.add_get(f"{ex}/shipments/{{shipment_id}}", export_handlers.export_get_shipment_handler)
    app.router.add_post(f"{ex}/shipments/{{shipment_id}}/items", export_handlers.export_add_item_handler)
    app.router.add_post(f"{ex}/shipments/{{shipment_id}}/documents", export_handlers.export_prepare_docs_handler)
    app.router.add_post(f"{ex}/shipments/{{shipment_id}}/documents/verify", export_handlers.export_verify_docs_handler)
    app.router.add_post(f"{ex}/shipments/{{shipment_id}}/risk", export_handlers.export_risk_handler)
    app.router.add_post(f"{ex}/shipments/{{shipment_id}}/dispatch", export_handlers.export_dispatch_handler)
    app.router.add_post(f"{ex}/shipments/{{shipment_id}}/arrive", export_handlers.export_arrive_handler)
    app.router.add_post(f"{ex}/shipments/{{shipment_id}}/customs", export_handlers.export_customs_handler)
    app.router.add_post(f"{ex}/shipments/{{shipment_id}}/deliver", export_handlers.export_deliver_handler)
    app.router.add_post(f"{ex}/shipments/{{shipment_id}}/complete", export_handlers.export_complete_handler)
    app.router.add_get(f"{ex}/incoterms", export_handlers.incoterms_list_handler)
    app.router.add_get(f"{ex}/requirements/{{country}}", export_handlers.country_requirements_handler)
    app.router.add_get(f"{ex}/opportunities", export_handlers.trade_opportunities_handler)

    lg = f"{prefix}/logistics"
    app.router.add_post(f"{lg}/plan", export_handlers.logistics_plan_handler)
    app.router.add_post(f"{lg}/dispatch", export_handlers.logistics_dispatch_handler)
    app.router.add_post(f"{lg}/deliveries", export_handlers.logistics_schedule_delivery_handler)
    app.router.add_get(f"{lg}/ports", export_handlers.ports_list_handler)
    app.router.add_post(f"{lg}/ports", export_handlers.ports_create_handler)
    app.router.add_post(f"{lg}/terminals", export_handlers.terminals_create_handler)
    app.router.add_get(f"{lg}/carriers", export_handlers.carriers_list_handler)
    app.router.add_post(f"{lg}/carriers", export_handlers.carriers_create_handler)
    app.router.add_get(f"{lg}/carriers/recommend", export_handlers.carriers_recommend_handler)
    app.router.add_post(f"{lg}/containers", export_handlers.containers_create_handler)
    app.router.add_post(f"{lg}/containers/load", export_handlers.containers_load_handler)
    app.router.add_post(f"{lg}/insurance", export_handlers.insurance_create_handler)
    app.router.add_post(f"{lg}/finance/estimate", export_handlers.finance_estimate_handler)

    sh = f"{prefix}/shipments"
    app.router.add_get(f"{sh}/{{shipment_id}}/tracking", export_handlers.tracking_timeline_handler)
    app.router.add_get(f"{sh}/{{shipment_id}}/documents", export_handlers.documents_list_handler)

    track = f"{prefix}/tracking"
    app.router.add_get(f"{track}/{{shipment_id}}", export_handlers.tracking_timeline_handler)

    docs = f"{prefix}/trade-documents"
    app.router.add_get(f"{docs}", export_handlers.documents_list_handler)
    app.router.add_post(f"{docs}/{{document_id}}/verify", export_handlers.documents_verify_handler)

    # Sprint 8.6 — Analytics / Dashboards / Forecast / KPI / Reports / Insights
    an = f"{prefix}/analytics"
    app.router.add_get(f"{an}/health", bi_handlers.analytics_health_handler)
    app.router.add_get(f"{an}/domains", bi_handlers.analytics_domains_handler)
    app.router.add_get(f"{an}/domains/{{domain}}", bi_handlers.analytics_domain_handler)
    app.router.add_post(f"{an}/metrics", bi_handlers.metrics_record_handler)

    dash = f"{prefix}/dashboards"
    app.router.add_get(f"{dash}", bi_handlers.dashboard_list_kinds_handler)
    app.router.add_get(f"{dash}/executive", bi_handlers.dashboard_executive_handler)
    app.router.add_post(f"{dash}/executive", bi_handlers.dashboard_executive_handler)
    app.router.add_get(f"{dash}/{{kind}}", bi_handlers.dashboard_build_handler)
    app.router.add_post(f"{dash}/{{kind}}", bi_handlers.dashboard_build_handler)

    bi_fc = f"{prefix}/bi/forecast"
    app.router.add_get(f"{bi_fc}/suite", bi_handlers.forecast_suite_handler)
    app.router.add_post(f"{bi_fc}/suite", bi_handlers.forecast_suite_handler)
    app.router.add_get(f"{bi_fc}/{{kind}}", bi_handlers.forecast_bi_handler)
    app.router.add_post(f"{bi_fc}/{{kind}}", bi_handlers.forecast_bi_handler)

    # Extend classic forecast routes with BI kinds
    app.router.add_get(f"{fc}/storage", bi_handlers.forecast_bi_handler)
    app.router.add_post(f"{fc}/storage", bi_handlers.forecast_bi_handler)
    app.router.add_get(f"{fc}/export", bi_handlers.forecast_bi_handler)
    app.router.add_post(f"{fc}/export", bi_handlers.forecast_bi_handler)
    app.router.add_get(f"{fc}/revenue", bi_handlers.forecast_bi_handler)
    app.router.add_post(f"{fc}/revenue", bi_handlers.forecast_bi_handler)
    app.router.add_get(f"{fc}/market_trend", bi_handlers.forecast_bi_handler)
    app.router.add_post(f"{fc}/market_trend", bi_handlers.forecast_bi_handler)

    kpi = f"{prefix}/kpi"
    app.router.add_get(f"{kpi}", bi_handlers.kpi_list_handler)
    app.router.add_post(f"{kpi}/calculate", bi_handlers.kpi_calculate_handler)
    app.router.add_get(f"{kpi}/{{name}}", bi_handlers.kpi_get_handler)
    app.router.add_post(f"{kpi}/{{name}}", bi_handlers.kpi_get_handler)

    reports = f"{prefix}/reports"
    app.router.add_get(f"{reports}", bi_handlers.reports_list_handler)
    app.router.add_post(f"{reports}/executive", bi_handlers.reports_executive_handler)

    insights = f"{prefix}/insights"
    app.router.add_get(f"{insights}", bi_handlers.insights_list_handler)
    app.router.add_post(f"{insights}/generate", bi_handlers.insights_generate_handler)
    app.router.add_post(f"{insights}/anomalies", bi_handlers.anomalies_detect_handler)

    sim = f"{prefix}/simulation"
    app.router.add_post(f"{sim}", bi_handlers.simulation_create_handler)
    app.router.add_post(f"{sim}/quick", bi_handlers.simulation_quick_handler)
    app.router.add_post(f"{sim}/{{scenario_id}}/run", bi_handlers.simulation_run_handler)

    # Sprint 8.7 — Portal / Mobile / Partner / Notifications / Webhooks
    portal = f"{prefix}/portal"
    app.router.add_get(f"{portal}/health", portal_handlers.portal_health_handler)
    app.router.add_post(f"{portal}/users", portal_handlers.portal_register_handler)
    app.router.add_get(f"{portal}/{{kind}}", portal_handlers.portal_build_handler)
    app.router.add_post(f"{portal}/{{kind}}", portal_handlers.portal_build_handler)
    app.router.add_post(f"{portal}/assistant", portal_handlers.portal_assistant_handler)
    app.router.add_post(f"{portal}/documents/share", portal_handlers.documents_share_handler)
    app.router.add_post(f"{portal}/messaging/threads", portal_handlers.messaging_thread_handler)
    app.router.add_post(f"{portal}/messaging/threads/{{thread_id}}/messages", portal_handlers.messaging_send_handler)
    app.router.add_post(f"{portal}/calendar", portal_handlers.calendar_create_handler)

    mobile = config.mobile_prefix
    app.router.add_post(f"{mobile}/auth", portal_handlers.mobile_auth_handler)
    app.router.add_get(f"{mobile}/profile/{{user_id}}", portal_handlers.mobile_profile_handler)
    app.router.add_get(f"{mobile}/home/{{user_id}}", portal_handlers.mobile_home_handler)
    app.router.add_post(f"{mobile}/assistant", portal_handlers.mobile_assistant_handler)
    app.router.add_get(f"{mobile}/products", portal_handlers.mobile_products_handler)
    app.router.add_get(f"{mobile}/orders", portal_handlers.mobile_orders_handler)
    app.router.add_get(f"{mobile}/notifications/{{user_id}}", portal_handlers.mobile_notifications_handler)
    app.router.add_get(f"{mobile}/analytics", portal_handlers.mobile_analytics_handler)
    app.router.add_get(f"{mobile}/documents", portal_handlers.mobile_documents_handler)
    app.router.add_get(f"{mobile}/messaging/threads", portal_handlers.mobile_messaging_threads_handler)

    partner = config.partner_prefix
    app.router.add_get(f"{partner}/connections", portal_handlers.partner_list_handler)
    app.router.add_post(f"{partner}/connections", portal_handlers.partner_connect_handler)
    app.router.add_post(f"{partner}/invoke", portal_handlers.partner_invoke_handler)

    notes = f"{prefix}/notifications"
    app.router.add_post(f"{notes}", portal_handlers.notifications_send_handler)
    app.router.add_get(f"{notes}/{{user_id}}", portal_handlers.notifications_inbox_handler)
    app.router.add_post(f"{notes}/ai-alert", portal_handlers.notifications_ai_alert_handler)

    wh_mgmt = f"{prefix}/webhooks"
    app.router.add_post(f"{wh_mgmt}/subscriptions", portal_handlers.webhook_subscribe_handler)
    app.router.add_post(f"{wh_mgmt}/trigger", portal_handlers.webhook_trigger_handler)

    # Sprint 8.8 — Production validation / commercial release ops
    ops = f"{prefix}/ops"
    app.router.add_get(f"{ops}/health", ops_handlers.ops_health_handler)
    app.router.add_get(f"{ops}/version", ops_handlers.ops_version_handler)
    app.router.add_get(f"{ops}/readiness", ops_handlers.ops_readiness_handler)
    app.router.add_post(f"{ops}/readiness", ops_handlers.ops_readiness_handler)
    app.router.add_get(f"{ops}/validation", ops_handlers.ops_validation_handler)
    app.router.add_post(f"{ops}/validation", ops_handlers.ops_validation_handler)
    app.router.add_get(f"{ops}/release", ops_handlers.ops_release_handler)
    app.router.add_post(f"{ops}/release", ops_handlers.ops_release_handler)
    app.router.add_get(f"{ops}/reports", ops_handlers.ops_reports_handler)
    app.router.add_post(f"{ops}/certify", ops_handlers.ops_certify_handler)
    app.router.add_post(f"{ops}/deploy/verify", ops_handlers.ops_deploy_verify_handler)

    # Internal API
    app.router.add_get(f"{internal}/pipeline", internal_handlers.pipeline_handler)
    app.router.add_get(f"{internal}/stats", internal_handlers.store_stats_handler)

    # Webhook API (inbound)
    app.router.add_post(f"{webhooks_prefix}/orders", webhooks.order_webhook_handler)
    app.router.add_post(f"{webhooks_prefix}/shipments", webhooks.shipment_webhook_handler)
    app.router.add_post(f"{webhooks_prefix}/partners", webhooks.partner_webhook_handler)
