"""Register Crypto Enterprise routes (Sprint 16.0)."""

from __future__ import annotations

from aiohttp import web

from applications.crypto_enterprise.api import (
    handlers,
    mi_handlers,
    mm_handlers,
    oc_handlers,
    rm_handlers,
    se_handlers,
    ta_handlers,
)
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

    # Sprint 16.2 — Market Microstructure (additive; prior routes unchanged)
    mm = DEFAULT_CONFIG.market_microstructure_api_prefix
    app.router.add_get(f"{mm}/health", mm_handlers.mm_health_handler)
    app.router.add_post(f"{mm}/bootstrap", mm_handlers.mm_bootstrap_handler)
    app.router.add_get(f"{mm}/order-book", mm_handlers.mm_order_book_handler)
    app.router.add_post(f"{mm}/order-book", mm_handlers.mm_order_book_handler)
    app.router.add_get(f"{mm}/trade-flow", mm_handlers.mm_trade_flow_handler)
    app.router.add_post(f"{mm}/trade-flow", mm_handlers.mm_trade_flow_handler)
    app.router.add_get(f"{mm}/derivatives", mm_handlers.mm_derivatives_handler)
    app.router.add_post(f"{mm}/derivatives", mm_handlers.mm_derivatives_handler)
    app.router.add_get(f"{mm}/liquidations", mm_handlers.mm_liquidations_handler)
    app.router.add_post(f"{mm}/liquidations", mm_handlers.mm_liquidations_handler)
    app.router.add_get(f"{mm}/liquidity", mm_handlers.mm_liquidity_handler)
    app.router.add_post(f"{mm}/liquidity", mm_handlers.mm_liquidity_handler)
    app.router.add_get(f"{mm}/ai", mm_handlers.mm_ai_handler)
    app.router.add_post(f"{mm}/ai", mm_handlers.mm_ai_handler)
    app.router.add_get(f"{mm}/dashboard", mm_handlers.mm_dashboard_handler)
    app.router.add_post(f"{mm}/dashboard", mm_handlers.mm_dashboard_handler)
    app.router.add_get(f"{mm}/knowledge", mm_handlers.mm_knowledge_handler)
    app.router.add_post(f"{mm}/knowledge", mm_handlers.mm_knowledge_handler)

    # Sprint 16.3 — Market Intelligence (additive; prior routes unchanged)
    mi = DEFAULT_CONFIG.market_intelligence_api_prefix
    app.router.add_get(f"{mi}/health", mi_handlers.mi_health_handler)
    app.router.add_post(f"{mi}/bootstrap", mi_handlers.mi_bootstrap_handler)
    app.router.add_get(f"{mi}/news", mi_handlers.mi_news_handler)
    app.router.add_post(f"{mi}/news", mi_handlers.mi_news_handler)
    app.router.add_get(f"{mi}/social", mi_handlers.mi_social_handler)
    app.router.add_post(f"{mi}/social", mi_handlers.mi_social_handler)
    app.router.add_get(f"{mi}/sentiment", mi_handlers.mi_sentiment_handler)
    app.router.add_post(f"{mi}/sentiment", mi_handlers.mi_sentiment_handler)
    app.router.add_get(f"{mi}/fundamentals", mi_handlers.mi_fundamentals_handler)
    app.router.add_post(f"{mi}/fundamentals", mi_handlers.mi_fundamentals_handler)
    app.router.add_get(f"{mi}/macro", mi_handlers.mi_macro_handler)
    app.router.add_post(f"{mi}/macro", mi_handlers.mi_macro_handler)
    app.router.add_get(f"{mi}/correlation", mi_handlers.mi_correlation_handler)
    app.router.add_post(f"{mi}/correlation", mi_handlers.mi_correlation_handler)
    app.router.add_get(f"{mi}/decision", mi_handlers.mi_decision_handler)
    app.router.add_post(f"{mi}/decision", mi_handlers.mi_decision_handler)
    app.router.add_get(f"{mi}/dashboard", mi_handlers.mi_dashboard_handler)
    app.router.add_post(f"{mi}/dashboard", mi_handlers.mi_dashboard_handler)
    app.router.add_get(f"{mi}/knowledge", mi_handlers.mi_knowledge_handler)
    app.router.add_post(f"{mi}/knowledge", mi_handlers.mi_knowledge_handler)

    # Sprint 16.4 — Strategy Engine (additive; prior routes unchanged)
    se = DEFAULT_CONFIG.strategy_engine_api_prefix
    app.router.add_get(f"{se}/health", se_handlers.se_health_handler)
    app.router.add_post(f"{se}/bootstrap", se_handlers.se_bootstrap_handler)
    app.router.add_get(f"{se}/strategies", se_handlers.se_strategies_handler)
    app.router.add_post(f"{se}/strategies", se_handlers.se_strategies_handler)
    app.router.add_get(f"{se}/backtesting", se_handlers.se_backtesting_handler)
    app.router.add_post(f"{se}/backtesting", se_handlers.se_backtesting_handler)
    app.router.add_get(f"{se}/performance", se_handlers.se_performance_handler)
    app.router.add_post(f"{se}/performance", se_handlers.se_performance_handler)
    app.router.add_get(f"{se}/signals", se_handlers.se_signals_handler)
    app.router.add_post(f"{se}/signals", se_handlers.se_signals_handler)
    app.router.add_get(f"{se}/portfolio", se_handlers.se_portfolio_handler)
    app.router.add_post(f"{se}/portfolio", se_handlers.se_portfolio_handler)
    app.router.add_get(f"{se}/ai", se_handlers.se_ai_handler)
    app.router.add_post(f"{se}/ai", se_handlers.se_ai_handler)
    app.router.add_get(f"{se}/dashboard", se_handlers.se_dashboard_handler)
    app.router.add_post(f"{se}/dashboard", se_handlers.se_dashboard_handler)
    app.router.add_get(f"{se}/knowledge", se_handlers.se_knowledge_handler)
    app.router.add_post(f"{se}/knowledge", se_handlers.se_knowledge_handler)

    # Sprint 16.5 — Risk Management (additive; prior routes unchanged)
    rm = DEFAULT_CONFIG.risk_management_api_prefix
    app.router.add_get(f"{rm}/health", rm_handlers.rm_health_handler)
    app.router.add_post(f"{rm}/bootstrap", rm_handlers.rm_bootstrap_handler)
    app.router.add_get(f"{rm}/sizing", rm_handlers.rm_sizing_handler)
    app.router.add_post(f"{rm}/sizing", rm_handlers.rm_sizing_handler)
    app.router.add_get(f"{rm}/analytics", rm_handlers.rm_analytics_handler)
    app.router.add_post(f"{rm}/analytics", rm_handlers.rm_analytics_handler)
    app.router.add_get(f"{rm}/optimization", rm_handlers.rm_optimization_handler)
    app.router.add_post(f"{rm}/optimization", rm_handlers.rm_optimization_handler)
    app.router.add_get(f"{rm}/models", rm_handlers.rm_models_handler)
    app.router.add_post(f"{rm}/models", rm_handlers.rm_models_handler)
    app.router.add_get(f"{rm}/protection", rm_handlers.rm_protection_handler)
    app.router.add_post(f"{rm}/protection", rm_handlers.rm_protection_handler)
    app.router.add_get(f"{rm}/ai", rm_handlers.rm_ai_handler)
    app.router.add_post(f"{rm}/ai", rm_handlers.rm_ai_handler)
    app.router.add_get(f"{rm}/dashboard", rm_handlers.rm_dashboard_handler)
    app.router.add_post(f"{rm}/dashboard", rm_handlers.rm_dashboard_handler)
    app.router.add_get(f"{rm}/knowledge", rm_handlers.rm_knowledge_handler)
    app.router.add_post(f"{rm}/knowledge", rm_handlers.rm_knowledge_handler)

    # Sprint 16.6 — On-Chain Intelligence (additive; prior routes unchanged)
    oc = DEFAULT_CONFIG.onchain_intelligence_api_prefix
    app.router.add_get(f"{oc}/health", oc_handlers.oc_health_handler)
    app.router.add_post(f"{oc}/bootstrap", oc_handlers.oc_bootstrap_handler)
    app.router.add_get(f"{oc}/chains", oc_handlers.oc_chains_handler)
    app.router.add_post(f"{oc}/chains", oc_handlers.oc_chains_handler)
    app.router.add_get(f"{oc}/wallets", oc_handlers.oc_wallets_handler)
    app.router.add_post(f"{oc}/wallets", oc_handlers.oc_wallets_handler)
    app.router.add_get(f"{oc}/transactions", oc_handlers.oc_transactions_handler)
    app.router.add_post(f"{oc}/transactions", oc_handlers.oc_transactions_handler)
    app.router.add_get(f"{oc}/stablecoins", oc_handlers.oc_stablecoins_handler)
    app.router.add_post(f"{oc}/stablecoins", oc_handlers.oc_stablecoins_handler)
    app.router.add_get(f"{oc}/defi", oc_handlers.oc_defi_handler)
    app.router.add_post(f"{oc}/defi", oc_handlers.oc_defi_handler)
    app.router.add_get(f"{oc}/nft", oc_handlers.oc_nft_handler)
    app.router.add_post(f"{oc}/nft", oc_handlers.oc_nft_handler)
    app.router.add_get(f"{oc}/ai", oc_handlers.oc_ai_handler)
    app.router.add_post(f"{oc}/ai", oc_handlers.oc_ai_handler)
    app.router.add_get(f"{oc}/dashboard", oc_handlers.oc_dashboard_handler)
    app.router.add_post(f"{oc}/dashboard", oc_handlers.oc_dashboard_handler)
    app.router.add_get(f"{oc}/knowledge", oc_handlers.oc_knowledge_handler)
    app.router.add_post(f"{oc}/knowledge", oc_handlers.oc_knowledge_handler)
