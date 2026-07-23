"""API handlers — Enterprise AI Agents & Autonomous Automation (Sprint 19.3)."""

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
    return enterprise_hub.ai_agents


async def aa_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "enterprise_ai_agents_ready": health.get("enterprise_ai_agents_ready"),
            "autonomous_automation_ready": health.get("autonomous_automation_ready"),
            "multi_agent_collaboration_ready": health.get("multi_agent_collaboration_ready"),
            "ai_agent_governance_ready": health.get("ai_agent_governance_ready"),
            "suite": _suite().status(),
        }
    )


async def aa_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def aa_registry_handler(request: web.Request) -> web.Response:
    try:
        registry = _suite().registry
        if request.method == "GET":
            return json_response(registry.status())
        body = await _read_json(request)
        action = body.get("action", "agent")
        if action == "capability":
            return json_response(
                registry.register_capability(
                    name=body.get("name", ""),
                    description=body.get("description", ""),
                ),
                status=201,
            )
        if action == "permission":
            return json_response(
                registry.register_permission(
                    name=body.get("name", ""),
                    scope=body.get("scope", "enterprise"),
                ),
                status=201,
            )
        if action == "lifecycle":
            return json_response(
                registry.set_lifecycle(
                    agent_id=body.get("agent_id", ""),
                    lifecycle=body.get("lifecycle", "active"),
                ),
                status=201,
            )
        if action == "version":
            return json_response(
                registry.version_agent(
                    agent_id=body.get("agent_id", ""),
                    note=body.get("note", ""),
                ),
                status=201,
            )
        return json_response(
            registry.register_agent(
                name=body.get("name", ""),
                agent_type=body.get("agent_type", "general"),
                capabilities=body.get("capabilities") if isinstance(body.get("capabilities"), list) else None,
                permissions=body.get("permissions") if isinstance(body.get("permissions"), list) else None,
                profile=body.get("profile") if isinstance(body.get("profile"), dict) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def aa_execution_handler(request: web.Request) -> web.Response:
    try:
        execution = _suite().execution
        if request.method == "GET":
            return json_response(execution.status())
        body = await _read_json(request)
        action = body.get("action", "assign")
        if action == "prioritize":
            return json_response(
                execution.prioritize(
                    task_id=body.get("task_id", ""),
                    priority=int(body.get("priority", 5) or 5),
                ),
                status=201,
            )
        if action == "execute":
            return json_response(execution.execute(task_id=body.get("task_id", "")), status=201)
        if action == "retry":
            return json_response(
                execution.retry(task_id=body.get("task_id", ""), reason=body.get("reason", "")),
                status=201,
            )
        if action == "history":
            return json_response(
                execution.record_history(
                    task_id=body.get("task_id", ""),
                    detail=body.get("detail", ""),
                ),
                status=201,
            )
        return json_response(
            execution.assign_task(
                agent_id=body.get("agent_id", ""),
                title=body.get("title", ""),
                priority=int(body.get("priority", 5) or 5),
                mode=body.get("mode", "sequential"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def aa_collaboration_handler(request: web.Request) -> web.Response:
    try:
        collab = _suite().collaboration
        if request.method == "GET":
            return json_response(collab.status())
        body = await _read_json(request)
        action = body.get("action", "communicate")
        if action == "share_context":
            return json_response(
                collab.share_context(
                    agent_ids=body.get("agent_ids") if isinstance(body.get("agent_ids"), list) else [],
                    label=body.get("label", "shared"),
                    payload=body.get("payload") if isinstance(body.get("payload"), dict) else None,
                ),
                status=201,
            )
        if action == "delegate":
            return json_response(
                collab.delegate(
                    from_agent_id=body.get("from_agent_id", ""),
                    to_agent_id=body.get("to_agent_id", ""),
                    task_ref=body.get("task_ref", ""),
                ),
                status=201,
            )
        if action == "consensus":
            return json_response(
                collab.consensus(
                    agent_ids=body.get("agent_ids") if isinstance(body.get("agent_ids"), list) else [],
                    topic=body.get("topic", ""),
                    outcome=body.get("outcome", "approved"),
                ),
                status=201,
            )
        if action == "conflict":
            return json_response(
                collab.resolve_conflict(
                    detail=body.get("detail", ""),
                    resolution=body.get("resolution", "escalate"),
                ),
                status=201,
            )
        if action == "plan":
            return json_response(
                collab.plan(
                    agent_ids=body.get("agent_ids") if isinstance(body.get("agent_ids"), list) else [],
                    objective=body.get("objective", ""),
                    steps=body.get("steps") if isinstance(body.get("steps"), list) else None,
                ),
                status=201,
            )
        return json_response(
            collab.communicate(
                from_agent_id=body.get("from_agent_id", ""),
                to_agent_id=body.get("to_agent_id", ""),
                message=body.get("message", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def aa_automation_handler(request: web.Request) -> web.Response:
    try:
        automation = _suite().automation
        if request.method == "GET":
            return json_response(automation.status())
        body = await _read_json(request)
        action = body.get("action", "create")
        if action == "approval":
            return json_response(
                automation.request_approval(
                    automation_id=body.get("automation_id", ""),
                    requester=body.get("requester", "system"),
                ),
                status=201,
            )
        if action == "hitl":
            return json_response(
                automation.human_in_loop(
                    automation_id=body.get("automation_id", ""),
                    operator=body.get("operator", "operator"),
                    decision=body.get("decision", "continue"),
                ),
                status=201,
            )
        if action == "emergency_stop":
            return json_response(
                automation.emergency_stop(
                    automation_id=body.get("automation_id", ""),
                    reason=body.get("reason", ""),
                ),
                status=201,
            )
        return json_response(
            automation.create(
                name=body.get("name", ""),
                kind=body.get("kind", "scheduled"),
                agent_id=body.get("agent_id", ""),
                rule=body.get("rule", ""),
                schedule=body.get("schedule", ""),
                event=body.get("event", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def aa_intelligence_handler(request: web.Request) -> web.Response:
    try:
        intel = _suite().intelligence
        if request.method == "GET":
            return json_response(intel.status())
        body = await _read_json(request)
        action = body.get("action", "insight")
        if action == "feedback":
            return json_response(
                intel.feedback(
                    agent_id=body.get("agent_id", ""),
                    outcome=body.get("outcome", ""),
                    score=float(body.get("score", 1) or 1),
                ),
                status=201,
            )
        return json_response(
            intel.insight(
                insight_type=body.get("insight_type", "task_optimization"),
                subject=body.get("subject", ""),
                detail=body.get("detail", ""),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def aa_governance_handler(request: web.Request) -> web.Response:
    try:
        gov = _suite().governance
        if request.method == "GET":
            return json_response(gov.status())
        body = await _read_json(request)
        action = body.get("action", "health")
        if action == "metrics":
            return json_response(
                gov.metrics(
                    agent_id=body.get("agent_id", ""),
                    latency_ms=float(body.get("latency_ms", 0) or 0),
                    success_rate=float(body.get("success_rate", 1) or 1),
                ),
                status=201,
            )
        if action == "audit":
            return json_response(
                gov.audit(
                    action=body.get("audit_action", body.get("name", "event")),
                    actor=body.get("actor", "system"),
                    detail=body.get("detail", ""),
                ),
                status=201,
            )
        if action == "security":
            return json_response(
                gov.security_event(
                    agent_id=body.get("agent_id", ""),
                    severity=body.get("severity", "info"),
                    detail=body.get("detail", ""),
                ),
                status=201,
            )
        if action == "permission":
            return json_response(
                gov.validate_permission(
                    agent_id=body.get("agent_id", ""),
                    permission=body.get("permission", ""),
                ),
                status=201,
            )
        if action == "resources":
            return json_response(
                gov.track_resources(
                    agent_id=body.get("agent_id", ""),
                    cpu=float(body.get("cpu", 0) or 0),
                    memory_mb=float(body.get("memory_mb", 0) or 0),
                ),
                status=201,
            )
        return json_response(gov.health_check(agent_id=body.get("agent_id", "")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def aa_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dashboard = _suite().dashboard
        if request.method == "GET":
            return json_response(dashboard.status())
        body = await _read_json(request)
        return json_response(
            dashboard.render(dashboard_type=body.get("dashboard_type", "agents")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def aa_meta_handler(request: web.Request) -> web.Response:
    try:
        meta = _suite().meta
        if request.method == "GET":
            return json_response(meta.status())
        body = await _read_json(request)
        return json_response(
            meta.publish(
                base=body.get("base", "agent_graph"),
                key=body.get("key", ""),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
