"""API handlers — Treasury Platform (Sprint 18.3)."""

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
    return finance_enterprise.treasury


async def tr_health_handler(request: web.Request) -> web.Response:
    health = finance_enterprise.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "treasury_platform_ready": health.get("treasury_platform_ready"),
            "budget_management_ready": health.get("budget_management_ready"),
            "financial_planning_ready": health.get("financial_planning_ready"),
            "ai_financial_forecasting_ready": health.get("ai_financial_forecasting_ready"),
            "suite": _suite().status(),
        }
    )


async def tr_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def tr_treasury_handler(request: web.Request) -> web.Response:
    try:
        treasury = _suite().treasury
        if request.method == "GET":
            return json_response(treasury.status())
        body = await _read_json(request)
        action = body.get("action", "entity")
        if action == "pool":
            return json_response(
                treasury.create_pool(
                    name=body.get("name", ""),
                    currency=body.get("currency", "USD"),
                    balance=float(body.get("balance", 0) or 0),
                ),
                status=201,
            )
        if action == "liquidity":
            return json_response(
                treasury.monitor_liquidity(
                    pool_id=body.get("pool_id", ""),
                    available=float(body.get("available", 0) or 0),
                    committed=float(body.get("committed", 0) or 0),
                ),
                status=201,
            )
        if action == "position":
            return json_response(
                treasury.cash_position(
                    label=body.get("label", ""),
                    amount=float(body.get("amount", 0) or 0),
                    currency=body.get("currency", "USD"),
                ),
                status=201,
            )
        if action == "intercompany":
            return json_response(
                treasury.intercompany_funding(
                    from_entity=body.get("from_entity", ""),
                    to_entity=body.get("to_entity", ""),
                    amount=float(body.get("amount", 0) or 0),
                    currency=body.get("currency", "USD"),
                ),
                status=201,
            )
        if action == "operate":
            return json_response(
                treasury.operate(
                    operation=body.get("operation", ""),
                    amount=float(body.get("amount", 0) or 0),
                    pool_id=body.get("pool_id", ""),
                    detail=body.get("detail", ""),
                ),
                status=201,
            )
        return json_response(
            treasury.register_entity(
                name=body.get("name", ""),
                entity_type=body.get("entity_type", "treasury_unit"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def tr_reconciliation_handler(request: web.Request) -> web.Response:
    try:
        recon = _suite().reconciliation
        if request.method == "GET":
            return json_response(recon.status())
        body = await _read_json(request)
        action = body.get("action", "import")
        if action == "auto_match":
            return json_response(
                recon.auto_match(
                    statement_id=body.get("statement_id", ""),
                    book_refs=body.get("book_refs") if isinstance(body.get("book_refs"), list) else None,
                ),
                status=201,
            )
        if action == "manual":
            return json_response(
                recon.manual_reconcile(
                    statement_id=body.get("statement_id", ""),
                    line_index=int(body.get("line_index", 0) or 0),
                    book_ref=body.get("book_ref", ""),
                    note=body.get("note", ""),
                ),
                status=201,
            )
        if action == "exception":
            return json_response(
                recon.exception(
                    statement_id=body.get("statement_id", ""),
                    reason=body.get("reason", ""),
                    severity=body.get("severity", "medium"),
                ),
                status=201,
            )
        if action == "report":
            return json_response(
                recon.report(statement_id=body.get("statement_id", "")),
                status=201,
            )
        if action == "audit":
            return json_response(
                recon.audit(
                    action=body.get("audit_action", body.get("name", "")),
                    actor=body.get("actor", "system"),
                    detail=body.get("detail", ""),
                ),
                status=201,
            )
        return json_response(
            recon.import_statement(
                account_ref=body.get("account_ref", ""),
                period=body.get("period", ""),
                lines=body.get("lines") if isinstance(body.get("lines"), list) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def tr_budgets_handler(request: web.Request) -> web.Response:
    try:
        budgets = _suite().budgets
        if request.method == "GET":
            return json_response(budgets.status())
        body = await _read_json(request)
        action = body.get("action", "create")
        if action == "approve":
            return json_response(
                budgets.approve(
                    budget_id=body.get("budget_id", ""),
                    approver=body.get("approver", "cfo"),
                ),
                status=201,
            )
        if action == "revise":
            return json_response(
                budgets.revise(
                    budget_id=body.get("budget_id", ""),
                    new_amount=float(body.get("new_amount", 0) or 0),
                    reason=body.get("reason", ""),
                ),
                status=201,
            )
        return json_response(
            budgets.create_budget(
                name=body.get("name", ""),
                budget_type=body.get("budget_type", "department"),
                amount=float(body.get("amount", 0) or 0),
                period=body.get("period", "2026"),
                owner_ref=body.get("owner_ref", ""),
                currency=body.get("currency", "USD"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def tr_planning_handler(request: web.Request) -> web.Response:
    try:
        planning = _suite().planning
        if request.method == "GET":
            return json_response(planning.status())
        body = await _read_json(request)
        action = body.get("action", "workspace")
        if action == "plan":
            return json_response(
                planning.add_plan(
                    workspace_id=body.get("workspace_id", ""),
                    plan_type=body.get("plan_type", "revenue"),
                    amount=float(body.get("amount", 0) or 0),
                    label=body.get("label", ""),
                ),
                status=201,
            )
        return json_response(
            planning.create_workspace(
                name=body.get("name", ""),
                period=body.get("period", "2026"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def tr_forecast_handler(request: web.Request) -> web.Response:
    try:
        forecasting = _suite().forecasting
        if request.method == "GET":
            return json_response(forecasting.status())
        body = await _read_json(request)
        action = body.get("action", "forecast")
        if action == "scenario":
            return json_response(
                forecasting.scenario(
                    name=body.get("name", ""),
                    base_amount=float(body.get("base_amount", 0) or 0),
                    uplift_pct=float(body.get("uplift_pct", 0) or 0),
                ),
                status=201,
            )
        if action == "sensitivity":
            return json_response(
                forecasting.sensitivity(
                    variable=body.get("variable", ""),
                    low=float(body.get("low", 0) or 0),
                    base=float(body.get("base", 0) or 0),
                    high=float(body.get("high", 0) or 0),
                ),
                status=201,
            )
        return json_response(
            forecasting.forecast(
                kind=body.get("kind", "cash_flow"),
                horizon_days=int(body.get("horizon_days", 90) or 90),
                projected=float(body.get("projected", 0) or 0),
                narrative=body.get("narrative", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def tr_variance_handler(request: web.Request) -> web.Response:
    try:
        variance = _suite().variance
        if request.method == "GET":
            return json_response(variance.status())
        body = await _read_json(request)
        action = body.get("action", "analyze")
        if action == "kpi":
            return json_response(
                variance.kpi(
                    name=body.get("name", ""),
                    value=float(body.get("value", 0) or 0),
                    target=float(body.get("target", 0) or 0),
                    unit=body.get("unit", ""),
                ),
                status=201,
            )
        return json_response(
            variance.analyze(
                variance_type=body.get("variance_type", "budget_vs_actual"),
                budget=float(body.get("budget", 0) or 0),
                actual=float(body.get("actual", 0) or 0),
                subject=body.get("subject", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def tr_ai_handler(request: web.Request) -> web.Response:
    try:
        ai = _suite().ai
        if request.method == "GET":
            return json_response(ai.status())
        body = await _read_json(request)
        action = body.get("action", "insight")
        if action == "nl_summary":
            return json_response(ai.nl_summary(audience=body.get("audience", "executive")), status=201)
        return json_response(
            ai.insight(
                insight_type=body.get("insight_type", "budget_deviation"),
                subject=body.get("subject", ""),
                score=float(body.get("score", 0.7) or 0.7),
                detail=body.get("detail", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def tr_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dashboard = _suite().dashboard
        if request.method == "GET":
            dtype = request.rel_url.query.get("dashboard_type", "treasury")
            return json_response(dashboard.render(dashboard_type=dtype))
        body = await _read_json(request)
        return json_response(
            dashboard.render(dashboard_type=body.get("dashboard_type", "treasury")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def tr_knowledge_handler(request: web.Request) -> web.Response:
    try:
        knowledge = _suite().knowledge
        if request.method == "GET":
            return json_response(knowledge.status())
        body = await _read_json(request)
        return json_response(
            knowledge.publish(
                base=body.get("base", "treasury"),
                key=body.get("key", ""),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
