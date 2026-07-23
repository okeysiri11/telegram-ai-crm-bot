"""API handlers — Digital Asset Treasury (Sprint 18.4)."""

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
    return finance_enterprise.digital_assets


async def da_health_handler(request: web.Request) -> web.Response:
    health = finance_enterprise.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "digital_asset_treasury_ready": health.get("digital_asset_treasury_ready"),
            "crypto_finance_integration_ready": health.get("crypto_finance_integration_ready"),
            "crypto_accounting_ready": health.get("crypto_accounting_ready"),
            "ai_digital_asset_intelligence_ready": health.get("ai_digital_asset_intelligence_ready"),
            "suite": _suite().status(),
        }
    )


async def da_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def da_registry_handler(request: web.Request) -> web.Response:
    try:
        registry = _suite().registry
        if request.method == "GET":
            return json_response(registry.status())
        body = await _read_json(request)
        action = body.get("action", "asset")
        if action == "token":
            return json_response(
                registry.register_token(
                    symbol=body.get("symbol", ""),
                    contract=body.get("contract", ""),
                    network=body.get("network", "ethereum"),
                    decimals=int(body.get("decimals", 18) or 18),
                ),
                status=201,
            )
        if action == "blockchain":
            return json_response(
                registry.register_blockchain(
                    network=body.get("network", ""),
                    chain_id=body.get("chain_id", ""),
                    native_symbol=body.get("native_symbol", ""),
                ),
                status=201,
            )
        if action == "exchange_account":
            return json_response(
                registry.register_exchange_account(
                    exchange=body.get("exchange", ""),
                    account_ref=body.get("account_ref", ""),
                    label=body.get("label", ""),
                ),
                status=201,
            )
        if action == "custody":
            return json_response(
                registry.register_custody(
                    provider=body.get("provider", ""),
                    vault_ref=body.get("vault_ref", ""),
                    label=body.get("label", ""),
                ),
                status=201,
            )
        return json_response(
            registry.register_asset(
                symbol=body.get("symbol", ""),
                name=body.get("name", ""),
                asset_type=body.get("asset_type", "crypto"),
                network=body.get("network", "ethereum"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def da_wallets_handler(request: web.Request) -> web.Response:
    try:
        wallets = _suite().wallets
        if request.method == "GET":
            return json_response(wallets.status())
        body = await _read_json(request)
        action = body.get("action", "create")
        if action == "address":
            return json_response(
                wallets.add_address(
                    wallet_id=body.get("wallet_id", ""),
                    address=body.get("address", ""),
                    derivation_path=body.get("derivation_path", ""),
                ),
                status=201,
            )
        if action == "balance":
            return json_response(
                wallets.update_balance(
                    wallet_id=body.get("wallet_id", ""),
                    balance=float(body.get("balance", 0) or 0),
                    asset=body.get("asset", "NATIVE"),
                ),
                status=201,
            )
        return json_response(
            wallets.create_wallet(
                label=body.get("label", ""),
                wallet_type=body.get("wallet_type", "hot"),
                network=body.get("network", "ethereum"),
                owner_ref=body.get("owner_ref", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def da_accounting_handler(request: web.Request) -> web.Response:
    try:
        accounting = _suite().accounting
        if request.method == "GET":
            return json_response(accounting.status())
        body = await _read_json(request)
        action = body.get("action", "ledger")
        if action == "cost_basis":
            return json_response(
                accounting.cost_basis(asset_symbol=body.get("asset_symbol", "")),
                status=201,
            )
        if action == "realized":
            return json_response(
                accounting.realized_pnl(
                    asset_symbol=body.get("asset_symbol", ""),
                    sell_quantity=float(body.get("sell_quantity", 0) or 0),
                    sell_price=float(body.get("sell_price", 0) or 0),
                    average_cost=float(body.get("average_cost", 0) or 0),
                ),
                status=201,
            )
        if action == "unrealized":
            return json_response(
                accounting.unrealized_pnl(
                    asset_symbol=body.get("asset_symbol", ""),
                    quantity=float(body.get("quantity", 0) or 0),
                    market_price=float(body.get("market_price", 0) or 0),
                    average_cost=float(body.get("average_cost", 0) or 0),
                ),
                status=201,
            )
        if action == "revalue":
            return json_response(
                accounting.revalue(
                    asset_symbol=body.get("asset_symbol", ""),
                    new_price=float(body.get("new_price", 0) or 0),
                    quantity=float(body.get("quantity", 0) or 0),
                ),
                status=201,
            )
        if action == "portfolio":
            return json_response(
                accounting.portfolio_valuation(
                    holdings=body.get("holdings") if isinstance(body.get("holdings"), list) else []
                ),
                status=201,
            )
        return json_response(
            accounting.post_ledger(
                asset_symbol=body.get("asset_symbol", ""),
                quantity=float(body.get("quantity", 0) or 0),
                unit_cost=float(body.get("unit_cost", 0) or 0),
                side=body.get("side", "buy"),
                wallet_id=body.get("wallet_id", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def da_operations_handler(request: web.Request) -> web.Response:
    try:
        operations = _suite().operations
        if request.method == "GET":
            return json_response(operations.status())
        body = await _read_json(request)
        return json_response(
            operations.operate(
                operation=body.get("operation", "deposit"),
                asset_symbol=body.get("asset_symbol", ""),
                amount=float(body.get("amount", 0) or 0),
                from_ref=body.get("from_ref", ""),
                to_ref=body.get("to_ref", ""),
                detail=body.get("detail", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def da_exchange_handler(request: web.Request) -> web.Response:
    try:
        exchange = _suite().exchange
        if request.method == "GET":
            return json_response(exchange.status())
        body = await _read_json(request)
        action = body.get("action", "link")
        if action == "sync":
            return json_response(
                exchange.sync_balances(
                    link_id=body.get("link_id", ""),
                    balances=body.get("balances") if isinstance(body.get("balances"), list) else None,
                ),
                status=201,
            )
        if action == "trade":
            return json_response(
                exchange.import_trade(
                    link_id=body.get("link_id", ""),
                    symbol=body.get("symbol", ""),
                    side=body.get("side", "buy"),
                    quantity=float(body.get("quantity", 0) or 0),
                    price=float(body.get("price", 0) or 0),
                    fee=float(body.get("fee", 0) or 0),
                ),
                status=201,
            )
        if action == "transfer":
            return json_response(
                exchange.import_transfer(
                    link_id=body.get("link_id", ""),
                    asset=body.get("asset", ""),
                    amount=float(body.get("amount", 0) or 0),
                    direction=body.get("direction", "in"),
                ),
                status=201,
            )
        if action == "reconcile":
            return json_response(
                exchange.reconcile(
                    link_id=body.get("link_id", ""),
                    books_total=float(body.get("books_total", 0) or 0),
                    exchange_total=float(body.get("exchange_total", 0) or 0),
                ),
                status=201,
            )
        return json_response(
            exchange.link_account(
                exchange=body.get("exchange", ""),
                account_ref=body.get("account_ref", ""),
                label=body.get("label", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def da_ai_handler(request: web.Request) -> web.Response:
    try:
        ai = _suite().ai
        if request.method == "GET":
            return json_response(ai.status())
        body = await _read_json(request)
        action = body.get("action", "insight")
        if action == "nl_report":
            return json_response(ai.nl_report(audience=body.get("audience", "treasury")), status=201)
        return json_response(
            ai.insight(
                insight_type=body.get("insight_type", "portfolio_risk"),
                subject=body.get("subject", ""),
                score=float(body.get("score", 0.7) or 0.7),
                detail=body.get("detail", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def da_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dashboard = _suite().dashboard
        if request.method == "GET":
            dtype = request.rel_url.query.get("dashboard_type", "digital_assets")
            return json_response(dashboard.render(dashboard_type=dtype))
        body = await _read_json(request)
        return json_response(
            dashboard.render(dashboard_type=body.get("dashboard_type", "digital_assets")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def da_knowledge_handler(request: web.Request) -> web.Response:
    try:
        knowledge = _suite().knowledge
        if request.method == "GET":
            return json_response(knowledge.status())
        body = await _read_json(request)
        return json_response(
            knowledge.publish(
                base=body.get("base", "digital_asset"),
                key=body.get("key", ""),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else None,
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
