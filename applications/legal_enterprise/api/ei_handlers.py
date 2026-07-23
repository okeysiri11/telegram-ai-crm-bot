"""API handlers — Executive Legal Intelligence (Sprint 17.7)."""

from __future__ import annotations

from aiohttp import web

from applications.legal_enterprise import legal_enterprise
from applications.legal_enterprise.api.middleware import json_response
from applications.legal_enterprise.shared.exceptions import NotFoundError, ValidationError


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
    return legal_enterprise.executive_intelligence


async def ei_health_handler(request: web.Request) -> web.Response:
    health = legal_enterprise.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "executive_legal_intelligence_ready": health.get("executive_legal_intelligence_ready"),
            "decision_support_ready": health.get("decision_support_ready"),
            "enterprise_legal_analytics_ready": health.get("enterprise_legal_analytics_ready"),
            "regulatory_forecasting_ready": health.get("regulatory_forecasting_ready"),
            "suite": _suite().status(),
        }
    )


async def ei_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ei_executive_handler(request: web.Request) -> web.Response:
    try:
        executive = _suite().executive
        if request.method == "GET":
            return json_response(executive.status())
        body = await _read_json(request)
        return json_response(
            executive.snapshot(
                section=body.get("section", "overview"),
                title=body.get("title", ""),
                items=body.get("items") if isinstance(body.get("items"), list) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ei_analytics_handler(request: web.Request) -> web.Response:
    try:
        analytics = _suite().analytics
        if request.method == "GET":
            return json_response(analytics.status())
        body = await _read_json(request)
        return json_response(
            analytics.report(
                kind=body.get("kind", "case_success"),
                metrics=body.get("metrics") if isinstance(body.get("metrics"), dict) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ei_risk_handler(request: web.Request) -> web.Response:
    try:
        risk = _suite().risk
        if request.method == "GET":
            return json_response(risk.status())
        body = await _read_json(request)
        action = body.get("action", "score")
        if action == "forecast":
            return json_response(
                risk.forecast(
                    forecast_type=body.get("forecast_type", "litigation"),
                    horizon_days=int(body.get("horizon_days", 90) or 90),
                    projected_score=float(body.get("projected_score", 55) or 55),
                    narrative=body.get("narrative", ""),
                ),
                status=201,
            )
        return json_response(
            risk.score(
                score_type=body.get("score_type", "enterprise"),
                subject=body.get("subject", ""),
                value=float(body.get("value", 50) or 50),
                detail=body.get("detail", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ei_forecast_handler(request: web.Request) -> web.Response:
    try:
        forecasting = _suite().forecasting
        if request.method == "GET":
            return json_response(forecasting.status())
        body = await _read_json(request)
        return json_response(
            forecasting.register(
                action=body.get("action", "upcoming_change"),
                title=body.get("title", ""),
                impact=body.get("impact", "medium"),
                industry=body.get("industry", ""),
                detail=body.get("detail", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ei_decisions_handler(request: web.Request) -> web.Response:
    try:
        decisions = _suite().decisions
        if request.method == "GET":
            return json_response(decisions.status())
        body = await _read_json(request)
        return json_response(
            decisions.recommend(
                kind=body.get("kind", "executive"),
                title=body.get("title", ""),
                body=body.get("body", ""),
                priority=body.get("priority", "medium"),
                items=body.get("items") if isinstance(body.get("items"), list) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ei_ai_handler(request: web.Request) -> web.Response:
    try:
        ai = _suite().ai
        if request.method == "GET":
            return json_response(ai.status())
        body = await _read_json(request)
        action = body.get("action", "report")
        if action == "ask":
            return json_response(
                ai.ask(
                    question=body.get("question", ""),
                    context=body.get("context") if isinstance(body.get("context"), dict) else None,
                ),
                status=201,
            )
        return json_response(
            ai.report(
                report_type=body.get("report_type", "daily_briefing"),
                audience=body.get("audience", "executive"),
                focus=body.get("focus", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ei_alerts_handler(request: web.Request) -> web.Response:
    try:
        alerts = _suite().alerts
        if request.method == "GET":
            return json_response(alerts.status())
        body = await _read_json(request)
        return json_response(
            alerts.raise_alert(
                alert_type=body.get("alert_type", "critical"),
                title=body.get("title", ""),
                severity=body.get("severity", "high"),
                detail=body.get("detail", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ei_knowledge_handler(request: web.Request) -> web.Response:
    try:
        knowledge = _suite().knowledge
        if request.method == "GET":
            return json_response(knowledge.status())
        body = await _read_json(request)
        return json_response(
            knowledge.publish(
                base=body.get("base", "executive"),
                key=body.get("key", ""),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ei_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dashboard = _suite().dashboard
        if request.method == "GET":
            dtype = request.rel_url.query.get("dashboard_type", "executive")
            return json_response(dashboard.render(dashboard_type=dtype))
        body = await _read_json(request)
        return json_response(
            dashboard.render(dashboard_type=body.get("dashboard_type", "executive")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
