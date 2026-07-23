"""API handlers — Payments Platform (Sprint 18.1)."""

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


def _suite():
    return finance_enterprise.payments


async def pay_health_handler(request: web.Request) -> web.Response:
    health = finance_enterprise.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "banking_platform_ready": health.get("banking_platform_ready"),
            "digital_wallets_ready": health.get("digital_wallets_ready"),
            "payment_engine_ready": health.get("payment_engine_ready"),
            "cash_management_ready": health.get("cash_management_ready"),
            "suite": _suite().status(),
        }
    )


async def pay_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def pay_banking_handler(request: web.Request) -> web.Response:
    try:
        banking = _suite().banking
        if request.method == "GET":
            return json_response(banking.status())
        body = await _read_json(request)
        action = body.get("action", "bank")
        if action == "account":
            return json_response(
                banking.register_account(
                    bank_id=body.get("bank_id", ""),
                    account_name=body.get("account_name", ""),
                    iban=body.get("iban", ""),
                    currency=body.get("currency", "USD"),
                    organization_id=body.get("organization_id", ""),
                ),
                status=201,
            )
        if action == "iban":
            return json_response(
                banking.set_iban(
                    bank_account_id=body.get("bank_account_id", ""),
                    iban=body.get("iban", ""),
                ),
                status=201,
            )
        if action == "swift":
            return json_response(
                banking.set_swift(bank_id=body.get("bank_id", ""), swift=body.get("swift", "")),
                status=201,
            )
        if action == "verify":
            return json_response(
                banking.verify_account(
                    bank_account_id=body.get("bank_account_id", ""),
                    method=body.get("method", "micro_deposit"),
                ),
                status=201,
            )
        if action == "statement":
            return json_response(
                banking.import_statement(
                    bank_account_id=body.get("bank_account_id", ""),
                    period=body.get("period", ""),
                    lines=body.get("lines") if isinstance(body.get("lines"), list) else None,
                ),
                status=201,
            )
        return json_response(
            banking.register_bank(
                name=body.get("name", ""),
                country=body.get("country", ""),
                bic=body.get("bic", ""),
                swift=body.get("swift", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def pay_wallets_handler(request: web.Request) -> web.Response:
    try:
        wallets = _suite().wallets
        if request.method == "GET":
            wid = request.rel_url.query.get("wallet_id")
            if wid:
                return json_response(wallets.balance(wallet_id=wid))
            return json_response(wallets.status())
        body = await _read_json(request)
        action = body.get("action", "create")
        if action == "credit":
            return json_response(
                wallets.credit(
                    wallet_id=body.get("wallet_id", ""),
                    amount=float(body.get("amount", 0) or 0),
                    memo=body.get("memo", ""),
                ),
                status=201,
            )
        if action == "debit":
            return json_response(
                wallets.debit(
                    wallet_id=body.get("wallet_id", ""),
                    amount=float(body.get("amount", 0) or 0),
                    memo=body.get("memo", ""),
                ),
                status=201,
            )
        if action == "balance":
            return json_response(wallets.balance(wallet_id=body.get("wallet_id", "")))
        return json_response(
            wallets.create_wallet(
                owner_ref=body.get("owner_ref", ""),
                wallet_type=body.get("wallet_type", "enterprise"),
                currency=body.get("currency", "USD"),
                label=body.get("label", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def pay_payments_handler(request: web.Request) -> web.Response:
    try:
        payments = _suite().payments
        if request.method == "GET":
            return json_response(payments.status())
        body = await _read_json(request)
        action = body.get("action", "create")
        if action == "status":
            return json_response(
                payments.update_status(
                    payment_id=body.get("payment_id", ""),
                    status=body.get("status", "pending"),
                    detail=body.get("detail", ""),
                ),
                status=201,
            )
        if action == "bulk":
            return json_response(
                payments.bulk(payments=body.get("payments") if isinstance(body.get("payments"), list) else []),
                status=201,
            )
        return json_response(
            payments.create_payment(
                payment_type=body.get("payment_type", "outgoing"),
                amount=float(body.get("amount", 0) or 0),
                currency=body.get("currency", "USD"),
                from_ref=body.get("from_ref", ""),
                to_ref=body.get("to_ref", ""),
                schedule_at=body.get("schedule_at", ""),
                recurrence=body.get("recurrence", ""),
                external_key=body.get("external_key", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def pay_cash_handler(request: web.Request) -> web.Response:
    try:
        cash = _suite().cash
        if request.method == "GET":
            return json_response(cash.status())
        body = await _read_json(request)
        action = body.get("action", "register")
        if action == "operate":
            return json_response(
                cash.operate(
                    register_id=body.get("register_id", ""),
                    operation=body.get("operation", "in"),
                    amount=float(body.get("amount", 0) or 0),
                    memo=body.get("memo", ""),
                ),
                status=201,
            )
        if action == "reconcile":
            return json_response(
                cash.reconcile(
                    register_id=body.get("register_id", ""),
                    counted_balance=float(body.get("counted_balance", 0) or 0),
                    note=body.get("note", ""),
                ),
                status=201,
            )
        if action == "flow":
            return json_response(
                cash.track_flow(
                    register_id=body.get("register_id", ""),
                    period=body.get("period", "daily"),
                ),
                status=201,
            )
        if action == "branch":
            return json_response(
                cash.branch_account(
                    branch=body.get("branch", ""),
                    name=body.get("name", ""),
                    currency=body.get("currency", "USD"),
                ),
                status=201,
            )
        return json_response(
            cash.open_register(
                name=body.get("name", ""),
                branch=body.get("branch", ""),
                currency=body.get("currency", "USD"),
                opening_balance=float(body.get("opening_balance", 0) or 0),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def pay_processing_handler(request: web.Request) -> web.Response:
    try:
        processing = _suite().processing
        if request.method == "GET":
            return json_response(processing.status())
        body = await _read_json(request)
        action = body.get("action", "authorize")
        if action == "approve":
            return json_response(
                processing.approve(
                    payment_id=body.get("payment_id", ""),
                    approver=body.get("approver", ""),
                    decision=body.get("decision", "approved"),
                    note=body.get("note", ""),
                ),
                status=201,
            )
        if action == "validate":
            return json_response(
                processing.validate_transaction(
                    payment_id=body.get("payment_id", ""),
                    checks=body.get("checks") if isinstance(body.get("checks"), list) else None,
                ),
                status=201,
            )
        if action == "recover":
            return json_response(
                processing.recover_failed(
                    payment_id=body.get("payment_id", ""),
                    reason=body.get("reason", ""),
                ),
                status=201,
            )
        if action == "notify":
            return json_response(
                processing.notify(
                    payment_id=body.get("payment_id", ""),
                    channel=body.get("channel", "email"),
                    message=body.get("message", ""),
                ),
                status=201,
            )
        return json_response(
            processing.authorize(
                payment_id=body.get("payment_id", ""),
                authorized_by=body.get("authorized_by", "treasury"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def pay_controls_handler(request: web.Request) -> web.Response:
    try:
        controls = _suite().controls
        if request.method == "GET":
            return json_response(controls.status())
        body = await _read_json(request)
        action = body.get("action", "limit")
        if action == "permission":
            return json_response(
                controls.grant(
                    role=body.get("role", ""),
                    permission=body.get("permission", ""),
                    resource=body.get("resource", "payments"),
                ),
                status=201,
            )
        if action == "matrix":
            return json_response(
                controls.approval_rule(
                    min_amount=float(body.get("min_amount", 0) or 0),
                    required_role=body.get("required_role", "cfo"),
                    currency=body.get("currency", "USD"),
                ),
                status=201,
            )
        if action == "audit":
            return json_response(
                controls.audit(
                    action=body.get("audit_action", body.get("name", "")),
                    actor=body.get("actor", "system"),
                    detail=body.get("detail", ""),
                ),
                status=201,
            )
        if action == "fraud":
            return json_response(
                controls.fraud_flag(
                    payment_id=body.get("payment_id", ""),
                    reason=body.get("reason", ""),
                    severity=body.get("severity", "medium"),
                ),
                status=201,
            )
        return json_response(
            controls.set_limit(
                role=body.get("role", ""),
                max_amount=float(body.get("max_amount", 0) or 0),
                currency=body.get("currency", "USD"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def pay_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dashboard = _suite().dashboard
        if request.method == "GET":
            dtype = request.rel_url.query.get("dashboard_type", "payments")
            return json_response(dashboard.render(dashboard_type=dtype))
        body = await _read_json(request)
        return json_response(
            dashboard.render(dashboard_type=body.get("dashboard_type", "payments")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def pay_knowledge_handler(request: web.Request) -> web.Response:
    try:
        knowledge = _suite().knowledge
        if request.method == "GET":
            return json_response(knowledge.status())
        body = await _read_json(request)
        return json_response(
            knowledge.publish(
                base=body.get("base", "payment"),
                key=body.get("key", ""),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
