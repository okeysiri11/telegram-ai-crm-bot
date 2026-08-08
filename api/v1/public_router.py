# Public API v1 router — frozen /api/v1 endpoints with legacy /v1 compatibility.

from __future__ import annotations

from aiohttp import web

from api.handlers import (
    ai_advertising_agent_feature_handler,
    ai_advertising_agent_handler,
    ai_conversation_skills_feature_handler,
    ai_conversation_skills_handler,
    ai_procurement_agent_feature_handler,
    ai_procurement_agent_handler,
    ai_sales_agent_feature_handler,
    ai_sales_agent_handler,
    analytics_feature_handler,
    analytics_handler,
    api_info_handler,
    auth_token_handler,
    communication_hub_feature_handler,
    communication_hub_handler,
    cross_posting_feature_handler,
    cross_posting_handler,
    deal_pipeline_feature_handler,
    deal_pipeline_handler,
    deals_create_handler,
    deals_delete_handler,
    deals_get_handler,
    deals_list_handler,
    deals_patch_handler,
    dealer_portal_handler,
    dealer_portal_module_handler,
    documents_create_handler,
    documents_list_handler,
    fx_rates_handler,
    inventory_list_handler,
    lead_marketplace_feature_handler,
    lead_marketplace_handler,
    notifications_create_handler,
    notifications_list_handler,
    orders_create_handler,
    orders_list_handler,
    partners_create_handler,
    partners_list_handler,
    pricing_calculate_handler,
    recommendation_engine_feature_handler,
    recommendation_engine_handler,
    vehicles_create_handler,
    vehicles_list_handler,
)
from api.v1.crm_foundation import (
    clients_create_handler,
    clients_delete_handler,
    clients_get_handler,
    clients_list_handler,
    clients_patch_handler,
    crm_deals_create_handler,
    crm_deals_delete_handler,
    crm_deals_get_handler,
    crm_deals_list_handler,
    crm_deals_patch_handler,
    leads_create_handler,
    leads_delete_handler,
    leads_get_handler,
    leads_list_handler,
    leads_patch_handler,
    reports_get_handler,
    reports_list_handler,
)
from platform_api.contracts import API_CONTRACT_VERSION
from platform_api.versioning import (
    PUBLIC_V1_PREFIX,
    build_public_openapi_spec,
    legacy_public_path,
    public_path,
    record_public_openapi_path,
    register_legacy_public_alias,
    wrap_legacy_handler,
)


async def api_v1_health(_request: web.Request) -> web.Response:
    from platform_api.responses import success_response

    return success_response(
        {
            "status": "ok",
            "api_version": "v1",
            "contract_version": API_CONTRACT_VERSION,
        }
    )


async def public_openapi_handler(_request: web.Request) -> web.Response:
    return web.json_response(build_public_openapi_spec())


async def public_docs_handler(_request: web.Request) -> web.Response:
    html = f"""<!DOCTYPE html>
<html><head><title>Platform Public API v1</title>
<link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
</head><body>
<div id="swagger-ui"></div>
<script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
<script>
SwaggerUIBundle({{url: '{PUBLIC_V1_PREFIX}/openapi.json', dom_id: '#swagger-ui'}});
</script></body></html>"""
    return web.Response(text=html, content_type="text/html")


def _alias(
    app: web.Application,
    method: str,
    suffix: str,
    handler,
    *,
    summary: str,
) -> None:
    v1_path = public_path(suffix)
    legacy_path = legacy_public_path(suffix)
    register_legacy_public_alias(
        app,
        method=method,
        legacy_path=legacy_path,
        v1_path=v1_path,
        handler=handler,
    )
    record_public_openapi_path(v1_path, method, summary=summary)


