"""API handlers — Enterprise AI Orchestration Platform (Sprint 20.1)."""

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
    return enterprise_hub.ai_orchestrator


async def aop_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "ai_orchestration_ready": health.get("ai_orchestration_ready"),
            "agent_registry_ready": health.get("agent_registry_ready"),
            "task_planning_ready": health.get("task_planning_ready"),
            "result_aggregation_ready": health.get("result_aggregation_ready"),
            "suite": _suite().status(),
        }
    )


async def aop_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def aop_agents_handler(request: web.Request) -> web.Response:
    try:
        reg = _suite().registry
        if request.method == "GET":
            return json_response(reg.status())
        body = await _read_json(request)
        return json_response(
            reg.register(
                name=body.get("name", ""),
                specialization=body.get("specialization", ""),
                tasks=body.get("tasks") if isinstance(body.get("tasks"), list) else None,
                model=body.get("model", "gpt-enterprise"),
                cost_per_task=float(body.get("cost_per_task", 0.01) or 0.01),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def aop_tasks_handler(request: web.Request) -> web.Response:
    try:
        tasks = _suite().tasks
        if request.method == "GET":
            return json_response(tasks.status())
        body = await _read_json(request)
        return json_response(
            tasks.create(
                request=body.get("request", ""),
                priority=body.get("priority", "normal"),
                meta=body.get("meta") if isinstance(body.get("meta"), dict) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def aop_orchestrate_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().orchestrator.orchestrate(
                request=body.get("request", ""),
                strategy=body.get("strategy", "sequential"),
                priority=body.get("priority", "normal"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def aop_plan_handler(request: web.Request) -> web.Response:
    try:
        planner = _suite().planner
        if request.method == "GET":
            return json_response({"plans": _suite().store.aop_plans.count()})
        body = await _read_json(request)
        return json_response(
            planner.plan(task_id=body.get("task_id", ""), steps=body.get("steps")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def aop_dispatch_handler(request: web.Request) -> web.Response:
    try:
        disp = _suite().dispatcher
        if request.method == "GET":
            return json_response({"dispatches": _suite().store.aop_dispatches.count()})
        body = await _read_json(request)
        return json_response(
            disp.dispatch(
                task_id=body.get("task_id", ""),
                plan_id=body.get("plan_id", ""),
                strategy=body.get("strategy", "sequential"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def aop_execute_handler(request: web.Request) -> web.Response:
    try:
        exe = _suite().execution
        if request.method == "GET":
            return json_response(exe.status())
        body = await _read_json(request)
        return json_response(
            exe.run(
                task_id=body.get("task_id", ""),
                dispatch_id=body.get("dispatch_id", ""),
                timeout_ms=int(body.get("timeout_ms", 30000) or 30000),
                max_retries=int(body.get("max_retries", 2) or 2),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def aop_context_handler(request: web.Request) -> web.Response:
    try:
        ctx = _suite().context
        if request.method == "GET":
            return json_response({"contexts": _suite().store.aop_contexts.count()})
        body = await _read_json(request)
        action = (body.get("action") or "open").lower()
        if action == "append":
            return json_response(
                ctx.append(
                    context_id=body.get("context_id", ""),
                    agent_id=body.get("agent_id", ""),
                    payload=body.get("payload") if isinstance(body.get("payload"), dict) else {},
                ),
                status=201,
            )
        return json_response(
            ctx.open(
                task_id=body.get("task_id", ""),
                seed=body.get("seed") if isinstance(body.get("seed"), dict) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def aop_memory_handler(request: web.Request) -> web.Response:
    try:
        mem = _suite().memory
        if request.method == "GET":
            return json_response(mem.status())
        body = await _read_json(request)
        return json_response(
            mem.route(
                task_id=body.get("task_id", ""),
                tier=body.get("tier", "short_term"),
                key=body.get("key", ""),
                value=body.get("value"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def aop_aggregate_handler(request: web.Request) -> web.Response:
    try:
        agg = _suite().aggregator
        if request.method == "GET":
            return json_response({"aggregations": _suite().store.aop_aggregations.count()})
        body = await _read_json(request)
        return json_response(agg.aggregate(execution_id=body.get("execution_id", "")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def aop_policy_handler(request: web.Request) -> web.Response:
    try:
        pol = _suite().policy
        if request.method == "GET":
            return json_response(pol.status())
        body = await _read_json(request)
        action = (body.get("action") or "define").lower()
        if action == "evaluate":
            return json_response(
                pol.evaluate(
                    strategy=body.get("strategy", "sequential"),
                    estimated_cost=float(body.get("estimated_cost", 0) or 0),
                ),
                status=201,
            )
        return json_response(
            pol.define(
                kind=body.get("kind", "collaboration"),
                name=body.get("name", ""),
                rules=body.get("rules") if isinstance(body.get("rules"), dict) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def aop_analytics_handler(request: web.Request) -> web.Response:
    try:
        suite = _suite()
        if request.method == "GET":
            kind = request.rel_url.query.get("kind", "performance")
            if kind == "cost":
                return json_response(suite.costs.report())
            if kind == "optimization":
                return json_response(suite.optimization.recommend())
            return json_response(suite.performance.report())
        body = await _read_json(request)
        kind = (body.get("kind") or "performance").lower()
        if kind == "cost":
            return json_response(suite.costs.report(), status=201)
        if kind == "optimization":
            return json_response(suite.optimization.recommend(), status=201)
        return json_response(suite.performance.report(agent_id=body.get("agent_id")), status=201)
    except Exception as exc:
        return _handle_error(exc)
