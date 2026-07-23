"""API handlers — Enterprise Autonomous AIOS (Sprint 20.4)."""

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
    return enterprise_hub.aios


async def aios_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "autonomous_aios_ready": health.get("autonomous_aios_ready"),
            "goal_manager_ready": health.get("goal_manager_ready"),
            "checkpoint_recovery_ready": health.get("checkpoint_recovery_ready"),
            "aios_governance_ready": health.get("aios_governance_ready"),
            "suite": _suite().status(),
        }
    )


async def aios_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def aios_goals_handler(request: web.Request) -> web.Response:
    try:
        goals = _suite().goals
        if request.method == "GET":
            return json_response(goals.status())
        body = await _read_json(request)
        return json_response(
            goals.create(
                title=body.get("title", ""),
                kind=body.get("kind", "operational"),
                priority=body.get("priority", "normal"),
                deadline=body.get("deadline"),
                depends_on=body.get("depends_on") if isinstance(body.get("depends_on"), list) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def aios_run_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().aios.run_goal(
                title=body.get("title", ""),
                kind=body.get("kind", "operational"),
                priority=body.get("priority", "normal"),
                mode=body.get("mode", "sequential"),
                budget=float(body.get("budget", 10) or 10),
                confirmed=bool(body.get("confirmed", True)),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def aios_plan_handler(request: web.Request) -> web.Response:
    try:
        planner = _suite().planner
        if request.method == "GET":
            return json_response({"plans": _suite().store.aios_plans.count()})
        body = await _read_json(request)
        return json_response(
            planner.plan(
                goal_id=body.get("goal_id", ""),
                mode=body.get("mode", "sequential"),
                steps=body.get("steps") if isinstance(body.get("steps"), list) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def aios_execute_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().executor.run_plan(
                plan_id=body.get("plan_id", ""),
                budget=float(body.get("budget", 10) or 10),
                confirmed=bool(body.get("confirmed", True)),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def aios_supervise_handler(request: web.Request) -> web.Response:
    try:
        sup = _suite().supervisor
        if request.method == "GET":
            return json_response(sup.status())
        body = await _read_json(request)
        return json_response(
            sup.inspect(
                task_id=body.get("task_id", ""),
                budget=float(body.get("budget", 10) or 10),
                spent=float(body.get("spent", 0) or 0),
                timeout=bool(body.get("timeout", False)),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def aios_recover_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().recovery.recover(
                task_id=body.get("task_id", ""),
                action=body.get("action", "retry"),
                new_assignee=body.get("new_assignee"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def aios_governance_handler(request: web.Request) -> web.Response:
    try:
        suite = _suite()
        if request.method == "GET":
            return json_response(
                {
                    "approvals": suite.store.aios_approvals.count(),
                    "limits": suite.store.aios_limits.count(),
                    "safety": suite.store.aios_safety.count(),
                    "escalations": suite.store.aios_escalations.count(),
                }
            )
        body = await _read_json(request)
        action = (body.get("action") or "safety").lower()
        if action == "approve":
            return json_response(
                suite.approvals.approve(approval_id=body.get("approval_id", ""), actor=body.get("actor", "user")),
                status=201,
            )
        if action == "require":
            return json_response(
                suite.approvals.require(goal_id=body.get("goal_id", ""), reason=body.get("reason", "review")),
                status=201,
            )
        if action == "limits":
            return json_response(
                suite.limits.define(
                    max_budget=float(body.get("max_budget", 10) or 10),
                    max_minutes=int(body.get("max_minutes", 60) or 60),
                ),
                status=201,
            )
        if action == "escalate":
            return json_response(
                suite.escalation.escalate(
                    task_id=body.get("task_id", ""),
                    reason=body.get("reason", "manual"),
                    level=body.get("level", "ops"),
                ),
                status=201,
            )
        return json_response(suite.safety.evaluate(operation=body.get("operation", "")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def aios_dashboard_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().dashboard())
    except Exception as exc:
        return _handle_error(exc)


async def aios_analytics_handler(request: web.Request) -> web.Response:
    try:
        suite = _suite()
        kind = request.rel_url.query.get("kind", "productivity")
        if request.method == "POST":
            body = await _read_json(request)
            kind = body.get("kind", kind)
        if kind == "efficiency":
            return json_response(suite.efficiency.report())
        if kind == "optimization":
            return json_response(suite.optimization.report())
        return json_response(suite.productivity.report())
    except Exception as exc:
        return _handle_error(exc)