def register_public_api_v1_routes(app: web.Application) -> None:
    app.router.add_get(PUBLIC_V1_PREFIX, api_v1_health)
    app.router.add_get(f"{PUBLIC_V1_PREFIX}/", api_v1_health)
    app.router.add_get(f"{PUBLIC_V1_PREFIX}/openapi.json", public_openapi_handler)
    app.router.add_get(f"{PUBLIC_V1_PREFIX}/docs", public_docs_handler)
    app.router.add_get(
        legacy_public_path("openapi.json"),
        wrap_legacy_handler(public_openapi_handler, successor=f"{PUBLIC_V1_PREFIX}/openapi.json"),
    )
    app.router.add_get(
        legacy_public_path("docs"),
        wrap_legacy_handler(public_docs_handler, successor=f"{PUBLIC_V1_PREFIX}/docs"),
    )

    _alias(app, "GET", "", api_info_handler, summary="API info")
    _alias(app, "POST", "auth/token", auth_token_handler, summary="Issue auth token")

    _alias(app, "GET", "deals", deals_list_handler, summary="List exchange deals")
    _alias(app, "POST", "deals", deals_create_handler, summary="Create exchange deal")
    _alias(app, "GET", "deals/{deal_id}", deals_get_handler, summary="Get exchange deal")
    _alias(app, "PATCH", "deals/{deal_id}", deals_patch_handler, summary="Update exchange deal status")
    _alias(app, "DELETE", "deals/{deal_id}", deals_delete_handler, summary="Cancel exchange deal")

    # Sprint 40.2 — CRM foundation (leads / clients / CRM deals / reports)
    _alias(app, "GET", "leads", leads_list_handler, summary="List CRM leads")
    _alias(app, "POST", "leads", leads_create_handler, summary="Create CRM lead")
    _alias(app, "GET", "leads/{lead_id}", leads_get_handler, summary="Get CRM lead")
    _alias(app, "PATCH", "leads/{lead_id}", leads_patch_handler, summary="Update CRM lead")
    _alias(app, "DELETE", "leads/{lead_id}", leads_delete_handler, summary="Delete CRM lead")

    _alias(app, "GET", "clients", clients_list_handler, summary="List CRM clients")
    _alias(app, "POST", "clients", clients_create_handler, summary="Create CRM client")
    _alias(app, "GET", "clients/{client_id}", clients_get_handler, summary="Get CRM client")
    _alias(app, "PATCH", "clients/{client_id}", clients_patch_handler, summary="Update CRM client")
    _alias(app, "DELETE", "clients/{client_id}", clients_delete_handler, summary="Delete CRM client")

    _alias(app, "GET", "crm/deals", crm_deals_list_handler, summary="List CRM sales deals")
    _alias(app, "POST", "crm/deals", crm_deals_create_handler, summary="Create CRM sales deal")
    _alias(app, "GET", "crm/deals/{deal_id}", crm_deals_get_handler, summary="Get CRM sales deal")
    _alias(app, "PATCH", "crm/deals/{deal_id}", crm_deals_patch_handler, summary="Update CRM sales deal")
    _alias(app, "DELETE", "crm/deals/{deal_id}", crm_deals_delete_handler, summary="Delete CRM sales deal")

    _alias(app, "GET", "reports", reports_list_handler, summary="List CRM reports")
    _alias(app, "GET", "reports/{report_id}", reports_get_handler, summary="Get CRM report")

    _alias(app, "GET", "partners", partners_list_handler, summary="List partners")
    _alias(app, "POST", "partners", partners_create_handler, summary="Create partner")
    _alias(app, "POST", "pricing/calculate", pricing_calculate_handler, summary="Calculate pricing")
    _alias(app, "GET", "fx/rates", fx_rates_handler, summary="FX rates")
    _alias(app, "GET", "vehicles", vehicles_list_handler, summary="List vehicles")
    _alias(app, "POST", "vehicles", vehicles_create_handler, summary="Create vehicle")
    _alias(app, "GET", "inventory", inventory_list_handler, summary="List inventory")
    _alias(app, "GET", "orders", orders_list_handler, summary="List orders")
    _alias(app, "POST", "orders", orders_create_handler, summary="Create order")
    _alias(app, "GET", "documents", documents_list_handler, summary="List documents")
    _alias(app, "POST", "documents", documents_create_handler, summary="Create document")
    _alias(app, "GET", "notifications", notifications_list_handler, summary="List notifications")
    _alias(app, "POST", "notifications", notifications_create_handler, summary="Create notification")
    _alias(app, "GET", "dealer-portal", dealer_portal_handler, summary="Dealer portal")
    _alias(app, "GET", "dealer-portal/modules/{module}", dealer_portal_module_handler, summary="Dealer portal module")
    _alias(app, "GET", "lead-marketplace", lead_marketplace_handler, summary="Lead marketplace")
    _alias(app, "GET", "lead-marketplace/features/{feature}", lead_marketplace_feature_handler, summary="Lead marketplace feature")
    _alias(app, "GET", "ai-procurement-agent", ai_procurement_agent_handler, summary="AI procurement agent")
    _alias(app, "GET", "ai-procurement-agent/features/{feature}", ai_procurement_agent_feature_handler, summary="AI procurement feature")
    _alias(app, "GET", "ai-advertising-agent", ai_advertising_agent_handler, summary="AI advertising agent")
    _alias(app, "GET", "ai-advertising-agent/features/{feature}", ai_advertising_agent_feature_handler, summary="AI advertising feature")
    _alias(app, "GET", "ai-sales-agent", ai_sales_agent_handler, summary="AI sales agent")
    _alias(app, "GET", "ai-sales-agent/features/{feature}", ai_sales_agent_feature_handler, summary="AI sales feature")
    _alias(app, "GET", "recommendation-engine", recommendation_engine_handler, summary="Recommendation engine")
    _alias(app, "GET", "recommendation-engine/features/{feature}", recommendation_engine_feature_handler, summary="Recommendation feature")
    _alias(app, "GET", "communication-hub", communication_hub_handler, summary="Communication hub")
    _alias(app, "GET", "communication-hub/features/{feature}", communication_hub_feature_handler, summary="Communication hub feature")
    _alias(app, "GET", "ai-conversation-skills", ai_conversation_skills_handler, summary="AI conversation skills")
    _alias(app, "GET", "ai-conversation-skills/features/{feature}", ai_conversation_skills_feature_handler, summary="AI conversation feature")
    _alias(app, "GET", "deal-pipeline", deal_pipeline_handler, summary="Deal pipeline")
    _alias(app, "GET", "deal-pipeline/features/{feature}", deal_pipeline_feature_handler, summary="Deal pipeline feature")
    _alias(app, "GET", "cross-posting", cross_posting_handler, summary="Cross posting")
    _alias(app, "GET", "cross-posting/features/{feature}", cross_posting_feature_handler, summary="Cross posting feature")
    _alias(app, "GET", "analytics", analytics_handler, summary="Analytics")
    _alias(app, "GET", "analytics/features/{feature}", analytics_feature_handler, summary="Analytics feature")

    # Epic 45.1 — Dual Experience modes
    from api.v1.mode_api import (
        mode_change_handler,
        mode_get_handler,
        mode_remember_handler,
        mode_settings_handler,
        mode_status_handler,
        mode_voice_handler,
    )

    _alias(app, "GET", "mode", mode_get_handler, summary="Get work mode")
    _alias(app, "GET", "mode/status", mode_status_handler, summary="Work mode status")
    _alias(app, "POST", "mode/change", mode_change_handler, summary="Change work mode")
    _alias(app, "POST", "mode/voice", mode_voice_handler, summary="Toggle voice mode")
    _alias(app, "POST", "mode/settings", mode_settings_handler, summary="Update mode settings")
    _alias(app, "POST", "mode/remember", mode_remember_handler, summary="Remember default mode")

    # Epic 45.2 — Continuous Memory
    from api.v1.memory_api import (
        memory_context_handler,
        memory_get_handler,
        memory_pin_handler,
        memory_project_handler,
        memory_remove_handler,
        memory_resume_handler,
        memory_save_handler,
        memory_search_handler,
        memory_summary_handler,
        memory_timeline_handler,
        memory_workspace_handler,
    )

    _alias(app, "GET", "memory", memory_get_handler, summary="Memory status")
    _alias(app, "GET", "memory/search", memory_search_handler, summary="Search everywhere")
    _alias(app, "GET", "memory/context", memory_context_handler, summary="Context Engine 2.0")
    _alias(app, "GET", "memory/timeline", memory_timeline_handler, summary="AI Timeline")
    _alias(app, "GET", "memory/resume", memory_resume_handler, summary="AI Resume")
    _alias(app, "GET", "memory/workspace", memory_workspace_handler, summary="AI Workspace")
    _alias(app, "POST", "memory/save", memory_save_handler, summary="Save memory")
    _alias(app, "POST", "memory/summary", memory_summary_handler, summary="Conversation summary")
    _alias(app, "POST", "memory/project", memory_project_handler, summary="Upsert project memory")
    _alias(app, "POST", "memory/pin", memory_pin_handler, summary="Pin memory")
    _alias(app, "DELETE", "memory/remove", memory_remove_handler, summary="Remove memory")
    _alias(app, "POST", "memory/remove", memory_remove_handler, summary="Remove memory (POST)")

    # Epic 45.3 — Universal Automation Engine
    from api.v1.workflows_api import (
        workflows_approve_handler,
        workflows_cancel_handler,
        workflows_clone_handler,
        workflows_create_handler,
        workflows_dashboard_handler,
        workflows_history_handler,
        workflows_jobs_handler,
        workflows_list_handler,
        workflows_remove_handler,
        workflows_run_handler,
        workflows_schedule_handler,
        workflows_status_handler,
        workflows_templates_handler,
    )

    _alias(app, "GET", "workflows", workflows_list_handler, summary="List workflows")
    _alias(app, "GET", "workflows/history", workflows_history_handler, summary="Workflow history")
    _alias(app, "GET", "workflows/templates", workflows_templates_handler, summary="Workflow templates")
    _alias(app, "GET", "workflows/jobs", workflows_jobs_handler, summary="Scheduled jobs")
    _alias(app, "GET", "workflows/status", workflows_status_handler, summary="Workflow/run status")
    _alias(app, "GET", "workflows/dashboard", workflows_dashboard_handler, summary="Owner automation dashboard")
    _alias(app, "POST", "workflows/run", workflows_run_handler, summary="Run workflow")
    _alias(app, "POST", "workflows/create", workflows_create_handler, summary="Create workflow")
    _alias(app, "POST", "workflows/clone", workflows_clone_handler, summary="Clone workflow")
    _alias(app, "POST", "workflows/schedule", workflows_schedule_handler, summary="Schedule workflow")
    _alias(app, "POST", "workflows/approve", workflows_approve_handler, summary="Approve workflow step")
    _alias(app, "POST", "workflows/cancel", workflows_cancel_handler, summary="Cancel workflow run")
    _alias(app, "DELETE", "workflows/remove", workflows_remove_handler, summary="Remove workflow")
    _alias(app, "POST", "workflows/remove", workflows_remove_handler, summary="Remove workflow (POST)")
