"""API handlers — AI Port Director (Sprint 15.7)."""

from __future__ import annotations

from aiohttp import web

from applications.port_enterprise import port_enterprise
from applications.port_enterprise.api.middleware import json_response
from applications.port_enterprise.shared.exceptions import NotFoundError, ValidationError


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
    return port_enterprise.ai_port_director


async def ad_health_handler(request: web.Request) -> web.Response:
    health = port_enterprise.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "ai_port_director_ready": health.get("ai_port_director_ready"),
            "predictive_logistics_ready": health.get("predictive_logistics_ready"),
            "autonomous_operations_ready": health.get("autonomous_operations_ready"),
            "executive_intelligence_ready": health.get("executive_intelligence_ready"),
            "suite": _suite().status(),
        }
    )


async def ad_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ad_director_handler(request: web.Request) -> web.Response:
    try:
        director = _suite().director
        if request.method == "GET":
            return json_response(director.status())
        body = await _read_json(request)
        action = body.get("action", "ask")
        if action == "nl":
            return json_response(
                director.natural_language(
                    utterance=body.get("utterance", ""),
                    intent=body.get("intent", "status"),
                ),
                status=201,
            )
        if action == "advise":
            return json_response(
                director.advise(
                    advisory_type=body.get("advisory_type", "port"),
                    subject=body.get("subject", ""),
                    recommendation=body.get("recommendation", ""),
                ),
                status=201,
            )
        return json_response(
            director.ask(prompt=body.get("prompt", ""), context=body.get("context", "port")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ad_decisions_handler(request: web.Request) -> web.Response:
    try:
        decisions = _suite().decisions
        if request.method == "GET":
            return json_response(decisions.status())
        body = await _read_json(request)
        action = body.get("action", "decide")
        if action == "scenario":
            assumptions = body.get("assumptions") if isinstance(body.get("assumptions"), dict) else None
            return json_response(
                decisions.scenario(name=body.get("name", ""), assumptions=assumptions),
                status=201,
            )
        if action == "recommend":
            return json_response(
                decisions.recommend(domain=body.get("domain", ""), action=body.get("recommend_action", body.get("action_text", ""))),
                status=201,
            )
        if action == "allocate":
            return json_response(
                decisions.allocate_resources(
                    resource=body.get("resource", ""),
                    quantity=float(body.get("quantity", 0) or 0),
                    target=body.get("target", ""),
                ),
                status=201,
            )
        if action == "priority":
            return json_response(
                decisions.set_priority(
                    item_ref=body.get("item_ref", ""),
                    priority=body.get("priority", "high"),
                ),
                status=201,
            )
        if action == "cost":
            return json_response(
                decisions.optimize_cost(
                    scope=body.get("scope", ""),
                    baseline=float(body.get("baseline", 0) or 0),
                ),
                status=201,
            )
        if action == "profitability":
            return json_response(
                decisions.profitability(
                    segment=body.get("segment", ""),
                    revenue=float(body.get("revenue", 0) or 0),
                    cost=float(body.get("cost", 0) or 0),
                ),
                status=201,
            )
        if action == "strategy":
            goals = body.get("goals") if isinstance(body.get("goals"), list) else None
            return json_response(
                decisions.strategic_plan(horizon=body.get("horizon", ""), goals=goals),
                status=201,
            )
        options = body.get("options") if isinstance(body.get("options"), list) else None
        return json_response(
            decisions.decide(topic=body.get("topic", ""), options=options),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ad_predictive_handler(request: web.Request) -> web.Response:
    try:
        predictive = _suite().predictive
        if request.method == "GET":
            return json_response(predictive.status())
        body = await _read_json(request)
        action = body.get("action", "arrival")
        if action == "departure":
            return json_response(
                predictive.predict_departure(
                    vessel_ref=body.get("vessel_ref", ""),
                    etd_hours=float(body.get("etd_hours", 0) or 0),
                ),
                status=201,
            )
        if action == "cargo_flow":
            return json_response(
                predictive.cargo_flow(
                    terminal_ref=body.get("terminal_ref", ""),
                    teu=float(body.get("teu", 0) or 0),
                    days=int(body.get("days", 7) or 7),
                ),
                status=201,
            )
        if action == "congestion":
            return json_response(
                predictive.congestion(terminal_ref=body.get("terminal_ref", "")),
                status=201,
            )
        if action == "equipment":
            return json_response(
                predictive.equipment_utilization(
                    equipment_type=body.get("equipment_type", ""),
                    utilization_pct=float(body.get("utilization_pct", 0) or 0),
                ),
                status=201,
            )
        if action == "demand":
            return json_response(
                predictive.demand(
                    corridor=body.get("corridor", ""),
                    baseline=float(body.get("baseline", 0) or 0),
                    days=int(body.get("days", 30) or 30),
                ),
                status=201,
            )
        if action == "supply_chain":
            return json_response(
                predictive.supply_chain(chain_ref=body.get("chain_ref", "")),
                status=201,
            )
        if action == "weather":
            return json_response(
                predictive.weather_impact(
                    location=body.get("location", ""),
                    severity=float(body.get("severity", 0) or 0),
                ),
                status=201,
            )
        return json_response(
            predictive.predict_arrival(
                vessel_ref=body.get("vessel_ref", ""),
                eta_hours=float(body.get("eta_hours", 0) or 0),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ad_autonomous_handler(request: web.Request) -> web.Response:
    try:
        autonomous = _suite().autonomous
        if request.method == "GET":
            return json_response(autonomous.status())
        body = await _read_json(request)
        action = body.get("action", "dock")
        if action == "berth":
            return json_response(
                autonomous.allocate_berth(
                    berth_ref=body.get("berth_ref", ""),
                    vessel_ref=body.get("vessel_ref", ""),
                ),
                status=201,
            )
        if action == "equipment":
            return json_response(
                autonomous.schedule_equipment(
                    equipment_ref=body.get("equipment_ref", ""),
                    task=body.get("task", ""),
                ),
                status=201,
            )
        if action == "move":
            return json_response(
                autonomous.plan_container_move(
                    container_ref=body.get("container_ref", ""),
                    from_slot=body.get("from_slot", ""),
                    to_slot=body.get("to_slot", ""),
                ),
                status=201,
            )
        if action == "yard":
            return json_response(
                autonomous.optimize_yard(yard_ref=body.get("yard_ref", "")),
                status=201,
            )
        if action == "fleet":
            return json_response(
                autonomous.coordinate_fleet(
                    fleet_ref=body.get("fleet_ref", ""),
                    objective=body.get("objective", "throughput"),
                ),
                status=201,
            )
        if action == "maintenance":
            return json_response(
                autonomous.schedule_maintenance(
                    asset_ref=body.get("asset_ref", ""),
                    due_at=body.get("due_at", ""),
                ),
                status=201,
            )
        if action == "emergency":
            return json_response(
                autonomous.emergency_plan(
                    incident_type=body.get("incident_type", ""),
                    severity=body.get("severity", "medium"),
                ),
                status=201,
            )
        return json_response(
            autonomous.schedule_dock(
                dock_ref=body.get("dock_ref", ""),
                vessel_ref=body.get("vessel_ref", ""),
                window_start=body.get("window_start", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ad_intelligence_handler(request: web.Request) -> web.Response:
    try:
        intel = _suite().intelligence
        if request.method == "GET":
            return json_response(intel.status())
        body = await _read_json(request)
        action = body.get("action", "risk")
        if action == "delay":
            return json_response(
                intel.delay_predict(
                    subject_ref=body.get("subject_ref", ""),
                    risk=float(body.get("risk", 0) or 0),
                ),
                status=201,
            )
        if action == "bottleneck":
            return json_response(
                intel.bottleneck(
                    location=body.get("location", ""),
                    severity=float(body.get("severity", 0) or 0),
                ),
                status=201,
            )
        if action == "incident":
            return json_response(
                intel.incident_predict(
                    domain=body.get("domain", ""),
                    probability=float(body.get("probability", 0) or 0),
                ),
                status=201,
            )
        if action == "capacity":
            return json_response(
                intel.capacity_forecast(
                    node=body.get("node", ""),
                    teu=float(body.get("teu", 0) or 0),
                ),
                status=201,
            )
        if action == "kpi":
            return json_response(
                intel.kpi_predict(
                    kpi=body.get("kpi", ""),
                    baseline=float(body.get("baseline", 0) or 0),
                ),
                status=201,
            )
        if action == "performance":
            return json_response(
                intel.optimize_performance(scope=body.get("scope", "")),
                status=201,
            )
        return json_response(
            intel.risk_assess(
                domain=body.get("domain", ""),
                score=float(body.get("score", 0) or 0),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ad_executive_handler(request: web.Request) -> web.Response:
    try:
        executive = _suite().executive
        if request.method == "GET":
            return json_response(executive.status())
        body = await _read_json(request)
        action = body.get("action", "chat")
        if action == "briefing":
            return json_response(
                executive.daily_briefing(date=body.get("date", "")),
                status=201,
            )
        if action == "health":
            return json_response(
                executive.health_score(score=float(body.get("score", 0) or 0)),
                status=201,
            )
        if action == "strategy":
            return json_response(
                executive.strategic_recommendation(
                    theme=body.get("theme", ""),
                    action=body.get("strategy_action", body.get("recommend_action", "")),
                ),
                status=201,
            )
        if action == "financial":
            return json_response(
                executive.financial_insight(
                    metric=body.get("metric", ""),
                    value=float(body.get("value", 0) or 0),
                ),
                status=201,
            )
        if action == "investment":
            return json_response(
                executive.investment_plan(
                    project=body.get("project", ""),
                    amount=float(body.get("amount", 0) or 0),
                ),
                status=201,
            )
        return json_response(
            executive.chat(message=body.get("message", ""), executive=body.get("executive", "CEO")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ad_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dash = _suite().dashboard
        if request.method == "GET":
            dtype = request.rel_url.query.get("type", "ai_director")
            return json_response(dash.render(dashboard_type=dtype))
        body = await _read_json(request)
        return json_response(
            dash.render(dashboard_type=body.get("dashboard_type", "ai_director")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ad_knowledge_handler(request: web.Request) -> web.Response:
    try:
        knowledge = _suite().knowledge
        if request.method == "GET":
            return json_response(knowledge.status())
        body = await _read_json(request)
        return json_response(
            knowledge.publish(
                registry_type=body.get("registry_type", "director"),
                key=body.get("key", ""),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else {},
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
