"""Register Legal Enterprise routes (Sprint 17.0+)."""

from __future__ import annotations

from aiohttp import web

from applications.legal_enterprise.api import (
    aa_handlers,
    cm_handlers,
    cp_handlers,
    di_handlers,
    handlers,
    ji_handlers,
    li_handlers,
)
from applications.legal_enterprise.api.middleware import auth_middleware
from applications.legal_enterprise.config import DEFAULT_CONFIG


def register_legal_enterprise_routes(app: web.Application) -> None:
    prefix = DEFAULT_CONFIG.api_prefix
    if auth_middleware not in app.middlewares:
        app.middlewares.append(auth_middleware)

    app.router.add_get(f"{prefix}/health", handlers.health_handler)
    app.router.add_post(f"{prefix}/bootstrap", handlers.bootstrap_handler)
    app.router.add_get(f"{prefix}/registry", handlers.registry_handler)
    app.router.add_post(f"{prefix}/registry", handlers.registry_handler)
    app.router.add_get(f"{prefix}/legislation", handlers.legislation_handler)
    app.router.add_post(f"{prefix}/legislation", handlers.legislation_handler)
    app.router.add_get(f"{prefix}/courts", handlers.courts_handler)
    app.router.add_post(f"{prefix}/courts", handlers.courts_handler)
    app.router.add_get(f"{prefix}/cases", handlers.cases_handler)
    app.router.add_post(f"{prefix}/cases", handlers.cases_handler)
    app.router.add_get(f"{prefix}/dashboard", handlers.dashboard_handler)
    app.router.add_post(f"{prefix}/dashboard", handlers.dashboard_handler)
    app.router.add_get(f"{prefix}/knowledge", handlers.knowledge_handler)
    app.router.add_post(f"{prefix}/knowledge", handlers.knowledge_handler)

    # Sprint 17.1 — Legislation Intelligence (additive; prior routes unchanged)
    li = DEFAULT_CONFIG.legislation_intelligence_api_prefix
    app.router.add_get(f"{li}/health", li_handlers.li_health_handler)
    app.router.add_post(f"{li}/bootstrap", li_handlers.li_bootstrap_handler)
    app.router.add_get(f"{li}/repository", li_handlers.li_repository_handler)
    app.router.add_post(f"{li}/repository", li_handlers.li_repository_handler)
    app.router.add_get(f"{li}/versions", li_handlers.li_versions_handler)
    app.router.add_post(f"{li}/versions", li_handlers.li_versions_handler)
    app.router.add_get(f"{li}/regulatory", li_handlers.li_regulatory_handler)
    app.router.add_post(f"{li}/regulatory", li_handlers.li_regulatory_handler)
    app.router.add_get(f"{li}/search", li_handlers.li_search_handler)
    app.router.add_post(f"{li}/search", li_handlers.li_search_handler)
    app.router.add_get(f"{li}/cross-refs", li_handlers.li_cross_refs_handler)
    app.router.add_post(f"{li}/cross-refs", li_handlers.li_cross_refs_handler)
    app.router.add_get(f"{li}/analysis", li_handlers.li_analysis_handler)
    app.router.add_post(f"{li}/analysis", li_handlers.li_analysis_handler)
    app.router.add_get(f"{li}/dashboard", li_handlers.li_dashboard_handler)
    app.router.add_post(f"{li}/dashboard", li_handlers.li_dashboard_handler)
    app.router.add_get(f"{li}/knowledge", li_handlers.li_knowledge_handler)
    app.router.add_post(f"{li}/knowledge", li_handlers.li_knowledge_handler)

    # Sprint 17.2 — Judicial Intelligence (additive; prior routes unchanged)
    ji = DEFAULT_CONFIG.judicial_intelligence_api_prefix
    app.router.add_get(f"{ji}/health", ji_handlers.ji_health_handler)
    app.router.add_post(f"{ji}/bootstrap", ji_handlers.ji_bootstrap_handler)
    app.router.add_get(f"{ji}/repository", ji_handlers.ji_repository_handler)
    app.router.add_post(f"{ji}/repository", ji_handlers.ji_repository_handler)
    app.router.add_get(f"{ji}/search", ji_handlers.ji_search_handler)
    app.router.add_post(f"{ji}/search", ji_handlers.ji_search_handler)
    app.router.add_get(f"{ji}/case-law", ji_handlers.ji_case_law_handler)
    app.router.add_post(f"{ji}/case-law", ji_handlers.ji_case_law_handler)
    app.router.add_get(f"{ji}/judges", ji_handlers.ji_judges_handler)
    app.router.add_post(f"{ji}/judges", ji_handlers.ji_judges_handler)
    app.router.add_get(f"{ji}/analysis", ji_handlers.ji_analysis_handler)
    app.router.add_post(f"{ji}/analysis", ji_handlers.ji_analysis_handler)
    app.router.add_get(f"{ji}/analytics", ji_handlers.ji_analytics_handler)
    app.router.add_post(f"{ji}/analytics", ji_handlers.ji_analytics_handler)
    app.router.add_get(f"{ji}/dashboard", ji_handlers.ji_dashboard_handler)
    app.router.add_post(f"{ji}/dashboard", ji_handlers.ji_dashboard_handler)
    app.router.add_get(f"{ji}/knowledge", ji_handlers.ji_knowledge_handler)
    app.router.add_post(f"{ji}/knowledge", ji_handlers.ji_knowledge_handler)

    # Sprint 17.3 — Case Management Platform (additive; prior routes unchanged)
    cm = DEFAULT_CONFIG.case_management_api_prefix
    app.router.add_get(f"{cm}/health", cm_handlers.cm_health_handler)
    app.router.add_post(f"{cm}/bootstrap", cm_handlers.cm_bootstrap_handler)
    app.router.add_get(f"{cm}/cases", cm_handlers.cm_cases_handler)
    app.router.add_post(f"{cm}/cases", cm_handlers.cm_cases_handler)
    app.router.add_get(f"{cm}/calendar", cm_handlers.cm_calendar_handler)
    app.router.add_post(f"{cm}/calendar", cm_handlers.cm_calendar_handler)
    app.router.add_get(f"{cm}/deadlines", cm_handlers.cm_deadlines_handler)
    app.router.add_post(f"{cm}/deadlines", cm_handlers.cm_deadlines_handler)
    app.router.add_get(f"{cm}/tasks", cm_handlers.cm_tasks_handler)
    app.router.add_post(f"{cm}/tasks", cm_handlers.cm_tasks_handler)
    app.router.add_get(f"{cm}/documents", cm_handlers.cm_documents_handler)
    app.router.add_post(f"{cm}/documents", cm_handlers.cm_documents_handler)
    app.router.add_get(f"{cm}/ai", cm_handlers.cm_ai_handler)
    app.router.add_post(f"{cm}/ai", cm_handlers.cm_ai_handler)
    app.router.add_get(f"{cm}/dashboard", cm_handlers.cm_dashboard_handler)
    app.router.add_post(f"{cm}/dashboard", cm_handlers.cm_dashboard_handler)
    app.router.add_get(f"{cm}/knowledge", cm_handlers.cm_knowledge_handler)
    app.router.add_post(f"{cm}/knowledge", cm_handlers.cm_knowledge_handler)

    # Sprint 17.4 — Document Intelligence (additive; prior routes unchanged)
    di = DEFAULT_CONFIG.document_intelligence_api_prefix
    app.router.add_get(f"{di}/health", di_handlers.di_health_handler)
    app.router.add_post(f"{di}/bootstrap", di_handlers.di_bootstrap_handler)
    app.router.add_get(f"{di}/contracts", di_handlers.di_contracts_handler)
    app.router.add_post(f"{di}/contracts", di_handlers.di_contracts_handler)
    app.router.add_get(f"{di}/ingest", di_handlers.di_ingest_handler)
    app.router.add_post(f"{di}/ingest", di_handlers.di_ingest_handler)
    app.router.add_get(f"{di}/clauses", di_handlers.di_clauses_handler)
    app.router.add_post(f"{di}/clauses", di_handlers.di_clauses_handler)
    app.router.add_get(f"{di}/risk", di_handlers.di_risk_handler)
    app.router.add_post(f"{di}/risk", di_handlers.di_risk_handler)
    app.router.add_get(f"{di}/comparison", di_handlers.di_comparison_handler)
    app.router.add_post(f"{di}/comparison", di_handlers.di_comparison_handler)
    app.router.add_get(f"{di}/drafting", di_handlers.di_drafting_handler)
    app.router.add_post(f"{di}/drafting", di_handlers.di_drafting_handler)
    app.router.add_get(f"{di}/dashboard", di_handlers.di_dashboard_handler)
    app.router.add_post(f"{di}/dashboard", di_handlers.di_dashboard_handler)
    app.router.add_get(f"{di}/knowledge", di_handlers.di_knowledge_handler)
    app.router.add_post(f"{di}/knowledge", di_handlers.di_knowledge_handler)

    # Sprint 17.5 — Compliance Platform (additive; prior routes unchanged)
    cp = DEFAULT_CONFIG.compliance_api_prefix
    app.router.add_get(f"{cp}/health", cp_handlers.cp_health_handler)
    app.router.add_post(f"{cp}/bootstrap", cp_handlers.cp_bootstrap_handler)
    app.router.add_get(f"{cp}/governance", cp_handlers.cp_governance_handler)
    app.router.add_post(f"{cp}/governance", cp_handlers.cp_governance_handler)
    app.router.add_get(f"{cp}/compliance", cp_handlers.cp_compliance_handler)
    app.router.add_post(f"{cp}/compliance", cp_handlers.cp_compliance_handler)
    app.router.add_get(f"{cp}/licenses", cp_handlers.cp_licenses_handler)
    app.router.add_post(f"{cp}/licenses", cp_handlers.cp_licenses_handler)
    app.router.add_get(f"{cp}/counterparties", cp_handlers.cp_counterparties_handler)
    app.router.add_post(f"{cp}/counterparties", cp_handlers.cp_counterparties_handler)
    app.router.add_get(f"{cp}/aml", cp_handlers.cp_aml_handler)
    app.router.add_post(f"{cp}/aml", cp_handlers.cp_aml_handler)
    app.router.add_get(f"{cp}/risk", cp_handlers.cp_risk_handler)
    app.router.add_post(f"{cp}/risk", cp_handlers.cp_risk_handler)
    app.router.add_get(f"{cp}/ai", cp_handlers.cp_ai_handler)
    app.router.add_post(f"{cp}/ai", cp_handlers.cp_ai_handler)
    app.router.add_get(f"{cp}/dashboard", cp_handlers.cp_dashboard_handler)
    app.router.add_post(f"{cp}/dashboard", cp_handlers.cp_dashboard_handler)
    app.router.add_get(f"{cp}/knowledge", cp_handlers.cp_knowledge_handler)
    app.router.add_post(f"{cp}/knowledge", cp_handlers.cp_knowledge_handler)

    # Sprint 17.6 — AI Legal Assistant (additive; prior routes unchanged)
    aa = DEFAULT_CONFIG.ai_legal_assistant_api_prefix
    app.router.add_get(f"{aa}/health", aa_handlers.aa_health_handler)
    app.router.add_post(f"{aa}/bootstrap", aa_handlers.aa_bootstrap_handler)
    app.router.add_get(f"{aa}/assistant", aa_handlers.aa_assistant_handler)
    app.router.add_post(f"{aa}/assistant", aa_handlers.aa_assistant_handler)
    app.router.add_get(f"{aa}/research", aa_handlers.aa_research_handler)
    app.router.add_post(f"{aa}/research", aa_handlers.aa_research_handler)
    app.router.add_get(f"{aa}/analysis", aa_handlers.aa_analysis_handler)
    app.router.add_post(f"{aa}/analysis", aa_handlers.aa_analysis_handler)
    app.router.add_get(f"{aa}/opinion", aa_handlers.aa_opinion_handler)
    app.router.add_post(f"{aa}/opinion", aa_handlers.aa_opinion_handler)
    app.router.add_get(f"{aa}/documents", aa_handlers.aa_documents_handler)
    app.router.add_post(f"{aa}/documents", aa_handlers.aa_documents_handler)
    app.router.add_get(f"{aa}/knowledge", aa_handlers.aa_knowledge_handler)
    app.router.add_post(f"{aa}/knowledge", aa_handlers.aa_knowledge_handler)
    app.router.add_get(f"{aa}/explain", aa_handlers.aa_explain_handler)
    app.router.add_post(f"{aa}/explain", aa_handlers.aa_explain_handler)
    app.router.add_get(f"{aa}/dashboard", aa_handlers.aa_dashboard_handler)
    app.router.add_post(f"{aa}/dashboard", aa_handlers.aa_dashboard_handler)
