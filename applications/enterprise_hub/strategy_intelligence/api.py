"""API handlers — Strategy Intelligence (Sprint 24.7)."""

from __future__ import annotations

import uuid

from aiohttp import web

from applications.enterprise_hub import enterprise_hub
from applications.enterprise_hub.api.middleware import json_response
from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError


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
    return enterprise_hub.strategy_intelligence


async def est_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "strategy_intelligence_ready": health.get("strategy_intelligence_ready"),
            "strategic_goals_ready": health.get("strategic_goals_ready"),
            "long_term_forecast_ready": health.get("long_term_forecast_ready"),
            "owner_strategy_ready": health.get("owner_strategy_ready"),
            "suite": _suite().status(),
        }
    )


async def est_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def est_strategy_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().create_strategy(
                strategy_id=body.get("strategy_id") or f"str_{uuid.uuid4().hex[:8]}",
                name=body.get("name", ""),
                goal=body.get("goal", ""),
                horizon=body.get("horizon", "year"),
                owner=body.get("owner", "platform_owner"),
                kpis=body.get("kpis"),
                version=body.get("version", "1.0"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def est_strategies_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().list_strategies())
    except Exception as exc:
        return _handle_error(exc)


async def est_goal_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().define_goal(
                goal_type=body.get("goal_type", ""),
                target_value=float(body.get("target_value", 0)),
                unit=body.get("unit", "pct"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def est_forecast_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().forecast(
                baseline=float(body.get("baseline", 0)),
                growth_rate=float(body.get("growth_rate", 0.1)),
                horizon=body.get("horizon", "year"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def est_scenarios_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().build_scenarios(
                baseline_value=float(body.get("baseline_value", 0)),
                strategy_id=body.get("strategy_id", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def est_investment_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().analyze_investment(
                investment=float(body.get("investment", 0)),
                annual_return=float(body.get("annual_return", 0)),
                cashflow_delta=float(body.get("cashflow_delta", 0)),
                profit_delta=float(body.get("profit_delta", 0)),
                staff_impact=float(body.get("staff_impact", 0)),
                customer_impact=float(body.get("customer_impact", 0)),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def est_expansion_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(_suite().plan_expansion(items=body.get("items")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def est_risk_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(_suite().assess_risk(scores=body.get("scores")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def est_council_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().council_review(
                strategy_id=body.get("strategy_id", ""),
                risk_score=float(body.get("risk_score", 0.3)),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def est_owner_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().owner_decide(
                action=body.get("action", ""),
                actor=body.get("actor", ""),
                strategy_id=body.get("strategy_id", ""),
                modifications=body.get("modifications"),
                notes=body.get("notes", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def est_dashboard_handler(request: web.Request) -> web.Response:
    try:
        strategy_id = request.rel_url.query.get("strategy_id")
        return json_response(_suite().owner_dashboard(strategy_id=strategy_id))
    except Exception as exc:
        return _handle_error(exc)
