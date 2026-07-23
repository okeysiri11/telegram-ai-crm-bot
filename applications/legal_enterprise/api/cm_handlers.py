"""API handlers — Case Management Platform (Sprint 17.3)."""

from __future__ import annotations

from aiohttp import web

from applications.legal_enterprise import legal_enterprise
from applications.legal_enterprise.api.middleware import json_response
from applications.legal_enterprise.shared.exceptions import NotFoundError, ValidationError


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
    return legal_enterprise.case_management_platform


async def cm_health_handler(request: web.Request) -> web.Response:
    health = legal_enterprise.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "case_management_ready": health.get("case_management_ready"),
            "court_calendar_ready": health.get("court_calendar_ready"),
            "procedural_timeline_ready": health.get("procedural_timeline_ready"),
            "ai_legal_workflow_ready": health.get("ai_legal_workflow_ready"),
            "suite": _suite().status(),
        }
    )


async def cm_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def cm_cases_handler(request: web.Request) -> web.Response:
    try:
        cases = _suite().cases
        if request.method == "GET":
            return json_response(cases.status())
        body = await _read_json(request)
        action = body.get("action", "register")
        if action == "status":
            return json_response(
                cases.set_status(
                    case_id=body.get("case_id", ""),
                    status=body.get("status", "active"),
                    note=body.get("note", ""),
                ),
                status=201,
            )
        if action == "priority":
            return json_response(
                cases.set_priority(case_id=body.get("case_id", ""), priority=body.get("priority", "medium")),
                status=201,
            )
        if action == "owner":
            return json_response(
                cases.assign_owner(case_id=body.get("case_id", ""), owner=body.get("owner", "")),
                status=201,
            )
        if action == "timeline":
            return json_response(
                cases.add_timeline(
                    case_id=body.get("case_id", ""),
                    event=body.get("event", ""),
                    detail=body.get("detail", ""),
                ),
                status=201,
            )
        if action == "relate":
            return json_response(
                cases.relate_cases(
                    case_id=body.get("case_id", ""),
                    related_case_id=body.get("related_case_id", ""),
                    relation=body.get("relation", "related"),
                ),
                status=201,
            )
        return json_response(
            cases.register(
                title=body.get("title", ""),
                case_number=body.get("case_number", ""),
                category=body.get("category", "civil"),
                priority=body.get("priority", "medium"),
                status=body.get("status", "intake"),
                owner=body.get("owner", ""),
                court_name=body.get("court_name", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def cm_calendar_handler(request: web.Request) -> web.Response:
    try:
        calendar = _suite().calendar
        if request.method == "GET":
            return json_response(calendar.status())
        body = await _read_json(request)
        action = body.get("action", "hearing")
        if action == "courtroom":
            return json_response(
                calendar.register_courtroom(
                    name=body.get("name", ""),
                    building=body.get("building", ""),
                    capacity=int(body.get("capacity", 0) or 0),
                ),
                status=201,
            )
        if action == "assign_judge":
            return json_response(
                calendar.assign_judge(
                    hearing_id=body.get("hearing_id", ""),
                    judge_name=body.get("judge_name", ""),
                ),
                status=201,
            )
        if action == "sync":
            return json_response(
                calendar.sync_calendar(
                    source=body.get("source", "court_system"),
                    events=int(body.get("events", 0) or 0),
                ),
                status=201,
            )
        if action == "reminder":
            return json_response(
                calendar.create_reminder(
                    hearing_id=body.get("hearing_id", ""),
                    remind_at=body.get("remind_at", ""),
                    channel=body.get("channel", "email"),
                ),
                status=201,
            )
        if action == "recurring":
            return json_response(
                calendar.recurring_event(
                    case_id=body.get("case_id", ""),
                    title=body.get("title", ""),
                    cadence=body.get("cadence", "weekly"),
                    next_at=body.get("next_at", ""),
                ),
                status=201,
            )
        return json_response(
            calendar.schedule_hearing(
                case_id=body.get("case_id", ""),
                title=body.get("title", ""),
                scheduled_at=body.get("scheduled_at", ""),
                judge_name=body.get("judge_name", ""),
                courtroom_id=body.get("courtroom_id", ""),
                hearing_type=body.get("hearing_type", "hearing"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def cm_deadlines_handler(request: web.Request) -> web.Response:
    try:
        deadlines = _suite().deadlines
        if request.method == "GET":
            return json_response(deadlines.status())
        body = await _read_json(request)
        action = body.get("action", "register")
        if action == "calculate":
            return json_response(
                deadlines.calculate_deadline(
                    case_id=body.get("case_id", ""),
                    deadline_type=body.get("deadline_type", "procedural"),
                    from_date=body.get("from_date", ""),
                    days=int(body.get("days", 30) or 30),
                ),
                status=201,
            )
        if action == "alert":
            return json_response(
                deadlines.risk_alert(
                    deadline_id=body.get("deadline_id", ""),
                    severity=body.get("severity", "high"),
                    message=body.get("message", ""),
                ),
                status=201,
            )
        return json_response(
            deadlines.register_deadline(
                case_id=body.get("case_id", ""),
                deadline_type=body.get("deadline_type", "procedural"),
                due_on=body.get("due_on", ""),
                title=body.get("title", ""),
                risk=body.get("risk", "normal"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def cm_tasks_handler(request: web.Request) -> web.Response:
    try:
        tasks = _suite().tasks
        if request.method == "GET":
            return json_response(tasks.status())
        body = await _read_json(request)
        action = body.get("action", "create")
        if action == "assign":
            return json_response(
                tasks.assign(task_id=body.get("task_id", ""), assignee=body.get("assignee", "")),
                status=201,
            )
        if action == "priority":
            return json_response(
                tasks.set_priority(task_id=body.get("task_id", ""), priority=body.get("priority", "medium")),
                status=201,
            )
        if action == "workflow":
            steps = body.get("steps") if isinstance(body.get("steps"), list) else None
            return json_response(
                tasks.automate_workflow(
                    case_id=body.get("case_id", ""),
                    workflow=body.get("workflow", ""),
                    steps=steps,
                ),
                status=201,
            )
        if action == "approval":
            return json_response(
                tasks.request_approval(
                    case_id=body.get("case_id", ""),
                    item=body.get("item", ""),
                    requester=body.get("requester", ""),
                    approver=body.get("approver", ""),
                ),
                status=201,
            )
        return json_response(
            tasks.create_task(
                case_id=body.get("case_id", ""),
                title=body.get("title", ""),
                assignee=body.get("assignee", ""),
                priority=body.get("priority", "medium"),
                due_on=body.get("due_on", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def cm_documents_handler(request: web.Request) -> web.Response:
    try:
        documents = _suite().documents
        if request.method == "GET":
            return json_response(documents.status())
        body = await _read_json(request)
        action = body.get("action", "register")
        if action == "evidence":
            return json_response(
                documents.register_evidence(
                    case_id=body.get("case_id", ""),
                    title=body.get("title", ""),
                    uri=body.get("uri", ""),
                ),
                status=201,
            )
        if action == "filing":
            return json_response(
                documents.register_filing(
                    case_id=body.get("case_id", ""),
                    title=body.get("title", ""),
                    uri=body.get("uri", ""),
                ),
                status=201,
            )
        if action == "version":
            return json_response(
                documents.record_version(
                    document_id=body.get("document_id", ""),
                    version=body.get("version", ""),
                    summary=body.get("summary", ""),
                ),
                status=201,
            )
        if action == "secure":
            return json_response(
                documents.secure_store(
                    document_id=body.get("document_id", ""),
                    vault_ref=body.get("vault_ref", ""),
                ),
                status=201,
            )
        if action == "sign":
            return json_response(
                documents.digital_signature(
                    document_id=body.get("document_id", ""),
                    signer=body.get("signer", ""),
                    signature_ref=body.get("signature_ref", ""),
                ),
                status=201,
            )
        return json_response(
            documents.register_document(
                case_id=body.get("case_id", ""),
                title=body.get("title", ""),
                document_type=body.get("document_type", "legal"),
                uri=body.get("uri", ""),
                version=body.get("version", "1.0"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def cm_ai_handler(request: web.Request) -> web.Response:
    try:
        ai = _suite().ai
        if request.method == "GET":
            return json_response(ai.status())
        body = await _read_json(request)
        action = body.get("action", "health_score")
        case_id = body.get("case_id", "")
        mapping = {
            "deadline_risk": ai.deadline_risk,
            "missing_documents": ai.missing_documents,
            "progress": ai.progress_analysis,
            "optimize": ai.optimize_workflow,
            "next_actions": ai.recommend_next_actions,
            "health_score": ai.health_score,
            "summary": ai.natural_language_summary,
        }
        if action not in mapping:
            return json_response({"error": f"unknown action: {action}"}, status=400)
        return json_response(mapping[action](case_id=case_id), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def cm_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dtype = request.rel_url.query.get("type", "case")
        if request.method == "POST":
            body = await _read_json(request)
            dtype = body.get("dashboard_type", dtype)
        return json_response(_suite().dashboard.render(dashboard_type=dtype))
    except Exception as exc:
        return _handle_error(exc)


async def cm_knowledge_handler(request: web.Request) -> web.Response:
    try:
        knowledge = _suite().knowledge
        if request.method == "GET":
            return json_response(knowledge.status())
        body = await _read_json(request)
        return json_response(
            knowledge.publish(
                base=body.get("base", ""),
                key=body.get("key", ""),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else {},
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
