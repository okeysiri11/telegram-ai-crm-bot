"""API handlers — Enterprise Edition (Sprint 12.5)."""

from __future__ import annotations

from aiohttp import web

from applications.enterprise import enterprise
from applications.enterprise.api.middleware import json_response
from applications.enterprise.shared.exceptions import NotFoundError, ValidationError


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
    return json_response(enterprise.health())


async def bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(enterprise.bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def platform_handler(request: web.Request) -> web.Response:
    try:
        plat = enterprise.platform
        if request.method == "GET":
            return json_response({
                "status": plat.status(),
                "organizations": plat.store.organizations.list_all(),
                "tenants": plat.store.tenants.list_all(),
                "workspaces": plat.store.workspaces.list_all(),
            })
        body = await _read_json(request)
        action = body.get("action", "organization")
        if action == "tenant":
            return json_response(plat.create_tenant(organization_id=body.get("organization_id", ""), name=body.get("name", "")), status=201)
        if action == "workspace":
            return json_response(plat.create_workspace(tenant_id=body.get("tenant_id", ""), name=body.get("name", "")), status=201)
        if action == "company":
            return json_response(plat.create_company(organization_id=body.get("organization_id", ""), name=body.get("name", "")), status=201)
        if action == "department":
            return json_response(plat.create_department(company_id=body.get("company_id", ""), name=body.get("name", "")), status=201)
        if action == "project":
            return json_response(plat.create_project(department_id=body.get("department_id", ""), name=body.get("name", "")), status=201)
        if action == "setting":
            return json_response(plat.set_global_setting(key=body.get("key", ""), value=body.get("value")), status=201)
        return json_response(plat.create_organization(name=body.get("name", ""), domain=body.get("domain", "")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def administration_handler(request: web.Request) -> web.Response:
    try:
        admin = enterprise.administration
        if request.method == "GET":
            return json_response(admin.status())
        body = await _read_json(request)
        action = body.get("action", "role")
        if action == "assign":
            return json_response(admin.assign_role(principal=body.get("principal", ""), role_id=body.get("role_id", "")), status=201)
        if action == "authenticate":
            return json_response(
                admin.authenticate(provider=body.get("provider", "sso"), principal=body.get("principal", ""), credentials=body.get("credentials")),
                status=201,
            )
        if action == "audit":
            return json_response(admin.audit(actor=body.get("actor", ""), action=body.get("audit_action", ""), resource=body.get("resource", ""), detail=body.get("detail", "")), status=201)
        if action == "security":
            return json_response(admin.security_alert(severity=body.get("severity", "info"), message=body.get("message", "")), status=201)
        if action == "policy":
            return json_response(admin.set_policy(name=body.get("name", ""), rules=body.get("rules")), status=201)
        if action == "compliance":
            return json_response(admin.compliance_check(framework=body.get("framework", ""), status=body.get("status", "compliant"), findings=body.get("findings")), status=201)
        return json_response(admin.define_role(name=body.get("name", ""), permissions=body.get("permissions")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def ai_handler(request: web.Request) -> web.Response:
    try:
        ai = enterprise.ai
        if request.method == "GET":
            role = request.rel_url.query.get("role")
            return json_response({"agents": ai.list_agents(role), "status": ai.status()})
        body = await _read_json(request)
        action = body.get("action", "register")
        if action == "invoke":
            return json_response(ai.invoke(agent_id=body.get("agent_id", ""), prompt=body.get("prompt", ""), context=body.get("context")))
        if action == "ensure_suite":
            return json_response({"agents": ai.ensure_suite()}, status=201)
        return json_response(ai.register(role=body.get("role", "chief"), name=body.get("name", ""), scope=body.get("scope", "")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def services_handler(request: web.Request) -> web.Response:
    try:
        svc = enterprise.services
        if request.method == "GET":
            q = request.rel_url.query.get("q")
            if q is not None:
                return json_response({"results": svc.search(q)})
            return json_response(svc.status())
        body = await _read_json(request)
        action = body.get("action", "route")
        if action == "schedule":
            return json_response(svc.schedule(name=body.get("name", ""), cron=body.get("cron", "@hourly"), payload=body.get("payload")), status=201)
        if action == "event":
            return json_response(svc.publish_event(topic=body.get("topic", ""), payload=body.get("payload"), source=body.get("source", "api")), status=201)
        if action == "index":
            return json_response(svc.search_index(key=body.get("key", ""), document=body.get("document") or {}), status=201)
        if action == "knowledge":
            return json_response(svc.store_knowledge(title=body.get("title", ""), body=body.get("body", ""), tags=body.get("tags")), status=201)
        if action == "backup":
            return json_response(svc.backup(label=body.get("label", "enterprise")), status=201)
        return json_response(svc.register_route(path=body.get("path", ""), target=body.get("target", ""), method=body.get("method", "GET")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def infrastructure_handler(request: web.Request) -> web.Response:
    try:
        infra = enterprise.infrastructure
        if request.method == "GET":
            return json_response({"status": infra.status(), "monitoring": infra.monitoring_snapshot()})
        body = await _read_json(request)
        action = body.get("action", "region")
        if action == "cluster":
            return json_response(infra.create_cluster(name=body.get("name", ""), region_id=body.get("region_id", ""), nodes=int(body.get("nodes", 3))), status=201)
        if action == "scale":
            return json_response(infra.scale(body.get("cluster_id", ""), nodes=int(body.get("nodes", 3))))
        if action == "balance":
            return json_response(infra.load_balance(body.get("cluster_id", "")))
        if action == "recover":
            return json_response(infra.disaster_recovery(body.get("cluster_id", "")))
        return json_response(infra.add_region(name=body.get("name", ""), code=body.get("code", "")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def analytics_handler(request: web.Request) -> web.Response:
    try:
        analytics = enterprise.analytics
        if request.method == "GET":
            return json_response({"reports": analytics.list_reports(request.rel_url.query.get("type")), "status": analytics.status()})
        body = await _read_json(request)
        return json_response(
            analytics.generate_report(report_type=body.get("report_type", "enterprise"), title=body.get("title", ""), metrics=body.get("metrics")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def knowledge_handler(request: web.Request) -> web.Response:
    try:
        knowledge = enterprise.knowledge
        if request.method == "GET":
            return json_response({"pages": knowledge.list_pages(request.rel_url.query.get("center")), "status": knowledge.status()})
        body = await _read_json(request)
        action = body.get("action", "publish")
        if action == "bootstrap":
            return json_response({"pages": knowledge.bootstrap_centers()}, status=201)
        return json_response(
            knowledge.publish_page(center=body.get("center", "wiki"), title=body.get("title", ""), body=body.get("body", "")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
