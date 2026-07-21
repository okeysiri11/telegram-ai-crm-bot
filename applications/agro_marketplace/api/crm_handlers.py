# CRM / Marketplace / Trading / Negotiation API handlers — Sprint 8.3.

from __future__ import annotations

from aiohttp import web

from applications.agro_marketplace import agro_marketplace
from applications.agro_marketplace.api.middleware import error_response, json_response
from applications.agro_marketplace.marketplace.models import (
    AgriculturalLead,
    BuyerProfile,
    CRMContactEntry,
    CRMTask,
    ExporterProfile,
    FarmerProfile,
    MarketplaceDeal,
    MarketplaceOrder,
    PriceRequest,
    PurchaseRequest,
    SalesOffer,
    SupplierProfile,
    TradingSession,
)
from applications.agro_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.agro_marketplace.shared.models import MarketplaceListing


# --- CRM ---


async def crm_metrics_handler(_request: web.Request) -> web.Response:
    return json_response(agro_marketplace.crm_engine.metrics())


async def crm_register_farmer_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        profile = await agro_marketplace.crm_engine.register_farmer(
            FarmerProfile(
                name=data.get("name", ""),
                email=data.get("email", ""),
                phone=data.get("phone", ""),
                country=data.get("country", ""),
                region=data.get("region", ""),
                crops=list(data.get("crops", [])),
                certifications=list(data.get("certifications", [])),
                farmer_id=data.get("farmer_id", ""),
            )
        )
        return json_response(profile.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def crm_list_farmers_handler(_request: web.Request) -> web.Response:
    return json_response({"items": [p.to_dict() for p in agro_marketplace.crm_engine.list_farmer_profiles()]})


async def crm_register_buyer_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        profile = await agro_marketplace.crm_engine.register_buyer(
            BuyerProfile(
                name=data.get("name", ""),
                email=data.get("email", ""),
                buyer_type=data.get("buyer_type", "processor"),
                country=data.get("country", ""),
                preferred_crops=list(data.get("preferred_crops", [])),
                budget_max=float(data.get("budget_max", 0)),
                buyer_id=data.get("buyer_id", ""),
            )
        )
        return json_response(profile.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def crm_list_buyers_handler(_request: web.Request) -> web.Response:
    return json_response({"items": [p.to_dict() for p in agro_marketplace.crm_engine.list_buyer_profiles()]})


async def crm_register_supplier_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        profile = agro_marketplace.crm_engine.register_supplier(
            SupplierProfile(
                name=data.get("name", ""),
                email=data.get("email", ""),
                category=data.get("category", "inputs"),
                country=data.get("country", ""),
                products=list(data.get("products", [])),
                supplier_id=data.get("supplier_id", ""),
            )
        )
        return json_response(profile.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def crm_list_suppliers_handler(_request: web.Request) -> web.Response:
    return json_response({"items": [p.to_dict() for p in agro_marketplace.crm_engine.list_supplier_profiles()]})


async def crm_register_exporter_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        profile = agro_marketplace.exporters.register(
            ExporterProfile(
                name=data.get("name", ""),
                email=data.get("email", ""),
                country=data.get("country", ""),
                destination_markets=list(data.get("destination_markets", [])),
                licenses=list(data.get("licenses", [])),
                exporter_id=data.get("exporter_id", ""),
            )
        )
        return json_response(profile.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def crm_list_exporters_handler(_request: web.Request) -> web.Response:
    return json_response({"items": [p.to_dict() for p in agro_marketplace.exporters.list_exporters()]})


async def crm_create_lead_handler(request: web.Request) -> web.Response:
    data = await request.json()
    lead = await agro_marketplace.crm_engine.create_lead(
        AgriculturalLead(
            name=data.get("name", ""),
            email=data.get("email", ""),
            role=data.get("role", "buyer"),
            source=data.get("source", "marketplace"),
            crop_interest=data.get("crop_interest", ""),
            region=data.get("region", ""),
            notes=data.get("notes", ""),
        )
    )
    return json_response(lead.to_dict(), status=201)


async def crm_list_leads_handler(_request: web.Request) -> web.Response:
    return json_response({"items": [l.to_dict() for l in agro_marketplace.crm_engine.list_leads()]})


async def crm_assign_lead_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        lead = await agro_marketplace.crm_engine.assign_lead(
            request.match_info["lead_id"],
            data.get("assignee_id", ""),
        )
        return json_response(lead.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def crm_qualify_lead_handler(request: web.Request) -> web.Response:
    try:
        lead = agro_marketplace.crm_engine.qualify_lead(request.match_info["lead_id"])
        return json_response(lead.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def crm_contact_handler(request: web.Request) -> web.Response:
    data = await request.json()
    entry = agro_marketplace.crm_engine.add_contact(
        CRMContactEntry(
            profile_id=data.get("profile_id", ""),
            profile_type=data.get("profile_type", "buyer"),
            channel=data.get("channel", "email"),
            subject=data.get("subject", ""),
            body=data.get("body", ""),
            direction=data.get("direction", "outbound"),
        )
    )
    return json_response(entry.to_dict(), status=201)


async def crm_timeline_handler(request: web.Request) -> web.Response:
    items = agro_marketplace.crm_engine.timeline(request.match_info["profile_id"])
    return json_response({"items": [i.to_dict() for i in items]})


async def crm_create_task_handler(request: web.Request) -> web.Response:
    data = await request.json()
    task = agro_marketplace.crm_engine.create_task(
        CRMTask(
            title=data.get("title", ""),
            related_id=data.get("related_id", ""),
            related_type=data.get("related_type", "lead"),
            assignee_id=data.get("assignee_id", ""),
            due_at=float(data.get("due_at", 0)),
        )
    )
    return json_response(task.to_dict(), status=201)


async def crm_list_tasks_handler(request: web.Request) -> web.Response:
    items = agro_marketplace.crm_engine.list_tasks(assignee_id=request.query.get("assignee_id") or None)
    return json_response({"items": [t.to_dict() for t in items]})


# --- Marketplace ---


async def marketplace_metrics_handler(_request: web.Request) -> web.Response:
    return json_response(agro_marketplace.marketplace.metrics())


async def marketplace_listing_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    listing = agro_marketplace.marketplace.create_listing(
        MarketplaceListing(
            product_id=data.get("product_id", ""),
            title=data.get("title", ""),
            description=data.get("description", ""),
        )
    )
    return json_response(listing.to_dict(), status=201)


async def marketplace_listings_handler(_request: web.Request) -> web.Response:
    return json_response({"items": [l.to_dict() for l in agro_marketplace.marketplace.list_listings()]})


async def marketplace_request_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        req = agro_marketplace.marketplace.create_purchase_request(
            PurchaseRequest(
                buyer_id=data.get("buyer_id", ""),
                crop_id=data.get("crop_id", ""),
                product_id=data.get("product_id", ""),
                quantity=float(data.get("quantity", 0)),
                max_price=float(data.get("max_price", 0)),
                region=data.get("region", ""),
                notes=data.get("notes", ""),
            )
        )
        return json_response(req.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def marketplace_requests_handler(_request: web.Request) -> web.Response:
    return json_response({"items": [r.to_dict() for r in agro_marketplace.marketplace.list_purchase_requests()]})


async def marketplace_offer_publish_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        offer = await agro_marketplace.offers.publish(
            SalesOffer(
                seller_id=data.get("seller_id", ""),
                seller_role=data.get("seller_role", "farmer"),
                product_id=data.get("product_id", ""),
                crop_id=data.get("crop_id", ""),
                listing_id=data.get("listing_id", ""),
                quantity=float(data.get("quantity", 0)),
                price=float(data.get("price", 0)),
                region=data.get("region", ""),
            )
        )
        return json_response(offer.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def marketplace_offers_handler(_request: web.Request) -> web.Response:
    return json_response({"items": [o.to_dict() for o in agro_marketplace.offers.list_offers()]})


async def marketplace_match_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        result = await agro_marketplace.marketplace.match_offer(
            data.get("offer_id", ""),
            data.get("request_id"),
        )
        return json_response(result)
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def marketplace_opportunities_handler(_request: web.Request) -> web.Response:
    return json_response({"items": agro_marketplace.marketplace.opportunities()})


async def marketplace_deal_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    deal = agro_marketplace.marketplace.create_deal(
        MarketplaceDeal(
            order_id=data.get("order_id", ""),
            contract_id=data.get("contract_id", ""),
            buyer_id=data.get("buyer_id", ""),
            seller_id=data.get("seller_id", ""),
            amount=float(data.get("amount", 0)),
            currency=data.get("currency", "USD"),
        )
    )
    return json_response(deal.to_dict(), status=201)


async def marketplace_deal_complete_handler(request: web.Request) -> web.Response:
    try:
        deal = await agro_marketplace.marketplace.complete_trade(request.match_info["deal_id"])
        return json_response(deal.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


# --- Trading ---


async def trading_rfq_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        rfq = agro_marketplace.trading.create_rfq(
            PriceRequest(
                buyer_id=data.get("buyer_id", ""),
                product_id=data.get("product_id", ""),
                crop_id=data.get("crop_id", ""),
                quantity=float(data.get("quantity", 0)),
                target_price=float(data.get("target_price", 0)),
            )
        )
        return json_response(rfq.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def trading_rfq_list_handler(_request: web.Request) -> web.Response:
    return json_response({"items": [r.to_dict() for r in agro_marketplace.trading.list_rfqs()]})


async def trading_rfq_respond_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        rfq = agro_marketplace.trading.respond_to_rfq(
            request.match_info["rfq_id"],
            data.get("offer_id", ""),
        )
        return json_response(rfq.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def trading_session_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    session = agro_marketplace.trading.open_session(
        TradingSession(
            buyer_id=data.get("buyer_id", ""),
            seller_id=data.get("seller_id", ""),
            product_id=data.get("product_id", ""),
        )
    )
    return json_response(session.to_dict(), status=201)


async def trading_history_handler(_request: web.Request) -> web.Response:
    return json_response(agro_marketplace.trading.trade_history())


async def trading_price_recommend_handler(request: web.Request) -> web.Response:
    try:
        result = await agro_marketplace.trading.price_recommendation(request.match_info["offer_id"])
        return json_response(result)
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def trading_contract_prepare_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        contract = await agro_marketplace.contracts.prepare(
            order_id=data.get("order_id", ""),
            negotiation_id=data.get("negotiation_id", ""),
            parties=data.get("parties"),
            terms=data.get("terms"),
        )
        return json_response(contract.to_dict(), status=201)
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def trading_contract_sign_handler(request: web.Request) -> web.Response:
    try:
        contract = await agro_marketplace.contracts.sign(request.match_info["contract_id"])
        return json_response(contract.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


# --- Negotiation ---


async def negotiation_start_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        negotiation = await agro_marketplace.negotiations.start(
            offer_id=data.get("offer_id", ""),
            buyer_id=data.get("buyer_id", ""),
            seller_id=data.get("seller_id", ""),
            price=float(data.get("price", 0)),
            quantity=float(data.get("quantity", 0)),
            request_id=data.get("request_id", ""),
            delivery_terms=data.get("delivery_terms", ""),
        )
        return json_response(negotiation.to_dict(), status=201)
    except (NotFoundError, ValidationError) as exc:
        status = 404 if isinstance(exc, NotFoundError) else 400
        return error_response(str(exc), status=status)


async def negotiation_list_handler(_request: web.Request) -> web.Response:
    return json_response({"items": [n.to_dict() for n in agro_marketplace.negotiations.list_negotiations()]})


async def negotiation_counter_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        negotiation = await agro_marketplace.negotiations.counter_offer(
            request.match_info["negotiation_id"],
            price=data.get("price"),
            quantity=data.get("quantity"),
            delivery_terms=data.get("delivery_terms"),
            actor_id=data.get("actor_id", ""),
        )
        return json_response(negotiation.to_dict())
    except (NotFoundError, ValidationError) as exc:
        status = 404 if isinstance(exc, NotFoundError) else 400
        return error_response(str(exc), status=status)


async def negotiation_agree_handler(request: web.Request) -> web.Response:
    try:
        negotiation = await agro_marketplace.negotiations.agree(request.match_info["negotiation_id"])
        return json_response(negotiation.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def negotiation_assist_handler(request: web.Request) -> web.Response:
    data = {}
    if request.method == "POST":
        try:
            data = await request.json()
        except Exception:
            data = {}
    try:
        suggestion = await agro_marketplace.negotiations.assistant_suggestion(
            request.match_info["negotiation_id"],
            target_price=float(data.get("target_price", 0)),
        )
        return json_response(suggestion)
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


# --- Orders ---


async def order_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        order = agro_marketplace.marketplace_orders.create(
            MarketplaceOrder(
                buyer_id=data.get("buyer_id", ""),
                seller_id=data.get("seller_id", ""),
                product_id=data.get("product_id", ""),
                offer_id=data.get("offer_id", ""),
                negotiation_id=data.get("negotiation_id", ""),
                quantity=float(data.get("quantity", 0)),
                unit_price=float(data.get("unit_price", 0)),
                currency=data.get("currency", "USD"),
            )
        )
        return json_response(order.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def order_list_handler(_request: web.Request) -> web.Response:
    return json_response({"items": [o.to_dict() for o in agro_marketplace.marketplace_orders.list_orders()]})


async def order_confirm_handler(request: web.Request) -> web.Response:
    try:
        order = await agro_marketplace.marketplace_orders.confirm(request.match_info["order_id"])
        return json_response(order.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


# --- AI recommendations ---


async def recommend_buyers_handler(request: web.Request) -> web.Response:
    try:
        offer = agro_marketplace.offers.get(request.match_info["offer_id"])
        items = await agro_marketplace.trading_ai.recommend_buyers(
            offer,
            agro_marketplace.crm_engine.list_buyer_profiles(),
        )
        return json_response({"items": items})
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def recommend_suppliers_handler(request: web.Request) -> web.Response:
    request_id = request.match_info["request_id"]
    req = next(
        (r for r in agro_marketplace.marketplace.list_purchase_requests(status=None) if r.request_id == request_id),
        None,
    )
    if req is None:
        return error_response(f"PurchaseRequest not found: {request_id}", status=404)
    items = await agro_marketplace.trading_ai.recommend_suppliers(
        req,
        agro_marketplace.crm_engine.list_supplier_profiles(),
    )
    return json_response({"items": items})
