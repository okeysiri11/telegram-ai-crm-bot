"""API handlers — Market Intelligence (Sprint 16.3)."""

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
    return crypto_enterprise.market_intelligence


async def mi_health_handler(request: web.Request) -> web.Response:
    health = crypto_enterprise.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "news_intelligence_ready": health.get("news_intelligence_ready"),
            "sentiment_intelligence_ready": health.get("sentiment_intelligence_ready"),
            "macro_intelligence_ready": health.get("macro_intelligence_ready"),
            "ai_correlation_engine_ready": health.get("ai_correlation_engine_ready"),
            "ai_decision_engine_ready": health.get("ai_decision_engine_ready"),
            "suite": _suite().status(),
        }
    )


async def mi_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def mi_news_handler(request: web.Request) -> web.Response:
    try:
        news = _suite().news
        if request.method == "GET":
            return json_response(news.status())
        body = await _read_json(request)
        action = body.get("action", "aggregate")
        if action == "classify":
            return json_response(
                news.classify(news_id=body.get("news_id", ""), category=body.get("category", "general")),
                status=201,
            )
        if action == "breaking":
            return json_response(
                news.breaking(
                    headline=body.get("headline", ""),
                    severity=float(body.get("severity", 0) or 0),
                ),
                status=201,
            )
        if action == "economic_calendar":
            events = body.get("events") if isinstance(body.get("events"), list) else []
            return json_response(news.economic_calendar(events=events), status=201)
        if action == "crypto_events":
            events = body.get("events") if isinstance(body.get("events"), list) else []
            return json_response(news.crypto_events(events=events), status=201)
        if action == "etf":
            return json_response(
                news.etf_news(ticker=body.get("ticker", ""), headline=body.get("headline", "")),
                status=201,
            )
        if action == "exchange":
            return json_response(
                news.exchange_announcement(exchange=body.get("exchange", ""), title=body.get("title", "")),
                status=201,
            )
        if action == "project":
            return json_response(
                news.project_announcement(project=body.get("project", ""), title=body.get("title", "")),
                status=201,
            )
        return json_response(
            news.aggregate(
                source=body.get("source", ""),
                headline=body.get("headline", ""),
                url=body.get("url", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def mi_social_handler(request: web.Request) -> web.Response:
    try:
        social = _suite().social
        if request.method == "GET":
            return json_response(social.status())
        body = await _read_json(request)
        action = body.get("action", "analyze")
        if action == "influencer":
            return json_response(
                social.influencer(
                    handle=body.get("handle", ""),
                    platform=body.get("platform", "x"),
                    followers=int(body.get("followers", 0) or 0),
                    influence_score=float(body.get("influence_score", 0) or 0),
                ),
                status=201,
            )
        if action == "trending":
            topics = body.get("topics") if isinstance(body.get("topics"), list) else []
            return json_response(social.trending(topics=topics), status=201)
        if action == "hashtags":
            tags = body.get("tags") if isinstance(body.get("tags"), list) else []
            return json_response(
                social.hashtags(tags=tags, volume=int(body.get("volume", 0) or 0)),
                status=201,
            )
        return json_response(
            social.analyze_source(
                source=body.get("source", "x"),
                handle=body.get("handle", ""),
                mentions=int(body.get("mentions", 0) or 0),
                engagement=float(body.get("engagement", 0) or 0),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def mi_sentiment_handler(request: web.Request) -> web.Response:
    try:
        sent = _suite().sentiment
        if request.method == "GET":
            return json_response(sent.status())
        body = await _read_json(request)
        action = body.get("action", "index")
        if action == "fear_greed":
            return json_response(sent.fear_greed(value=int(body.get("value", 0) or 0)), status=201)
        if action == "classify":
            return json_response(
                sent.classify(
                    text=body.get("text", ""),
                    label=body.get("label", "neutral"),
                    confidence=float(body.get("confidence", 0) or 0),
                ),
                status=201,
            )
        if action == "history":
            points = body.get("points") if isinstance(body.get("points"), list) else []
            return json_response(sent.history(points=points), status=201)
        if action == "trend":
            return json_response(
                sent.trend(
                    direction=body.get("direction", "flat"),
                    strength=float(body.get("strength", 0) or 0),
                ),
                status=201,
            )
        if action == "regional":
            return json_response(
                sent.regional(
                    region=body.get("region", ""),
                    score=float(body.get("score", 0) or 0),
                    label=body.get("label", "neutral"),
                ),
                status=201,
            )
        return json_response(
            sent.market_index(score=float(body.get("score", 50) or 50), label=body.get("label", "")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def mi_fundamentals_handler(request: web.Request) -> web.Response:
    try:
        fund = _suite().fundamentals
        if request.method == "GET":
            return json_response(fund.status())
        body = await _read_json(request)
        action = body.get("action", "project")
        if action == "token":
            return json_response(
                fund.token_fundamentals(
                    symbol=body.get("symbol", ""),
                    market_cap=float(body.get("market_cap", 0) or 0),
                    fdv=float(body.get("fdv", 0) or 0),
                    holders=int(body.get("holders", 0) or 0),
                ),
                status=201,
            )
        if action == "unlock":
            unlocks = body.get("unlocks") if isinstance(body.get("unlocks"), list) else []
            return json_response(
                fund.unlock_calendar(symbol=body.get("symbol", ""), unlocks=unlocks),
                status=201,
            )
        if action == "tokenomics":
            return json_response(
                fund.tokenomics(
                    symbol=body.get("symbol", ""),
                    circulating_pct=float(body.get("circulating_pct", 0) or 0),
                    inflation_pct=float(body.get("inflation_pct", 0) or 0),
                ),
                status=201,
            )
        if action == "developer":
            return json_response(
                fund.developer_activity(
                    symbol=body.get("symbol", ""),
                    commits_30d=int(body.get("commits_30d", 0) or 0),
                    contributors=int(body.get("contributors", 0) or 0),
                ),
                status=201,
            )
        if action == "github":
            return json_response(
                fund.github_activity(
                    repo=body.get("repo", ""),
                    stars=int(body.get("stars", 0) or 0),
                    forks=int(body.get("forks", 0) or 0),
                    open_issues=int(body.get("open_issues", 0) or 0),
                ),
                status=201,
            )
        if action == "partnership":
            return json_response(
                fund.partnership(
                    project=body.get("project", ""),
                    partner=body.get("partner", ""),
                    kind=body.get("kind", "strategic"),
                ),
                status=201,
            )
        if action == "protocol":
            return json_response(
                fund.protocol_update(
                    protocol=body.get("protocol", ""),
                    version=body.get("version", ""),
                    summary=body.get("summary", ""),
                ),
                status=201,
            )
        return json_response(
            fund.register_project(
                name=body.get("name", ""),
                symbol=body.get("symbol", ""),
                category=body.get("category", "protocol"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def mi_macro_handler(request: web.Request) -> web.Response:
    try:
        macro = _suite().macro
        if request.method == "GET":
            return json_response(macro.status())
        body = await _read_json(request)
        action = body.get("action", "event")
        title = body.get("title", "")
        scheduled_at = body.get("scheduled_at", "")
        if action == "fed":
            return json_response(macro.fed(title=title, scheduled_at=scheduled_at), status=201)
        if action == "inflation":
            return json_response(macro.inflation(title=title, scheduled_at=scheduled_at), status=201)
        if action == "interest_rate":
            return json_response(macro.interest_rate(title=title, scheduled_at=scheduled_at), status=201)
        if action == "employment":
            return json_response(macro.employment(title=title, scheduled_at=scheduled_at), status=201)
        if action == "gdp":
            return json_response(macro.gdp(title=title, scheduled_at=scheduled_at), status=201)
        if action == "global":
            return json_response(macro.global_macro(title=title, scheduled_at=scheduled_at), status=201)
        return json_response(
            macro.event(
                event_type=body.get("event_type", "global"),
                title=title,
                scheduled_at=scheduled_at,
                impact=body.get("impact", "high"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def mi_correlation_handler(request: web.Request) -> web.Response:
    try:
        corr = _suite().correlation
        if request.method == "GET":
            return json_response(corr.status())
        body = await _read_json(request)
        return json_response(
            corr.correlate(
                correlation_type=body.get("correlation_type", "news_price"),
                symbol=body.get("symbol", ""),
                coefficient=float(body.get("coefficient", 0) or 0),
                window=body.get("window", "7d"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def mi_decision_handler(request: web.Request) -> web.Response:
    try:
        decision = _suite().decision
        if request.method == "GET":
            return json_response(decision.status())
        body = await _read_json(request)
        action = body.get("action", "summary")
        if action == "risk":
            return json_response(
                decision.risk_level(
                    symbol=body.get("symbol", ""),
                    level=body.get("level", "medium"),
                    score=float(body.get("score", 0) or 0),
                ),
                status=201,
            )
        if action == "opportunity":
            return json_response(
                decision.opportunity(
                    symbol=body.get("symbol", ""),
                    score=float(body.get("score", 0) or 0),
                ),
                status=201,
            )
        if action == "probabilities":
            return json_response(
                decision.probabilities(
                    symbol=body.get("symbol", ""),
                    bullish=float(body.get("bullish", 0) or 0),
                    bearish=float(body.get("bearish", 0) or 0),
                ),
                status=201,
            )
        if action == "volatility":
            return json_response(
                decision.volatility_forecast(
                    symbol=body.get("symbol", ""),
                    forecast_pct=float(body.get("forecast_pct", 0) or 0),
                    horizon=body.get("horizon", "7d"),
                ),
                status=201,
            )
        if action == "outlook":
            return json_response(
                decision.outlook(
                    symbol=body.get("symbol", ""),
                    horizon=body.get("horizon", "short"),
                    bias=body.get("bias", "neutral"),
                    narrative=body.get("narrative", ""),
                ),
                status=201,
            )
        if action == "explain":
            return json_response(
                decision.explain(symbol=body.get("symbol", ""), explanation=body.get("explanation", "")),
                status=201,
            )
        return json_response(
            decision.market_summary(symbol=body.get("symbol", ""), summary=body.get("summary", "")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def mi_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dash = _suite().dashboard
        if request.method == "GET":
            dtype = request.rel_url.query.get("type", "news")
            return json_response(dash.render(dashboard_type=dtype))
        body = await _read_json(request)
        return json_response(
            dash.render(dashboard_type=body.get("dashboard_type", "news")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def mi_knowledge_handler(request: web.Request) -> web.Response:
    try:
        knowledge = _suite().knowledge
        if request.method == "GET":
            return json_response(knowledge.status())
        body = await _read_json(request)
        return json_response(
            knowledge.publish(
                registry_type=body.get("registry_type", "intelligence"),
                key=body.get("key", ""),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else {},
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
