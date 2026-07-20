# Register Auto Marketplace API routes on aiohttp application.

from __future__ import annotations

from aiohttp import web

from applications.auto_marketplace.api import ai_sales_handlers, catalog_handlers, crm_handlers, finance_handlers, internal_handlers, rest_handlers, webhooks
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
    app.router.add_get(f"{prefix}/vehicles", rest_handlers.list_vehicles_handler)
    app.router.add_post(f"{prefix}/vehicles", rest_handlers.create_vehicle_handler)
    app.router.add_get(f"{prefix}/vehicles/{{vehicle_id}}", rest_handlers.get_vehicle_handler)
    app.router.add_get(f"{prefix}/search", rest_handlers.search_vehicles_handler)
    app.router.add_get(f"{prefix}/dealers", rest_handlers.list_dealers_handler)
    app.router.add_post(f"{prefix}/dealers", rest_handlers.create_dealer_handler)
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

    # Sprint 6.5 — Documents, Contracts & Financial Operations
    fin = f"{prefix}/finance"
    app.router.add_get(f"{fin}/metrics", finance_handlers.finance_metrics_handler)
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
