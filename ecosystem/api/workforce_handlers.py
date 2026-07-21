# Workforce API handlers — Sprint 7.4.

from __future__ import annotations

from aiohttp import web

from ecosystem import ecosystem
from ecosystem.api.middleware import error_response, json_response
from ecosystem.shared.exceptions import EcosystemError, NotFoundError, ValidationError
from ecosystem.workforce.models import DepartmentType, ExecutiveRole, PlanHorizon, TaskPriority


def _handle_error(exc: Exception) -> web.Response:
    if isinstance(exc, ValidationError):
        return error_response(str(exc), status=400)
    if isinstance(exc, NotFoundError):
        return error_response(str(exc), status=404)
    if isinstance(exc, EcosystemError):
        return error_response(str(exc), status=400)
    raise exc


async def workforce_metrics_handler(_request: web.Request) -> web.Response:
    return json_response(ecosystem.engine.workforce.metrics())


async def list_executives_handler(_request: web.Request) -> web.Response:
    executives = ecosystem.engine.workforce.executives.list_executives()
    return json_response({"executives": [e.to_dict() for e in executives]})


async def executive_decide_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        role = ExecutiveRole(data.get("role", "chief_executive_ai"))
        decision = await ecosystem.engine.workforce.executives.decide(
            role,
            data["title"],
            rationale=data.get("rationale", ""),
            approved=bool(data.get("approved", True)),
            task_id=data.get("task_id", ""),
            metadata=data.get("metadata"),
        )
        return json_response(decision.to_dict(), status=201)
    except (KeyError, ValueError, EcosystemError) as exc:
        return _handle_error(exc if isinstance(exc, EcosystemError) else ValidationError(str(exc)))


async def executive_support_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        result = ecosystem.engine.workforce.executives.decision_support(
            data["topic"],
            context=data.get("context"),
        )
        return json_response(result)
    except (KeyError, EcosystemError) as exc:
        return _handle_error(exc if isinstance(exc, EcosystemError) else ValidationError("topic required"))


async def list_departments_handler(_request: web.Request) -> web.Response:
    depts = ecosystem.engine.workforce.departments.list_departments()
    return json_response({"departments": [d.to_dict() for d in depts]})


async def department_roster_handler(request: web.Request) -> web.Response:
    try:
        dept_type = DepartmentType(request.match_info["department_type"])
        return json_response(ecosystem.engine.workforce.management.department_roster(dept_type))
    except (ValueError, EcosystemError) as exc:
        return _handle_error(exc if isinstance(exc, EcosystemError) else ValidationError(str(exc)))


async def list_specialists_handler(request: web.Request) -> web.Response:
    dept_raw = request.query.get("department_type")
    dept = DepartmentType(dept_raw) if dept_raw else None
    specialists = ecosystem.engine.workforce.specialists.list_specialists(department_type=dept)
    return json_response({"specialists": [s.to_dict() for s in specialists]})


async def org_chart_handler(_request: web.Request) -> web.Response:
    return json_response(ecosystem.engine.workforce.management.org_chart())


async def delegate_task_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        priority = TaskPriority(data.get("priority", "normal"))
        dept = DepartmentType(data["department_type"]) if data.get("department_type") else None
        task = await ecosystem.engine.workforce.coordination.delegate(
            data["title"],
            description=data.get("description", ""),
            priority=priority,
            department_type=dept,
            requires_approval=bool(data.get("requires_approval", False)),
            application_id=data.get("application_id", ""),
        )
        return json_response(task.to_dict(), status=201)
    except (KeyError, ValueError, EcosystemError) as exc:
        return _handle_error(exc if isinstance(exc, EcosystemError) else ValidationError(str(exc)))


async def execute_task_handler(request: web.Request) -> web.Response:
    try:
        task_id = request.match_info["task_id"]
        data = await request.json() if request.can_read_body else {}
        task = await ecosystem.engine.workforce.coordination.execute(task_id, result=data.get("result"))
        return json_response(task.to_dict())
    except EcosystemError as exc:
        return _handle_error(exc)


