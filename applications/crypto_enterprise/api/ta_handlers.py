"""API handlers — Technical Analysis (Sprint 16.1)."""

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
    return crypto_enterprise.technical_analysis


async def ta_health_handler(request: web.Request) -> web.Response:
    health = crypto_enterprise.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "tradingview_integration_ready": health.get("tradingview_integration_ready"),
            "technical_analysis_ready": health.get("technical_analysis_ready"),
            "pattern_recognition_ready": health.get("pattern_recognition_ready"),
            "ai_technical_intelligence_ready": health.get("ai_technical_intelligence_ready"),
            "suite": _suite().status(),
        }
    )


async def ta_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ta_tradingview_handler(request: web.Request) -> web.Response:
    try:
        tv = _suite().tradingview
        if request.method == "GET":
            return json_response(tv.status())
        body = await _read_json(request)
        action = body.get("action", "connect")
        if action == "watchlist":
            symbols = body.get("symbols") if isinstance(body.get("symbols"), list) else []
            return json_response(
                tv.sync_watchlist(name=body.get("name", ""), symbols=symbols),
                status=201,
            )
        if action == "chart_sync":
            return json_response(
                tv.sync_chart(symbol=body.get("symbol", ""), timeframe=body.get("timeframe", "1h")),
                status=201,
            )
        if action == "timeframe":
            return json_response(
                tv.set_timeframe(chart_id=body.get("chart_id", ""), timeframe=body.get("timeframe", "1h")),
                status=201,
            )
        if action == "drawing":
            payload = body.get("payload") if isinstance(body.get("payload"), dict) else None
            return json_response(
                tv.sync_drawing(
                    chart_id=body.get("chart_id", ""),
                    drawing_type=body.get("drawing_type", "trendline"),
                    payload=payload,
                ),
                status=201,
            )
        if action == "alert":
            return json_response(
                tv.create_alert(
                    symbol=body.get("symbol", ""),
                    condition=body.get("condition", ""),
                    price=float(body.get("price", 0) or 0),
                ),
                status=201,
            )
        if action == "multi_chart":
            symbols = body.get("symbols") if isinstance(body.get("symbols"), list) else []
            return json_response(
                tv.multi_chart(layout=body.get("layout", "2x2"), symbols=symbols),
                status=201,
            )
        return json_response(
            tv.connect_api(account=body.get("account", ""), api_ref=body.get("api_ref", "")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ta_charts_handler(request: web.Request) -> web.Response:
    try:
        charts = _suite().charts
        if request.method == "GET":
            return json_response(charts.status())
        body = await _read_json(request)
        action = body.get("action", "create")
        if action == "mtf":
            tfs = body.get("timeframes") if isinstance(body.get("timeframes"), list) else None
            return json_response(
                charts.multi_timeframe(symbol=body.get("symbol", ""), timeframes=tfs),
                status=201,
            )
        if action == "playback":
            return json_response(
                charts.playback(
                    chart_id=body.get("chart_id", ""),
                    from_ts=body.get("from_ts", ""),
                    to_ts=body.get("to_ts", ""),
                ),
                status=201,
            )
        return json_response(
            charts.create(
                symbol=body.get("symbol", ""),
                chart_type=body.get("chart_type", "candlestick"),
                timeframe=body.get("timeframe", "1h"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ta_indicators_handler(request: web.Request) -> web.Response:
    try:
        indicators = _suite().indicators
        if request.method == "GET":
            return json_response(indicators.status())
        body = await _read_json(request)
        params = body.get("params") if isinstance(body.get("params"), dict) else None
        return json_response(
            indicators.compute(
                indicator=body.get("indicator", "rsi"),
                symbol=body.get("symbol", ""),
                timeframe=body.get("timeframe", "1h"),
                period=int(body.get("period", 14) or 14),
                params=params,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ta_structures_handler(request: web.Request) -> web.Response:
    try:
        structures = _suite().structures
        if request.method == "GET":
            return json_response(structures.status())
        body = await _read_json(request)
        return json_response(
            structures.detect(
                structure=body.get("structure", "support"),
                symbol=body.get("symbol", ""),
                price=float(body.get("price", 0) or 0),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ta_patterns_handler(request: web.Request) -> web.Response:
    try:
        patterns = _suite().patterns
        if request.method == "GET":
            return json_response(patterns.status())
        body = await _read_json(request)
        return json_response(
            patterns.recognize(
                pattern=body.get("pattern", "bull_flag"),
                symbol=body.get("symbol", ""),
                timeframe=body.get("timeframe", "1h"),
                candle_pattern=body.get("candle_pattern", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ta_ai_handler(request: web.Request) -> web.Response:
    try:
        ai = _suite().ai
        if request.method == "GET":
            return json_response(ai.status())
        body = await _read_json(request)
        action = body.get("action", "trend")
        if action == "momentum":
            return json_response(
                ai.momentum(symbol=body.get("symbol", ""), rsi=float(body.get("rsi", 55) or 55)),
                status=201,
            )
        if action == "volatility":
            return json_response(
                ai.volatility(symbol=body.get("symbol", ""), atr_pct=float(body.get("atr_pct", 0) or 0)),
                status=201,
            )
        if action == "confluence":
            inds = body.get("indicators") if isinstance(body.get("indicators"), list) else []
            return json_response(
                ai.confluence(symbol=body.get("symbol", ""), indicators=inds),
                status=201,
            )
        if action == "mtf":
            tfs = body.get("timeframes") if isinstance(body.get("timeframes"), list) else []
            return json_response(
                ai.multi_timeframe_confirm(symbol=body.get("symbol", ""), timeframes=tfs),
                status=201,
            )
        if action == "signal":
            return json_response(
                ai.signal_confidence(
                    symbol=body.get("symbol", ""),
                    side=body.get("side", "long"),
                    confidence=float(body.get("confidence", 0) or 0),
                ),
                status=201,
            )
        if action == "setup":
            return json_response(
                ai.trade_setup(
                    symbol=body.get("symbol", ""),
                    entry=float(body.get("entry", 0) or 0),
                    stop=float(body.get("stop", 0) or 0),
                    target=float(body.get("target", 0) or 0),
                ),
                status=201,
            )
        return json_response(
            ai.trend_strength(
                symbol=body.get("symbol", ""),
                score=float(body.get("score", 0) or 0),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ta_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dash = _suite().dashboard
        if request.method == "GET":
            dtype = request.rel_url.query.get("type", "trading")
            return json_response(dash.render(dashboard_type=dtype))
        body = await _read_json(request)
        return json_response(
            dash.render(dashboard_type=body.get("dashboard_type", "trading")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ta_knowledge_handler(request: web.Request) -> web.Response:
    try:
        knowledge = _suite().knowledge
        if request.method == "GET":
            return json_response(knowledge.status())
        body = await _read_json(request)
        return json_response(
            knowledge.publish(
                registry_type=body.get("registry_type", "technical"),
                key=body.get("key", ""),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else {},
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
