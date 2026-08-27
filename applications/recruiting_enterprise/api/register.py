"""Register Recruiting Ops routes (Sprint Recruiting 1.0)."""

from __future__ import annotations

from aiohttp import web

from applications.recruiting_enterprise.api import ops_handlers
from applications.recruiting_enterprise.config import DEFAULT_CONFIG


def register_recruiting_enterprise_routes(app: web.Application) -> None:
    ops = DEFAULT_CONFIG.api_prefix
    app.router.add_get(f"{ops}/health", ops_handlers.ops_health_handler)
    app.router.add_get(f"{ops}/roles", ops_handlers.ops_roles_handler)
    app.router.add_get(f"{ops}/catalogs", ops_handlers.ops_catalogs_handler)
    app.router.add_get(f"{ops}/vanguard/contract", ops_handlers.ops_vanguard_contract_handler)
    app.router.add_post(f"{ops}/vanguard/leads", ops_handlers.ops_vanguard_ingest_handler)
    app.router.add_get(f"{ops}/projects", ops_handlers.ops_projects_handler)
    app.router.add_get(f"{ops}/projects/{{project_key}}", ops_handlers.ops_project_overview_handler)
    app.router.add_get(f"{ops}/projects/{{project_key}}/integration", ops_handlers.ops_project_integration_handler)
    app.router.add_post(f"{ops}/projects/{{project_key}}/integration", ops_handlers.ops_project_integration_handler)
    app.router.add_post(f"{ops}/projects/{{project_key}}/integration/check", ops_handlers.ops_project_integration_handler)
    app.router.add_get(f"{ops}/lookup", ops_handlers.ops_lookup_handler)
    app.router.add_get(f"{ops}/dashboard", ops_handlers.ops_dashboard_handler)
    app.router.add_post(f"{ops}/dashboard", ops_handlers.ops_dashboard_handler)
    app.router.add_get(f"{ops}/analytics", ops_handlers.ops_analytics_handler)
    app.router.add_get(f"{ops}/activity", ops_handlers.ops_activity_handler)
    app.router.add_get(f"{ops}/leads", ops_handlers.ops_leads_handler)
    app.router.add_post(f"{ops}/leads", ops_handlers.ops_leads_handler)
    app.router.add_post(f"{ops}/leads/{{lead_id}}/assign", ops_handlers.ops_lead_assign_handler)
    app.router.add_post(f"{ops}/leads/{{lead_id}}/notes", ops_handlers.ops_lead_note_handler)
    app.router.add_post(f"{ops}/leads/{{lead_id}}/qualify", ops_handlers.ops_lead_qualify_handler)
    app.router.add_post(f"{ops}/leads/{{lead_id}}/convert", ops_handlers.ops_lead_convert_handler)
    app.router.add_get(f"{ops}/candidates", ops_handlers.ops_candidates_handler)
    app.router.add_post(f"{ops}/candidates", ops_handlers.ops_candidates_handler)
    app.router.add_post(f"{ops}/candidates/{{candidate_id}}/stage", ops_handlers.ops_candidate_stage_handler)
    app.router.add_get(f"{ops}/vacancies", ops_handlers.ops_vacancies_handler)
    app.router.add_post(f"{ops}/vacancies", ops_handlers.ops_vacancies_handler)
    app.router.add_get(f"{ops}/campaigns", ops_handlers.ops_campaigns_handler)
    app.router.add_post(f"{ops}/campaigns", ops_handlers.ops_campaigns_handler)
    app.router.add_get(f"{ops}/tasks", ops_handlers.ops_tasks_handler)
    app.router.add_post(f"{ops}/tasks", ops_handlers.ops_tasks_handler)
    app.router.add_post(f"{ops}/tasks/{{task_id}}/complete", ops_handlers.ops_task_complete_handler)
    app.router.add_get(f"{ops}/communications", ops_handlers.ops_communications_handler)
    app.router.add_post(f"{ops}/communications", ops_handlers.ops_communications_handler)
