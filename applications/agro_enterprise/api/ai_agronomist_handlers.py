"""API handlers — AI Agronomist (Sprint 14.7)."""

from __future__ import annotations

from aiohttp import web

from applications.agro_enterprise import agro_enterprise
from applications.agro_enterprise.api.middleware import json_response
from applications.agro_enterprise.shared.exceptions import NotFoundError, ValidationError


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
    return agro_enterprise.ai_agronomist


async def aa_health_handler(request: web.Request) -> web.Response:
    health = agro_enterprise.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "ai_agronomist_ready": health.get("ai_agronomist_ready"),
            "enterprise_decision_support_ready": health.get("enterprise_decision_support_ready"),
            "autonomous_planning_ready": health.get("autonomous_planning_ready"),
            "executive_intelligence_ready": health.get("executive_intelligence_ready"),
            "suite": _suite().status(),
        }
    )


async def aa_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def aa_agronomist_handler(request: web.Request) -> web.Response:
    try:
        agronomist = _suite().agronomist
        if request.method == "GET":
            return json_response(agronomist.status())
        body = await _read_json(request)
        action = body.get("action", "consult")
        if action == "advise":
            return json_response(
                agronomist.advise(
                    advisory_type=body.get("advisory_type", "crop"),
                    farm_id=body.get("farm_id", ""),
                    details=body.get("details") if isinstance(body.get("details"), dict) else {},
                ),
                status=201,
            )
        return json_response(
            agronomist.consult(
                query=body.get("query", ""),
                farm_id=body.get("farm_id", ""),
                context=body.get("context") if isinstance(body.get("context"), dict) else {},
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def aa_decisions_handler(request: web.Request) -> web.Response:
    try:
        decisions = _suite().decisions
        if request.method == "GET":
            return json_response(decisions.status())
        body = await _read_json(request)
        action = body.get("action", "decide")
        if action == "scenario":
            return json_response(
                decisions.scenario(
                    farm_id=body.get("farm_id", ""),
                    name=body.get("name", ""),
                    assumptions=body.get("assumptions") if isinstance(body.get("assumptions"), dict) else {},
                ),
                status=201,
            )
        if action == "recommend":
            return json_response(
                decisions.recommend(farm_id=body.get("farm_id", ""), focus=body.get("focus", "operations")),
                status=201,
            )
        if action == "prioritize":
            tasks = body.get("tasks") if isinstance(body.get("tasks"), list) else []
            return json_response(
                decisions.prioritize(farm_id=body.get("farm_id", ""), tasks=tasks),
                status=201,
            )
        options = body.get("options") if isinstance(body.get("options"), list) else None
        return json_response(
            decisions.decide(
                intent=body.get("intent", "operational"),
                farm_id=body.get("farm_id", ""),
                options=options,
                risk_score=float(body.get("risk_score", 0.4) or 0.4),
                cost=float(body.get("cost", 0) or 0),
                profit=float(body.get("profit", 0) or 0),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def aa_planning_handler(request: web.Request) -> web.Response:
    try:
        planning = _suite().planning
        if request.method == "GET":
            return json_response(planning.status())
        body = await _read_json(request)
        action = body.get("action", "create")
        if action == "activate":
            return json_response(planning.activate(body.get("plan_id", "")), status=201)
        assets = body.get("assets") if isinstance(body.get("assets"), list) else None
        return json_response(
            planning.create_plan(
                plan_type=body.get("plan_type", "season"),
                farm_id=body.get("farm_id", ""),
                title=body.get("title", ""),
                window_start=body.get("window_start", ""),
                window_end=body.get("window_end", ""),
                assets=assets,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def aa_forecast_handler(request: web.Request) -> web.Response:
    try:
        forecasts = _suite().forecasts
        if request.method == "GET":
            return json_response(forecasts.status())
        body = await _read_json(request)
        return json_response(
            forecasts.forecast(
                forecast_type=body.get("forecast_type", "yield"),
                farm_id=body.get("farm_id", ""),
                horizon_days=int(body.get("horizon_days", 30) or 30),
                baseline=float(body.get("baseline", 1) or 1),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def aa_optimization_handler(request: web.Request) -> web.Response:
    try:
        optimization = _suite().optimization
        if request.method == "GET":
            return json_response(optimization.status())
        body = await _read_json(request)
        return json_response(
            optimization.optimize(
                opt_type=body.get("opt_type", "resource"),
                farm_id=body.get("farm_id", ""),
                current_cost=float(body.get("current_cost", 100) or 100),
                utilization=float(body.get("utilization", 0.7) or 0.7),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def aa_executive_handler(request: web.Request) -> web.Response:
    try:
        executive = _suite().executive
        if request.method == "GET":
            farm_id = request.rel_url.query.get("farm_id")
            if farm_id:
                return json_response(executive.business_health(farm_id=farm_id))
            return json_response(executive.status())
        body = await _read_json(request)
        action = body.get("action", "chat")
        if action == "briefing":
            return json_response(
                executive.daily_briefing(
                    farm_id=body.get("farm_id", ""),
                    executive_id=body.get("executive_id", "ceo"),
                ),
                status=201,
            )
        if action == "strategic":
            return json_response(executive.strategic(farm_id=body.get("farm_id", "")), status=201)
        if action == "investment":
            return json_response(
                executive.investment_recommendation(
                    theme=body.get("theme", ""),
                    amount=float(body.get("amount", 0) or 0),
                ),
                status=201,
            )
        return json_response(
            executive.chat(message=body.get("message", ""), executive_id=body.get("executive_id", "ceo")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def aa_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dash = _suite().dashboard
        if request.method == "GET":
            dtype = request.rel_url.query.get("type", "agronomist")
            return json_response(dash.render(dashboard_type=dtype))
        body = await _read_json(request)
        return json_response(
            dash.render(dashboard_type=body.get("dashboard_type", "agronomist")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def aa_knowledge_handler(request: web.Request) -> web.Response:
    try:
        knowledge = _suite().knowledge
        if request.method == "GET":
            return json_response(knowledge.status())
        body = await _read_json(request)
        return json_response(
            knowledge.publish(
                registry_type=body.get("registry_type", "agronomist"),
                key=body.get("key", ""),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else {},
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
