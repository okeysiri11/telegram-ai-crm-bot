"""API handlers — AI Marketplace (Sprint 12.1)."""

from __future__ import annotations

from aiohttp import web

from applications.marketplace import marketplace
from applications.marketplace.api.middleware import json_response
from applications.marketplace.shared.exceptions import CompatibilityError, NotFoundError, ValidationError


async def _read_json(request: web.Request) -> dict:
    try:
        data = await request.json()
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _handle_error(exc: Exception) -> web.Response:
    if isinstance(exc, NotFoundError):
        return json_response({"error": str(exc)}, status=404)
    if isinstance(exc, (ValidationError, CompatibilityError)):
        return json_response({"error": str(exc)}, status=400)
    return json_response({"error": str(exc)}, status=500)


async def health_handler(request: web.Request) -> web.Response:
    return json_response(marketplace.health())


async def packages_handler(request: web.Request) -> web.Response:
    try:
        core = marketplace.core
        if request.method == "GET":
            kind = request.rel_url.query.get("kind")
            category = request.rel_url.query.get("category")
            return json_response({"packages": core.list_packages(kind=kind, category=category), "registries": {
                "package": core.package_registry(),
                "plugin": core.plugin_registry(),
                "connector": core.connector_registry(),
                "workflow": core.workflow_registry(),
                "application": core.application_registry(),
                "agent": core.agent_registry(),
            }})
        body = await _read_json(request)
        action = body.get("action", "publish")
        if action == "install":
            return json_response(core.install(body.get("package_id", ""), org_id=body.get("org_id", ""), user_id=body.get("user_id", "")), status=201)
        if action == "update":
            return json_response(core.update(body.get("installation_id", ""), to_version=body.get("to_version", "")))
        if action == "rollback":
            return json_response(core.rollback(body.get("installation_id", "")))
        if action == "compatibility":
            return json_response(core.check_compatibility(body.get("package_id", ""), platform_version=body.get("platform_version", "3.0.0")))
        if action == "dependencies":
            return json_response(core.resolve_dependencies(body.get("package_id", "")))
        if action == "license":
            return json_response(core.issue_license(body.get("package_id", ""), org_id=body.get("org_id", ""), seats=int(body.get("seats", 1)), plan=body.get("plan", "enterprise")), status=201)
        if action == "rate":
            return json_response(core.rate(body.get("package_id", ""), score=float(body.get("score", 5)), reviewer=body.get("reviewer", ""), comment=body.get("comment", "")), status=201)
        return json_response(
            core.publish_package(
                name=body.get("name", ""),
                kind=body.get("kind", "plugin"),
                category=body.get("category", "custom_enterprise"),
                version=body.get("version", "1.0.0"),
                publisher=body.get("publisher", ""),
                dependencies=body.get("dependencies"),
                metadata=body.get("metadata"),
                private=bool(body.get("private", False)),
                org_id=body.get("org_id", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def agents_handler(request: web.Request) -> web.Response:
    try:
        ai = marketplace.ai
        if request.method == "GET":
            return json_response({"agents": ai.list_agents(), "status": ai.status()})
        body = await _read_json(request)
        action = body.get("action", "publish")
        if action == "install":
            return json_response(ai.install_agent(body.get("package_id", ""), org_id=body.get("org_id", ""), user_id=body.get("user_id", "")), status=201)
        if action == "update":
            return json_response(ai.update_agent(body.get("installation_id", ""), to_version=body.get("to_version", "")))
        if action == "share":
            return json_response(ai.share_agent(body.get("package_id", ""), with_org_id=body.get("with_org_id", "")))
        if action == "permissions":
            return json_response(ai.agent_permissions(body.get("package_id", ""), permissions=body.get("permissions")))
        if action == "rate":
            return json_response(ai.rate_agent(body.get("package_id", ""), score=float(body.get("score", 5)), reviewer=body.get("reviewer", ""), comment=body.get("comment", "")), status=201)
        return json_response(
            ai.publish_agent(
                name=body.get("name", ""),
                category=body.get("category", "custom_enterprise"),
                version=body.get("version", "1.0.0"),
                publisher=body.get("publisher", ""),
                permissions=body.get("permissions"),
                metadata=body.get("metadata"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def workflows_handler(request: web.Request) -> web.Response:
    try:
        wf = marketplace.workflows
        if request.method == "GET":
            return json_response({
                "templates": wf.list_templates(),
                "automation_packs": wf.list_automation_packs(),
                "business_packs": wf.list_business_packs(),
                "status": wf.status(),
            })
        body = await _read_json(request)
        action = body.get("action", "publish")
        if action == "export":
            return json_response(wf.export_workflow(body.get("package_id", "")))
        if action == "import":
            return json_response(wf.import_workflow(payload=body.get("payload") or {}, publisher=body.get("publisher", "")), status=201)
        return json_response(
            wf.publish_workflow(
                name=body.get("name", ""),
                steps=body.get("steps"),
                category=body.get("category", "custom_enterprise"),
                pack_type=body.get("pack_type", "template"),
                version=body.get("version", "1.0.0"),
                publisher=body.get("publisher", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def connectors_handler(request: web.Request) -> web.Response:
    try:
        conn = marketplace.connectors
        if request.method == "GET":
            return json_response({"catalog": conn.catalog(), "connectors": conn.list_connectors()})
        body = await _read_json(request)
        return json_response(conn.install_connector(body.get("package_id", ""), org_id=body.get("org_id", "")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def security_handler(request: web.Request) -> web.Response:
    try:
        body = await _read_json(request)
        action = body.get("action", "full")
        pid = body.get("package_id", "")
        sec = marketplace.security
        if action == "verify":
            return json_response(sec.verify_plugin(pid))
        if action == "sign":
            return json_response(sec.digital_signature(pid, signer=body.get("signer", "marketplace")))
        if action == "permissions":
            return json_response(sec.permission_scanner(pid))
        if action == "sandbox":
            return json_response(sec.sandbox_validation(pid))
        if action == "dependencies":
            return json_response(sec.dependency_validation(pid))
        return json_response(sec.full_scan(pid))
    except Exception as exc:
        return _handle_error(exc)


async def portal_handler(request: web.Request) -> web.Response:
    try:
        portal = marketplace.portal
        if request.method == "GET":
            package_id = request.rel_url.query.get("package_id", "")
            if package_id:
                return json_response({"analytics": portal.analytics(package_id), "documentation": portal.documentation(package_id)})
            return json_response(portal.status())
        body = await _read_json(request)
        action = body.get("action", "publish")
        if action == "validate":
            return json_response(portal.validate_package(body.get("package_id", "")))
        if action == "analytics":
            return json_response(portal.analytics(body.get("package_id", "")))
        return json_response(
            portal.publish(
                name=body.get("name", ""),
                kind=body.get("kind", "plugin"),
                category=body.get("category", "custom_enterprise"),
                version=body.get("version", "1.0.0"),
                publisher=body.get("publisher", ""),
                documentation=body.get("documentation", ""),
                api_reference=body.get("api_reference", ""),
                dependencies=body.get("dependencies"),
                metadata=body.get("metadata"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def enterprise_handler(request: web.Request) -> web.Response:
    try:
        ent = marketplace.enterprise
        if request.method == "GET":
            org_id = request.rel_url.query.get("org_id", "")
            return json_response({
                "status": ent.status(),
                "repository": ent.company_repository(org_id) if org_id else {},
                "private_catalog": ent.private_marketplace_catalog(org_id) if org_id else {},
            })
        body = await _read_json(request)
        action = body.get("action", "create_market")
        if action == "internal":
            return json_response(
                ent.publish_internal(
                    org_id=body.get("org_id", ""),
                    name=body.get("name", ""),
                    kind=body.get("kind", "plugin"),
                    category=body.get("category", "custom_enterprise"),
                    version=body.get("version", "1.0.0"),
                ),
                status=201,
            )
        if action == "role":
            return json_response(ent.grant_role(body.get("market_id", ""), principal=body.get("principal", ""), role=body.get("role", "viewer")))
        if action == "repository":
            return json_response(ent.company_repository(body.get("org_id", "")))
        return json_response(ent.create_org_marketplace(org_id=body.get("org_id", ""), name=body.get("name", "")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def installations_handler(request: web.Request) -> web.Response:
    return json_response({"installations": marketplace.core.list_installations()})
