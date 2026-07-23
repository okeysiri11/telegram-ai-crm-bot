"""API handlers — AI Orchestrator (Sprint 19.1)."""

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
    return enterprise_hub.orchestrator


async def orch_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "ai_orchestrator_ready": health.get("ai_orchestrator_ready"),
            "workflow_engine_ready": health.get("workflow_engine_ready"),
            "cross_platform_routing_ready": health.get("cross_platform_routing_ready"),
            "ai_decision_engine_ready": health.get("ai_decision_engine_ready"),
            "suite": _suite().status(),
        }
    )


async def orch_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def orch_core_handler(request: web.Request) -> web.Response:
    try:
        core = _suite().core
        if request.method == "GET":
            return json_response(core.status())
        body = await _read_json(request)
        action = body.get("action", "register")
        if action == "plan":
            return json_response(
                core.plan(
                    workflow_id=body.get("workflow_id", ""),
                    context=body.get("context") if isinstance(body.get("context"), dict) else None,
                ),
                status=201,
            )
        if action == "enqueue":
            return json_response(
                core.enqueue(
                    plan_id=body.get("plan_id", ""),
                    priority=int(body.get("priority", 5) or 5),
                ),
                status=201,
            )
        if action == "execute":
            return json_response(
                core.execute(
                    workflow_id=body.get("workflow_id", ""),
                    plan_id=body.get("plan_id", ""),
                ),
                status=201,
            )
        if action == "schedule":
            return json_response(
                core.schedule(
                    workflow_id=body.get("workflow_id", ""),
                    cron=body.get("cron", "0 * * * *"),
                ),
                status=201,
            )
        if action == "retry":
            return json_response(core.retry(execution_id=body.get("execution_id", "")), status=201)
        if action == "rollback":
            return json_response(
                core.rollback(
                    execution_id=body.get("execution_id", ""),
                    reason=body.get("reason", ""),
                ),
                status=201,
            )
        if action == "dependencies":
            return json_response(
                core.resolve_dependencies(
                    workflow_id=body.get("workflow_id", ""),
                    depends_on=body.get("depends_on") if isinstance(body.get("depends_on"), list) else None,
                ),
                status=201,
            )
        return json_response(
            core.register_workflow(
                name=body.get("name", ""),
                kind=body.get("kind", "sequential"),
                steps=body.get("steps") if isinstance(body.get("steps"), list) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def orch_intent_handler(request: web.Request) -> web.Response:
    try:
        intent = _suite().intent
        if request.method == "GET":
            return json_response(intent.status())
        body = await _read_json(request)
        return json_response(
            intent.detect(
                utterance=body.get("utterance", ""),
                task_class=body.get("task_class", "operation"),
                priority=body.get("priority", "normal"),
                confidence=float(body.get("confidence", 0.8) or 0.8),
                entities=body.get("entities") if isinstance(body.get("entities"), list) else None,
                context=body.get("context", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def orch_workflow_handler(request: web.Request) -> web.Response:
    try:
        wi = _suite().workflow_intel
        if request.method == "GET":
            return json_response(wi.status())
        body = await _read_json(request)
        action = body.get("action", "template")
        if action == "generate":
            return json_response(
                wi.generate(
                    name=body.get("name", ""),
                    intent=body.get("intent", ""),
                    platforms=body.get("platforms") if isinstance(body.get("platforms"), list) else None,
                ),
                status=201,
            )
        if action == "approval":
            return json_response(
                wi.add_approval(
                    workflow_ref=body.get("workflow_ref", ""),
                    approver=body.get("approver", "executive"),
                ),
                status=201,
            )
        return json_response(
            wi.create_template(
                name=body.get("name", ""),
                kind=body.get("kind", "sequential"),
                steps=body.get("steps") if isinstance(body.get("steps"), list) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def orch_routing_handler(request: web.Request) -> web.Response:
    try:
        routing = _suite().routing
        if request.method == "GET":
            return json_response(routing.status())
        body = await _read_json(request)
        action = body.get("action", "route")
        if action == "coordinate":
            return json_response(
                routing.coordinate(
                    platforms=body.get("platforms") if isinstance(body.get("platforms"), list) else [],
                    action=body.get("task", body.get("coord_action", "")),
                    label=body.get("label", ""),
                ),
                status=201,
            )
        return json_response(
            routing.route(
                platform=body.get("platform", ""),
                action=body.get("task", body.get("route_action", "")),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else None,
                workflow_ref=body.get("workflow_ref", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def orch_decisions_handler(request: web.Request) -> web.Response:
    try:
        decisions = _suite().decisions
        if request.method == "GET":
            return json_response(decisions.status())
        body = await _read_json(request)
        return json_response(
            decisions.decide(
                decision_type=body.get("decision_type", "recommendation"),
                subject=body.get("subject", ""),
                selected=body.get("selected", ""),
                score=float(body.get("score", 0.8) or 0.8),
                detail=body.get("detail", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def orch_monitoring_handler(request: web.Request) -> web.Response:
    try:
        monitoring = _suite().monitoring
        if request.method == "GET":
            return json_response(monitoring.status())
        body = await _read_json(request)
        action = body.get("action", "track")
        if action == "failure":
            return json_response(
                monitoring.failure(
                    execution_id=body.get("execution_id", ""),
                    reason=body.get("reason", ""),
                    analysis=body.get("analysis", ""),
                ),
                status=201,
            )
        if action == "history":
            return json_response(
                monitoring.history(
                    execution_id=body.get("execution_id", ""),
                    summary=body.get("summary", ""),
                ),
                status=201,
            )
        return json_response(
            monitoring.track(
                execution_id=body.get("execution_id", ""),
                task=body.get("task", ""),
                status=body.get("status", "running"),
                duration_ms=float(body.get("duration_ms", 0) or 0),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def orch_explain_handler(request: web.Request) -> web.Response:
    try:
        explainability = _suite().explainability
        if request.method == "GET":
            return json_response(explainability.status())
        body = await _read_json(request)
        return json_response(
            explainability.explain(
                explain_type=body.get("explain_type", "nl_explanation"),
                subject=body.get("subject", ""),
                confidence=float(body.get("confidence", 0.85) or 0.85),
                narrative=body.get("narrative", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def orch_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dashboard = _suite().dashboard
        if request.method == "GET":
            dtype = request.rel_url.query.get("dashboard_type", "orchestrator")
            return json_response(dashboard.render(dashboard_type=dtype))
        body = await _read_json(request)
        return json_response(
            dashboard.render(dashboard_type=body.get("dashboard_type", "orchestrator")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def orch_knowledge_handler(request: web.Request) -> web.Response:
    try:
        knowledge = _suite().knowledge
        if request.method == "GET":
            return json_response(knowledge.status())
        body = await _read_json(request)
        return json_response(
            knowledge.publish(
                base=body.get("base", "workflow"),
                key=body.get("key", ""),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
