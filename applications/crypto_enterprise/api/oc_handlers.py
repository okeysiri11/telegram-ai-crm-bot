"""API handlers — On-Chain Intelligence (Sprint 16.6)."""

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


def _suite():
    return crypto_enterprise.onchain_intelligence


async def oc_health_handler(request: web.Request) -> web.Response:
    health = crypto_enterprise.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "onchain_intelligence_ready": health.get("onchain_intelligence_ready"),
            "whale_intelligence_ready": health.get("whale_intelligence_ready"),
            "blockchain_analytics_ready": health.get("blockchain_analytics_ready"),
            "institution_monitoring_ready": health.get("institution_monitoring_ready"),
            "ai_onchain_intelligence_ready": health.get("ai_onchain_intelligence_ready"),
            "suite": _suite().status(),
        }
    )


async def oc_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def oc_chains_handler(request: web.Request) -> web.Response:
    try:
        chains = _suite().chains
        if request.method == "GET":
            return json_response(chains.status())
        body = await _read_json(request)
        action = body.get("action", "connect")
        if action == "multi":
            selected = body.get("chains") if isinstance(body.get("chains"), list) else None
            return json_response(chains.multi_chain(chains=selected), status=201)
        return json_response(
            chains.connect(chain=body.get("chain", ""), rpc_ref=body.get("rpc_ref", "")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def oc_wallets_handler(request: web.Request) -> web.Response:
    try:
        wallets = _suite().wallets
        if request.method == "GET":
            return json_response(wallets.status())
        body = await _read_json(request)
        action = body.get("action", "register")
        if action == "classify":
            return json_response(
                wallets.classify(
                    address=body.get("address", ""),
                    wallet_type=body.get("wallet_type", "unknown"),
                    confidence=float(body.get("confidence", 0) or 0),
                ),
                status=201,
            )
        return json_response(
            wallets.register(
                address=body.get("address", ""),
                chain=body.get("chain", "ethereum"),
                wallet_type=body.get("wallet_type", "unknown"),
                label=body.get("label", ""),
                balance_usd=float(body.get("balance_usd", 0) or 0),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def oc_transactions_handler(request: web.Request) -> web.Response:
    try:
        tx = _suite().transactions
        if request.method == "GET":
            return json_response(tx.status())
        body = await _read_json(request)
        action = body.get("action", "monitor")
        if action == "large":
            return json_response(
                tx.large_transfer(
                    chain=body.get("chain", "ethereum"),
                    amount_usd=float(body.get("amount_usd", 0) or 0),
                    asset=body.get("asset", "ETH"),
                    threshold_usd=float(body.get("threshold_usd", 1_000_000) or 1_000_000),
                ),
                status=201,
            )
        if action == "cross_chain":
            return json_response(
                tx.cross_chain(
                    from_chain=body.get("from_chain", ""),
                    to_chain=body.get("to_chain", ""),
                    amount_usd=float(body.get("amount_usd", 0) or 0),
                    asset=body.get("asset", "ETH"),
                ),
                status=201,
            )
        if action == "exchange_flow":
            return json_response(
                tx.exchange_flow(
                    direction=body.get("direction", "inflow"),
                    exchange=body.get("exchange", ""),
                    amount_usd=float(body.get("amount_usd", 0) or 0),
                    asset=body.get("asset", "ETH"),
                ),
                status=201,
            )
        if action == "bridge":
            return json_response(
                tx.bridge(
                    bridge=body.get("bridge", ""),
                    from_chain=body.get("from_chain", ""),
                    to_chain=body.get("to_chain", ""),
                    amount_usd=float(body.get("amount_usd", 0) or 0),
                ),
                status=201,
            )
        if action == "contract":
            return json_response(
                tx.smart_contract(
                    chain=body.get("chain", "ethereum"),
                    contract=body.get("contract", ""),
                    method=body.get("method", ""),
                    value_usd=float(body.get("value_usd", 0) or 0),
                ),
                status=201,
            )
        if action == "mint_burn":
            return json_response(
                tx.mint_burn(
                    asset=body.get("asset", ""),
                    action=body.get("mint_burn_action", "mint"),
                    amount=float(body.get("amount", 0) or 0),
                    chain=body.get("chain", "ethereum"),
                ),
                status=201,
            )
        return json_response(
            tx.monitor(
                chain=body.get("chain", "ethereum"),
                tx_hash=body.get("tx_hash", ""),
                from_addr=body.get("from_addr", ""),
                to_addr=body.get("to_addr", ""),
                amount_usd=float(body.get("amount_usd", 0) or 0),
                asset=body.get("asset", "ETH"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def oc_stablecoins_handler(request: web.Request) -> web.Response:
    try:
        stable = _suite().stablecoins
        if request.method == "GET":
            return json_response(stable.status())
        body = await _read_json(request)
        action = body.get("action", "flow")
        if action == "mint":
            return json_response(
                stable.mint(
                    stablecoin=body.get("stablecoin", "USDT"),
                    amount=float(body.get("amount", 0) or 0),
                    chain=body.get("chain", "ethereum"),
                ),
                status=201,
            )
        if action == "burn":
            return json_response(
                stable.burn(
                    stablecoin=body.get("stablecoin", "USDT"),
                    amount=float(body.get("amount", 0) or 0),
                    chain=body.get("chain", "ethereum"),
                ),
                status=201,
            )
        if action == "expansion":
            return json_response(
                stable.liquidity_expansion(
                    stablecoin=body.get("stablecoin", "USDT"),
                    expansion_usd=float(body.get("expansion_usd", 0) or 0),
                ),
                status=201,
            )
        return json_response(
            stable.flow(
                stablecoin=body.get("stablecoin", "USDT"),
                direction=body.get("direction", "inflow"),
                amount_usd=float(body.get("amount_usd", 0) or 0),
                chain=body.get("chain", "ethereum"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def oc_defi_handler(request: web.Request) -> web.Response:
    try:
        defi = _suite().defi
        if request.method == "GET":
            return json_response(defi.status())
        body = await _read_json(request)
        action = body.get("action", "tvl")
        if action == "pool":
            return json_response(
                defi.liquidity_pool(
                    protocol=body.get("protocol", ""),
                    pair=body.get("pair", ""),
                    liquidity_usd=float(body.get("liquidity_usd", 0) or 0),
                ),
                status=201,
            )
        if action == "yield":
            return json_response(
                defi.yield_protocol(
                    protocol=body.get("protocol", ""),
                    apy=float(body.get("apy", 0) or 0),
                    tvl_usd=float(body.get("tvl_usd", 0) or 0),
                ),
                status=201,
            )
        if action == "dex_volume":
            return json_response(
                defi.dex_volume(
                    dex=body.get("dex", ""),
                    volume_usd=float(body.get("volume_usd", 0) or 0),
                    chain=body.get("chain", "ethereum"),
                ),
                status=201,
            )
        if action == "dex_whale":
            return json_response(
                defi.dex_whale(
                    dex=body.get("dex", ""),
                    wallet=body.get("wallet", ""),
                    volume_usd=float(body.get("volume_usd", 0) or 0),
                ),
                status=201,
            )
        if action == "risk":
            return json_response(
                defi.protocol_risk(
                    protocol=body.get("protocol", ""),
                    risk_score=float(body.get("risk_score", 0) or 0),
                ),
                status=201,
            )
        return json_response(
            defi.tvl(
                protocol=body.get("protocol", ""),
                chain=body.get("chain", "ethereum"),
                tvl_usd=float(body.get("tvl_usd", 0) or 0),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def oc_nft_handler(request: web.Request) -> web.Response:
    try:
        nft = _suite().nft
        if request.method == "GET":
            return json_response(nft.status())
        body = await _read_json(request)
        action = body.get("action", "activity")
        if action == "unlock":
            return json_response(
                nft.token_unlock(
                    symbol=body.get("symbol", ""),
                    unlock_usd=float(body.get("unlock_usd", 0) or 0),
                    unlock_at=body.get("unlock_at", ""),
                ),
                status=201,
            )
        if action == "vesting":
            schedule = body.get("schedule") if isinstance(body.get("schedule"), list) else []
            return json_response(
                nft.vesting(symbol=body.get("symbol", ""), schedule=schedule),
                status=201,
            )
        if action == "governance":
            return json_response(
                nft.governance(
                    protocol=body.get("protocol", ""),
                    proposal=body.get("proposal", ""),
                    status=body.get("status", "active"),
                ),
                status=201,
            )
        if action == "treasury":
            return json_response(
                nft.treasury(
                    protocol=body.get("protocol", ""),
                    balance_usd=float(body.get("balance_usd", 0) or 0),
                ),
                status=201,
            )
        return json_response(
            nft.nft_activity(
                collection=body.get("collection", ""),
                volume_usd=float(body.get("volume_usd", 0) or 0),
                sales=int(body.get("sales", 0) or 0),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def oc_ai_handler(request: web.Request) -> web.Response:
    try:
        ai = _suite().ai
        if request.method == "GET":
            return json_response(ai.status())
        body = await _read_json(request)
        action = body.get("action", "whale")
        if action == "institutional":
            return json_response(
                ai.institutional_accumulation(
                    asset=body.get("asset", ""),
                    amount_usd=float(body.get("amount_usd", 0) or 0),
                ),
                status=201,
            )
        if action == "distribution":
            return json_response(
                ai.distribution(
                    asset=body.get("asset", ""),
                    amount_usd=float(body.get("amount_usd", 0) or 0),
                ),
                status=201,
            )
        if action == "smart_money":
            return json_response(
                ai.smart_money(
                    wallet=body.get("wallet", ""),
                    action=body.get("trade_action", "buy"),
                    asset=body.get("asset", ""),
                ),
                status=201,
            )
        if action == "rotation":
            return json_response(
                ai.capital_rotation(
                    from_asset=body.get("from_asset", ""),
                    to_asset=body.get("to_asset", ""),
                    amount_usd=float(body.get("amount_usd", 0) or 0),
                ),
                status=201,
            )
        if action == "health":
            return json_response(
                ai.network_health(
                    chain=body.get("chain", "ethereum"),
                    score=float(body.get("score", 0) or 0),
                ),
                status=201,
            )
        if action == "risk":
            return json_response(
                ai.blockchain_risk(
                    chain=body.get("chain", "ethereum"),
                    score=float(body.get("score", 0) or 0),
                ),
                status=201,
            )
        if action == "impact":
            return json_response(
                ai.market_impact_forecast(
                    asset=body.get("asset", ""),
                    impact_pct=float(body.get("impact_pct", 0) or 0),
                    horizon=body.get("horizon", "7d"),
                ),
                status=201,
            )
        if action == "report":
            return json_response(
                ai.report(title=body.get("title", ""), narrative=body.get("narrative", "")),
                status=201,
            )
        return json_response(
            ai.whale_activity(
                chain=body.get("chain", "ethereum"),
                intensity=float(body.get("intensity", 0) or 0),
                side=body.get("side", "accumulate"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def oc_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dash = _suite().dashboard
        if request.method == "GET":
            dtype = request.rel_url.query.get("type", "onchain")
            return json_response(dash.render(dashboard_type=dtype))
        body = await _read_json(request)
        return json_response(
            dash.render(dashboard_type=body.get("dashboard_type", "onchain")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def oc_knowledge_handler(request: web.Request) -> web.Response:
    try:
        knowledge = _suite().knowledge
        if request.method == "GET":
            return json_response(knowledge.status())
        body = await _read_json(request)
        return json_response(
            knowledge.publish(
                registry_type=body.get("registry_type", "blockchain"),
                key=body.get("key", ""),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else {},
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
