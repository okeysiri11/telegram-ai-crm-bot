"""API handlers — Enterprise Multi-Tenant Platform (Sprint 20.0)."""

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
    return enterprise_hub.tenancy


async def tenancy_health_handler(request: web.Request) -> web.Response:
    health = enterprise_hub.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "multi_tenant_ready": health.get("multi_tenant_ready"),
            "workspace_ready": health.get("workspace_ready"),
            "isolation_ready": health.get("isolation_ready"),
            "licensing_ready": health.get("licensing_ready"),
            "billing_ready": health.get("billing_ready"),
            "suite": _suite().status(),
        }
    )


async def tenancy_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def tenancy_tenants_handler(request: web.Request) -> web.Response:
    try:
        mgr = _suite().tenants
        if request.method == "GET":
            return json_response(mgr.status())
        body = await _read_json(request)
        return json_response(
            mgr.create_tenant(
                name=body.get("name", ""),
                slug=body.get("slug"),
                license_tier=body.get("license_tier", "business"),
                environment=body.get("environment", "production"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def tenancy_organizations_handler(request: web.Request) -> web.Response:
    try:
        orgs = _suite().organizations
        if request.method == "GET":
            tenant_id = request.rel_url.query.get("tenant_id")
            if tenant_id:
                return json_response(orgs.hierarchy(tenant_id=tenant_id))
            return json_response(orgs.status())
        body = await _read_json(request)
        return json_response(
            orgs.create_node(
                tenant_id=body.get("tenant_id", ""),
                name=body.get("name", ""),
                level=body.get("level", "company"),
                parent_id=body.get("parent_id"),
                code=body.get("code"),
                meta=body.get("meta") if isinstance(body.get("meta"), dict) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def tenancy_workspaces_handler(request: web.Request) -> web.Response:
    try:
        ws = _suite().workspaces
        if request.method == "GET":
            tenant_id = request.rel_url.query.get("tenant_id")
            if tenant_id:
                return json_response({"workspaces": ws.list_for_tenant(tenant_id)})
            return json_response(ws.status())
        body = await _read_json(request)
        return json_response(
            ws.create(
                tenant_id=body.get("tenant_id", ""),
                name=body.get("name", ""),
                kind=body.get("kind", "crm"),
                settings=body.get("settings") if isinstance(body.get("settings"), dict) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def tenancy_isolation_handler(request: web.Request) -> web.Response:
    try:
        iso = _suite().isolation
        if request.method == "GET":
            return json_response(iso.status())
        body = await _read_json(request)
        return json_response(
            iso.enforce(
                tenant_id=body.get("tenant_id", ""),
                scope=body.get("scope", "data"),
                resource_key=body.get("resource_key", "default"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def tenancy_routing_handler(request: web.Request) -> web.Response:
    try:
        router = _suite().routing
        if request.method == "GET":
            return json_response(router.status())
        body = await _read_json(request)
        return json_response(
            router.route(
                tenant_id=body.get("tenant_id", ""),
                target=body.get("target", "crm"),
                path=body.get("path", "/"),
                workspace_id=body.get("workspace_id"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def tenancy_provisioning_handler(request: web.Request) -> web.Response:
    try:
        prov = _suite().provisioning
        if request.method == "GET":
            return json_response(prov.status())
        body = await _read_json(request)
        return json_response(
            prov.provision(
                tenant_id=body.get("tenant_id", ""),
                include_ai=bool(body.get("include_ai", True)),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def tenancy_branding_handler(request: web.Request) -> web.Response:
    try:
        branding = _suite().branding
        if request.method == "GET":
            return json_response(branding.status())
        body = await _read_json(request)
        return json_response(
            branding.apply(
                tenant_id=body.get("tenant_id", ""),
                logo=body.get("logo"),
                colors=body.get("colors") if isinstance(body.get("colors"), dict) else None,
                domain=body.get("domain"),
                theme=body.get("theme", "light"),
                language=body.get("language", "en"),
                timezone=body.get("timezone", "UTC"),
                currency=body.get("currency", "USD"),
                locale=body.get("locale", "en-US"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def tenancy_licensing_handler(request: web.Request) -> web.Response:
    try:
        lic = _suite().licensing
        if request.method == "GET":
            return json_response(lic.status())
        body = await _read_json(request)
        return json_response(
            lic.assign(
                tenant_id=body.get("tenant_id", ""),
                tier=body.get("tier", "business"),
                seats=body.get("seats"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def tenancy_billing_handler(request: web.Request) -> web.Response:
    try:
        billing = _suite().billing
        if request.method == "GET":
            tenant_id = request.rel_url.query.get("tenant_id")
            if tenant_id:
                return json_response(billing.history(tenant_id=tenant_id))
            return json_response(billing.status())
        body = await _read_json(request)
        action = (body.get("action") or "subscribe").lower()
        if action == "invoice":
            return json_response(
                billing.invoice(
                    tenant_id=body.get("tenant_id", ""),
                    subscription_id=body.get("subscription_id", ""),
                    amount=float(body.get("amount", 0) or 0),
                    currency=body.get("currency", "USD"),
                ),
                status=201,
            )
        if action == "pay":
            return json_response(
                billing.pay(invoice_id=body.get("invoice_id", ""), method=body.get("method", "card")),
                status=201,
            )
        if action == "limits":
            return json_response(
                billing.set_limits(
                    tenant_id=body.get("tenant_id", ""),
                    limits=body.get("limits") if isinstance(body.get("limits"), dict) else {},
                ),
                status=201,
            )
        return json_response(
            billing.subscribe(
                tenant_id=body.get("tenant_id", ""),
                plan=body.get("plan", "business"),
                amount=float(body.get("amount", 0) or 0),
                currency=body.get("currency", "USD"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def tenancy_onboarding_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            return json_response({"onboarding": _suite().store.tn_onboarding.count()})
        body = await _read_json(request)
        return json_response(
            _suite().setup.run(
                name=body.get("name", "New Tenant"),
                license_tier=body.get("license_tier", "business"),
                language=body.get("language", "en"),
                currency=body.get("currency", "USD"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def tenancy_migration_handler(request: web.Request) -> web.Response:
    try:
        mig = _suite().migration
        if request.method == "GET":
            return json_response({"migrations": _suite().store.tn_migrations.count()})
        body = await _read_json(request)
        action = (body.get("action") or "export").lower()
        if action == "import_workspace":
            return json_response(
                mig.import_workspace(
                    tenant_id=body.get("tenant_id", ""),
                    payload=body.get("payload") if isinstance(body.get("payload"), dict) else {},
                ),
                status=201,
            )
        if action == "merge":
            return json_response(
                mig.merge_organizations(
                    tenant_id=body.get("tenant_id", ""),
                    source_org_id=body.get("source_org_id", ""),
                    target_org_id=body.get("target_org_id", ""),
                ),
                status=201,
            )
        if action == "move":
            return json_response(
                mig.move_organization(
                    tenant_id=body.get("tenant_id", ""),
                    org_id=body.get("org_id", ""),
                    new_parent_id=body.get("new_parent_id"),
                ),
                status=201,
            )
        return json_response(
            mig.export_workspace(workspace_id=body.get("workspace_id", "")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def tenancy_analytics_handler(request: web.Request) -> web.Response:
    try:
        mgr = _suite().tenants
        if request.method == "GET":
            tenant_id = request.rel_url.query.get("tenant_id")
            if not tenant_id:
                return json_response(mgr.status())
            return json_response(mgr.analytics(tenant_id=tenant_id))
        body = await _read_json(request)
        return json_response(
            mgr.record_usage(
                tenant_id=body.get("tenant_id", ""),
                active_users=int(body.get("active_users", 0) or 0),
                ai_cost=float(body.get("ai_cost", 0) or 0),
                module=body.get("module", "crm"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
