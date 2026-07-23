"""API handlers — AI Crypto Trader (Sprint 16.7)."""

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
    return crypto_enterprise.ai_trader


async def at_health_handler(request: web.Request) -> web.Response:
    health = crypto_enterprise.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "ai_crypto_trader_ready": health.get("ai_crypto_trader_ready"),
            "decision_support_ready": health.get("decision_support_ready"),
            "trade_recommendation_engine_ready": health.get("trade_recommendation_engine_ready"),
            "executive_intelligence_ready": health.get("executive_intelligence_ready"),
            "ai_explainability_ready": health.get("ai_explainability_ready"),
            "suite": _suite().status(),
        }
    )


async def at_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def at_decision_handler(request: web.Request) -> web.Response:
    try:
        decision = _suite().decision
        if request.method == "GET":
            return json_response(decision.status())
        body = await _read_json(request)
        action = body.get("action", "decide")
        if action == "multi_factor":
            scores = body.get("scores") if isinstance(body.get("scores"), dict) else {}
            return json_response(
                decision.multi_factor(symbol=body.get("symbol", ""), scores=scores),
                status=201,
            )
        if action == "scenario":
            return json_response(
                decision.scenario(
                    symbol=body.get("symbol", ""),
                    name=body.get("name", ""),
                    outcome=body.get("outcome", ""),
                    probability=float(body.get("probability", 0) or 0),
                ),
                status=201,
            )
        if action == "opportunity":
            return json_response(
                decision.rank_opportunity(
                    symbol=body.get("symbol", ""),
                    score=float(body.get("score", 0) or 0),
                    thesis=body.get("thesis", ""),
                ),
                status=201,
            )
        if action == "risk":
            return json_response(
                decision.classify_risk(
                    symbol=body.get("symbol", ""),
                    risk=body.get("risk", "medium"),
                    rationale=body.get("rationale", ""),
                ),
                status=201,
            )
        factors = body.get("factors") if isinstance(body.get("factors"), list) else None
        return json_response(
            decision.decide(
                symbol=body.get("symbol", ""),
                factors=factors,
                bullish=float(body.get("bullish", 0.5) or 0.5),
                bearish=float(body.get("bearish", 0.3) or 0.3),
                confidence=float(body.get("confidence", 0.7) or 0.7),
                risk=body.get("risk", "medium"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def at_assistant_handler(request: web.Request) -> web.Response:
    try:
        assistant = _suite().assistant
        if request.method == "GET":
            return json_response(assistant.status())
        body = await _read_json(request)
        action = body.get("action", "chat")
        if action == "compare":
            symbols = body.get("symbols") if isinstance(body.get("symbols"), list) else []
            return json_response(
                assistant.compare_assets(symbols=symbols, winner=body.get("winner", "")),
                status=201,
            )
        if action == "briefing":
            return json_response(
                assistant.briefing(
                    briefing_type=body.get("briefing_type", "daily"),
                    summary=body.get("summary", ""),
                ),
                status=201,
            )
        return json_response(
            assistant.chat(
                topic=body.get("topic", "market"),
                question=body.get("question", ""),
                answer=body.get("answer", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def at_recommendations_handler(request: web.Request) -> web.Response:
    try:
        rec = _suite().recommendations
        if request.method == "GET":
            return json_response(rec.status())
        body = await _read_json(request)
        action = body.get("action", "recommend")
        if action == "alternative":
            return json_response(
                rec.alternative(
                    recommendation_id=body.get("recommendation_id", ""),
                    name=body.get("name", ""),
                    narrative=body.get("narrative", ""),
                ),
                status=201,
            )
        targets = body.get("targets") if isinstance(body.get("targets"), list) else []
        return json_response(
            rec.recommend(
                symbol=body.get("symbol", ""),
                side=body.get("side", "long"),
                entry_low=float(body.get("entry_low", 0) or 0),
                entry_high=float(body.get("entry_high", 0) or 0),
                stop=float(body.get("stop", 0) or 0),
                targets=targets,
                size=float(body.get("size", 0) or 0),
                duration=body.get("duration", "swing"),
                confidence=float(body.get("confidence", 0.7) or 0.7),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def at_portfolio_handler(request: web.Request) -> web.Response:
    try:
        port = _suite().portfolio_intel
        if request.method == "GET":
            return json_response(port.status())
        body = await _read_json(request)
        action = body.get("action", "health")
        if action == "allocation":
            return json_response(
                port.allocation_review(
                    portfolio_id=body.get("portfolio_id", ""),
                    advice=body.get("advice", ""),
                ),
                status=201,
            )
        if action == "exposure":
            return json_response(
                port.exposure_review(
                    portfolio_id=body.get("portfolio_id", ""),
                    long_pct=float(body.get("long_pct", 0) or 0),
                    short_pct=float(body.get("short_pct", 0) or 0),
                ),
                status=201,
            )
        if action == "diversification":
            return json_response(
                port.diversification(
                    portfolio_id=body.get("portfolio_id", ""),
                    suggestion=body.get("suggestion", ""),
                ),
                status=201,
            )
        if action == "optimize":
            return json_response(
                port.optimize_advice(
                    portfolio_id=body.get("portfolio_id", ""),
                    advice=body.get("advice", ""),
                ),
                status=201,
            )
        if action == "drawdown":
            return json_response(
                port.drawdown(
                    portfolio_id=body.get("portfolio_id", ""),
                    current_dd=float(body.get("current_dd", 0) or 0),
                    limit_dd=float(body.get("limit_dd", 0) or 0),
                ),
                status=201,
            )
        return json_response(
            port.health(
                portfolio_id=body.get("portfolio_id", ""),
                score=float(body.get("score", 0) or 0),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def at_executive_handler(request: web.Request) -> web.Response:
    try:
        exe = _suite().executive
        if request.method == "GET":
            return json_response(exe.status())
        body = await _read_json(request)
        action = body.get("action", "overview")
        if action == "opportunities":
            symbols = body.get("symbols") if isinstance(body.get("symbols"), list) else []
            return json_response(exe.top_opportunities(symbols=symbols), status=201)
        if action == "high_risk":
            symbols = body.get("symbols") if isinstance(body.get("symbols"), list) else []
            return json_response(exe.high_risk_assets(symbols=symbols), status=201)
        if action == "watchlist":
            symbols = body.get("symbols") if isinstance(body.get("symbols"), list) else []
            priorities = body.get("priorities") if isinstance(body.get("priorities"), list) else None
            return json_response(exe.watchlist(symbols=symbols, priorities=priorities), status=201)
        if action == "macro":
            return json_response(exe.macro_impact(summary=body.get("summary", "")), status=201)
        if action == "whale":
            return json_response(exe.whale_summary(summary=body.get("summary", "")), status=201)
        if action == "institutional":
            return json_response(exe.institutional_flow(summary=body.get("summary", "")), status=201)
        if action == "actions":
            recs = body.get("recommendations") if isinstance(body.get("recommendations"), list) else []
            return json_response(exe.actions(recommendations=recs), status=201)
        return json_response(
            exe.market_overview(summary=body.get("summary", ""), bias=body.get("bias", "neutral")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def at_explainability_handler(request: web.Request) -> web.Response:
    try:
        expl = _suite().explainability
        if request.method == "GET":
            return json_response(expl.status())
        body = await _read_json(request)
        action = body.get("action", "trace")
        if action == "evidence":
            evidence = body.get("evidence") if isinstance(body.get("evidence"), dict) else {}
            return json_response(
                expl.evidence(decision_id=body.get("decision_id", ""), evidence=evidence),
                status=201,
            )
        if action == "summarize":
            return json_response(
                expl.summarize(
                    decision_id=body.get("decision_id", ""),
                    indicators=body.get("indicators", ""),
                    news=body.get("news", ""),
                    onchain=body.get("onchain", ""),
                    risk=body.get("risk", ""),
                    confidence_explanation=body.get("confidence_explanation", ""),
                ),
                status=201,
            )
        if action == "report":
            return json_response(
                expl.report(
                    decision_id=body.get("decision_id", ""),
                    narrative=body.get("narrative", ""),
                ),
                status=201,
            )
        steps = body.get("steps") if isinstance(body.get("steps"), list) else []
        return json_response(
            expl.trace(decision_id=body.get("decision_id", ""), steps=steps),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def at_alerts_handler(request: web.Request) -> web.Response:
    try:
        alerts = _suite().alerts
        if request.method == "GET":
            return json_response(alerts.status())
        body = await _read_json(request)
        return json_response(
            alerts.raise_alert(
                alert_type=body.get("alert_type", "high_confidence"),
                symbol=body.get("symbol", ""),
                severity=body.get("severity", "info"),
                message=body.get("message", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def at_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dash = _suite().dashboard
        if request.method == "GET":
            dtype = request.rel_url.query.get("type", "ai_trader")
            return json_response(dash.render(dashboard_type=dtype))
        body = await _read_json(request)
        return json_response(
            dash.render(dashboard_type=body.get("dashboard_type", "ai_trader")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def at_knowledge_handler(request: web.Request) -> web.Response:
    try:
        knowledge = _suite().knowledge
        if request.method == "GET":
            return json_response(knowledge.status())
        body = await _read_json(request)
        return json_response(
            knowledge.publish(
                registry_type=body.get("registry_type", "decision"),
                key=body.get("key", ""),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else {},
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
