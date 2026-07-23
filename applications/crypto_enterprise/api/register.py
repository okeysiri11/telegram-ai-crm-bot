"""Register Crypto Enterprise routes (Sprint 16.0)."""

from __future__ import annotations

from aiohttp import web

from applications.crypto_enterprise.api import handlers, ta_handlers
from applications.crypto_enterprise.api.middleware import auth_middleware
from applications.crypto_enterprise.config import DEFAULT_CONFIG


def register_crypto_enterprise_routes(app: web.Application) -> None:
    prefix = DEFAULT_CONFIG.api_prefix
    if auth_middleware not in app.middlewares:
        app.middlewares.append(auth_middleware)

    app.router.add_get(f"{prefix}/health", handlers.health_handler)
    app.router.add_post(f"{prefix}/bootstrap", handlers.bootstrap_handler)
    app.router.add_get(f"{prefix}/exchanges", handlers.exchanges_handler)
    app.router.add_post(f"{prefix}/exchanges", handlers.exchanges_handler)
    app.router.add_get(f"{prefix}/markets", handlers.markets_handler)
    app.router.add_post(f"{prefix}/markets", handlers.markets_handler)
    app.router.add_get(f"{prefix}/assets", handlers.assets_handler)
    app.router.add_post(f"{prefix}/assets", handlers.assets_handler)
    app.router.add_get(f"{prefix}/portfolio", handlers.portfolio_handler)
    app.router.add_post(f"{prefix}/portfolio", handlers.portfolio_handler)
    app.router.add_get(f"{prefix}/dashboard", handlers.dashboard_handler)
    app.router.add_post(f"{prefix}/dashboard", handlers.dashboard_handler)
    app.router.add_get(f"{prefix}/knowledge", handlers.knowledge_handler)
    app.router.add_post(f"{prefix}/knowledge", handlers.knowledge_handler)

    # Sprint 16.1 — Technical Analysis (additive; prior routes unchanged)
    ta = DEFAULT_CONFIG.technical_analysis_api_prefix
    app.router.add_get(f"{ta}/health", ta_handlers.ta_health_handler)
    app.router.add_post(f"{ta}/bootstrap", ta_handlers.ta_bootstrap_handler)
    app.router.add_get(f"{ta}/tradingview", ta_handlers.ta_tradingview_handler)
    app.router.add_post(f"{ta}/tradingview", ta_handlers.ta_tradingview_handler)
    app.router.add_get(f"{ta}/charts", ta_handlers.ta_charts_handler)
    app.router.add_post(f"{ta}/charts", ta_handlers.ta_charts_handler)
    app.router.add_get(f"{ta}/indicators", ta_handlers.ta_indicators_handler)
    app.router.add_post(f"{ta}/indicators", ta_handlers.ta_indicators_handler)
    app.router.add_get(f"{ta}/structures", ta_handlers.ta_structures_handler)
    app.router.add_post(f"{ta}/structures", ta_handlers.ta_structures_handler)
    app.router.add_get(f"{ta}/patterns", ta_handlers.ta_patterns_handler)
    app.router.add_post(f"{ta}/patterns", ta_handlers.ta_patterns_handler)
    app.router.add_get(f"{ta}/ai", ta_handlers.ta_ai_handler)
    app.router.add_post(f"{ta}/ai", ta_handlers.ta_ai_handler)
    app.router.add_get(f"{ta}/dashboard", ta_handlers.ta_dashboard_handler)
    app.router.add_post(f"{ta}/dashboard", ta_handlers.ta_dashboard_handler)
    app.router.add_get(f"{ta}/knowledge", ta_handlers.ta_knowledge_handler)
    app.router.add_post(f"{ta}/knowledge", ta_handlers.ta_knowledge_handler)