async def run_workflow_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        priority = TaskPriority(data.get("priority", "normal"))
        dept = DepartmentType(data["department_type"]) if data.get("department_type") else None
        task = await ecosystem.engine.workforce.execution.run(
            data["title"],
            description=data.get("description", ""),
            priority=priority,
            department_type=dept,
            application_id=data.get("application_id", ""),
            auto_approve=bool(data.get("auto_approve", True)),
        )
        return json_response(task.to_dict(), status=201)
    except (KeyError, ValueError, EcosystemError) as exc:
        return _handle_error(exc if isinstance(exc, EcosystemError) else ValidationError(str(exc)))


async def escalate_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        to_role = ExecutiveRole(data["to_role"]) if data.get("to_role") else None
        escalation = await ecosystem.engine.workforce.coordination.escalate(
            data["task_id"],
            data.get("reason", "Escalation requested"),
            to_role=to_role,
        )
        return json_response(escalation.to_dict(), status=201)
    except (KeyError, ValueError, EcosystemError) as exc:
        return _handle_error(exc if isinstance(exc, EcosystemError) else ValidationError(str(exc)))


async def balance_handler(_request: web.Request) -> web.Response:
    return json_response(ecosystem.engine.workforce.coordination.balance_work())


async def collaborate_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        session = await ecosystem.engine.workforce.coordination.collaborate(
            data["topic"],
            data.get("departments", []),
            shared_memory=data.get("shared_memory"),
            knowledge_refs=data.get("knowledge_refs"),
        )
        return json_response(session.to_dict(), status=201)
    except (KeyError, EcosystemError) as exc:
        return _handle_error(exc if isinstance(exc, EcosystemError) else ValidationError(str(exc)))


async def list_tasks_handler(request: web.Request) -> web.Response:
    from ecosystem.workforce.models import TaskStatus

    status_raw = request.query.get("status")
    dept_raw = request.query.get("department_type")
    status = TaskStatus(status_raw) if status_raw else None
    dept = DepartmentType(dept_raw) if dept_raw else None
    tasks = ecosystem.engine.workforce.coordination.list_tasks(status=status, department_type=dept)
    return json_response({"tasks": [t.to_dict() for t in tasks]})


async def create_objective_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        horizon = PlanHorizon(data.get("horizon", "company"))
        dept = DepartmentType(data["department_type"]) if data.get("department_type") else None
        objective = ecosystem.engine.workforce.planning.set_objective(
            data["title"],
            horizon=horizon,
            department_type=dept,
            target_metric=data.get("target_metric", ""),
            target_value=float(data.get("target_value", 100)),
            owner_role=data.get("owner_role", ""),
        )
        return json_response(objective.to_dict(), status=201)
    except (KeyError, ValueError, EcosystemError) as exc:
        return _handle_error(exc if isinstance(exc, EcosystemError) else ValidationError(str(exc)))


async def update_objective_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        objective = await ecosystem.engine.workforce.planning.update_progress(
            request.match_info["objective_id"],
            float(data["current_value"]),
        )
        return json_response(objective.to_dict())
    except (KeyError, ValueError, EcosystemError) as exc:
        return _handle_error(exc if isinstance(exc, EcosystemError) else ValidationError(str(exc)))


async def create_plan_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        horizon = PlanHorizon(data.get("horizon", "weekly"))
        dept = DepartmentType(data["department_type"]) if data.get("department_type") else None
        plan = await ecosystem.engine.workforce.planning.create_plan(
            data["title"],
            horizon,
            data.get("items", []),
            department_type=dept,
        )
        return json_response(plan.to_dict(), status=201)
    except (KeyError, ValueError, EcosystemError) as exc:
        return _handle_error(exc if isinstance(exc, EcosystemError) else ValidationError(str(exc)))


async def performance_handler(_request: web.Request) -> web.Response:
    return json_response(ecosystem.engine.workforce.planning.performance_report())


async def governance_audit_handler(_request: web.Request) -> web.Response:
    return json_response({
        "audit": ecosystem.engine.workforce.governance.audit_trail(),
        "compliance": ecosystem.engine.workforce.governance.compliance_check(),
        "escalation_policy": ecosystem.engine.workforce.governance.escalation_policy(),
    })
