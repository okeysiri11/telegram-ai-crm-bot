"""API handlers — Strategy Engine (Sprint 16.4)."""

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
    return crypto_enterprise.strategy_engine


async def se_health_handler(request: web.Request) -> web.Response:
    health = crypto_enterprise.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "strategy_builder_ready": health.get("strategy_builder_ready"),
            "backtesting_engine_ready": health.get("backtesting_engine_ready"),
            "signal_generation_ready": health.get("signal_generation_ready"),
            "ai_strategy_intelligence_ready": health.get("ai_strategy_intelligence_ready"),
            "portfolio_simulation_ready": health.get("portfolio_simulation_ready"),
            "suite": _suite().status(),
        }
    )


async def se_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def se_strategies_handler(request: web.Request) -> web.Response:
    try:
        builder = _suite().builder
        if request.method == "GET":
            return json_response(builder.status())
        body = await _read_json(request)
        action = body.get("action", "register")
        if action == "visual":
            nodes = body.get("nodes") if isinstance(body.get("nodes"), list) else None
            return json_response(
                builder.create_visual(name=body.get("name", ""), nodes=nodes),
                status=201,
            )
        if action == "rule":
            return json_response(
                builder.add_rule(
                    strategy_id=body.get("strategy_id", ""),
                    condition_type=body.get("condition_type", "indicator"),
                    expression=body.get("expression", ""),
                    timeframe=body.get("timeframe", "1h"),
                ),
                status=201,
            )
        if action == "mtf":
            tfs = body.get("timeframes") if isinstance(body.get("timeframes"), list) else []
            return json_response(
                builder.multi_timeframe(
                    strategy_id=body.get("strategy_id", ""),
                    timeframes=tfs,
                    logic=body.get("logic", "and"),
                ),
                status=201,
            )
        if action == "template":
            return json_response(
                builder.from_template(
                    template=body.get("template", "custom"),
                    name=body.get("name", ""),
                    symbol=body.get("symbol", "BTCUSDT"),
                ),
                status=201,
            )
        rules = body.get("rules") if isinstance(body.get("rules"), list) else None
        return json_response(
            builder.register(
                name=body.get("name", ""),
                symbol=body.get("symbol", "BTCUSDT"),
                template=body.get("template", "custom"),
                rules=rules,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def se_backtesting_handler(request: web.Request) -> web.Response:
    try:
        bt = _suite().backtesting
        if request.method == "GET":
            return json_response(bt.status())
        body = await _read_json(request)
        action = body.get("action", "run")
        if action == "replay":
            return json_response(
                bt.historical_replay(
                    strategy_id=body.get("strategy_id", ""),
                    from_ts=body.get("from_ts", ""),
                    to_ts=body.get("to_ts", ""),
                    bars=int(body.get("bars", 1000) or 1000),
                ),
                status=201,
            )
        if action == "market_data":
            return json_response(
                bt.load_market_data(
                    symbol=body.get("symbol", ""),
                    bars=int(body.get("bars", 1000) or 1000),
                    timeframe=body.get("timeframe", "1h"),
                ),
                status=201,
            )
        if action == "walk_forward":
            return json_response(
                bt.walk_forward(
                    strategy_id=body.get("strategy_id", ""),
                    windows=int(body.get("windows", 5) or 5),
                ),
                status=201,
            )
        if action == "monte_carlo":
            return json_response(
                bt.monte_carlo(
                    strategy_id=body.get("strategy_id", ""),
                    simulations=int(body.get("simulations", 1000) or 1000),
                ),
                status=201,
            )
        if action == "optimize":
            params = body.get("params") if isinstance(body.get("params"), dict) else None
            return json_response(
                bt.optimize(strategy_id=body.get("strategy_id", ""), params=params),
                status=201,
            )
        if action == "compare":
            ids = body.get("strategy_ids") if isinstance(body.get("strategy_ids"), list) else []
            return json_response(bt.compare(strategy_ids=ids), status=201)
        if action == "portfolio":
            ids = body.get("strategy_ids") if isinstance(body.get("strategy_ids"), list) else []
            return json_response(
                bt.portfolio_backtest(
                    strategy_ids=ids,
                    capital=float(body.get("capital", 100000) or 100000),
                ),
                status=201,
            )
        return json_response(
            bt.run(
                strategy_id=body.get("strategy_id", ""),
                from_ts=body.get("from_ts", ""),
                to_ts=body.get("to_ts", ""),
                capital=float(body.get("capital", 100000) or 100000),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def se_performance_handler(request: web.Request) -> web.Response:
    try:
        perf = _suite().performance
        if request.method == "GET":
            return json_response(perf.status())
        body = await _read_json(request)
        return json_response(perf.compute(backtest_id=body.get("backtest_id", "")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def se_signals_handler(request: web.Request) -> web.Response:
    try:
        signals = _suite().signals
        if request.method == "GET":
            return json_response(signals.status())
        body = await _read_json(request)
        action = body.get("action", "entry")
        if action == "exit":
            return json_response(
                signals.exit(
                    strategy_id=body.get("strategy_id", ""),
                    symbol=body.get("symbol", ""),
                    price=float(body.get("price", 0) or 0),
                    reason=body.get("reason", "target"),
                ),
                status=201,
            )
        if action == "take_profit":
            targets = body.get("targets") if isinstance(body.get("targets"), list) else []
            return json_response(
                signals.take_profit(
                    strategy_id=body.get("strategy_id", ""),
                    symbol=body.get("symbol", ""),
                    targets=targets,
                ),
                status=201,
            )
        if action == "stop_loss":
            return json_response(
                signals.stop_loss(
                    strategy_id=body.get("strategy_id", ""),
                    symbol=body.get("symbol", ""),
                    stop=float(body.get("stop", 0) or 0),
                ),
                status=201,
            )
        if action == "trailing":
            return json_response(
                signals.trailing_stop(
                    strategy_id=body.get("strategy_id", ""),
                    symbol=body.get("symbol", ""),
                    trail_pct=float(body.get("trail_pct", 0) or 0),
                ),
                status=201,
            )
        if action == "scale":
            sizes = body.get("sizes") if isinstance(body.get("sizes"), list) else []
            return json_response(
                signals.scale_position(
                    strategy_id=body.get("strategy_id", ""),
                    symbol=body.get("symbol", ""),
                    sizes=sizes,
                ),
                status=201,
            )
        return json_response(
            signals.entry(
                strategy_id=body.get("strategy_id", ""),
                symbol=body.get("symbol", ""),
                side=body.get("side", "long"),
                price=float(body.get("price", 0) or 0),
                confidence=float(body.get("confidence", 0.7) or 0.7),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def se_portfolio_handler(request: web.Request) -> web.Response:
    try:
        sim = _suite().portfolio_sim
        if request.method == "GET":
            return json_response(sim.status())
        body = await _read_json(request)
        action = body.get("action", "allocate")
        if action == "multi_asset":
            assets = body.get("assets") if isinstance(body.get("assets"), list) else []
            return json_response(
                sim.multi_asset(assets=assets, capital=float(body.get("capital", 0) or 0)),
                status=201,
            )
        if action == "exposure":
            return json_response(
                sim.exposure(
                    long_pct=float(body.get("long_pct", 0) or 0),
                    short_pct=float(body.get("short_pct", 0) or 0),
                    cash_pct=float(body.get("cash_pct", 0) or 0),
                ),
                status=201,
            )
        if action == "correlation":
            assets = body.get("assets") if isinstance(body.get("assets"), list) else []
            matrix = body.get("matrix") if isinstance(body.get("matrix"), list) else None
            return json_response(sim.correlation(assets=assets, matrix=matrix), status=201)
        if action == "diversification":
            return json_response(
                sim.diversification(
                    score=float(body.get("score", 0) or 0),
                    holdings=int(body.get("holdings", 0) or 0),
                ),
                status=201,
            )
        allocations = body.get("allocations") if isinstance(body.get("allocations"), dict) else {}
        return json_response(
            sim.allocate(name=body.get("name", ""), allocations=allocations),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def se_ai_handler(request: web.Request) -> web.Response:
    try:
        ai = _suite().ai
        if request.method == "GET":
            return json_response(ai.status())
        body = await _read_json(request)
        action = body.get("action", "evaluate")
        if action == "regime":
            return json_response(
                ai.detect_regime(
                    symbol=body.get("symbol", ""),
                    regime=body.get("regime", "trending"),
                    confidence=float(body.get("confidence", 0) or 0),
                ),
                status=201,
            )
        if action == "adaptive":
            ids = body.get("strategy_ids") if isinstance(body.get("strategy_ids"), list) else []
            return json_response(
                ai.adaptive_select(
                    symbol=body.get("symbol", ""),
                    strategy_ids=ids,
                    selected_id=body.get("selected_id", ""),
                ),
                status=201,
            )
        if action == "optimize":
            return json_response(
                ai.optimize_strategy(
                    strategy_id=body.get("strategy_id", ""),
                    improvement=float(body.get("improvement", 0) or 0),
                ),
                status=201,
            )
        if action == "scenario":
            return json_response(
                ai.scenario(
                    strategy_id=body.get("strategy_id", ""),
                    name=body.get("name", ""),
                    outcome=body.get("outcome", ""),
                ),
                status=201,
            )
        if action == "recommend":
            return json_response(
                ai.recommend(
                    symbol=body.get("symbol", ""),
                    action=body.get("trade_action", "hold"),
                    rationale=body.get("rationale", ""),
                ),
                status=201,
            )
        if action == "explain":
            return json_response(
                ai.explain(
                    strategy_id=body.get("strategy_id", ""),
                    explanation=body.get("explanation", ""),
                ),
                status=201,
            )
        if action == "report":
            return json_response(
                ai.report(
                    strategy_id=body.get("strategy_id", ""),
                    narrative=body.get("narrative", ""),
                ),
                status=201,
            )
        return json_response(
            ai.evaluate(
                strategy_id=body.get("strategy_id", ""),
                score=float(body.get("score", 0) or 0),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def se_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dash = _suite().dashboard
        if request.method == "GET":
            dtype = request.rel_url.query.get("type", "strategy")
            return json_response(dash.render(dashboard_type=dtype))
        body = await _read_json(request)
        return json_response(
            dash.render(dashboard_type=body.get("dashboard_type", "strategy")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def se_knowledge_handler(request: web.Request) -> web.Response:
    try:
        knowledge = _suite().knowledge
        if request.method == "GET":
            return json_response(knowledge.status())
        body = await _read_json(request)
        return json_response(
            knowledge.publish(
                registry_type=body.get("registry_type", "strategy"),
                key=body.get("key", ""),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else {},
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
