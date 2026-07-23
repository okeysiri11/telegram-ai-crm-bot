"""Register Legal Enterprise routes (Sprint 17.0+)."""

from __future__ import annotations

from aiohttp import web

from applications.legal_enterprise.api import handlers, ji_handlers, li_handlers
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
