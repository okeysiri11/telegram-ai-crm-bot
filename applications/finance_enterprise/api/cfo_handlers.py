"""API handlers — AI CFO & Decision Support (Sprint 18.6)."""

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
    return finance_enterprise.ai_cfo


async def cfo_health_handler(request: web.Request) -> web.Response:
    health = finance_enterprise.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "ai_cfo_ready": health.get("ai_cfo_ready"),
            "financial_decision_support_ready": health.get("financial_decision_support_ready"),
            "financial_modeling_ready": health.get("financial_modeling_ready"),
            "executive_financial_intelligence_ready": health.get(
                "executive_financial_intelligence_ready"
            ),
            "suite": _suite().status(),
        }
    )


async def cfo_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def cfo_workspace_handler(request: web.Request) -> web.Response:
    try:
        workspace = _suite().workspace
        if request.method == "GET":
            return json_response(workspace.status())
        body = await _read_json(request)
        action = body.get("action", "open")
        if action == "chat":
            return json_response(
                workspace.chat(
                    workspace_id=body.get("workspace_id", ""),
                    message=body.get("message", ""),
                    role=body.get("role", "executive_assistant"),
                    context=body.get("context", ""),
                ),
                status=201,
            )
        if action == "ask":
            return json_response(
                workspace.ask(
                    workspace_id=body.get("workspace_id", ""),
                    question=body.get("question", ""),
                ),
                status=201,
            )
        return json_response(
            workspace.open_workspace(
                label=body.get("label", ""),
                owner=body.get("owner", "cfo"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def cfo_performance_handler(request: web.Request) -> web.Response:
    try:
        performance = _suite().performance
        if request.method == "GET":
            return json_response(performance.status())
        body = await _read_json(request)
        return json_response(
            performance.analyze(
                analysis_type=body.get("analysis_type", "revenue"),
                subject=body.get("subject", ""),
                value=float(body.get("value", 0) or 0),
                prior=float(body.get("prior", 0) or 0),
                detail=body.get("detail", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def cfo_strategy_handler(request: web.Request) -> web.Response:
    try:
        strategy = _suite().strategy
        if request.method == "GET":
            return json_response(strategy.status())
        body = await _read_json(request)
        return json_response(
            strategy.plan(
                plan_type=body.get("plan_type", "capital_allocation"),
                label=body.get("label", ""),
                amount=float(body.get("amount", 0) or 0),
                priority=int(body.get("priority", 1) or 1),
                detail=body.get("detail", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def cfo_modeling_handler(request: web.Request) -> web.Response:
    try:
        modeling = _suite().modeling
        if request.method == "GET":
            return json_response(modeling.status())
        body = await _read_json(request)
        return json_response(
            modeling.model(
                model_type=body.get("model_type", "roi"),
                label=body.get("label", ""),
                inputs=body.get("inputs") if isinstance(body.get("inputs"), dict) else None,
                result=float(body.get("result", 0) or 0),
                detail=body.get("detail", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def cfo_risk_handler(request: web.Request) -> web.Response:
    try:
        risk = _suite().risk
        if request.method == "GET":
            return json_response(risk.status())
        body = await _read_json(request)
        return json_response(
            risk.assess(
                risk_type=body.get("risk_type", "liquidity"),
                subject=body.get("subject", ""),
                score=float(body.get("score", 0.5) or 0.5),
                mitigation=body.get("mitigation", ""),
                detail=body.get("detail", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def cfo_decisions_handler(request: web.Request) -> web.Response:
    try:
        decisions = _suite().decisions
        if request.method == "GET":
            return json_response(decisions.status())
        body = await _read_json(request)
        return json_response(
            decisions.recommend(
                recommendation_type=body.get("recommendation_type", "executive"),
                subject=body.get("subject", ""),
                priority=int(body.get("priority", 1) or 1),
                score=float(body.get("score", 0.75) or 0.75),
                detail=body.get("detail", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def cfo_executive_handler(request: web.Request) -> web.Response:
    try:
        executive = _suite().executive
        if request.method == "GET":
            return json_response(executive.status())
        body = await _read_json(request)
        return json_response(
            executive.report(
                report_type=body.get("report_type", "daily_briefing"),
                audience=body.get("audience", "executive"),
                narrative=body.get("narrative", ""),
                period=body.get("period", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def cfo_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dashboard = _suite().dashboard
        if request.method == "GET":
            dtype = request.rel_url.query.get("dashboard_type", "ai_cfo")
            return json_response(dashboard.render(dashboard_type=dtype))
        body = await _read_json(request)
        return json_response(
            dashboard.render(dashboard_type=body.get("dashboard_type", "ai_cfo")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def cfo_knowledge_handler(request: web.Request) -> web.Response:
    try:
        knowledge = _suite().knowledge
        if request.method == "GET":
            return json_response(knowledge.status())
        body = await _read_json(request)
        return json_response(
            knowledge.publish(
                base=body.get("base", "intelligence"),
                key=body.get("key", ""),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
