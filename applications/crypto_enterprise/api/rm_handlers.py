"""API handlers — Risk Management (Sprint 16.5)."""

from __future__ import annotations

from aiohttp import web

from applications.crypto_enterprise import crypto_enterprise
from applications.crypto_enterprise.api.middleware import json_response
from applications.crypto_enterprise.shared.exceptions import NotFoundError, ValidationError


async def _read_json(request: web.Request) -> dict:
    try:
        data = await request.json()
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _handle_error(exc: Exception) -> web.Response:
    if isinstance(exc, NotFoundError):
        return json_response({"error": str(exc)}, status=404)
    if isinstance(exc, ValidationError):
        return json_response({"error": str(exc)}, status=400)
    return json_response({"error": str(exc)}, status=500)


def _suite():
    return crypto_enterprise.risk_management


async def rm_health_handler(request: web.Request) -> web.Response:
    health = crypto_enterprise.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "risk_management_ready": health.get("risk_management_ready"),
            "portfolio_optimization_ready": health.get("portfolio_optimization_ready"),
            "position_sizing_ready": health.get("position_sizing_ready"),
            "ai_risk_intelligence_ready": health.get("ai_risk_intelligence_ready"),
            "capital_protection_ready": health.get("capital_protection_ready"),
            "suite": _suite().status(),
        }
    )


