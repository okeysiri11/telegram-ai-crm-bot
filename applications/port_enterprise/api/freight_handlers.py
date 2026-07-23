"""API handlers — Freight Marketplace (Sprint 15.6)."""

from __future__ import annotations

from aiohttp import web

from applications.port_enterprise import port_enterprise
from applications.port_enterprise.api.middleware import json_response
from applications.port_enterprise.shared.exceptions import NotFoundError, ValidationError


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
    return port_enterprise.freight_marketplace


async def fm_health_handler(request: web.Request) -> web.Response:
    health = port_enterprise.health()
    return json_response(
        {
            "status": "ok",
            "application_version": health["application_version"],
            "enterprise_foundation": health.get("enterprise_foundation"),
            "freight_marketplace_ready": health.get("freight_marketplace_ready"),
            "freight_exchange_ready": health.get("freight_exchange_ready"),
            "global_logistics_network_ready": health.get("global_logistics_network_ready"),
            "ai_logistics_marketplace_ready": health.get("ai_logistics_marketplace_ready"),
            "carrier_platform_ready": health.get("carrier_platform_ready"),
            "suite": _suite().status(),
        }
    )


async def fm_bootstrap_handler(request: web.Request) -> web.Response:
    try:
        return json_response(_suite().bootstrap(), status=201)
    except Exception as exc:
        return _handle_error(exc)


