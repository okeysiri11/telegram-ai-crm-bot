"""API handlers — Finance Enterprise (Sprint 18.0)."""

from __future__ import annotations

from aiohttp import web

from applications.finance_enterprise import finance_enterprise
from applications.finance_enterprise.api.middleware import json_response
from applications.finance_enterprise.shared.exceptions import NotFoundError, ValidationError


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
    return json_response(finance_enterprise.health())


async def bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(finance_enterprise.bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def registry_handler(request: web.Request) -> web.Response:
    try:
        registry = finance_enterprise.registry
        if request.method == "GET":
            return json_response(registry.status())
        body = await _read_json(request)
        action = body.get("action", "organization")
        if action == "customer":
            return json_response(
                registry.register_customer(
                    name=body.get("name", ""),
                    organization_id=body.get("organization_id", ""),
                    country=body.get("country", ""),
                ),
                status=201,
            )
        if action == "vendor":
            return json_response(
                registry.register_vendor(
                    name=body.get("name", ""),
                    organization_id=body.get("organization_id", ""),
                    country=body.get("country", ""),
                ),
                status=201,
            )
        if action == "financial_account":
            return json_response(
                registry.register_financial_account(
                    name=body.get("name", ""),
                    account_code=body.get("account_code", ""),
                    currency=body.get("currency", ""),
                    organization_id=body.get("organization_id", ""),
                ),
                status=201,
            )
        if action == "currency":
            return json_response(
                registry.register_currency(
                    code=body.get("code", ""),
                    name=body.get("name", ""),
                    decimals=int(body.get("decimals", 2) or 2),
                ),
                status=201,
            )
        if action == "cost_center":
            return json_response(
                registry.register_cost_center(
                    code=body.get("code", ""),
                    name=body.get("name", ""),
                    organization_id=body.get("organization_id", ""),
                ),
                status=201,
            )
        if action == "entity":
            return json_response(
                registry.register_entity(
                    name=body.get("name", ""),
                    entity_type=body.get("entity_type", "other"),
                    ref_id=body.get("ref_id", ""),
                ),
                status=201,
            )
        return json_response(
            registry.register_organization(
                name=body.get("name", ""),
                jurisdiction=body.get("jurisdiction", ""),
                registration_no=body.get("registration_no", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def ledger_handler(request: web.Request) -> web.Response:
    try:
        ledger = finance_enterprise.ledger
        if request.method == "GET":
            action = request.rel_url.query.get("action", "status")
            if action == "balance":
                return json_response(ledger.balance(account_code=request.rel_url.query.get("account_code", "")))
            if action == "trial_balance":
                return json_response(ledger.trial_balance())
            return json_response(ledger.status())
        body = await _read_json(request)
        action = body.get("action", "account")
        if action == "journal":
            lines = body.get("lines") if isinstance(body.get("lines"), list) else []
            return json_response(
                ledger.create_journal_entry(
                    description=body.get("description", ""),
                    lines=lines,
                    reference=body.get("reference", ""),
                    currency=body.get("currency", ""),
                ),
                status=201,
            )
        if action == "post":
            return json_response(ledger.post(journal_id=body.get("journal_id", "")), status=201)
        if action == "trial_balance":
            return json_response(ledger.trial_balance(), status=201)
        if action == "balance":
            return json_response(ledger.balance(account_code=body.get("account_code", "")))
        return json_response(
            ledger.add_account(
                code=body.get("code", ""),
                name=body.get("name", ""),
                account_type=body.get("account_type", "asset"),
                parent_code=body.get("parent_code", ""),
                currency=body.get("currency", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def currency_handler(request: web.Request) -> web.Response:
    try:
        currency = finance_enterprise.currency
        if request.method == "GET":
            return json_response(currency.status())
        body = await _read_json(request)
        action = body.get("action", "rate")
        if action == "base":
            return json_response(currency.set_base_currency(code=body.get("code", "")), status=201)
        if action == "convert":
            rate = body.get("rate")
            return json_response(
                currency.convert(
                    amount=float(body.get("amount", 0) or 0),
                    from_currency=body.get("from_currency", ""),
                    to_currency=body.get("to_currency", ""),
                    rate=float(rate) if rate is not None else None,
                ),
                status=201,
            )
        return json_response(
            currency.register_rate(
                from_currency=body.get("from_currency", ""),
                to_currency=body.get("to_currency", ""),
                rate=float(body.get("rate", 0) or 0),
                as_of=body.get("as_of", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def architecture_handler(request: web.Request) -> web.Response:
    try:
        architecture = finance_enterprise.architecture
        if request.method == "GET":
            return json_response(architecture.status())
        body = await _read_json(request)
        action = body.get("action", "event")
        if action == "audit":
            return json_response(
                architecture.audit(
                    action=body.get("audit_action", body.get("name", "")),
                    actor=body.get("actor", "system"),
                    resource=body.get("resource", ""),
                    detail=body.get("detail", ""),
                ),
                status=201,
            )
        if action == "permission":
            return json_response(
                architecture.grant_permission(
                    role=body.get("role", ""),
                    permission=body.get("permission", ""),
                    resource=body.get("resource", "*"),
                ),
                status=201,
            )
        if action == "config":
            return json_response(
                architecture.set_config(key=body.get("key", ""), value=body.get("value")),
                status=201,
            )
        return json_response(
            architecture.publish_event(
                event_type=body.get("event_type", ""),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def dashboard_handler(request: web.Request) -> web.Response:
    try:
        dashboard = finance_enterprise.dashboard
        if request.method == "GET":
            dtype = request.rel_url.query.get("dashboard_type", "overview")
            return json_response(dashboard.render(dashboard_type=dtype))
        body = await _read_json(request)
        return json_response(
            dashboard.render(dashboard_type=body.get("dashboard_type", "overview")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def knowledge_handler(request: web.Request) -> web.Response:
    try:
        knowledge = finance_enterprise.knowledge
        if request.method == "GET":
            return json_response(knowledge.status())
        body = await _read_json(request)
        action = body.get("action", "publish")
        if action == "relate":
            return json_response(
                knowledge.relate(
                    from_node=body.get("from_node", ""),
                    to_node=body.get("to_node", ""),
                    relation=body.get("relation", "related_to"),
                ),
                status=201,
            )
        return json_response(
            knowledge.publish(
                base=body.get("base", "finance"),
                key=body.get("key", ""),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
