# AI Sales API handlers — Sprint 6.4.

from __future__ import annotations

from aiohttp import web

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.ai_sales.models import AgentType, ConversationChannel, KnowledgeArticle
from applications.auto_marketplace.api.middleware import json_response
from applications.auto_marketplace.crm.models import CRMLead, CRMRole, CustomerProfile, LeadSource
from applications.auto_marketplace.shared.exceptions import AuthorizationError, AutoMarketplaceError, NotFoundError


def _check_ai_perm(request: web.Request, permission: str = "crm.read") -> None:
    principal = request.get("principal") or {}
    role = principal.get("role", CRMRole.AI_AGENT.value)
    if not auto_marketplace.crm_engine.security.authorize(role, permission):
        if role != CRMRole.AI_AGENT.value and not auto_marketplace.crm_engine.security.authorize(role, "crm.read"):
            raise AuthorizationError(f"Permission denied: {permission}")


async def ai_sales_metrics_handler(_request: web.Request) -> web.Response:
    return json_response(auto_marketplace.ai_sales_engine.metrics())


async def dispatch_agent_handler(request: web.Request) -> web.Response:
    _check_ai_perm(request)
    data = await request.json()
    agent_type = data.get("agent_type", AgentType.CUSTOMER_ASSISTANT.value)
    context = data.get("context", {})
    result = await auto_marketplace.ai_sales_engine.dispatch_agent(agent_type, context)
    return json_response(result)


async def customer_intelligence_handler(request: web.Request) -> web.Response:
    _check_ai_perm(request)
    customer_id = request.match_info["customer_id"]
    profile = await auto_marketplace.ai_sales_engine.intelligence.analyze_profile(customer_id)
    return json_response(profile.to_dict())


async def customer_intent_handler(request: web.Request) -> web.Response:
    _check_ai_perm(request)
    customer_id = request.match_info["customer_id"]
    intent = await auto_marketplace.ai_sales_engine.intelligence.purchase_intent(customer_id)
    return json_response(intent)


async def customer_communication_history_handler(request: web.Request) -> web.Response:
    _check_ai_perm(request)
    customer_id = request.match_info["customer_id"]
    history = auto_marketplace.ai_sales_engine.intelligence.communication_history(customer_id)
    return json_response({"items": history})


async def recommendations_personalized_handler(request: web.Request) -> web.Response:
    _check_ai_perm(request)
    customer_id = request.match_info["customer_id"]
    limit = int(request.query.get("limit", "5"))
    items = await auto_marketplace.ai_sales_engine.recommendations.personalized(customer_id, limit=limit)
    return json_response({"items": [i.to_dict() for i in items]})


async def recommendations_alternatives_handler(request: web.Request) -> web.Response:
    _check_ai_perm(request)
    vehicle_id = request.match_info["vehicle_id"]
    items = await auto_marketplace.ai_sales_engine.recommendations.alternatives(vehicle_id)
    return json_response({"items": [i.to_dict() for i in items]})


async def recommendations_upsell_handler(request: web.Request) -> web.Response:
    _check_ai_perm(request)
    data = await request.json()
    items = await auto_marketplace.ai_sales_engine.recommendations.upsell(
        data.get("customer_id", ""),
        data.get("vehicle_id", ""),
    )
    return json_response({"items": [i.to_dict() for i in items]})


async def recommendations_cross_sell_handler(request: web.Request) -> web.Response:
    _check_ai_perm(request)
    customer_id = request.match_info["customer_id"]
    items = await auto_marketplace.ai_sales_engine.recommendations.cross_sell(customer_id)
    return json_response({"items": [i.to_dict() for i in items]})


async def recommendations_trade_in_handler(request: web.Request) -> web.Response:
    _check_ai_perm(request)
    customer_id = request.match_info["customer_id"]
    result = await auto_marketplace.ai_sales_engine.recommendations.trade_in_suggestions(customer_id)
    return json_response(result)


async def recommendations_accessories_handler(request: web.Request) -> web.Response:
    _check_ai_perm(request)
    vehicle_id = request.match_info["vehicle_id"]
    items = await auto_marketplace.ai_sales_engine.recommendations.accessory_recommendations(vehicle_id)
    return json_response({"items": items})


async def lead_intelligence_handler(request: web.Request) -> web.Response:
    _check_ai_perm(request)
    lead_id = request.match_info["lead_id"]
    report = await auto_marketplace.ai_sales_engine.leads.analyze_lead(lead_id)
    return json_response(report.to_dict())


async def qualify_lead_ai_handler(request: web.Request) -> web.Response:
    _check_ai_perm(request, "leads.manage")
    data = await request.json() if request.can_read_body else {}
    report = await auto_marketplace.ai_sales_engine.leads.qualify_lead(
        request.match_info["lead_id"],
        agent_id=data.get("agent_id", "ai-agent"),
    )
    return json_response(report.to_dict())


