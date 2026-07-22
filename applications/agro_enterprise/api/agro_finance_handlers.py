"""API handlers — Agro Finance (Sprint 14.6)."""

from __future__ import annotations

from aiohttp import web

from applications.agro_enterprise import agro_enterprise
from applications.agro_enterprise.api.middleware import json_response
from applications.agro_enterprise.shared.exceptions import NotFoundError, ValidationError


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
    return agro_enterprise.agro_finance


async def af_health_handler(request: web.Request) -> web.Response:
    health = agro_enterprise.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "agro_finance_ready": health.get("agro_finance_ready"),
            "commodity_exchange_ready": health.get("commodity_exchange_ready"),
            "risk_intelligence_ready": health.get("risk_intelligence_ready"),
            "crop_insurance_ready": health.get("crop_insurance_ready"),
            "market_intelligence_ready": health.get("market_intelligence_ready"),
            "suite": _suite().status(),
        }
    )


async def af_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def af_exchange_handler(request: web.Request) -> web.Response:
    try:
        exchange = _suite().exchange
        if request.method == "GET":
            cid = request.rel_url.query.get("commodity_id")
            view = request.rel_url.query.get("view", "status")
            if view == "depth" and cid:
                return json_response(exchange.market_depth(cid))
            if view == "history":
                return json_response({"trades": exchange.trade_history(cid)})
            return json_response(exchange.status())
        body = await _read_json(request)
        action = body.get("action", "register")
        if action == "order":
            return json_response(
                exchange.place_order(
                    commodity_id=body.get("commodity_id", ""),
                    side=body.get("side", "buy"),
                    trade_type=body.get("trade_type", "spot"),
                    quantity=float(body.get("quantity", 0) or 0),
                    price=float(body.get("price", 0) or 0),
                    party=body.get("party", ""),
                ),
                status=201,
            )
        if action == "trade":
            return json_response(
                exchange.execute_trade(
                    buy_order_id=body.get("buy_order_id", ""),
                    sell_order_id=body.get("sell_order_id", ""),
                ),
                status=201,
            )
        return json_response(
            exchange.register_commodity(
                symbol=body.get("symbol", ""),
                name=body.get("name", ""),
                unit=body.get("unit", "t"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def af_contracts_handler(request: web.Request) -> web.Response:
    try:
        contracts = _suite().contracts
        if request.method == "GET":
            return json_response(contracts.status())
        body = await _read_json(request)
        action = body.get("action", "create")
        if action == "lifecycle":
            return json_response(
                contracts.advance_lifecycle(body.get("contract_id", ""), status=body.get("status", "active")),
                status=201,
            )
        if action == "sign":
            return json_response(
                contracts.e_sign(body.get("contract_id", ""), signer=body.get("signer", "")),
                status=201,
            )
        if action == "vault":
            return json_response(
                contracts.vault_document(
                    contract_id=body.get("contract_id", ""),
                    title=body.get("title", ""),
                    doc_type=body.get("doc_type", "pdf"),
                ),
                status=201,
            )
        return json_response(
            contracts.create_contract(
                contract_type=body.get("contract_type", "purchase"),
                party=body.get("party", ""),
                commodity=body.get("commodity", ""),
                tons=float(body.get("tons", 0) or 0),
                value=float(body.get("value", 0) or 0),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def af_finance_handler(request: web.Request) -> web.Response:
    try:
        finance = _suite().finance
        if request.method == "GET":
            farm_id = request.rel_url.query.get("farm_id")
            if farm_id:
                return json_response(finance.profitability(farm_id))
            return json_response(finance.status())
        body = await _read_json(request)
        action = body.get("action", "budget")
        if action == "cashflow":
            return json_response(
                finance.cash_flow(
                    farm_id=body.get("farm_id", ""),
                    inflow=float(body.get("inflow", 0) or 0),
                    outflow=float(body.get("outflow", 0) or 0),
                ),
                status=201,
            )
        if action == "cost":
            return json_response(
                finance.cost_entry(
                    farm_id=body.get("farm_id", ""),
                    category=body.get("category", ""),
                    amount=float(body.get("amount", 0) or 0),
                ),
                status=201,
            )
        if action == "credit":
            return json_response(
                finance.credit(
                    farm_id=body.get("farm_id", ""),
                    limit=float(body.get("limit", 0) or 0),
                    utilized=float(body.get("utilized", 0) or 0),
                ),
                status=201,
            )
        if action == "loan":
            return json_response(
                finance.loan(
                    farm_id=body.get("farm_id", ""),
                    principal=float(body.get("principal", 0) or 0),
                    rate_pct=float(body.get("rate_pct", 0) or 0),
                    term_months=int(body.get("term_months", 12) or 12),
                ),
                status=201,
            )
        if action == "subsidy":
            return json_response(
                finance.subsidy(
                    farm_id=body.get("farm_id", ""),
                    program=body.get("program", ""),
                    amount=float(body.get("amount", 0) or 0),
                ),
                status=201,
            )
        if action == "grant":
            return json_response(
                finance.grant(
                    farm_id=body.get("farm_id", ""),
                    program=body.get("program", ""),
                    amount=float(body.get("amount", 0) or 0),
                ),
                status=201,
            )
        return json_response(
            finance.create_budget(
                farm_id=body.get("farm_id", ""),
                year=int(body.get("year", 2026) or 2026),
                revenue=float(body.get("revenue", 0) or 0),
                costs=float(body.get("costs", 0) or 0),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def af_insurance_handler(request: web.Request) -> web.Response:
    try:
        insurance = _suite().insurance
        if request.method == "GET":
            if request.rel_url.query.get("view") == "premiums":
                return json_response(insurance.premium_analytics())
            return json_response(insurance.status())
        body = await _read_json(request)
        action = body.get("action", "insurer")
        if action == "policy":
            return json_response(
                insurance.create_policy(
                    insurer_id=body.get("insurer_id", ""),
                    farm_id=body.get("farm_id", ""),
                    crop=body.get("crop", ""),
                    coverage=float(body.get("coverage", 0) or 0),
                    premium=float(body.get("premium", 0) or 0),
                ),
                status=201,
            )
        if action == "coverage":
            return json_response(
                insurance.coverage_calc(
                    hectares=float(body.get("hectares", 0) or 0),
                    yield_t_ha=float(body.get("yield_t_ha", 0) or 0),
                    price=float(body.get("price", 0) or 0),
                    coverage_pct=float(body.get("coverage_pct", 0.7) or 0.7),
                ),
                status=201,
            )
        if action == "risk_score":
            return json_response(
                insurance.risk_score(
                    farm_id=body.get("farm_id", ""),
                    weather=float(body.get("weather", 0.3) or 0.3),
                    market=float(body.get("market", 0.2) or 0.2),
                    production=float(body.get("production", 0.25) or 0.25),
                ),
                status=201,
            )
        if action == "claim":
            return json_response(
                insurance.claim(
                    policy_id=body.get("policy_id", ""),
                    amount=float(body.get("amount", 0) or 0),
                    damage_pct=float(body.get("damage_pct", 0) or 0),
                ),
                status=201,
            )
        return json_response(insurance.register_insurer(name=body.get("name", "")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def af_risk_handler(request: web.Request) -> web.Response:
    try:
        risk = _suite().risk
        if request.method == "GET":
            entity_id = request.rel_url.query.get("entity_id")
            if entity_id:
                return json_response(risk.portfolio_score(entity_id))
            return json_response(risk.status())
        body = await _read_json(request)
        action = body.get("action", "assess")
        if action == "warning":
            return json_response(
                risk.early_warning(
                    entity_id=body.get("entity_id", ""),
                    signal=body.get("signal", ""),
                    severity=float(body.get("severity", 0.6) or 0.6),
                ),
                status=201,
            )
        return json_response(
            risk.assess(
                risk_type=body.get("risk_type", "market"),
                entity_id=body.get("entity_id", ""),
                severity=float(body.get("severity", 0.5) or 0.5),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def af_market_handler(request: web.Request) -> web.Response:
    try:
        market = _suite().market
        if request.method == "GET":
            return json_response(market.status())
        body = await _read_json(request)
        action = body.get("action", "price")
        if action == "trend":
            return json_response(market.trend(body.get("commodity", "")), status=201)
        if action == "supply_demand":
            return json_response(
                market.supply_demand(
                    commodity=body.get("commodity", ""),
                    supply_t=float(body.get("supply_t", 0) or 0),
                    demand_t=float(body.get("demand_t", 0) or 0),
                ),
                status=201,
            )
        if action == "forecast":
            return json_response(
                market.forecast(
                    commodity=body.get("commodity", ""),
                    horizon_days=int(body.get("horizon_days", 30) or 30),
                ),
                status=201,
            )
        if action == "export":
            return json_response(
                market.export_analytics(
                    region=body.get("region", ""),
                    commodity=body.get("commodity", ""),
                    tons=float(body.get("tons", 0) or 0),
                    value=float(body.get("value", 0) or 0),
                ),
                status=201,
            )
        if action == "insight":
            return json_response(market.trading_insight(commodity=body.get("commodity", "")), status=201)
        return json_response(
            market.publish_price(
                commodity=body.get("commodity", ""),
                price=float(body.get("price", 0) or 0),
                market=body.get("market", "local"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def af_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dash = _suite().dashboard
        if request.method == "GET":
            dtype = request.rel_url.query.get("type", "finance")
            return json_response(dash.render(dashboard_type=dtype))
        body = await _read_json(request)
        return json_response(
            dash.render(dashboard_type=body.get("dashboard_type", "finance")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def af_knowledge_handler(request: web.Request) -> web.Response:
    try:
        knowledge = _suite().knowledge
        if request.method == "GET":
            return json_response(knowledge.status())
        body = await _read_json(request)
        return json_response(
            knowledge.publish(
                registry_type=body.get("registry_type", "financial"),
                key=body.get("key", ""),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else {},
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
