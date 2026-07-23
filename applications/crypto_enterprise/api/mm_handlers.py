"""API handlers — Market Microstructure (Sprint 16.2)."""

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
    return crypto_enterprise.market_microstructure


async def mm_health_handler(request: web.Request) -> web.Response:
    health = crypto_enterprise.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "order_book_intelligence_ready": health.get("order_book_intelligence_ready"),
            "trade_flow_analytics_ready": health.get("trade_flow_analytics_ready"),
            "derivatives_intelligence_ready": health.get("derivatives_intelligence_ready"),
            "liquidity_intelligence_ready": health.get("liquidity_intelligence_ready"),
            "ai_market_interpretation_ready": health.get("ai_market_interpretation_ready"),
            "suite": _suite().status(),
        }
    )


async def mm_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def mm_order_book_handler(request: web.Request) -> web.Response:
    try:
        ob = _suite().order_book
        if request.method == "GET":
            return json_response(ob.status())
        body = await _read_json(request)
        action = body.get("action", "snapshot")
        if action == "depth":
            return json_response(
                ob.depth(symbol=body.get("symbol", ""), levels=int(body.get("levels", 10) or 10)),
                status=201,
            )
        if action == "bid_ask":
            return json_response(
                ob.bid_ask(
                    symbol=body.get("symbol", ""),
                    bid=float(body.get("bid", 0) or 0),
                    ask=float(body.get("ask", 0) or 0),
                ),
                status=201,
            )
        if action == "heatmap":
            return json_response(
                ob.heatmap(symbol=body.get("symbol", ""), buckets=int(body.get("buckets", 20) or 20)),
                status=201,
            )
        if action == "imbalance":
            return json_response(
                ob.imbalance(
                    symbol=body.get("symbol", ""),
                    bid_volume=float(body.get("bid_volume", 0) or 0),
                    ask_volume=float(body.get("ask_volume", 0) or 0),
                ),
                status=201,
            )
        if action == "large_order":
            return json_response(
                ob.large_order(
                    symbol=body.get("symbol", ""),
                    side=body.get("side", "buy"),
                    size=float(body.get("size", 0) or 0),
                    price=float(body.get("price", 0) or 0),
                ),
                status=201,
            )
        if action == "iceberg":
            return json_response(
                ob.iceberg(
                    symbol=body.get("symbol", ""),
                    side=body.get("side", "buy"),
                    visible=float(body.get("visible", 0) or 0),
                    estimated_total=float(body.get("estimated_total", 0) or 0),
                ),
                status=201,
            )
        if action == "spoofing":
            return json_response(
                ob.spoofing(
                    symbol=body.get("symbol", ""),
                    side=body.get("side", "buy"),
                    size=float(body.get("size", 0) or 0),
                    cancelled_pct=float(body.get("cancelled_pct", 0) or 0),
                ),
                status=201,
            )
        bids = body.get("bids") if isinstance(body.get("bids"), list) else None
        asks = body.get("asks") if isinstance(body.get("asks"), list) else None
        return json_response(ob.snapshot(symbol=body.get("symbol", ""), bids=bids, asks=asks), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def mm_trade_flow_handler(request: web.Request) -> web.Response:
    try:
        tf = _suite().trade_flow
        if request.method == "GET":
            return json_response(tf.status())
        body = await _read_json(request)
        action = body.get("action", "time_and_sales")
        if action == "classify":
            return json_response(
                tf.classify(
                    symbol=body.get("symbol", ""),
                    trade_class=body.get("trade_class", "aggressive"),
                    size=float(body.get("size", 0) or 0),
                ),
                status=201,
            )
        if action == "pressure":
            return json_response(
                tf.pressure(
                    symbol=body.get("symbol", ""),
                    buy_volume=float(body.get("buy_volume", 0) or 0),
                    sell_volume=float(body.get("sell_volume", 0) or 0),
                ),
                status=201,
            )
        if action == "volume_delta":
            return json_response(
                tf.volume_delta(symbol=body.get("symbol", ""), delta=float(body.get("delta", 0) or 0)),
                status=201,
            )
        if action == "cvd":
            return json_response(
                tf.cvd(symbol=body.get("symbol", ""), cumulative=float(body.get("cumulative", 0) or 0)),
                status=201,
            )
        if action == "aggressive":
            return json_response(
                tf.aggressive(
                    symbol=body.get("symbol", ""),
                    side=body.get("side", "buy"),
                    size=float(body.get("size", 0) or 0),
                ),
                status=201,
            )
        if action == "large_trade":
            return json_response(
                tf.large_trade(
                    symbol=body.get("symbol", ""),
                    side=body.get("side", "buy"),
                    size=float(body.get("size", 0) or 0),
                    price=float(body.get("price", 0) or 0),
                ),
                status=201,
            )
        if action == "analytics":
            return json_response(tf.analytics(symbol=body.get("symbol", "")), status=201)
        return json_response(
            tf.time_and_sales(
                symbol=body.get("symbol", ""),
                price=float(body.get("price", 0) or 0),
                size=float(body.get("size", 0) or 0),
                side=body.get("side", "buy"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def mm_derivatives_handler(request: web.Request) -> web.Response:
    try:
        der = _suite().derivatives
        if request.method == "GET":
            return json_response(der.status())
        body = await _read_json(request)
        action = body.get("action", "open_interest")
        if action == "funding":
            return json_response(
                der.funding_rate(symbol=body.get("symbol", ""), rate=float(body.get("rate", 0) or 0)),
                status=201,
            )
        if action == "long_short":
            return json_response(
                der.long_short_ratio(
                    symbol=body.get("symbol", ""),
                    long_pct=float(body.get("long_pct", 50) or 50),
                    short_pct=float(body.get("short_pct", 50) or 50),
                ),
                status=201,
            )
        if action == "basis":
            return json_response(
                der.basis(
                    symbol=body.get("symbol", ""),
                    spot=float(body.get("spot", 0) or 0),
                    futures=float(body.get("futures", 0) or 0),
                ),
                status=201,
            )
        if action == "premium":
            return json_response(
                der.futures_premium(
                    symbol=body.get("symbol", ""),
                    premium_pct=float(body.get("premium_pct", 0) or 0),
                ),
                status=201,
            )
        if action == "options":
            return json_response(
                der.options_overview(
                    symbol=body.get("symbol", ""),
                    put_call_ratio=float(body.get("put_call_ratio", 0) or 0),
                    iv=float(body.get("iv", 0) or 0),
                ),
                status=201,
            )
        if action == "expiration":
            expiries = body.get("expiries") if isinstance(body.get("expiries"), list) else []
            return json_response(
                der.expiration_calendar(symbol=body.get("symbol", ""), expiries=expiries),
                status=201,
            )
        return json_response(
            der.open_interest(
                symbol=body.get("symbol", ""),
                oi=float(body.get("oi", 0) or 0),
                change_pct=float(body.get("change_pct", 0) or 0),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def mm_liquidations_handler(request: web.Request) -> web.Response:
    try:
        liq = _suite().liquidations
        if request.method == "GET":
            return json_response(liq.status())
        body = await _read_json(request)
        action = body.get("action", "liquidation")
        if action == "heatmap":
            return json_response(
                liq.heatmap(symbol=body.get("symbol", ""), clusters=int(body.get("clusters", 8) or 8)),
                status=201,
            )
        if action == "cluster":
            return json_response(
                liq.cluster(
                    symbol=body.get("symbol", ""),
                    price=float(body.get("price", 0) or 0),
                    size=float(body.get("size", 0) or 0),
                    side=body.get("side", "long"),
                ),
                status=201,
            )
        if action == "cascade":
            return json_response(
                liq.cascade(
                    symbol=body.get("symbol", ""),
                    levels=int(body.get("levels", 3) or 3),
                    total_size=float(body.get("total_size", 0) or 0),
                ),
                status=201,
            )
        if action == "alert":
            return json_response(
                liq.alert(
                    symbol=body.get("symbol", ""),
                    side=body.get("side", "long"),
                    size=float(body.get("size", 0) or 0),
                    price=float(body.get("price", 0) or 0),
                ),
                status=201,
            )
        return json_response(
            liq.liquidation(
                symbol=body.get("symbol", ""),
                side=body.get("side", "long"),
                size=float(body.get("size", 0) or 0),
                price=float(body.get("price", 0) or 0),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def mm_liquidity_handler(request: web.Request) -> web.Response:
    try:
        liq = _suite().liquidity
        if request.method == "GET":
            return json_response(liq.status())
        body = await _read_json(request)
        action = body.get("action", "zone")
        if action == "support":
            return json_response(
                liq.support_liquidity(
                    symbol=body.get("symbol", ""),
                    price=float(body.get("price", 0) or 0),
                    size=float(body.get("size", 0) or 0),
                ),
                status=201,
            )
        if action == "resistance":
            return json_response(
                liq.resistance_liquidity(
                    symbol=body.get("symbol", ""),
                    price=float(body.get("price", 0) or 0),
                    size=float(body.get("size", 0) or 0),
                ),
                status=201,
            )
        if action == "stop_hunt":
            return json_response(
                liq.stop_hunt(
                    symbol=body.get("symbol", ""),
                    direction=body.get("direction", "below"),
                    swept_price=float(body.get("swept_price", 0) or 0),
                ),
                status=201,
            )
        if action == "market_maker":
            return json_response(
                liq.market_maker(
                    symbol=body.get("symbol", ""),
                    activity_score=float(body.get("activity_score", 0) or 0),
                ),
                status=201,
            )
        if action == "absorption":
            return json_response(
                liq.absorption(
                    symbol=body.get("symbol", ""),
                    side=body.get("side", "buy"),
                    size=float(body.get("size", 0) or 0),
                ),
                status=201,
            )
        return json_response(
            liq.zone(
                symbol=body.get("symbol", ""),
                price_low=float(body.get("price_low", 0) or 0),
                price_high=float(body.get("price_high", 0) or 0),
                strength=float(body.get("strength", 0) or 0),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def mm_ai_handler(request: web.Request) -> web.Response:
    try:
        ai = _suite().ai
        if request.method == "GET":
            return json_response(ai.status())
        body = await _read_json(request)
        action = body.get("action", "structure")
        if action == "institutional":
            return json_response(
                ai.institutional(
                    symbol=body.get("symbol", ""),
                    intensity=float(body.get("intensity", 0) or 0),
                ),
                status=201,
            )
        if action == "whale":
            return json_response(
                ai.whale(
                    symbol=body.get("symbol", ""),
                    size_usd=float(body.get("size_usd", 0) or 0),
                    side=body.get("side", "buy"),
                ),
                status=201,
            )
        if action == "momentum":
            return json_response(
                ai.momentum_shift(
                    symbol=body.get("symbol", ""),
                    from_bias=body.get("from_bias", "neutral"),
                    to_bias=body.get("to_bias", "long"),
                ),
                status=201,
            )
        if action == "continuation":
            return json_response(
                ai.trend_continuation(
                    symbol=body.get("symbol", ""),
                    probability=float(body.get("probability", 0) or 0),
                ),
                status=201,
            )
        if action == "reversal":
            return json_response(
                ai.reversal(
                    symbol=body.get("symbol", ""),
                    probability=float(body.get("probability", 0) or 0),
                ),
                status=201,
            )
        if action == "bias":
            return json_response(
                ai.trade_bias(
                    symbol=body.get("symbol", ""),
                    bias=body.get("bias", "neutral"),
                    confidence=float(body.get("confidence", 0) or 0),
                ),
                status=201,
            )
        if action == "confidence":
            drivers = body.get("drivers") if isinstance(body.get("drivers"), list) else None
            return json_response(
                ai.confidence_score(
                    symbol=body.get("symbol", ""),
                    score=float(body.get("score", 0) or 0),
                    drivers=drivers,
                ),
                status=201,
            )
        return json_response(
            ai.market_structure(
                symbol=body.get("symbol", ""),
                structure=body.get("structure", "range"),
                score=float(body.get("score", 0) or 0),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def mm_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dash = _suite().dashboard
        if request.method == "GET":
            dtype = request.rel_url.query.get("type", "order_flow")
            return json_response(dash.render(dashboard_type=dtype))
        body = await _read_json(request)
        return json_response(
            dash.render(dashboard_type=body.get("dashboard_type", "order_flow")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def mm_knowledge_handler(request: web.Request) -> web.Response:
    try:
        knowledge = _suite().knowledge
        if request.method == "GET":
            return json_response(knowledge.status())
        body = await _read_json(request)
        return json_response(
            knowledge.publish(
                registry_type=body.get("registry_type", "microstructure"),
                key=body.get("key", ""),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else {},
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