async def fm_marketplace_handler(request: web.Request) -> web.Response:
    try:
        mp = _suite().marketplace
        if request.method == "GET":
            return json_response(mp.status())
        body = await _read_json(request)
        action = body.get("action", "list")
        if action == "available":
            return json_response(
                mp.available_freight(
                    corridor=body.get("corridor", ""),
                    capacity_teu=float(body.get("capacity_teu", 0) or 0),
                ),
                status=201,
            )
        if action == "request":
            return json_response(
                mp.transport_request(
                    shipper=body.get("shipper", ""),
                    origin=body.get("origin", ""),
                    destination=body.get("destination", ""),
                    teu=float(body.get("teu", 1) or 1),
                ),
                status=201,
            )
        if action == "match":
            return json_response(
                mp.instant_match(
                    request_id=body.get("request_id", ""),
                    carrier_id=body.get("carrier_id", ""),
                    score=float(body.get("score", 0.9) or 0.9),
                ),
                status=201,
            )
        if action == "search":
            return json_response(
                mp.search(query=body.get("query", ""), mode=body.get("mode", "all")),
                status=201,
            )
        if action == "analytics":
            return json_response(mp.analytics(period=body.get("period", "monthly")), status=201)
        return json_response(
            mp.list_cargo(
                title=body.get("title", ""),
                origin=body.get("origin", ""),
                destination=body.get("destination", ""),
                teu=float(body.get("teu", 1) or 1),
                price=float(body.get("price", 0) or 0),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def fm_carriers_handler(request: web.Request) -> web.Response:
    try:
        carriers = _suite().carriers
        if request.method == "GET":
            return json_response(carriers.status())
        body = await _read_json(request)
        action = body.get("action", "register")
        if action == "rate":
            return json_response(
                carriers.rate(
                    body.get("carrier_id", ""),
                    score=float(body.get("score", 0) or 0),
                    comment=body.get("comment", ""),
                ),
                status=201,
            )
        return json_response(
            carriers.register(
                name=body.get("name", ""),
                carrier_type=body.get("carrier_type", "shipping"),
                country=body.get("country", ""),
                scac=body.get("scac", ""),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def fm_exchange_handler(request: web.Request) -> web.Response:
    try:
        exchange = _suite().exchange
        if request.method == "GET":
            return json_response(exchange.status())
        body = await _read_json(request)
        action = body.get("action", "spot")
        if action == "contract":
            return json_response(
                exchange.contract(
                    shipper=body.get("shipper", ""),
                    carrier_id=body.get("carrier_id", ""),
                    corridor=body.get("corridor", ""),
                    rate=float(body.get("rate", 0) or 0),
                    term_months=int(body.get("term_months", 12) or 12),
                ),
                status=201,
            )
        if action == "tender":
            return json_response(
                exchange.tender(
                    title=body.get("title", ""),
                    corridor=body.get("corridor", ""),
                    teu=float(body.get("teu", 0) or 0),
                ),
                status=201,
            )
        if action == "bid":
            return json_response(
                exchange.bid(
                    tender_id=body.get("tender_id", ""),
                    carrier_id=body.get("carrier_id", ""),
                    price=float(body.get("price", 0) or 0),
                ),
                status=201,
            )
        if action == "auction":
            return json_response(
                exchange.auction(
                    spot_id=body.get("spot_id", ""),
                    start_price=float(body.get("start_price", 0) or 0),
                ),
                status=201,
            )
        if action == "negotiate":
            return json_response(
                exchange.negotiate(
                    subject_ref=body.get("subject_ref", ""),
                    offer=float(body.get("offer", 0) or 0),
                    counter=float(body.get("counter", 0) or 0),
                ),
                status=201,
            )
        if action == "book":
            return json_response(
                exchange.book(
                    shipper=body.get("shipper", ""),
                    carrier_id=body.get("carrier_id", ""),
                    origin=body.get("origin", ""),
                    destination=body.get("destination", ""),
                    price=float(body.get("price", 0) or 0),
                ),
                status=201,
            )
        return json_response(
            exchange.spot(
                corridor=body.get("corridor", ""),
                teu=float(body.get("teu", 0) or 0),
                ask_price=float(body.get("ask_price", 0) or 0),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def fm_network_handler(request: web.Request) -> web.Response:
    try:
        network = _suite().network
        if request.method == "GET":
            return json_response(network.status())
        body = await _read_json(request)
        action = body.get("action", "partner")
        if action == "port":
            return json_response(
                network.register_port_node(name=body.get("name", ""), unlocode=body.get("unlocode", "")),
                status=201,
            )
        if action == "warehouse":
            return json_response(
                network.register_warehouse_node(name=body.get("name", ""), region=body.get("region", "")),
                status=201,
            )
        if action == "distribution":
            return json_response(
                network.register_distribution_node(name=body.get("name", ""), region=body.get("region", "")),
                status=201,
            )
        if action == "corridor":
            modes = body.get("modes") if isinstance(body.get("modes"), list) else None
            return json_response(
                network.register_corridor(name=body.get("name", ""), modes=modes),
                status=201,
            )
        if action == "route":
            return json_response(
                network.register_route(
                    origin=body.get("origin", ""),
                    destination=body.get("destination", ""),
                    mode=body.get("mode", "sea"),
                ),
                status=201,
            )
        if action == "performance":
            return json_response(
                network.partner_performance(
                    partner_id=body.get("partner_id", ""),
                    otif_pct=float(body.get("otif_pct", 0) or 0),
                    score=float(body.get("score", 0) or 0),
                ),
                status=201,
            )
        return json_response(
            network.register_partner(
                name=body.get("name", ""),
                country=body.get("country", ""),
                role=body.get("role", "logistics"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def fm_collaboration_handler(request: web.Request) -> web.Response:
    try:
        collab = _suite().collaboration
        if request.method == "GET":
            return json_response(collab.status())
        body = await _read_json(request)
        action = body.get("action", "workspace")
        if action == "customer_portal":
            return json_response(
                collab.customer_portal(
                    customer=body.get("customer", ""),
                    workspace_id=body.get("workspace_id", ""),
                ),
                status=201,
            )
        if action == "carrier_portal":
            return json_response(
                collab.carrier_portal(
                    carrier_id=body.get("carrier_id", ""),
                    workspace_id=body.get("workspace_id", ""),
                ),
                status=201,
            )
        if action == "document":
            return json_response(
                collab.share_document(
                    workspace_id=body.get("workspace_id", ""),
                    title=body.get("title", ""),
                    doc_type=body.get("doc_type", "other"),
                ),
                status=201,
            )
        if action == "notify":
            return json_response(
                collab.notify(
                    workspace_id=body.get("workspace_id", ""),
                    message=body.get("message", ""),
                    channel=body.get("channel", "realtime"),
                ),
                status=201,
            )
        if action == "collaborate":
            return json_response(
                collab.collaborate(
                    workspace_id=body.get("workspace_id", ""),
                    actor=body.get("actor", ""),
                    note=body.get("note", ""),
                ),
                status=201,
            )
        return json_response(
            collab.workspace(shipment_ref=body.get("shipment_ref", ""), title=body.get("title", "")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def fm_ai_handler(request: web.Request) -> web.Response:
    try:
        ai = _suite().ai
        if request.method == "GET":
            return json_response(ai.status())
        body = await _read_json(request)
        action = body.get("action", "recommend")
        if action == "match":
            return json_response(
                ai.match_freight(
                    request_id=body.get("request_id", ""),
                    carrier_id=body.get("carrier_id", ""),
                ),
                status=201,
            )
        if action == "pricing":
            return json_response(
                ai.dynamic_pricing(
                    corridor=body.get("corridor", ""),
                    baseline=float(body.get("baseline", 0) or 0),
                ),
                status=201,
            )
        if action == "capacity":
            return json_response(
                ai.capacity_predict(
                    corridor=body.get("corridor", ""),
                    teu=float(body.get("teu", 0) or 0),
                ),
                status=201,
            )
        if action == "demand":
            return json_response(
                ai.demand_forecast(
                    corridor=body.get("corridor", ""),
                    days=int(body.get("days", 30) or 30),
                    baseline=float(body.get("baseline", 1000) or 1000),
                ),
                status=201,
            )
        if action == "route":
            return json_response(
                ai.optimize_route(
                    origin=body.get("origin", ""),
                    destination=body.get("destination", ""),
                    mode=body.get("mode", "multimodal"),
                ),
                status=201,
            )
        if action == "cost":
            return json_response(
                ai.optimize_cost(
                    booking_ref=body.get("booking_ref", ""),
                    baseline_cost=float(body.get("baseline_cost", 0) or 0),
                ),
                status=201,
            )
        if action == "fraud":
            return json_response(
                ai.fraud_detect(
                    subject_ref=body.get("subject_ref", ""),
                    anomaly_score=float(body.get("anomaly_score", 0) or 0),
                ),
                status=201,
            )
        return json_response(
            ai.recommend_carrier(
                origin=body.get("origin", ""),
                destination=body.get("destination", ""),
                mode=body.get("mode", "sea"),
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def fm_dashboard_handler(request: web.Request) -> web.Response:
    try:
        dash = _suite().dashboard
        if request.method == "GET":
            dtype = request.rel_url.query.get("type", "marketplace")
            return json_response(dash.render(dashboard_type=dtype))
        body = await _read_json(request)
        return json_response(
            dash.render(dashboard_type=body.get("dashboard_type", "marketplace")),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)


async def fm_knowledge_handler(request: web.Request) -> web.Response:
    try:
        knowledge = _suite().knowledge
        if request.method == "GET":
            return json_response(knowledge.status())
        body = await _read_json(request)
        return json_response(
            knowledge.publish(
                registry_type=body.get("registry_type", "marketplace"),
                key=body.get("key", ""),
                payload=body.get("payload") if isinstance(body.get("payload"), dict) else {},
            ),
            status=201,
        )
    except Exception as exc:
        return _handle_error(exc)
