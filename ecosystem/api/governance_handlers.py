# Platform governance API handlers — Sprint 7.6.

from __future__ import annotations

from aiohttp import web

from ecosystem import ecosystem
from ecosystem.api.middleware import error_response, json_response
from ecosystem.governance.models import (
    GovernanceDomain,
    LifecycleKind,
    LifecycleState,
    RiskCategory,
    RiskSeverity,
)
from ecosystem.shared.exceptions import EcosystemError, NotFoundError, ValidationError


def _handle_error(exc: Exception) -> web.Response:
    if isinstance(exc, ValidationError):
        return error_response(str(exc), status=400)
    if isinstance(exc, NotFoundError):
        return error_response(str(exc), status=404)
    if isinstance(exc, EcosystemError):
        return error_response(str(exc), status=400)
    raise exc


async def governance_metrics_handler(_request: web.Request) -> web.Response:
    return json_response(ecosystem.engine.governance.metrics())


async def governance_cycle_handler(_request: web.Request) -> web.Response:
    result = await ecosystem.engine.governance.run_governance_cycle()
    return json_response(result, status=201)


async def list_policies_handler(request: web.Request) -> web.Response:
    domain_raw = request.query.get("domain")
    domain = GovernanceDomain(domain_raw) if domain_raw else None
    policies = ecosystem.engine.governance.policies.list_policies(domain=domain)
    return json_response({"policies": [p.to_dict() for p in policies]})


async def create_policy_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        domain = GovernanceDomain(data.get("domain", "platform"))
        policy = await ecosystem.engine.governance.policies.create(
            data["name"],
            domain,
            description=data.get("description", ""),
            rules=data.get("rules"),
            retention_days=int(data.get("retention_days", 365)),
        )
        return json_response(policy.to_dict(), status=201)
    except (KeyError, ValueError, EcosystemError) as exc:
        return _handle_error(exc if isinstance(exc, EcosystemError) else ValidationError(str(exc)))


async def update_policy_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        policy = await ecosystem.engine.governance.policies.update(request.match_info["policy_id"], **data)
        return json_response(policy.to_dict())
    except EcosystemError as exc:
        return _handle_error(exc)


async def compliance_evaluate_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        check = await ecosystem.engine.governance.compliance.evaluate(
            data["policy_id"],
            data.get("subject_type", "application"),
            data["subject_id"],
            context=data.get("context"),
        )
        return json_response(check.to_dict(), status=201)
    except (KeyError, EcosystemError) as exc:
        return _handle_error(exc if isinstance(exc, EcosystemError) else ValidationError(str(exc)))


async def compliance_audit_handler(_request: web.Request) -> web.Response:
    result = await ecosystem.engine.governance.compliance.continuous_audit()
    return json_response(result)


async def compliance_list_handler(_request: web.Request) -> web.Response:
    checks = ecosystem.engine.governance.compliance.list_checks()
    return json_response({"checks": [c.to_dict() for c in checks]})


async def access_review_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        review = ecosystem.engine.governance.compliance.access_review(
            data["subject_id"],
            reviewer=data.get("reviewer", "compliance"),
        )
        return json_response(review.to_dict(), status=201)
    except (KeyError, EcosystemError) as exc:
        return _handle_error(exc if isinstance(exc, EcosystemError) else ValidationError(str(exc)))


async def audit_trail_handler(request: web.Request) -> web.Response:
    resource_type = request.query.get("resource_type", "")
    trail = ecosystem.engine.governance.audit.trail(resource_type=resource_type)
    return json_response({"entries": [e.to_dict() for e in trail]})


async def lifecycle_register_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        kind = LifecycleKind(data.get("kind", "application"))
        record = await ecosystem.engine.governance.lifecycle.register(
            kind,
            data["name"],
            entity_id=data.get("entity_id", ""),
            version=data.get("version", "1.0.0"),
            metadata=data.get("metadata"),
        )
        return json_response(record.to_dict(), status=201)
    except (KeyError, ValueError, EcosystemError) as exc:
        return _handle_error(exc if isinstance(exc, EcosystemError) else ValidationError(str(exc)))


