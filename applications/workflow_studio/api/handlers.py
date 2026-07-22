"""API handlers — Workflow Studio (Sprint 12.2)."""

from __future__ import annotations

from aiohttp import web

from applications.workflow_studio import workflow_studio
from applications.workflow_studio.api.middleware import json_response
from applications.workflow_studio.shared.exceptions import NotFoundError, ValidationError


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


async def health_handler(request: web.Request) -> web.Response:
    return json_response(workflow_studio.health())


async def workflows_handler(request: web.Request) -> web.Response:
    try:
        editor = workflow_studio.editor
        if request.method == "GET":
            return json_response({"workflows": editor.store.workflows.list_all(), "status": editor.status()})
        body = await _read_json(request)
        return json_response(
            editor.create_workflow(name=body.get("name", ""), description=body.get("description", ""), template_key=body.get("template_key", "")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def canvas_handler(request: web.Request) -> web.Response:
    try:
        editor = workflow_studio.editor
        workflow_id = request.match_info["workflow_id"]
        if request.method == "GET":
            return json_response(editor.canvas(workflow_id))
        body = await _read_json(request)
        action = body.get("action", "add_node")
        if action == "zoom":
            return json_response(editor.set_zoom(workflow_id, zoom=float(body.get("zoom", 1))))
        if action == "grid":
            return json_response(editor.set_grid(workflow_id, enabled=bool(body.get("enabled", True))))
        if action == "connect":
            return json_response(editor.connect(workflow_id, source_id=body.get("source_id", ""), target_id=body.get("target_id", ""), label=body.get("label", "")), status=201)
        if action == "group":
            return json_response(editor.group_nodes(workflow_id, node_ids=body.get("node_ids") or [], name=body.get("name", "Group")), status=201)
        if action == "comment":
            return json_response(editor.add_comment(workflow_id, text=body.get("text", ""), x=float(body.get("x", 0)), y=float(body.get("y", 0)), author=body.get("author", "")), status=201)
        if action == "copy":
            return json_response(editor.clipboard_copy(workflow_id, node_ids=body.get("node_ids") or [], user_id=body.get("user_id", "default")))
        if action == "paste":
            return json_response(editor.clipboard_paste(workflow_id, user_id=body.get("user_id", "default")))
        if action == "undo":
            return json_response(editor.undo(workflow_id))
        if action == "redo":
            return json_response(editor.redo(workflow_id))
        if action == "update_node":
            return json_response(editor.update_node(body.get("node_id", ""), properties=body.get("properties"), x=body.get("x"), y=body.get("y"), label=body.get("label")))
        return json_response(
            editor.add_node(
                workflow_id,
                node_type=body.get("node_type", "api"),
                label=body.get("label", ""),
                x=float(body.get("x", 0)),
                y=float(body.get("y", 0)),
                properties=body.get("properties"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def execute_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        action = body.get("action", "run")
        engine = workflow_studio.engine
        if action == "breakpoint":
            return json_response(engine.set_breakpoint(body.get("workflow_id", ""), node_id=body.get("node_id", ""), enabled=bool(body.get("enabled", True))), status=201)
        if action == "retry":
            exe = engine.retry(body.get("execution_id", ""))
            workflow_studio.monitoring.record_metrics(exe)
            return json_response(exe)
        if action == "rollback":
            return json_response(engine.rollback_execution(body.get("execution_id", "")))
        if action == "debugger":
            return json_response(engine.debugger_state(body.get("execution_id", "")))
        if action == "logs":
            return json_response({"logs": engine.live_logs(body.get("execution_id", ""))})
        exe = engine.execute(body.get("workflow_id", ""), mode=body.get("mode", "visual"), input_data=body.get("input"))
        workflow_studio.monitoring.record_metrics(exe)
        return json_response(exe, status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ai_builder_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        action = body.get("action", "generate")
        ai = workflow_studio.ai_builder
        if action == "optimize":
            return json_response(ai.optimize_workflow(body.get("workflow_id", "")))
        if action == "suggest":
            return json_response(ai.suggest_missing_nodes(body.get("workflow_id", "")))
        if action == "bottlenecks":
            return json_response(ai.detect_bottlenecks(body.get("workflow_id", "")))
        if action == "cost":
            return json_response(ai.estimate_execution_cost(body.get("workflow_id", "")))
        if action == "docs":
            return json_response(ai.auto_documentation(body.get("workflow_id", "")))
        return json_response(ai.generate_from_prompt(prompt=body.get("prompt", ""), name=body.get("name", "")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def templates_handler(request: web.Request) -> web.Response:
    try:
        templates = workflow_studio.templates
        if request.method == "GET":
            return json_response({"templates": templates.list_templates()})
        body = await _read_json(request)
        return json_response(templates.instantiate(key=body.get("key", ""), name=body.get("name", "")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def enterprise_handler(request: web.Request) -> web.Response:
    try:
        ent = workflow_studio.enterprise
        body = await _read_json(request)
        action = body.get("action", "version")
        if action == "history":
            return json_response({"versions": ent.version_history(body.get("workflow_id", ""))})
        if action == "compare":
            return json_response(ent.compare(body.get("version_a", ""), body.get("version_b", "")))
        if action == "merge":
            return json_response(ent.merge(body.get("workflow_id", ""), from_version_id=body.get("from_version_id", "")))
        if action == "permissions":
            return json_response(ent.set_permissions(body.get("workflow_id", ""), principal=body.get("principal", ""), role=body.get("role", "viewer")), status=201)
        if action == "share":
            return json_response(ent.share(body.get("workflow_id", ""), with_org_id=body.get("with_org_id", ""), with_user=body.get("with_user", "")), status=201)
        if action == "library":
            return json_response(ent.organization_library(body.get("org_id", "")))
        if action == "lock":
            return json_response(ent.multi_user_lock(body.get("workflow_id", ""), user_id=body.get("user_id", "")))
        return json_response(ent.save_version(body.get("workflow_id", ""), author=body.get("author", "")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def monitoring_handler(request: web.Request) -> web.Response:
    try:
        mon = workflow_studio.monitoring
        if request.method == "GET":
            workflow_id = request.rel_url.query.get("workflow_id")
            return json_response({
                "metrics": mon.execution_metrics(workflow_id),
                "dashboard": mon.performance_dashboard(),
                "failures": mon.failure_analysis(),
                "heatmap": mon.execution_heatmap(workflow_id) if workflow_id else {},
            })
        body = await _read_json(request)
        return json_response(mon.execution_heatmap(body.get("workflow_id", "")))
    except Exception as exc:
        return _handle_error(exc)
