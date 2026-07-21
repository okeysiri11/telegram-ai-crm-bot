# Optimization API handlers — Sprint 7.5.

from __future__ import annotations

from aiohttp import web

from ecosystem import ecosystem
from ecosystem.api.middleware import error_response, json_response
from ecosystem.optimization.models import MetricDomain, RecommendationCategory, SimulationType
from ecosystem.shared.exceptions import EcosystemError, NotFoundError, ValidationError


def _handle_error(exc: Exception) -> web.Response:
    if isinstance(exc, ValidationError):
        return error_response(str(exc), status=400)
    if isinstance(exc, NotFoundError):
        return error_response(str(exc), status=404)
    if isinstance(exc, EcosystemError):
        return error_response(str(exc), status=400)
    raise exc


async def optimization_metrics_handler(_request: web.Request) -> web.Response:
    return json_response(ecosystem.engine.optimization.metrics())


async def optimize_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json() if request.can_read_body else {}
        result = await ecosystem.engine.optimization.optimize(scope=data.get("scope", "ecosystem"))
        return json_response(result, status=201)
    except EcosystemError as exc:
        return _handle_error(exc)


async def learning_cycle_handler(_request: web.Request) -> web.Response:
    cycle = await ecosystem.engine.optimization.learning.run_learning_cycle()
    return json_response(cycle.to_dict(), status=201)


async def learning_history_handler(_request: web.Request) -> web.Response:
    return json_response(ecosystem.engine.optimization.learning.analyze_history())


async def record_execution_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        record = ecosystem.engine.optimization.learning.record_execution(
            data.get("source", "api"),
            data["action"],
            outcome=data.get("outcome", "success"),
            duration_ms=float(data.get("duration_ms", 0)),
            application_id=data.get("application_id", ""),
            agent_id=data.get("agent_id", ""),
            metadata=data.get("metadata"),
        )
        return json_response(record.to_dict(), status=201)
    except (KeyError, ValueError, EcosystemError) as exc:
        return _handle_error(exc if isinstance(exc, EcosystemError) else ValidationError(str(exc)))


async def track_decision_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        outcome = ecosystem.engine.optimization.learning.track_decision(
            data.get("decision_id", ""),
            data.get("decision_type", "general"),
            expected=data.get("expected", ""),
            actual=data.get("actual", ""),
            success=bool(data.get("success", True)),
            score=float(data.get("score", 1.0)),
            lessons=data.get("lessons"),
        )
        return json_response(outcome.to_dict(), status=201)
    except (ValueError, EcosystemError) as exc:
        return _handle_error(exc if isinstance(exc, EcosystemError) else ValidationError(str(exc)))


async def feedback_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        item = ecosystem.engine.optimization.feedback.submit(
            float(data["rating"]),
            comment=data.get("comment", ""),
            source=data.get("source", "user"),
            target_type=data.get("target_type", "workflow"),
            target_id=data.get("target_id", ""),
            tags=data.get("tags"),
        )
        return json_response(item.to_dict(), status=201)
    except (KeyError, ValueError, EcosystemError) as exc:
        return _handle_error(exc if isinstance(exc, EcosystemError) else ValidationError(str(exc)))


async def simulation_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        sim_type = SimulationType(data.get("simulation_type", "what_if"))
        run = await ecosystem.engine.optimization.simulation.run(
            data["name"],
            sim_type,
            data.get("assumptions", {}),
        )
        return json_response(run.to_dict(), status=201)
    except (KeyError, ValueError, EcosystemError) as exc:
        return _handle_error(exc if isinstance(exc, EcosystemError) else ValidationError(str(exc)))


async def list_simulations_handler(request: web.Request) -> web.Response:
    raw = request.query.get("type")
    sim_type = SimulationType(raw) if raw else None
    runs = ecosystem.engine.optimization.simulation.list_runs(simulation_type=sim_type)
    return json_response({"simulations": [r.to_dict() for r in runs]})


async def recommendations_generate_handler(_request: web.Request) -> web.Response:
    recs = await ecosystem.engine.optimization.recommendations.generate(force=True)
    return json_response({"recommendations": [r.to_dict() for r in recs]}, status=201)


async def recommendations_list_handler(request: web.Request) -> web.Response:
    raw = request.query.get("category")
    category = RecommendationCategory(raw) if raw else None
    recs = ecosystem.engine.optimization.recommendations.list_recommendations(category=category)
    return json_response({"recommendations": [r.to_dict() for r in recs]})


async def performance_collect_handler(_request: web.Request) -> web.Response:
    snaps = await ecosystem.engine.optimization.performance.collect_ecosystem_metrics()
    return json_response({"snapshots": [s.to_dict() for s in snaps]}, status=201)


async def performance_dashboard_handler(_request: web.Request) -> web.Response:
    return json_response(ecosystem.engine.optimization.performance.dashboard())


async def performance_record_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        domain = MetricDomain(data.get("domain", "application"))
        snap = await ecosystem.engine.optimization.performance.record(
            data["name"],
            float(data["value"]),
            domain=domain,
            unit=data.get("unit", ""),
            target=float(data.get("target", 0)),
            metadata=data.get("metadata"),
        )
        return json_response(snap.to_dict(), status=201)
    except (KeyError, ValueError, EcosystemError) as exc:
        return _handle_error(exc if isinstance(exc, EcosystemError) else ValidationError(str(exc)))


async def benchmark_handler(_request: web.Request) -> web.Response:
    results = ecosystem.engine.optimization.benchmark.run_suite()
    return json_response({"benchmarks": [b.to_dict() for b in results]})


async def strategy_update_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        strategy = await ecosystem.engine.optimization.strategy.update_from_recommendations(
            data["title"],
            focus=data.get("focus", "ecosystem_optimization"),
            recommendation_ids=data.get("recommendation_ids"),
        )
        return json_response(strategy.to_dict(), status=201)
    except (KeyError, EcosystemError) as exc:
        return _handle_error(exc if isinstance(exc, EcosystemError) else ValidationError(str(exc)))


async def strategy_list_handler(_request: web.Request) -> web.Response:
    strategies = ecosystem.engine.optimization.strategy.list_strategies()
    return json_response({"strategies": [s.to_dict() for s in strategies]})
