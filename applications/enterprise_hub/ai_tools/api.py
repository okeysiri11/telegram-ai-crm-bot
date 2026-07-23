"""API handlers — Enterprise AI Tools & Skills (Sprint 20.2)."""

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
    return enterprise_hub.ai_tools


async def ats_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "ai_tools_ready": health.get("ai_tools_ready"),
            "skill_engine_ready": health.get("skill_engine_ready"),
            "tool_sandbox_ready": health.get("tool_sandbox_ready"),
            "tool_marketplace_ready": health.get("tool_marketplace_ready"),
            "suite": _suite().status(),
        }
    )


async def ats_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ats_tools_handler(request: web.Request) -> web.Response:
    try:
        tools = _suite().tools
        if request.method == "GET":
            return json_response({"catalog": tools.catalog(), **tools.status()})
        body = await _read_json(request)
        return json_response(
            tools.register(
                name=body.get("name", ""),
                domain=body.get("domain", "custom"),
                description=body.get("description", ""),
                owner=body.get("owner", "platform"),
                version=body.get("version", "1.0"),
                permissions=body.get("permissions") if isinstance(body.get("permissions"), list) else None,
                cost_per_call=float(body.get("cost_per_call", 0.01) or 0.01),
                limits=body.get("limits") if isinstance(body.get("limits"), dict) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ats_execute_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        return json_response(
            _suite().executor.execute(
                tool_id=body.get("tool_id", ""),
                params=body.get("params") if isinstance(body.get("params"), dict) else None,
                agent_id=body.get("agent_id", "system"),
                user_id=body.get("user_id", "system"),
                role=body.get("role", "agent"),
                confirmed=bool(body.get("confirmed", True)),
                needs_network=bool(body.get("needs_network", False)),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ats_skills_handler(request: web.Request) -> web.Response:
    try:
        skills = _suite().skills
        if request.method == "GET":
            return json_response(skills.status())
        body = await _read_json(request)
        action = (body.get("action") or "register").lower()
        if action == "run":
            return json_response(
                skills.run(
                    skill_id=body.get("skill_id", ""),
                    agent_id=body.get("agent_id", "system"),
                    user_id=body.get("user_id", "system"),
                    role=body.get("role", "agent"),
                    params=body.get("params") if isinstance(body.get("params"), dict) else None,
                ),
                status=201,
            )
        return json_response(
            skills.register(
                name=body.get("name", ""),
                description=body.get("description", ""),
                steps=body.get("steps") if isinstance(body.get("steps"), list) else None,
                category=body.get("category", "general"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ats_policy_handler(request: web.Request) -> web.Response:
    try:
        pol = _suite().policy
        if request.method == "GET":
            return json_response(pol.status())
        body = await _read_json(request)
        action = (body.get("action") or "define").lower()
        if action == "authorize":
            return json_response(
                pol.authorize(
                    agent_id=body.get("agent_id", "system"),
                    role=body.get("role", "agent"),
                    domain=body.get("domain", "custom"),
                    cost=float(body.get("cost", 0) or 0),
                    confirmed=bool(body.get("confirmed", False)),
                ),
                status=201,
            )
        return json_response(
            pol.define(
                name=body.get("name", ""),
                allowed_agents=body.get("allowed_agents"),
                allowed_roles=body.get("allowed_roles"),
                allowed_domains=body.get("allowed_domains"),
                max_cost=float(body.get("max_cost", 10) or 10),
                require_confirmation=bool(body.get("require_confirmation", False)),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ats_marketplace_handler(request: web.Request) -> web.Response:
    try:
        suite = _suite()
        if request.method == "GET":
            return json_response({"packages": suite.store.ats_packages.count()})
        body = await _read_json(request)
        action = (body.get("action") or "publish").lower()
        if action == "sign":
            return json_response(suite.signatures.sign(package_id=body.get("package_id", "")), status=201)
        if action == "install":
            return json_response(
                suite.marketplace.install(
                    package_id=body.get("package_id", ""),
                    signature_id=body.get("signature_id"),
                ),
                status=201,
            )
        if action == "disable":
            return json_response(suite.marketplace.disable(package_id=body.get("package_id", "")), status=201)
        return json_response(
            suite.packages.publish(
                name=body.get("name", ""),
                kind=body.get("kind", "tool"),
                version=body.get("version", "1.0.0"),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ats_audit_handler(request: web.Request) -> web.Response:
    try:
        audit = _suite().audit
        if request.method == "GET":
            return json_response(audit.status())
        body = await _read_json(request)
        return json_response(
            audit.log(
                event=body.get("event", "note"),
                tool_id=body.get("tool_id"),
                skill_id=body.get("skill_id"),
                agent_id=body.get("agent_id", "system"),
                permissions=body.get("permissions") if isinstance(body.get("permissions"), list) else None,
                detail=body.get("detail") if isinstance(body.get("detail"), dict) else None,
                error=body.get("error"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ats_analytics_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().analytics())
    except Exception as exc:
        return _handle_error(exc)


async def ats_sandbox_handler(request: web.Request) -> web.Response:
    try:
        sbx = _suite().sandbox
        if request.method == "GET":
            return json_response({"sandboxes": _suite().store.ats_sandboxes.count()})
        body = await _read_json(request)
        return json_response(
            sbx.create(
                tool_id=body.get("tool_id", ""),
                allow_network=bool(body.get("allow_network", False)),
                allow_files=bool(body.get("allow_files", True)),
                cpu_limit=float(body.get("cpu_limit", 1) or 1),
                memory_mb=int(body.get("memory_mb", 256) or 256),
                timeout_ms=int(body.get("timeout_ms", 5000) or 5000),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