async def rm_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def rm_sizing_handler(request: web.Request) -> web.Response:
    try:
        sizing = _suite().sizing
        if request.method == "GET":
            return json_response(sizing.status())
        body = await _read_json(request)
        return json_response(
            sizing.size(
                method=body.get("method", "percentage"),
                symbol=body.get("symbol", ""),
                capital=float(body.get("capital", 0) or 0),
                risk_pct=float(body.get("risk_pct", 1) or 1),
                stop_distance=float(body.get("stop_distance", 0) or 0),
                atr=float(body.get("atr", 0) or 0),
                win_rate=float(body.get("win_rate", 0.55) or 0.55),
                payoff=float(body.get("payoff", 1.5) or 1.5),
                volatility=float(body.get("volatility", 0) or 0),
                max_exposure_pct=float(body.get("max_exposure_pct", 10) or 10),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def rm_analytics_handler(request: web.Request) -> web.Response:
    try:
        analytics = _suite().analytics
        if request.method == "GET":
            return json_response(analytics.status())
        body = await _read_json(request)
        action = body.get("action", "risk_per_trade")
        if action == "portfolio_risk":
            return json_response(
                analytics.portfolio_risk(
                    portfolio_id=body.get("portfolio_id", ""),
                    var_pct=float(body.get("var_pct", 0) or 0),
                    exposure_pct=float(body.get("exposure_pct", 0) or 0),
                ),
                status=201,
            )
        if action == "drawdown":
            return json_response(
                analytics.drawdown(
                    portfolio_id=body.get("portfolio_id", ""),
                    current_dd=float(body.get("current_dd", 0) or 0),
                    max_dd=float(body.get("max_dd", 0) or 0),
                ),
                status=201,
            )
        if action == "loss_limit":
            return json_response(
                analytics.loss_limit(
                    period=body.get("period", "daily"),
                    limit_pct=float(body.get("limit_pct", 0) or 0),
                    realized_pct=float(body.get("realized_pct", 0) or 0),
                ),
                status=201,
            )
        if action == "heatmap":
            cells = body.get("cells") if isinstance(body.get("cells"), list) else None
            return json_response(
                analytics.heatmap(portfolio_id=body.get("portfolio_id", ""), cells=cells),
                status=201,
            )
        return json_response(
            analytics.risk_per_trade(
                symbol=body.get("symbol", ""),
                risk_amount=float(body.get("risk_amount", 0) or 0),
                capital=float(body.get("capital", 0) or 0),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def rm_optimization_handler(request: web.Request) -> web.Response:
    try:
        opt = _suite().optimization
        if request.method == "GET":
            return json_response(opt.status())
        body = await _read_json(request)
        action = body.get("action", "asset")
        if action == "sector":
            sectors = body.get("sectors") if isinstance(body.get("sectors"), dict) else {}
            return json_response(
                opt.sector_allocation(name=body.get("name", ""), sectors=sectors),
                status=201,
            )
        if action == "correlation":
            assets = body.get("assets") if isinstance(body.get("assets"), list) else []
            matrix = body.get("matrix") if isinstance(body.get("matrix"), list) else None
            return json_response(opt.correlation_matrix(assets=assets, matrix=matrix), status=201)
        if action == "diversification":
            return json_response(
                opt.diversification(
                    score=float(body.get("score", 0) or 0),
                    holdings=int(body.get("holdings", 0) or 0),
                ),
                status=201,
            )
        if action == "rebalance":
            target = body.get("target") if isinstance(body.get("target"), dict) else {}
            return json_response(
                opt.rebalance(
                    portfolio_id=body.get("portfolio_id", ""),
                    target=target,
                    threshold_pct=float(body.get("threshold_pct", 5) or 5),
                ),
                status=201,
            )
        if action == "efficiency":
            return json_response(
                opt.capital_efficiency(
                    portfolio_id=body.get("portfolio_id", ""),
                    deployed_pct=float(body.get("deployed_pct", 0) or 0),
                    idle_pct=float(body.get("idle_pct", 0) or 0),
                ),
                status=201,
            )
        weights = body.get("weights") if isinstance(body.get("weights"), dict) else {}
        return json_response(
            opt.asset_allocation(name=body.get("name", ""), weights=weights),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def rm_models_handler(request: web.Request) -> web.Response:
    try:
        models = _suite().models
        if request.method == "GET":
            return json_response(models.status())
        body = await _read_json(request)
        action = body.get("action", "var")
        if action == "cvar":
            return json_response(
                models.cvar(
                    portfolio_id=body.get("portfolio_id", ""),
                    confidence=float(body.get("confidence", 0.95) or 0.95),
                    cvar_pct=float(body.get("cvar_pct", 0) or 0),
                ),
                status=201,
            )
        if action == "monte_carlo":
            return json_response(
                models.monte_carlo(
                    portfolio_id=body.get("portfolio_id", ""),
                    simulations=int(body.get("simulations", 5000) or 5000),
                ),
                status=201,
            )
        if action == "stress":
            return json_response(
                models.stress_test(
                    portfolio_id=body.get("portfolio_id", ""),
                    scenario=body.get("scenario", ""),
                    shock_pct=float(body.get("shock_pct", 0) or 0),
                ),
                status=201,
            )
        if action == "scenario":
            return json_response(
                models.scenario(
                    portfolio_id=body.get("portfolio_id", ""),
                    name=body.get("name", ""),
                    outcome=body.get("outcome", ""),
                ),
                status=201,
            )
        if action == "tail":
            return json_response(
                models.tail_risk(
                    portfolio_id=body.get("portfolio_id", ""),
                    tail_pct=float(body.get("tail_pct", 0) or 0),
                ),
                status=201,
            )
        return json_response(
            models.var(
                portfolio_id=body.get("portfolio_id", ""),
                confidence=float(body.get("confidence", 0.95) or 0.95),
                var_pct=float(body.get("var_pct", 0) or 0),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def rm_protection_handler(request: web.Request) -> web.Response:
    try:
        protection = _suite().protection
        if request.method == "GET":
            return json_response(protection.status())
        body = await _read_json(request)
        action = body.get("action", "dynamic_stop")
        if action == "adaptive_tp":
            targets = body.get("targets") if isinstance(body.get("targets"), list) else []
            return json_response(
                protection.adaptive_tp(symbol=body.get("symbol", ""), targets=targets),
                status=201,
            )
        if action == "trailing":
            return json_response(
                protection.trailing_stop(
                    symbol=body.get("symbol", ""),
                    trail_pct=float(body.get("trail_pct", 0) or 0),
                ),
                status=201,
            )
        if action == "breakeven":
            return json_response(
                protection.breakeven(
                    symbol=body.get("symbol", ""),
                    trigger_r=float(body.get("trigger_r", 1) or 1),
                ),
                status=201,
            )
        if action == "partial":
            levels = body.get("levels") if isinstance(body.get("levels"), list) else []
            return json_response(
                protection.partial_profit(symbol=body.get("symbol", ""), levels=levels),
                status=201,
            )
        if action == "emergency":
            return json_response(
                protection.emergency_exit(
                    symbol=body.get("symbol", ""),
                    reason=body.get("reason", ""),
                ),
                status=201,
            )
        return json_response(
            protection.dynamic_stop(
                symbol=body.get("symbol", ""),
                stop=float(body.get("stop", 0) or 0),
                atr_mult=float(body.get("atr_mult", 1.5) or 1.5),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def rm_ai_handler(request: web.Request) -> web.Response:
    try:
        ai = _suite().ai
        if request.method == "GET":
            return json_response(ai.status())
        body = await _read_json(request)
        action = body.get("action", "market_risk")
        if action == "health":
            return json_response(
                ai.portfolio_health(
                    portfolio_id=body.get("portfolio_id", ""),
                    score=float(body.get("score", 0) or 0),
                ),
                status=201,
            )
        if action == "capital":
            return json_response(
                ai.capital_preservation(
                    portfolio_id=body.get("portfolio_id", ""),
                    score=float(body.get("score", 0) or 0),
                ),
                status=201,
            )
        if action == "exposure":
            return json_response(
                ai.exposure_recommendation(
                    portfolio_id=body.get("portfolio_id", ""),
                    action=body.get("rec_action", "hold"),
                    rationale=body.get("rationale", ""),
                ),
                status=201,
            )
        if action == "leverage":
            return json_response(
                ai.leverage_recommendation(
                    symbol=body.get("symbol", ""),
                    max_leverage=float(body.get("max_leverage", 1) or 1),
                    rationale=body.get("rationale", ""),
                ),
                status=201,
            )
        if action == "approval":
            return json_response(
                ai.trade_approval(
                    symbol=body.get("symbol", ""),
                    side=body.get("side", "long"),
                    size=float(body.get("size", 0) or 0),
                    risk_pct=float(body.get("risk_pct", 0) or 0),
                    approved=bool(body.get("approved", True)),
                ),
                status=201,
            )
        if action == "warning":
            return json_response(
                ai.warning(
                    portfolio_id=body.get("portfolio_id", ""),
                    severity=body.get("severity", "info"),
                    message=body.get("message", ""),
                ),
                status=201,
            )
        if action == "report":
            return json_response(
                ai.report(
                    portfolio_id=body.get("portfolio_id", ""),
                    narrative=body.get("narrative", ""),
                ),
                status=201,
            )
        return json_response(
            ai.market_risk_score(
                symbol=body.get("symbol", ""),
                score=float(body.get("score", 0) or 0),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def rm_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dash = _suite().dashboard
        if request.method == "GET":
            dtype = request.rel_url.query.get("type", "risk")
            return json_response(dash.render(dashboard_type=dtype))
        body = await _read_json(request)
        return json_response(
            dash.render(dashboard_type=body.get("dashboard_type", "risk")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def rm_knowledge_handler(request: web.Request) -> web.Response:
    try:
        knowledge = _suite().knowledge
        if request.method == "GET":
            return json_response(knowledge.status())
        body = await _read_json(request)
        return json_response(
            knowledge.publish(
                registry_type=body.get("registry_type", "risk"),
                key=body.get("key", ""),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else {},
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
