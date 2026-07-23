"""API handlers — Financial Reporting & BI (Sprint 18.5)."""

from __future__ import annotations

from aiohttp import web

from applications.finance_enterprise import finance_enterprise
from applications.finance_enterprise.api.middleware import json_response
from applications.finance_enterprise.shared.exceptions import NotFoundError, ValidationError


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
    return finance_enterprise.reporting


async def rpt_health_handler(request: web.Request) -> web.Response:
    health = finance_enterprise.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "financial_reporting_ready": health.get("financial_reporting_ready"),
            "business_intelligence_ready": health.get("business_intelligence_ready"),
            "executive_analytics_ready": health.get("executive_analytics_ready"),
            "enterprise_bi_ready": health.get("enterprise_bi_ready"),
            "suite": _suite().status(),
        }
    )


async def rpt_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def rpt_statements_handler(request: web.Request) -> web.Response:
    try:
        statements = _suite().statements
        if request.method == "GET":
            return json_response(statements.status())
        body = await _read_json(request)
        return json_response(
            statements.generate(
                statement_type=body.get("statement_type", "balance_sheet"),
                period=body.get("period", ""),
                entity_ref=body.get("entity_ref", ""),
                lines=body.get("lines") if isinstance(body.get("lines"), list) else None,
                totals=body.get("totals") if isinstance(body.get("totals"), dict) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def rpt_management_handler(request: web.Request) -> web.Response:
    try:
        management = _suite().management
        if request.method == "GET":
            return json_response(management.status())
        body = await _read_json(request)
        return json_response(
            management.generate(
                report_type=body.get("report_type", "department"),
                subject=body.get("subject", ""),
                period=body.get("period", ""),
                budget=float(body.get("budget", 0) or 0),
                actual=float(body.get("actual", 0) or 0),
                detail=body.get("detail", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def rpt_intelligence_handler(request: web.Request) -> web.Response:
    try:
        intelligence = _suite().intelligence
        if request.method == "GET":
            return json_response(intelligence.status())
        body = await _read_json(request)
        action = body.get("action", "analyze")
        if action == "kpi":
            return json_response(
                intelligence.register_kpi(
                    name=body.get("name", ""),
                    kpi_type=body.get("kpi_type", "margin"),
                    value=float(body.get("value", 0) or 0),
                    unit=body.get("unit", "%"),
                ),
                status=201,
            )
        return json_response(
            intelligence.analyze(
                analytic_type=body.get("analytic_type", "revenue"),
                subject=body.get("subject", ""),
                value=float(body.get("value", 0) or 0),
                prior=float(body.get("prior", 0) or 0),
                detail=body.get("detail", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def rpt_consolidation_handler(request: web.Request) -> web.Response:
    try:
        consolidation = _suite().consolidation
        if request.method == "GET":
            return json_response(consolidation.status())
        body = await _read_json(request)
        return json_response(
            consolidation.consolidate(
                consolidation_type=body.get("consolidation_type", "multi_company"),
                label=body.get("label", ""),
                companies=body.get("companies") if isinstance(body.get("companies"), list) else None,
                amount=float(body.get("amount", 0) or 0),
                eliminated=float(body.get("eliminated", 0) or 0),
                detail=body.get("detail", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def rpt_forecast_handler(request: web.Request) -> web.Response:
    try:
        forecasting = _suite().forecasting
        if request.method == "GET":
            return json_response(forecasting.status())
        body = await _read_json(request)
        action = body.get("action", "forecast")
        if action == "scenario":
            return json_response(
                forecasting.scenario(
                    name=body.get("name", ""),
                    base=float(body.get("base", 0) or 0),
                    uplift_pct=float(body.get("uplift_pct", 0) or 0),
                    detail=body.get("detail", ""),
                ),
                status=201,
            )
        if action == "sensitivity":
            return json_response(
                forecasting.sensitivity(
                    driver=body.get("driver", ""),
                    base=float(body.get("base", 0) or 0),
                    shock_pct=float(body.get("shock_pct", 0) or 0),
                    impact=float(body.get("impact", 0) or 0),
                ),
                status=201,
            )
        return json_response(
            forecasting.forecast(
                kind=body.get("kind", "revenue"),
                horizon_days=int(body.get("horizon_days", 90) or 90),
                projected=float(body.get("projected", 0) or 0),
                confidence=float(body.get("confidence", 0.8) or 0.8),
                label=body.get("label", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def rpt_ai_handler(request: web.Request) -> web.Response:
    try:
        ai = _suite().ai
        if request.method == "GET":
            return json_response(ai.status())
        body = await _read_json(request)
        action = body.get("action", "insight")
        if action == "nl_report":
            return json_response(ai.nl_report(audience=body.get("audience", "executive")), status=201)
        if action == "health_score":
            return json_response(
                ai.health_score(
                    subject=body.get("subject", "group"),
                    score=float(body.get("score", 0.82) or 0.82),
                ),
                status=201,
            )
        return json_response(
            ai.insight(
                insight_type=body.get("insight_type", "financial_health"),
                subject=body.get("subject", ""),
                score=float(body.get("score", 0.7) or 0.7),
                detail=body.get("detail", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def rpt_dashboard_handler(request: web.Request) -> web.Response:
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


async def rpt_knowledge_handler(request: web.Request) -> web.Response:
    try:
        knowledge = _suite().knowledge
        if request.method == "GET":
            return json_response(knowledge.status())
        body = await _read_json(request)
        return json_response(
            knowledge.publish(
                base=body.get("base", "reporting"),
                key=body.get("key", ""),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
