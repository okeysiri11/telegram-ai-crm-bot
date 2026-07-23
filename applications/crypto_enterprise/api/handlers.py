"""API handlers — Crypto Enterprise (Sprint 16.0)."""

from __future__ import annotations

from aiohttp import web

from applications.crypto_enterprise import crypto_enterprise
from applications.crypto_enterprise.api.middleware import json_response
from applications.crypto_enterprise.shared.exceptions import NotFoundError, ValidationError


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
    return json_response(crypto_enterprise.health())


async def bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(crypto_enterprise.bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def exchanges_handler(request: web.Request) -> web.Response:
    try:
        exchanges = crypto_enterprise.exchanges
        if request.method == "GET":
            return json_response(exchanges.status())
        body = await _read_json(request)
        action = body.get("action", "register")
        if action == "api_key":
            perms = body.get("permissions") if isinstance(body.get("permissions"), list) else None
            return json_response(
                exchanges.store_api_key(
                    exchange_id=body.get("exchange_id", ""),
                    label=body.get("label", ""),
                    api_key_ref=body.get("api_key_ref", ""),
                    permissions=perms,
                ),
                status=201,
            )
        if action == "connect":
            return json_response(
                exchanges.connect(exchange_id=body.get("exchange_id", ""), mode=body.get("mode", "read_only")),
                status=201,
            )
        if action == "binance":
            return json_response(exchanges.integrate_binance(name=body.get("name", "Binance")), status=201)
        if action == "bybit":
            return json_response(exchanges.integrate_bybit(name=body.get("name", "Bybit")), status=201)
        if action == "okx":
            return json_response(exchanges.integrate_okx(name=body.get("name", "OKX")), status=201)
        if action == "kraken":
            return json_response(exchanges.integrate_kraken(name=body.get("name", "Kraken")), status=201)
        if action == "htx":
            return json_response(exchanges.integrate_htx(name=body.get("name", "HTX")), status=201)
        if action == "coinbase":
            return json_response(exchanges.integrate_coinbase(name=body.get("name", "Coinbase")), status=201)
        return json_response(
            exchanges.register_exchange(
                name=body.get("name", ""),
                exchange_code=body.get("exchange_code", ""),
                region=body.get("region", "global"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def markets_handler(request: web.Request) -> web.Response:
    try:
        markets = crypto_enterprise.markets
        if request.method == "GET":
            return json_response(markets.status())
        body = await _read_json(request)
        action = body.get("action", "spot")
        if action == "futures":
            return json_response(
                markets.register_futures(
                    symbol=body.get("symbol", ""),
                    base=body.get("base", ""),
                    quote=body.get("quote", ""),
                    exchange_id=body.get("exchange_id", ""),
                    expiry=body.get("expiry", ""),
                ),
                status=201,
            )
        if action == "options":
            return json_response(
                markets.register_options(
                    symbol=body.get("symbol", ""),
                    base=body.get("base", ""),
                    quote=body.get("quote", ""),
                    exchange_id=body.get("exchange_id", ""),
                    option_type=body.get("option_type", "call"),
                ),
                status=201,
            )
        if action == "perpetual":
            return json_response(
                markets.register_perpetual(
                    symbol=body.get("symbol", ""),
                    base=body.get("base", ""),
                    quote=body.get("quote", ""),
                    exchange_id=body.get("exchange_id", ""),
                ),
                status=201,
            )
        if action == "ticker":
            return json_response(
                markets.ticker(
                    symbol=body.get("symbol", ""),
                    last=float(body.get("last", 0) or 0),
                    bid=float(body.get("bid", 0) or 0),
                    ask=float(body.get("ask", 0) or 0),
                    volume=float(body.get("volume", 0) or 0),
                ),
                status=201,
            )
        if action == "candle":
            return json_response(
                markets.candle(
                    symbol=body.get("symbol", ""),
                    interval=body.get("interval", "1h"),
                    open_=float(body.get("open", 0) or 0),
                    high=float(body.get("high", 0) or 0),
                    low=float(body.get("low", 0) or 0),
                    close=float(body.get("close", 0) or 0),
                    volume=float(body.get("volume", 0) or 0),
                ),
                status=201,
            )
        if action == "historical":
            return json_response(
                markets.historical(
                    symbol=body.get("symbol", ""),
                    from_ts=body.get("from_ts", ""),
                    to_ts=body.get("to_ts", ""),
                    bars=int(body.get("bars", 0) or 0),
                ),
                status=201,
            )
        if action == "stream":
            return json_response(
                markets.stream(symbol=body.get("symbol", ""), channel=body.get("channel", "trades")),
                status=201,
            )
        return json_response(
            markets.register_spot(
                symbol=body.get("symbol", ""),
                base=body.get("base", ""),
                quote=body.get("quote", ""),
                exchange_id=body.get("exchange_id", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def assets_handler(request: web.Request) -> web.Response:
    try:
        assets = crypto_enterprise.assets
        if request.method == "GET":
            return json_response(assets.status())
        body = await _read_json(request)
        action = body.get("action", "coin")
        if action == "token":
            return json_response(
                assets.register_token(
                    symbol=body.get("symbol", ""),
                    name=body.get("name", ""),
                    blockchain_id=body.get("blockchain_id", ""),
                    contract=body.get("contract", ""),
                ),
                status=201,
            )
        if action == "blockchain":
            return json_response(
                assets.register_blockchain(
                    name=body.get("name", ""),
                    chain_id=body.get("chain_id", ""),
                    native_symbol=body.get("native_symbol", ""),
                ),
                status=201,
            )
        if action == "stablecoin":
            return json_response(
                assets.register_stablecoin(
                    symbol=body.get("symbol", ""),
                    name=body.get("name", ""),
                    peg=body.get("peg", "USD"),
                    blockchain_id=body.get("blockchain_id", ""),
                ),
                status=201,
            )
        if action == "pair":
            return json_response(
                assets.register_pair(
                    base=body.get("base", ""),
                    quote=body.get("quote", ""),
                    symbol=body.get("symbol", ""),
                ),
                status=201,
            )
        return json_response(
            assets.register_coin(
                symbol=body.get("symbol", ""),
                name=body.get("name", ""),
                blockchain_id=body.get("blockchain_id", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def portfolio_handler(request: web.Request) -> web.Response:
    try:
        portfolio = crypto_enterprise.portfolio
        if request.method == "GET":
            return json_response(portfolio.status())
        body = await _read_json(request)
        action = body.get("action", "register")
        if action == "wallet":
            return json_response(
                portfolio.register_wallet(
                    portfolio_id=body.get("portfolio_id", ""),
                    address=body.get("address", ""),
                    blockchain_id=body.get("blockchain_id", ""),
                    label=body.get("label", ""),
                ),
                status=201,
            )
        if action == "allocate":
            return json_response(
                portfolio.allocate(
                    portfolio_id=body.get("portfolio_id", ""),
                    asset=body.get("asset", ""),
                    weight_pct=float(body.get("weight_pct", 0) or 0),
                    amount=float(body.get("amount", 0) or 0),
                ),
                status=201,
            )
        if action == "pnl":
            return json_response(
                portfolio.track_pnl(
                    portfolio_id=body.get("portfolio_id", ""),
                    realized=float(body.get("realized", 0) or 0),
                    unrealized=float(body.get("unrealized", 0) or 0),
                ),
                status=201,
            )
        if action == "balance":
            balances = body.get("balances") if isinstance(body.get("balances"), dict) else None
            return json_response(
                portfolio.balance_snapshot(
                    portfolio_id=body.get("portfolio_id", ""),
                    balances=balances,
                    total_value=float(body.get("total_value", 0) or 0),
                ),
                status=201,
            )
        return json_response(
            portfolio.register_portfolio(
                name=body.get("name", ""),
                owner=body.get("owner", ""),
                base_currency=body.get("base_currency", "USD"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def dashboard_handler(request: web.Request) -> web.Response:
    try:
        dash = crypto_enterprise.dashboard
        if request.method == "GET":
            dtype = request.rel_url.query.get("type", "market")
            return json_response(dash.render(dashboard_type=dtype))
        body = await _read_json(request)
        return json_response(
            dash.render(dashboard_type=body.get("dashboard_type", "market")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def knowledge_handler(request: web.Request) -> web.Response:
    try:
        knowledge = crypto_enterprise.knowledge
        if request.method == "GET":
            return json_response(knowledge.status())
        body = await _read_json(request)
        return json_response(
            knowledge.publish(
                base=body.get("base", "crypto"),
                key=body.get("key", ""),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else {},
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