async def lifecycle_transition_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        state = LifecycleState(data["state"])
        record = await ecosystem.engine.governance.lifecycle.transition(request.match_info["record_id"], state)
        return json_response(record.to_dict())
    except (KeyError, ValueError, EcosystemError) as exc:
        return _handle_error(exc if isinstance(exc, EcosystemError) else ValidationError(str(exc)))


async def lifecycle_list_handler(request: web.Request) -> web.Response:
    kind_raw = request.query.get("kind")
    state_raw = request.query.get("state")
    kind = LifecycleKind(kind_raw) if kind_raw else None
    state = LifecycleState(state_raw) if state_raw else None
    records = ecosystem.engine.governance.lifecycle.list_records(kind=kind, state=state)
    return json_response({"records": [r.to_dict() for r in records]})


async def risk_assess_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        risk = await ecosystem.engine.governance.risk.assess(
            data["title"],
            category=RiskCategory(data.get("category", "operational")),
            severity=RiskSeverity(data.get("severity", "medium")),
            description=data.get("description", ""),
            mitigation=data.get("mitigation", ""),
            related_policy_id=data.get("related_policy_id", ""),
        )
        return json_response(risk.to_dict(), status=201)
    except (KeyError, ValueError, EcosystemError) as exc:
        return _handle_error(exc if isinstance(exc, EcosystemError) else ValidationError(str(exc)))


async def risk_list_handler(_request: web.Request) -> web.Response:
    risks = ecosystem.engine.governance.risk.list_risks()
    return json_response({
        "risks": [r.to_dict() for r in risks],
        "continuity": ecosystem.engine.governance.risk.continuity_policy(),
        "disaster_recovery": ecosystem.engine.governance.risk.disaster_recovery_policy(),
    })


async def admin_overview_handler(_request: web.Request) -> web.Response:
    return json_response(ecosystem.engine.governance.administration.platform_overview())


async def admin_license_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        license_rec = ecosystem.engine.governance.administration.create_license(
            data["organization_id"],
            plan=data.get("plan", "standard"),
            seats=int(data.get("seats", 10)),
            features=data.get("features"),
        )
        return json_response(license_rec.to_dict(), status=201)
    except (KeyError, ValueError, EcosystemError) as exc:
        return _handle_error(exc if isinstance(exc, EcosystemError) else ValidationError(str(exc)))


async def admin_flags_handler(request: web.Request) -> web.Response:
    if request.method == "GET":
        flags = ecosystem.engine.governance.administration.list_flags()
        return json_response({"flags": [f.to_dict() for f in flags]})
    try:
        data = await request.json()
        flag = ecosystem.engine.governance.administration.set_feature_flag(
            data["name"],
            bool(data.get("enabled", False)),
            description=data.get("description", ""),
        )
        return json_response(flag.to_dict())
    except (KeyError, EcosystemError) as exc:
        return _handle_error(exc if isinstance(exc, EcosystemError) else ValidationError(str(exc)))


async def catalog_list_handler(request: web.Request) -> web.Response:
    entry_type = request.query.get("entry_type", "")
    entries = ecosystem.engine.governance.catalog.list_entries(entry_type=entry_type)
    return json_response({"entries": [e.to_dict() for e in entries]})


async def catalog_register_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        entry = ecosystem.engine.governance.catalog.register(
            data["name"],
            entry_type=data.get("entry_type", "application"),
            version=data.get("version", "1.0.0"),
            owner=data.get("owner", ""),
            tags=data.get("tags"),
            metadata=data.get("metadata"),
        )
        return json_response(entry.to_dict(), status=201)
    except (KeyError, EcosystemError) as exc:
        return _handle_error(exc if isinstance(exc, EcosystemError) else ValidationError(str(exc)))
