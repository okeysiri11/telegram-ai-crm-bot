"""API handlers — Seller AI (Sprint 13.5)."""

from __future__ import annotations

from aiohttp import web

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.middleware import json_response
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError


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
    return auto_marketplace.seller_ai


async def sa_health_handler(request: web.Request) -> web.Response:
    health = auto_marketplace.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "seller_ai_ready": health.get("seller_ai_ready"),
            "auction_platform_ready": health.get("auction_platform_ready"),
            "global_automotive_network_ready": health.get("global_automotive_network_ready"),
            "enterprise_automotive_marketplace_ready": health.get("enterprise_automotive_marketplace_ready"),
            "suite": _suite().status(),
        }
    )


async def sa_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def sa_seller_handler(request: web.Request) -> web.Response:
    try:
        seller = _suite().seller
        if request.method == "GET":
            sid = request.rel_url.query.get("seller_id")
            if sid:
                return json_response(seller.seller_dashboard(sid))
            return json_response(seller.status())
        body = await _read_json(request)
        action = body.get("action", "create_seller")
        if action == "listing":
            return json_response(
                seller.create_listing(
                    seller_id=body.get("seller_id", ""),
                    vin=body.get("vin", ""),
                    make=body.get("make", ""),
                    model=body.get("model", ""),
                    year=body.get("year"),
                    ask_price=float(body.get("ask_price", 0) or 0),
                    photos=body.get("photos"),
                    description=body.get("description", ""),
                ),
                status=201,
            )
        if action == "generate":
            return json_response(seller.generate_listing_copy(body.get("listing_id", "")), status=201)
        if action == "position":
            return json_response(
                seller.analyze_market_position(
                    listing_id=body.get("listing_id", ""),
                    market_avg=float(body.get("market_avg", 18000) or 18000),
                    demand_index=float(body.get("demand_index", 0.6) or 0.6),
                ),
                status=201,
            )
        return json_response(
            seller.create_seller(name=body.get("name", ""), seller_type=body.get("seller_type", "private"), region=body.get("region", "")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def sa_auction_handler(request: web.Request) -> web.Response:
    try:
        auctions = _suite().auctions
        if request.method == "GET":
            aid = request.rel_url.query.get("auction_id")
            if aid:
                return json_response(auctions.analytics(aid))
            return json_response(auctions.status())
        body = await _read_json(request)
        action = body.get("action", "create")
        if action == "bid":
            return json_response(
                auctions.place_bid(
                    auction_id=body.get("auction_id", ""),
                    bidder_id=body.get("bidder_id", ""),
                    amount=float(body.get("amount", 0) or 0),
                    proxy_max=body.get("proxy_max"),
                ),
                status=201,
            )
        if action == "close":
            return json_response(auctions.close_auction(body.get("auction_id", "")))
        return json_response(
            auctions.create_auction(
                listing_id=body.get("listing_id", ""),
                mode=body.get("mode", "timed"),
                reserve_price=float(body.get("reserve_price", 0) or 0),
                start_price=float(body.get("start_price", 0) or 0),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def sa_pricing_handler(request: web.Request) -> web.Response:
    try:
        pricing = _suite().pricing
        if request.method == "GET":
            return json_response(pricing.status())
        body = await _read_json(request)
        return json_response(
            pricing.quote(
                vin=body.get("vin", ""),
                make=body.get("make", ""),
                model=body.get("model", ""),
                year=body.get("year"),
                mileage=int(body.get("mileage", 50000) or 50000),
                base_market=float(body.get("base_market", 18000) or 18000),
                region=body.get("region", "EU"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def sa_network_handler(request: web.Request) -> web.Response:
    try:
        network = _suite().network
        if request.method == "GET":
            return json_response(network.status())
        body = await _read_json(request)
        action = body.get("action", "dealer")
        if action == "trade":
            return json_response(
                network.publish_trade_listing(
                    direction=body.get("direction", "export"),
                    vin=body.get("vin", ""),
                    origin_country=body.get("origin_country", ""),
                    destination_country=body.get("destination_country", ""),
                    price=float(body.get("price", 0) or 0),
                ),
                status=201,
            )
        if action == "shipping":
            return json_response(
                network.add_shipping_route(origin=body.get("origin", ""), destination=body.get("destination", ""), carrier=body.get("carrier", "")),
                status=201,
            )
        if action == "regulations":
            return json_response(network.country_regulations(body.get("country", "")), status=201)
        return json_response(
            network.register_dealer(name=body.get("name", ""), country=body.get("country", ""), role=body.get("role", "dealer")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def sa_matching_handler(request: web.Request) -> web.Response:
    try:
        matching = _suite().matching
        if request.method == "GET":
            return json_response(matching.status())
        body = await _read_json(request)
        return json_response(
            matching.match(
                buyer_region=body.get("buyer_region", ""),
                make=body.get("make", ""),
                budget=float(body.get("budget", 0) or 0),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def sa_bi_handler(request: web.Request) -> web.Response:
    try:
        bi = _suite().bi
        if request.method == "GET":
            rtype = request.rel_url.query.get("type", "market")
            return json_response(bi.report(report_type=rtype))
        body = await _read_json(request)
        return json_response(bi.report(report_type=body.get("report_type", "market")), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def sa_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dash = _suite().dashboard
        if request.method == "GET":
            return json_response(dash.render(dashboard_type=request.rel_url.query.get("type", "marketplace")))
        body = await _read_json(request)
        return json_response(dash.render(dashboard_type=body.get("dashboard_type", "marketplace")), status=201)
    except Exception as exc:
        return _handle_error(exc)
