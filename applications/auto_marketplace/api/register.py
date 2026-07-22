# Register Auto Marketplace API routes on aiohttp application.

from __future__ import annotations

from aiohttp import web

from applications.auto_marketplace.api import (
    ai_sales_handlers,
    auto_ai_handlers,
    bi_handlers,
    catalog_handlers,
    crm_handlers,
    finance_handlers,
    foundation_handlers,
    internal_handlers,
    marketplace_handlers,
    ops_handlers,
    portal_handlers,
    rest_handlers,
    transaction_handlers,
    webhooks,
)
from applications.auto_marketplace.api.middleware import auth_middleware
from applications.auto_marketplace.config import DEFAULT_CONFIG


def register_auto_marketplace_routes(app: web.Application) -> None:
    """Mount REST, internal, and webhook routes for Auto Marketplace."""
    config = DEFAULT_CONFIG
    prefix = config.api_prefix
    internal = config.internal_prefix
    webhooks_prefix = config.webhook_prefix

    app.middlewares.append(auth_middleware)

    # Public REST API
    app.router.add_get(f"{prefix}/health", rest_handlers.health_handler)

    # Sprint 10.1 — foundation catalog / vehicles / search / dealers / buyers / crm
    app.router.add_get(f"{prefix}/catalog", foundation_handlers.catalog_root_handler)
    app.router.add_get(f"{prefix}/vehicles", rest_handlers.list_vehicles_handler)
    app.router.add_post(f"{prefix}/vehicles", foundation_handlers.vehicles_create_foundation_handler)
    app.router.add_get(f"{prefix}/vehicles/brands", foundation_handlers.vehicles_taxonomy_brands_handler)
    app.router.add_post(f"{prefix}/vehicles/brands", foundation_handlers.vehicles_taxonomy_brands_handler)
    app.router.add_get(f"{prefix}/vehicles/models", foundation_handlers.vehicles_taxonomy_models_handler)
    app.router.add_post(f"{prefix}/vehicles/models", foundation_handlers.vehicles_taxonomy_models_handler)
    app.router.add_post(f"{prefix}/vehicles/vin", foundation_handlers.vehicles_vin_handler)
    app.router.add_get(f"{prefix}/vehicles/{{vehicle_id}}", rest_handlers.get_vehicle_handler)
    app.router.add_post(f"{prefix}/inspection", foundation_handlers.inspection_create_handler)
    app.router.add_get(f"{prefix}/inspection", auto_ai_handlers.inspection_ai_health_handler)
    app.router.add_post(f"{prefix}/inspection/analyze", auto_ai_handlers.inspection_ai_analyze_handler)

    app.router.add_get(f"{prefix}/recommendations", auto_ai_handlers.recommendations_health_handler)
    app.router.add_post(f"{prefix}/recommendations/personal", auto_ai_handlers.recommendations_personal_handler)
    app.router.add_post(f"{prefix}/recommendations/similar", auto_ai_handlers.recommendations_similar_handler)
    app.router.add_post(
        f"{prefix}/recommendations/alternatives",
        auto_ai_handlers.recommendations_alternatives_handler,
    )
    app.router.add_post(f"{prefix}/recommendations/budget", auto_ai_handlers.recommendations_budget_handler)
    app.router.add_post(
        f"{prefix}/recommendations/ownership-cost",
        auto_ai_handlers.recommendations_ownership_handler,
    )
    app.router.add_post(f"{prefix}/recommendations/family", auto_ai_handlers.recommendations_family_handler)
    app.router.add_post(
        f"{prefix}/recommendations/commercial",
        auto_ai_handlers.recommendations_commercial_handler,
    )
    app.router.add_post(f"{prefix}/recommendations/fleet", auto_ai_handlers.recommendations_fleet_handler)

    app.router.add_get(f"{prefix}/pricing-ai", auto_ai_handlers.pricing_ai_health_handler)
    app.router.add_post(f"{prefix}/pricing-ai/analyze", auto_ai_handlers.pricing_ai_analyze_handler)

    app.router.add_get(f"{prefix}/forecast", auto_ai_handlers.forecast_health_handler)
    app.router.add_post(f"{prefix}/forecast", auto_ai_handlers.forecast_vehicle_handler)

    app.router.add_get(f"{prefix}/assistant", auto_ai_handlers.assistant_health_handler)
    app.router.add_post(f"{prefix}/assistant/ask", auto_ai_handlers.assistant_ask_handler)
    app.router.add_post(f"{prefix}/assistant/knowledge", auto_ai_handlers.knowledge_card_handler)

    app.router.add_get(f"{prefix}/search", foundation_handlers.search_advanced_handler)
    app.router.add_get(f"{prefix}/search/filters", foundation_handlers.search_filters_handler)

    app.router.add_get(f"{prefix}/dealers", foundation_handlers.dealers_list_foundation_handler)
    app.router.add_post(f"{prefix}/dealers", foundation_handlers.dealers_create_foundation_handler)

    # Sprint 10.2 — marketplace / VIN / history / dealer network / verification / pricing
    app.router.add_get(f"{prefix}/marketplace", marketplace_handlers.marketplace_health_handler)
    app.router.add_get(f"{prefix}/marketplace/browse", marketplace_handlers.marketplace_browse_handler)
    app.router.add_get(f"{prefix}/marketplace/listings", marketplace_handlers.marketplace_listings_handler)
    app.router.add_post(f"{prefix}/marketplace/listings", marketplace_handlers.marketplace_listings_handler)
    app.router.add_post(
        f"{prefix}/marketplace/listings/{{listing_id}}/publish",
        marketplace_handlers.marketplace_publish_handler,
    )
    app.router.add_get(f"{prefix}/marketplace/auctions", marketplace_handlers.marketplace_auctions_handler)
    app.router.add_post(f"{prefix}/marketplace/auctions", marketplace_handlers.marketplace_auctions_handler)
    app.router.add_post(
        f"{prefix}/marketplace/auctions/{{auction_id}}/bids",
        marketplace_handlers.marketplace_bid_handler,
    )

    app.router.add_get(f"{prefix}/vin", marketplace_handlers.vin_health_handler)
    app.router.add_post(f"{prefix}/vin/decode", marketplace_handlers.vin_decode_handler)
    app.router.add_get(f"{prefix}/vin/{{vin}}", marketplace_handlers.vin_get_handler)

    app.router.add_get(f"{prefix}/history", marketplace_handlers.history_health_handler)
    app.router.add_get(f"{prefix}/history/{{vin}}", marketplace_handlers.history_get_handler)
    app.router.add_post(f"{prefix}/history/{{vin}}/events", marketplace_handlers.history_event_handler)
    app.router.add_post(f"{prefix}/history/ownership", marketplace_handlers.ownership_transfer_handler)

    app.router.add_get(f"{prefix}/dealers/network", marketplace_handlers.dealers_network_list_handler)
    app.router.add_post(f"{prefix}/dealers/network", marketplace_handlers.dealers_network_create_handler)
    app.router.add_post(
        f"{prefix}/dealers/{{dealer_id}}/verify",
        marketplace_handlers.dealers_verify_handler,
    )
    app.router.add_post(
        f"{prefix}/dealers/{{dealer_id}}/rate",
        marketplace_handlers.dealers_rate_handler,
    )
    app.router.add_get(
        f"{prefix}/dealers/{{dealer_id}}/analytics",
        marketplace_handlers.dealers_analytics_handler,
    )
    app.router.add_post(
        f"{prefix}/dealers/{{dealer_id}}/leads",
        marketplace_handlers.dealers_assign_lead_handler,
    )

    app.router.add_get(f"{prefix}/verification", marketplace_handlers.verification_health_handler)
    app.router.add_post(f"{prefix}/verification", marketplace_handlers.verification_run_handler)

    app.router.add_get(f"{prefix}/pricing", marketplace_handlers.pricing_health_handler)
    app.router.add_post(f"{prefix}/pricing/value", marketplace_handlers.pricing_value_handler)

    app.router.add_get(f"{prefix}/buyers", foundation_handlers.buyers_list_handler)
    app.router.add_post(f"{prefix}/buyers", foundation_handlers.buyers_create_handler)
    app.router.add_get(f"{prefix}/buyers/{{buyer_id}}", foundation_handlers.buyers_get_handler)

    app.router.add_get(f"{prefix}/crm", foundation_handlers.crm_root_handler)
    app.router.add_get(f"{prefix}/crm/requests", foundation_handlers.crm_requests_handler)
    app.router.add_post(f"{prefix}/crm/requests", foundation_handlers.crm_requests_handler)
    app.router.add_get(f"{prefix}/crm/appointments", foundation_handlers.crm_appointments_handler)
    app.router.add_post(f"{prefix}/crm/appointments", foundation_handlers.crm_appointments_handler)
    app.router.add_get(f"{prefix}/crm/negotiations", foundation_handlers.crm_negotiations_handler)
    app.router.add_post(f"{prefix}/crm/negotiations", foundation_handlers.crm_negotiations_handler)
    app.router.add_get(f"{prefix}/crm/reservations", foundation_handlers.crm_reservations_handler)
    app.router.add_post(f"{prefix}/crm/reservations", foundation_handlers.crm_reservations_handler)
    app.router.add_get(
        f"{prefix}/crm/customers/{{customer_id}}/history",
        foundation_handlers.crm_history_handler,
    )
    app.router.add_post(f"{prefix}/customers", rest_handlers.create_customer_handler)
    app.router.add_post(f"{prefix}/leads", rest_handlers.create_lead_handler)
    app.router.add_get(f"{prefix}/customers/{{customer_id}}/recommendations", rest_handlers.recommendations_handler)
    app.router.add_get(f"{prefix}/analytics", rest_handlers.analytics_handler)
    app.router.add_get(f"{prefix}/dashboard", rest_handlers.dashboard_handler)
    app.router.add_get(f"{prefix}/mobile/feed", rest_handlers.mobile_feed_handler)

    # Sprint 6.2 — Vehicle Catalog & Inventory Engine
    catalog = f"{prefix}/catalog"
    app.router.add_get(f"{catalog}/vehicles", catalog_handlers.catalog_list_handler)
    app.router.add_post(f"{catalog}/vehicles", catalog_handlers.catalog_create_handler)
    app.router.add_get(f"{catalog}/vehicles/{{vehicle_id}}", catalog_handlers.catalog_get_handler)
    app.router.add_patch(f"{catalog}/vehicles/{{vehicle_id}}", catalog_handlers.catalog_update_handler)
    app.router.add_post(f"{catalog}/vehicles/{{vehicle_id}}/archive", catalog_handlers.catalog_archive_handler)
    app.router.add_post(f"{catalog}/vehicles/{{vehicle_id}}/restore", catalog_handlers.catalog_restore_handler)
    app.router.add_post(f"{catalog}/vehicles/bulk/import", catalog_handlers.catalog_bulk_import_handler)
    app.router.add_post(f"{catalog}/vehicles/bulk/update", catalog_handlers.catalog_bulk_update_handler)
    app.router.add_post(f"{catalog}/vin/validate", catalog_handlers.catalog_vin_validate_handler)
    app.router.add_get(f"{catalog}/vehicles/{{vehicle_id}}/duplicates", catalog_handlers.catalog_duplicates_handler)

    inv = f"{prefix}/inventory"
    app.router.add_get(f"{inv}/availability", catalog_handlers.inventory_availability_handler)
    app.router.add_get(f"{inv}/dealers/{{dealer_id}}", catalog_handlers.inventory_dealer_handler)
    app.router.add_post(f"{inv}/vehicles/{{vehicle_id}}/reserve", catalog_handlers.inventory_reserve_handler)
    app.router.add_post(f"{inv}/vehicles/{{vehicle_id}}/sold", catalog_handlers.inventory_sold_handler)
    app.router.add_post(f"{inv}/vehicles/{{vehicle_id}}/incoming", catalog_handlers.inventory_incoming_handler)

    app.router.add_get(f"{prefix}/catalog/search", catalog_handlers.search_catalog_handler)

    app.router.add_get(f"{prefix}/vehicles/{{vehicle_id}}/media", catalog_handlers.media_list_handler)
    app.router.add_post(f"{prefix}/vehicles/{{vehicle_id}}/media", catalog_handlers.media_upload_handler)
    app.router.add_post(f"{prefix}/vehicles/{{vehicle_id}}/media/reorder", catalog_handlers.media_reorder_handler)
    app.router.add_post(f"{prefix}/media/{{media_id}}/optimize", catalog_handlers.media_optimize_handler)

    # Sprint 6.3 — CRM & Sales Pipeline Engine
    crm = f"{prefix}/crm"
    app.router.add_get(f"{crm}/metrics", crm_handlers.crm_metrics_handler)
    app.router.add_get(f"{crm}/customers", crm_handlers.list_customers_handler)
    app.router.add_post(f"{crm}/customers", crm_handlers.create_customer_handler)
    app.router.add_get(f"{crm}/customers/{{customer_id}}", crm_handlers.get_customer_handler)
    app.router.add_get(f"{crm}/customers/{{customer_id}}/timeline", crm_handlers.customer_timeline_handler)
    app.router.add_get(f"{crm}/leads", crm_handlers.list_leads_handler)
    app.router.add_post(f"{crm}/leads", crm_handlers.create_lead_handler)
    app.router.add_post(f"{crm}/leads/{{lead_id}}/qualify", crm_handlers.qualify_lead_handler)
    app.router.add_get(f"{crm}/leads/{{lead_id}}/next-action", crm_handlers.ai_next_action_handler)
    app.router.add_get(f"{crm}/deals", crm_handlers.list_deals_handler)
    app.router.add_post(f"{crm}/deals", crm_handlers.create_deal_handler)
    app.router.add_post(f"{crm}/deals/{{deal_id}}/advance", crm_handlers.advance_deal_handler)
    app.router.add_post(f"{crm}/deals/{{deal_id}}/win", crm_handlers.win_deal_handler)
    app.router.add_post(f"{crm}/deals/{{deal_id}}/lose", crm_handlers.lose_deal_handler)
    app.router.add_get(f"{crm}/pipeline", crm_handlers.pipeline_view_handler)
    app.router.add_get(f"{crm}/pipeline/forecast", crm_handlers.pipeline_forecast_handler)
    app.router.add_get(f"{crm}/pipeline/conversion", crm_handlers.pipeline_conversion_handler)
    app.router.add_get(f"{crm}/tasks", crm_handlers.list_tasks_handler)
    app.router.add_post(f"{crm}/tasks", crm_handlers.create_task_handler)
    app.router.add_post(f"{crm}/activities/calls", crm_handlers.log_call_handler)
    app.router.add_post(f"{crm}/activities/emails", crm_handlers.log_email_handler)
    app.router.add_post(f"{crm}/calendar/meetings", crm_handlers.schedule_meeting_handler)

    # Sprint 6.4 — AI Sales Agents & Customer Intelligence
    ai = f"{prefix}/ai"
    app.router.add_get(f"{ai}", auto_ai_handlers.auto_ai_health_handler)
    app.router.add_get(f"{ai}/metrics", ai_sales_handlers.ai_sales_metrics_handler)
    app.router.add_post(f"{ai}/agents/dispatch", ai_sales_handlers.dispatch_agent_handler)
    app.router.add_get(f"{ai}/customers/{{customer_id}}/intelligence", ai_sales_handlers.customer_intelligence_handler)
    app.router.add_get(f"{ai}/customers/{{customer_id}}/intent", ai_sales_handlers.customer_intent_handler)
    app.router.add_get(f"{ai}/customers/{{customer_id}}/communications", ai_sales_handlers.customer_communication_history_handler)
    app.router.add_get(f"{ai}/customers/{{customer_id}}/recommendations", ai_sales_handlers.recommendations_personalized_handler)
    app.router.add_get(f"{ai}/customers/{{customer_id}}/recommendations/cross-sell", ai_sales_handlers.recommendations_cross_sell_handler)
    app.router.add_get(f"{ai}/customers/{{customer_id}}/recommendations/trade-in", ai_sales_handlers.recommendations_trade_in_handler)
    app.router.add_get(f"{ai}/vehicles/{{vehicle_id}}/recommendations/alternatives", ai_sales_handlers.recommendations_alternatives_handler)
    app.router.add_get(f"{ai}/vehicles/{{vehicle_id}}/recommendations/accessories", ai_sales_handlers.recommendations_accessories_handler)
    app.router.add_post(f"{ai}/recommendations/upsell", ai_sales_handlers.recommendations_upsell_handler)
    app.router.add_get(f"{ai}/leads/{{lead_id}}/intelligence", ai_sales_handlers.lead_intelligence_handler)
    app.router.add_post(f"{ai}/leads/{{lead_id}}/qualify", ai_sales_handlers.qualify_lead_ai_handler)
    app.router.add_post(f"{ai}/leads/setup", ai_sales_handlers.create_lead_for_ai_test_handler)
    app.router.add_post(f"{ai}/conversations", ai_sales_handlers.start_conversation_handler)
    app.router.add_post(f"{ai}/conversations/{{session_id}}/turns", ai_sales_handlers.append_conversation_turn_handler)
    app.router.add_post(f"{ai}/conversations/{{session_id}}/summarize", ai_sales_handlers.summarize_conversation_handler)
    app.router.add_get(f"{ai}/customers/{{customer_id}}/conversations/context", ai_sales_handlers.conversation_context_handler)
    app.router.add_post(f"{ai}/offers", ai_sales_handlers.generate_offer_handler)
    app.router.add_post(f"{ai}/offers/{{offer_id}}/negotiate", ai_sales_handlers.negotiate_offer_handler)
    app.router.add_get(f"{ai}/knowledge/search", ai_sales_handlers.knowledge_search_handler)
    app.router.add_post(f"{ai}/workflows/onboard", ai_sales_handlers.onboard_customer_handler)
    app.router.add_post(f"{ai}/workflows/follow-up", ai_sales_handlers.schedule_follow_up_ai_handler)

    # Sprint 10.4 — Auctions, Financing, Insurance & Vehicle Transactions
    app.router.add_get(f"{prefix}/auctions", transaction_handlers.auctions_list_create_handler)
    app.router.add_post(f"{prefix}/auctions", transaction_handlers.auctions_list_create_handler)
    app.router.add_get(f"{prefix}/auctions/health", transaction_handlers.auctions_health_handler)
    app.router.add_post(f"{prefix}/auctions/{{auction_id}}/start", transaction_handlers.auctions_start_handler)
    app.router.add_post(f"{prefix}/auctions/{{auction_id}}/bids", transaction_handlers.auctions_bid_handler)
    app.router.add_post(f"{prefix}/auctions/{{auction_id}}/auto-bid", transaction_handlers.auctions_auto_bid_handler)
    app.router.add_post(f"{prefix}/auctions/{{auction_id}}/buy-now", transaction_handlers.auctions_buy_now_handler)
    app.router.add_post(f"{prefix}/auctions/{{auction_id}}/close", transaction_handlers.auctions_close_handler)

    app.router.add_get(f"{prefix}/leasing", transaction_handlers.leasing_health_handler)
    app.router.add_post(f"{prefix}/leasing/quote", transaction_handlers.leasing_quote_handler)
    app.router.add_post(f"{prefix}/leasing/compare", transaction_handlers.leasing_compare_handler)
    app.router.add_post(
        f"{prefix}/leasing/{{lease_id}}/contract",
        transaction_handlers.leasing_contract_handler,
    )

    app.router.add_get(f"{prefix}/insurance", transaction_handlers.insurance_health_handler)
    app.router.add_post(f"{prefix}/insurance/quote", transaction_handlers.insurance_quote_handler)
    app.router.add_post(f"{prefix}/insurance/compare", transaction_handlers.insurance_compare_handler)
    app.router.add_post(
        f"{prefix}/insurance/{{quote_id}}/claims",
        transaction_handlers.insurance_claim_handler,
    )

    app.router.add_get(f"{prefix}/transactions", transaction_handlers.transactions_list_create_handler)
    app.router.add_post(f"{prefix}/transactions", transaction_handlers.transactions_list_create_handler)
    app.router.add_get(f"{prefix}/transactions/health", transaction_handlers.transactions_health_handler)
    app.router.add_post(
        f"{prefix}/transactions/{{transaction_id}}/reserve",
        transaction_handlers.transactions_reserve_handler,
    )
    app.router.add_post(
        f"{prefix}/transactions/{{transaction_id}}/offer",
        transaction_handlers.transactions_offer_handler,
    )
    app.router.add_post(
        f"{prefix}/transactions/{{transaction_id}}/counter",
        transaction_handlers.transactions_counter_handler,
    )
    app.router.add_post(
        f"{prefix}/transactions/{{transaction_id}}/contract",
        transaction_handlers.transactions_contract_handler,
    )
    app.router.add_post(
        f"{prefix}/transactions/{{transaction_id}}/sign",
        transaction_handlers.transactions_sign_handler,
    )
    app.router.add_post(
        f"{prefix}/transactions/{{transaction_id}}/pay",
        transaction_handlers.transactions_pay_handler,
    )
    app.router.add_post(
        f"{prefix}/transactions/{{transaction_id}}/transfer",
        transaction_handlers.transactions_transfer_handler,
    )
    app.router.add_post(
        f"{prefix}/transactions/{{transaction_id}}/deliver",
        transaction_handlers.transactions_deliver_handler,
    )
    app.router.add_post(
        f"{prefix}/transactions/{{transaction_id}}/complete",
        transaction_handlers.transactions_complete_handler,
    )

    app.router.add_get(f"{prefix}/payments", transaction_handlers.payments_list_create_handler)
    app.router.add_post(f"{prefix}/payments", transaction_handlers.payments_list_create_handler)
    app.router.add_post(
        f"{prefix}/payments/{{payment_id}}/capture",
        transaction_handlers.payments_capture_handler,
    )
    app.router.add_post(
        f"{prefix}/payments/{{payment_id}}/refund",
        transaction_handlers.payments_refund_handler,
    )
    app.router.add_post(f"{prefix}/payments/installments", transaction_handlers.payments_installments_handler)

    # Sprint 6.5 — Documents, Contracts & Financial Operations
    fin = f"{prefix}/finance"
    app.router.add_get(f"{fin}/metrics", finance_handlers.finance_metrics_handler)
    app.router.add_post(f"{fin}/calculator", transaction_handlers.finance_calculator_handler)
    app.router.add_post(f"{fin}/compare", transaction_handlers.finance_compare_handler)
    app.router.add_get(f"{fin}/loans", transaction_handlers.finance_loans_handler)
    app.router.add_post(f"{fin}/loans", transaction_handlers.finance_loans_handler)
    app.router.add_post(f"{fin}/loans/{{offer_id}}/approve", transaction_handlers.finance_approve_handler)
    app.router.add_get(f"{fin}/documents/templates", finance_handlers.list_document_templates_handler)
    app.router.add_post(f"{fin}/documents/generate", finance_handlers.generate_document_handler)
    app.router.add_get(f"{fin}/documents/{{document_id}}", finance_handlers.get_document_handler)
    app.router.add_post(f"{fin}/documents/{{document_id}}/approve", finance_handlers.approve_document_handler)
    app.router.add_get(f"{fin}/documents/{{document_id}}/export", finance_handlers.export_document_handler)
    app.router.add_post(f"{fin}/contracts", finance_handlers.create_contract_handler)
    app.router.add_get(f"{fin}/contracts/{{contract_id}}", finance_handlers.get_contract_handler)
    app.router.add_post(f"{fin}/contracts/{{contract_id}}/sign", finance_handlers.sign_contract_handler)
    app.router.add_get(f"{fin}/contracts/{{contract_id}}/analyze", finance_handlers.analyze_contract_handler)
    app.router.add_post(f"{fin}/payments", finance_handlers.create_payment_handler)
    app.router.add_post(f"{fin}/payments/{{payment_id}}/capture", finance_handlers.capture_payment_handler)
    app.router.add_post(f"{fin}/invoices", finance_handlers.generate_invoice_handler)
    app.router.add_post(f"{fin}/refunds", finance_handlers.request_refund_handler)
    app.router.add_post(f"{fin}/refunds/{{refund_id}}/process", finance_handlers.process_refund_handler)
    app.router.add_post(f"{fin}/settlements", finance_handlers.create_settlement_handler)
    app.router.add_post(f"{fin}/settlements/{{settlement_id}}/complete", finance_handlers.complete_settlement_handler)
    app.router.add_get(f"{fin}/reports/summary", finance_handlers.financial_report_handler)
    app.router.add_get(f"{fin}/audit", finance_handlers.audit_log_handler)

    # Sprint 6.6 — Business Intelligence & Executive Dashboard
    bi = f"{prefix}/bi"
    app.router.add_get(f"{bi}/metrics", bi_handlers.bi_metrics_handler)
    app.router.add_get(f"{bi}/dashboard/{{role}}", bi_handlers.dashboard_handler)
    app.router.add_get(f"{bi}/dashboard", bi_handlers.dashboard_handler)
    app.router.add_get(f"{bi}/kpis", bi_handlers.kpi_handler)
    app.router.add_get(f"{bi}/kpis/{{name}}", bi_handlers.kpi_single_handler)
    app.router.add_get(f"{bi}/analytics", bi_handlers.analytics_handler)
    app.router.add_get(f"{bi}/analytics/{{domain}}", bi_handlers.analytics_handler)
    app.router.add_get(f"{bi}/forecast/{{type}}", bi_handlers.forecast_handler)
    app.router.add_get(f"{bi}/forecast", bi_handlers.forecast_handler)
    app.router.add_post(f"{bi}/reports", bi_handlers.generate_report_handler)
    app.router.add_get(f"{bi}/reports/{{report_id}}/export", bi_handlers.export_report_handler)
    app.router.add_get(f"{bi}/insights", bi_handlers.insights_handler)
    app.router.add_get(f"{bi}/statistics", bi_handlers.statistics_handler)
    app.router.add_get(f"{bi}/charts/{{type}}", bi_handlers.visualizations_handler)

    # Sprint 6.7 — Customer Portal, Dealer Portal & Mobile API
    portal = f"{prefix}/portal"
    app.router.add_get(f"{portal}/metrics", portal_handlers.portal_metrics_handler)
    app.router.add_post(f"{portal}/auth/register", portal_handlers.register_customer_handler)
    app.router.add_post(f"{portal}/auth/login", portal_handlers.login_handler)
    app.router.add_post(f"{portal}/auth/oauth", portal_handlers.oauth_login_handler)
    app.router.add_route("*", f"{portal}/customer/profile", portal_handlers.customer_profile_handler)
    app.router.add_route("*", f"{portal}/customer/search", portal_handlers.customer_search_handler)
    app.router.add_post(f"{portal}/customer/search/smart", portal_handlers.smart_search_handler)
    app.router.add_route("*", f"{portal}/customer/favorites", portal_handlers.favorites_list_handler)
    app.router.add_route("*", f"{portal}/customer/saved-searches", portal_handlers.saved_searches_handler)
    app.router.add_route("*", f"{portal}/customer/garage", portal_handlers.garage_handler)
    app.router.add_get(f"{portal}/customer/history", portal_handlers.purchase_history_handler)
    app.router.add_post(f"{portal}/customer/test-drive", portal_handlers.test_drive_handler)
    app.router.add_post(f"{portal}/customer/trade-in", portal_handlers.trade_in_handler)
    app.router.add_post(f"{portal}/customer/offers", portal_handlers.offer_request_handler)
    app.router.add_post(f"{portal}/customer/assistant", portal_handlers.customer_ai_handler)
    app.router.add_get(f"{portal}/customer/recommendations", portal_handlers.customer_recommendations_handler)
    app.router.add_get(f"{portal}/customer/notifications", portal_handlers.portal_notifications_handler)
    app.router.add_post(f"{portal}/customer/vehicles/{{vehicle_id}}/view", portal_handlers.view_vehicle_handler)
    app.router.add_get(f"{portal}/dealer/dashboard", portal_handlers.dealer_dashboard_handler)
    app.router.add_route("*", f"{portal}/dealer/inventory", portal_handlers.dealer_inventory_handler)
    app.router.add_get(f"{portal}/dealer/leads", portal_handlers.dealer_leads_handler)
    app.router.add_get(f"{portal}/dealer/sales", portal_handlers.dealer_sales_handler)
    app.router.add_get(f"{portal}/dealer/analytics", portal_handlers.dealer_analytics_handler)
    app.router.add_get(f"{portal}/dealer/finance", portal_handlers.dealer_finance_handler)
    app.router.add_get(f"{portal}/dealer/documents", portal_handlers.dealer_documents_handler)

    mobile = config.mobile_api_prefix
    app.router.add_get(f"{mobile}/info", portal_handlers.mobile_info_handler)
    app.router.add_get(f"{mobile}/feed", portal_handlers.mobile_feed_handler)
    app.router.add_get(f"{mobile}/sync", portal_handlers.mobile_sync_handler)
    app.router.add_post(f"{mobile}/push/register", portal_handlers.mobile_push_register_handler)

    pub = f"{prefix}/public"
    app.router.add_get(f"{pub}/search", portal_handlers.public_search_handler)
    app.router.add_get(f"{pub}/vehicles/{{vehicle_id}}", portal_handlers.public_vehicle_handler)
    app.router.add_get(f"{pub}/stats", portal_handlers.public_stats_handler)

    partner = config.partner_api_prefix
    app.router.add_post(f"{partner}/connect", portal_handlers.partner_connect_handler)
    app.router.add_post(f"{partner}/insurance/quote", portal_handlers.partner_insurance_handler)
    app.router.add_post(f"{partner}/financing/quote", portal_handlers.partner_financing_handler)
    app.router.add_post(f"{partner}/inspection/schedule", portal_handlers.partner_inspection_handler)
    app.router.add_post(f"{partner}/logistics/schedule", portal_handlers.partner_logistics_handler)
    app.router.add_post(f"{partner}/webhooks", portal_handlers.partner_webhook_handler)

    # Sprint 6.8 — Production Release & Operations
    ops = f"{prefix}/ops"
    app.router.add_get(f"{ops}/health", ops_handlers.ops_health_handler)
    app.router.add_get(f"{ops}/ready", ops_handlers.ops_readiness_handler)
    app.router.add_get(f"{ops}/live", ops_handlers.ops_liveness_handler)
    app.router.add_get(f"{ops}/metrics", ops_handlers.ops_metrics_handler)
    app.router.add_get(f"{ops}/release/report", ops_handlers.release_report_handler)
    app.router.add_get(f"{ops}/release/manifest", ops_handlers.release_manifest_handler)
    app.router.add_get(f"{ops}/deployment/checklist", ops_handlers.deployment_checklist_handler)
    app.router.add_get(f"{ops}/deployment/preflight", ops_handlers.deployment_preflight_handler)
    app.router.add_get(f"{ops}/deployment/rollback", ops_handlers.rollback_procedure_handler)
    app.router.add_post(f"{ops}/backups", ops_handlers.backup_create_handler)
    app.router.add_get(f"{ops}/backups/procedures", ops_handlers.backup_procedures_handler)
    app.router.add_get(f"{ops}/maintenance", ops_handlers.maintenance_status_handler)
    app.router.add_post(f"{ops}/maintenance/enable", ops_handlers.maintenance_enable_handler)
    app.router.add_post(f"{ops}/maintenance/disable", ops_handlers.maintenance_disable_handler)
    app.router.add_get(f"{ops}/support", ops_handlers.support_guide_handler)
    app.router.add_get(f"{ops}/guides/admin", ops_handlers.admin_guide_handler)
    app.router.add_get(f"{ops}/guides/user", ops_handlers.user_guide_handler)
    app.router.add_get(f"{ops}/incidents", ops_handlers.incident_guide_handler)
    app.router.add_get(f"{ops}/observability", ops_handlers.observability_handler)

    # Internal API
    app.router.add_get(f"{internal}/health", internal_handlers.internal_health_handler)
    app.router.add_get(f"{internal}/pipeline", internal_handlers.internal_pipeline_handler)
    app.router.add_get(f"{internal}/inventory", internal_handlers.internal_inventory_handler)
    app.router.add_post(f"{internal}/deals", internal_handlers.internal_create_deal_handler)
    app.router.add_post(f"{internal}/payments", internal_handlers.internal_create_payment_handler)
    app.router.add_post(f"{internal}/payments/{{payment_id}}/capture", internal_handlers.internal_capture_payment_handler)
    app.router.add_post(f"{internal}/ai/pricing", internal_handlers.internal_ai_pricing_handler)
    app.router.add_post(f"{internal}/ai/plan", internal_handlers.internal_ai_plan_handler)

    # Webhooks
    app.router.add_post(f"{webhooks_prefix}/payments", webhooks.payment_webhook_handler)
    app.router.add_post(f"{webhooks_prefix}/delivery", webhooks.delivery_webhook_handler)
    app.router.add_post(f"{webhooks_prefix}/crm", webhooks.crm_webhook_handler)
