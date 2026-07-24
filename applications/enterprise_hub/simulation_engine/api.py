"""API handlers — Enterprise Simulation & Decision Intelligence (Sprint 20.9)."""

from __future__ import annotations

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
    return enterprise_hub.simulation_engine


async def esi_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "simulation_engine_ready": health.get("simulation_engine_ready"),
            "decision_intelligence_ready": health.get("decision_intelligence_ready"),
            "forecasting_ready": health.get("forecasting_ready"),
            "risk_engine_ready": health.get("risk_engine_ready"),
            "recommendation_engine_ready": health.get("recommendation_engine_ready"),
            "suite": _suite().status(),
        }
    )


async def esi_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def esi_scenarios_handler(request: web.Request) -> web.Response:
    try:
        suite = _suite()
        if request.method == "GET":
            return json_response(suite.scenarios.status())
        body = await _read_json(request)
        return json_response(
            suite.scenarios.create(
                domain=body.get("domain", "custom"),
                question=body.get("question", ""),
                kind=body.get("kind", "what_if"),
                parameters=body.get("parameters") if isinstance(body.get("parameters"), dict) else None,
                twin_context_id=body.get("twin_context_id"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def esi_decisions_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().decisions.evaluate(
                options=body.get("options") if isinstance(body.get("options"), list) else None,
                weights=body.get("weights") if isinstance(body.get("weights"), dict) else None,
                context=body.get("context", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def esi_forecasts_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().forecasts.forecast(
                target=body.get("target", "sales"),
                horizon=body.get("horizon", "90d"),
                baseline=float(body.get("baseline", 100) or 100),
                growth_pct=float(body.get("growth_pct", 5) or 5),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def esi_optimize_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().optimization.optimize_all(
                context=body.get("context") if isinstance(body.get("context"), dict) else None
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def esi_risk_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().risks.assess(
                scenario_id=body.get("scenario_id"),
                exposures=body.get("exposures") if isinstance(body.get("exposures"), dict) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def esi_monte_carlo_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().monte_carlo.run(
                scenario_id=body.get("scenario_id"),
                iterations=int(body.get("iterations", 100) or 100),
                mean=float(body.get("mean", 100) or 100),
                stdev=float(body.get("stdev", 15) or 15),
                seed=int(body.get("seed", 42) or 42),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def esi_sensitivity_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().sensitivity.analyze(
                parameters=body.get("parameters") if isinstance(body.get("parameters"), dict) else None,
                outcome_key=body.get("outcome_key", "profit"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def esi_dashboard_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().dashboard())
    except Exception as exc:
        return _handle_error(exc)


async def esi_analytics_handler(request: web.Request) -> web.Response:
    try:
        suite = _suite()
        return json_response(
            {
                "predictions": suite.predictions.report(),
                "confidence": suite.confidence.report(),
                "recommendations": suite.recommendation_analytics.report(),
                "executive": suite.executive.report(),
            }
        )
    except Exception as exc:
        return _handle_error(exc)


async def esi_recommendations_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().recommendation_engine.generate(
                scenario_id=body.get("scenario_id"),
                decision_id=body.get("decision_id"),
                risk_id=body.get("risk_id"),
                actions=body.get("actions") if isinstance(body.get("actions"), list) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def esi_schedule_handler(request: web.Request) -> web.Response:
    try:
        suite = _suite()
        if request.method == "GET":
            return json_response(suite.scheduler.status())
        body = await _read_json(request)
        action = (body.get("action") or "schedule").lower()
        if action == "schedule":
            return json_response(
                suite.scheduler.schedule(
                    scenario_id=body.get("scenario_id", ""),
                    mode=body.get("mode", "manual"),
                    run_at=body.get("run_at", "immediate"),
                    priority=int(body.get("priority", 5) or 5),
                    event_type=body.get("event_type"),
                    interval_sec=body.get("interval_sec"),
                ),
                status=201,
            )
        if action == "execute":
            return json_response(suite.scheduler.execute(schedule_id=body.get("schedule_id", "")), status=201)
        if action == "on_event":
            return json_response(
                {"runs": suite.scheduler.on_event(event_type=body.get("event_type", ""), payload=body.get("payload") if isinstance(body.get("payload"), dict) else None)},
                status=201,
            )
        if action == "tick_continuous":
            return json_response({"runs": suite.scheduler.tick_continuous()}, status=201)
        raise ValidationError(f"unknown action: {action}")
    except Exception as exc:
        return _handle_error(exc)