async def start_conversation_handler(request: web.Request) -> web.Response:
    _check_ai_perm(request)
    data = await request.json()
    channel = ConversationChannel(data.get("channel", "chat"))
    session = await auto_marketplace.ai_sales_engine.conversations.start_session(
        data["customer_id"],
        channel=channel,
        agent_type=data.get("agent_type", AgentType.CUSTOMER_ASSISTANT.value),
    )
    return json_response(session.to_dict(), status=201)


async def append_conversation_turn_handler(request: web.Request) -> web.Response:
    _check_ai_perm(request)
    data = await request.json()
    session = await auto_marketplace.ai_sales_engine.conversations.append_turn(
        request.match_info["session_id"],
        role=data.get("role", "user"),
        content=data.get("content", ""),
    )
    suggestion = await auto_marketplace.ai_sales_engine.conversations.suggest_response(session.session_id)
    return json_response({**session.to_dict(), "suggested_response": suggestion})


async def summarize_conversation_handler(request: web.Request) -> web.Response:
    _check_ai_perm(request)
    summary = await auto_marketplace.ai_sales_engine.conversations.summarize(request.match_info["session_id"])
    return json_response({"summary": summary})


async def conversation_context_handler(request: web.Request) -> web.Response:
    _check_ai_perm(request)
    ctx = auto_marketplace.ai_sales_engine.conversations.multi_channel_context(request.match_info["customer_id"])
    return json_response(ctx)


async def generate_offer_handler(request: web.Request) -> web.Response:
    _check_ai_perm(request, "deals.write")
    data = await request.json()
    offer = await auto_marketplace.ai_sales_engine.negotiation.generate_offer(
        data["customer_id"],
        data["vehicle_id"],
        dealer_id=data.get("dealer_id", ""),
        amount=float(data.get("amount", 0)),
        trade_in_value=float(data.get("trade_in_value", 0)),
        accessories=data.get("accessories"),
    )
    return json_response(offer.to_dict(), status=201)


async def negotiate_offer_handler(request: web.Request) -> web.Response:
    _check_ai_perm(request, "deals.write")
    data = await request.json()
    result = await auto_marketplace.ai_sales_engine.negotiation.negotiate_terms(
        request.match_info["offer_id"],
        float(data.get("customer_counter", 0)),
    )
    return json_response(result)


async def knowledge_search_handler(request: web.Request) -> web.Response:
    _check_ai_perm(request)
    query = request.query.get("q", "")
    category = request.query.get("category", "")
    items = auto_marketplace.ai_sales_engine.knowledge.search(query, category=category)
    return json_response({"items": [a.to_dict() for a in items]})


async def schedule_follow_up_ai_handler(request: web.Request) -> web.Response:
    _check_ai_perm(request)
    data = await request.json()
    from events.publisher import publish
    from applications.auto_marketplace.ai_sales.events import FollowUpScheduledEvent

    result = await auto_marketplace.ai_sales_engine.workflow.schedule_follow_up(
        data["lead_id"],
        data["customer_id"],
        delay_hours=int(data.get("delay_hours", 24)),
        channel=data.get("channel", "email"),
    )
    await publish(
        FollowUpScheduledEvent(
            lead_id=data["lead_id"],
            customer_id=data["customer_id"],
            scheduled_at=result.get("scheduled_at", 0),
            channel=result.get("channel", "email"),
        )
    )
    return json_response(result, status=201)


async def onboard_customer_handler(request: web.Request) -> web.Response:
    _check_ai_perm(request)
    data = await request.json()
    result = await auto_marketplace.ai_sales_engine.workflow.onboard_customer(data["customer_id"])
    return json_response(result, status=201)


async def create_lead_for_ai_test_handler(request: web.Request) -> web.Response:
    """Helper: create customer + lead for AI tests."""
    _check_ai_perm(request, "leads.write")
    data = await request.json()
    profile = await auto_marketplace.crm_engine.customers.create(
        CustomerProfile(
            first_name=data.get("first_name", "AI"),
            email=data.get("email", "ai@test.com"),
            preferences=data.get("preferences", {"budget_max": 40000, "make": "Toyota"}),
        )
    )
    lead = await auto_marketplace.crm_engine.leads.create(
        CRMLead(
            customer_id=profile.customer_id,
            vehicle_id=data.get("vehicle_id", ""),
            dealer_id=data.get("dealer_id", "d1"),
            source=LeadSource.AI_AGENT,
        ),
        profile,
    )
    return json_response({"customer": profile.to_dict(), "lead": lead.to_dict()}, status=201)
