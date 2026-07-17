# Public API Gateway v1 — REST route handlers.

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from aiohttp import web

from api.middleware import api_context, require_api_auth
from services.pg_api_gateway_engine import ApiGatewayEngineV1
from services.pg_notification_api_engine import NotificationApiEngineV1


def _json(data: Any, *, status: int = 200) -> web.Response:
    return web.json_response(
        {"data": data, "api_version": "v1"},
        status=status,
    )


def _actor(request: web.Request) -> int:
    return api_context(request).actor_user_id


@require_api_auth
async def deals_list_handler(request: web.Request) -> web.Response:
    from services.pg_deal_workflow import DealWorkflowService

    deals = await DealWorkflowService.get_my_deals(_actor(request))
    return _json([
        {
            "id": str(d.id),
            "status": d.status,
            "client_id": str(d.client_id) if d.client_id else None,
            "manager_id": d.manager_id,
            "asset_in_type": d.asset_in_type,
            "asset_out_type": d.asset_out_type,
        }
        for d in deals
    ])


@require_api_auth
async def deals_create_handler(request: web.Request) -> web.Response:
    from services.pg_deal_workflow import DealWorkflowService

    body = await request.json()
    deal = await DealWorkflowService.create_deal(
        _actor(request),
        client_id=body.get("client_id"),
        asset_in_type=body["asset_in_type"],
        asset_in_amount=Decimal(str(body["asset_in_amount"])),
        asset_out_type=body["asset_out_type"],
        asset_out_amount=Decimal(str(body["asset_out_amount"])),
        manager_id=body.get("manager_id"),
        partner_id=body.get("partner_id"),
    )
    return _json({"id": str(deal.id), "status": deal.status}, status=201)


@require_api_auth
async def partners_list_handler(request: web.Request) -> web.Response:
    from services.pg_partner_engine import PartnerEngine

    partners = await PartnerEngine.list_partners(_actor(request))
    return _json([
        {
            "id": str(p.id),
            "company_name": p.company_name,
            "partner_type": p.partner_type,
            "status": p.status,
        }
        for p in partners
    ])


@require_api_auth
async def partners_create_handler(request: web.Request) -> web.Response:
    from services.pg_partner_engine import PartnerEngine

    body = await request.json()
    partner = await PartnerEngine.create_partner(
        _actor(request),
        partner_type=body["partner_type"],
        company_name=body["company_name"],
        contact_person=body.get("contact_person"),
    )
    return _json({"id": str(partner.id), "company_name": partner.company_name}, status=201)


@require_api_auth
async def pricing_calculate_handler(request: web.Request) -> web.Response:
    from services.pg_pricing_engine import PricingEngineV1

    body = await request.json()
    result = await PricingEngineV1.calculate_client_price(
        asset=body["asset"],
        partner_id=uuid.UUID(body["partner_id"]) if body.get("partner_id") else None,
        manager_id=body.get("manager_id"),
        side=body.get("side", "ask"),
    )
    return _json(result)


@require_api_auth
async def fx_rates_handler(request: web.Request) -> web.Response:
    from services.pg_market_data_engine import MarketDataEngineV1

    base = request.query.get("base", "USD")
    quote = request.query.get("quote", "EUR")
    rate = await MarketDataEngineV1.get_pair_rate(
        _actor(request),
        base=base,
        quote=quote,
    )
    return _json(rate)


@require_api_auth
async def vehicles_list_handler(request: web.Request) -> web.Response:
    from services.pg_automotive_inventory_engine import AutomotiveInventoryEngineV1

    vehicles = await AutomotiveInventoryEngineV1.list_vehicles(_actor(request))
    return _json(vehicles)


@require_api_auth
async def vehicles_create_handler(request: web.Request) -> web.Response:
    from services.pg_automotive_inventory_engine import AutomotiveInventoryEngineV1

    body = await request.json()
    vehicle = await AutomotiveInventoryEngineV1.create_vehicle(
        _actor(request),
        vin=body["vin"],
        stock_number=body["stock_number"],
        make=body["make"],
        model=body["model"],
        year=int(body["year"]),
        purchase_price=Decimal(str(body["purchase_price"])) if body.get("purchase_price") else None,
        target_price=Decimal(str(body["target_price"])) if body.get("target_price") else None,
    )
    return _json(vehicle, status=201)


@require_api_auth
async def inventory_list_handler(request: web.Request) -> web.Response:
    from services.pg_automotive_inventory_engine import AutomotiveInventoryEngineV1

    status = request.query.get("status")
    vehicles = await AutomotiveInventoryEngineV1.list_vehicles(
        _actor(request),
        status=status,
    )
    return _json(vehicles)


@require_api_auth
async def orders_list_handler(request: web.Request) -> web.Response:
    from services.pg_automotive_procurement_engine import AutomotiveProcurementEngineV1

    orders = await AutomotiveProcurementEngineV1.list_purchase_orders(_actor(request))
    return _json(orders)


@require_api_auth
async def orders_create_handler(request: web.Request) -> web.Response:
    from services.pg_automotive_procurement_engine import AutomotiveProcurementEngineV1

    body = await request.json()
    order = await AutomotiveProcurementEngineV1.create_purchase_order(
        _actor(request),
        order_number=body["order_number"],
        source=body["source"],
        make=body["make"],
        model=body["model"],
        year=int(body["year"]),
        vin=body.get("vin"),
        agreed_price=Decimal(str(body["agreed_price"])) if body.get("agreed_price") else None,
    )
    return _json(order, status=201)


@require_api_auth
async def documents_list_handler(request: web.Request) -> web.Response:
    from services.pg_document_engine import DocumentEngineV1

    document_type = request.query.get("document_type")
    docs = await DocumentEngineV1.list_documents(
        _actor(request),
        document_type=document_type,
    )
    return _json(docs)


@require_api_auth
async def documents_create_handler(request: web.Request) -> web.Response:
    from services.pg_document_engine import DocumentEngineV1

    body = await request.json()
    result = await DocumentEngineV1.generate_document(
        _actor(request),
        template_code=body["template_code"],
        title=body["title"],
        variables=body.get("variables"),
    )
    return _json(result, status=201)


@require_api_auth
async def notifications_list_handler(request: web.Request) -> web.Response:
    notifications = await NotificationApiEngineV1.list_pending(limit=100)
    return _json(notifications)


@require_api_auth
async def notifications_create_handler(request: web.Request) -> web.Response:
    body = await request.json()
    result = await NotificationApiEngineV1.create(body)
    return _json(result, status=201)


@require_api_auth
async def dealer_portal_handler(request: web.Request) -> web.Response:
    from services.pg_dealer_portal_v1 import DealerPortalV1

    tenant_id = uuid.UUID(request.query.get("tenant_id", ""))
    refresh = request.query.get("refresh", "").lower() in {"1", "true", "yes"}
    portal = await DealerPortalV1.get_portal(_actor(request), tenant_id, refresh=refresh)
    return _json(portal)


@require_api_auth
async def dealer_portal_module_handler(request: web.Request) -> web.Response:
    from services.pg_dealer_portal_v1 import DealerPortalV1

    tenant_id = uuid.UUID(request.query.get("tenant_id", ""))
    module = request.match_info["module"]
    refresh = request.query.get("refresh", "").lower() in {"1", "true", "yes"}
    data = await DealerPortalV1.get_module(_actor(request), tenant_id, module, refresh=refresh)
    return _json(data)


@require_api_auth
async def lead_marketplace_handler(request: web.Request) -> web.Response:
    from services.pg_lead_marketplace_v1 import LeadMarketplaceV1

    tenant_id = uuid.UUID(request.query.get("tenant_id", ""))
    marketplace = await LeadMarketplaceV1.get_marketplace(_actor(request), tenant_id)
    return _json(marketplace)


@require_api_auth
async def lead_marketplace_feature_handler(request: web.Request) -> web.Response:
    from services.pg_lead_marketplace_v1 import LeadMarketplaceV1

    tenant_id = uuid.UUID(request.query.get("tenant_id", ""))
    feature = request.match_info["feature"]
    data = await LeadMarketplaceV1.get_feature(_actor(request), tenant_id, feature)
    return _json(data)


@require_api_auth
async def ai_procurement_agent_handler(request: web.Request) -> web.Response:
    from services.pg_ai_procurement_agent_v1 import ProcurementAgentV1

    agent = await ProcurementAgentV1.get_agent(_actor(request))
    return _json(agent)


@require_api_auth
async def ai_procurement_agent_feature_handler(request: web.Request) -> web.Response:
    from services.pg_ai_procurement_agent_v1 import ProcurementAgentV1

    feature = request.match_info["feature"]
    data = await ProcurementAgentV1.get_feature(_actor(request), feature)
    return _json(data)


@require_api_auth
async def ai_advertising_agent_handler(request: web.Request) -> web.Response:
    from services.pg_ai_advertising_agent_v1 import AdvertisingAgentV1

    tenant_id = uuid.UUID(request.query.get("tenant_id", ""))
    agent = await AdvertisingAgentV1.get_agent(_actor(request), tenant_id)
    return _json(agent)


@require_api_auth
async def ai_advertising_agent_feature_handler(request: web.Request) -> web.Response:
    from services.pg_ai_advertising_agent_v1 import AdvertisingAgentV1

    tenant_id = uuid.UUID(request.query.get("tenant_id", ""))
    feature = request.match_info["feature"]
    data = await AdvertisingAgentV1.get_feature(_actor(request), tenant_id, feature)
    return _json(data)


@require_api_auth
async def ai_sales_agent_handler(request: web.Request) -> web.Response:
    from services.pg_ai_sales_agent_v1 import SalesAgentV1

    tenant_id = uuid.UUID(request.query.get("tenant_id", ""))
    agent = await SalesAgentV1.get_agent(_actor(request), tenant_id)
    return _json(agent)


@require_api_auth
async def ai_sales_agent_feature_handler(request: web.Request) -> web.Response:
    from services.pg_ai_sales_agent_v1 import SalesAgentV1

    tenant_id = uuid.UUID(request.query.get("tenant_id", ""))
    feature = request.match_info["feature"]
    data = await SalesAgentV1.get_feature(_actor(request), tenant_id, feature)
    return _json(data)


@require_api_auth
async def recommendation_engine_handler(request: web.Request) -> web.Response:
    from services.pg_recommendation_engine_v1 import RecommendationEngineV1Product

    tenant_id = uuid.UUID(request.query.get("tenant_id", ""))
    engine = await RecommendationEngineV1Product.get_engine(_actor(request), tenant_id)
    return _json(engine)


@require_api_auth
async def recommendation_engine_feature_handler(request: web.Request) -> web.Response:
    from services.pg_recommendation_engine_v1 import RecommendationEngineV1Product

    tenant_id = uuid.UUID(request.query.get("tenant_id", ""))
    feature = request.match_info["feature"]
    profile_id_raw = request.query.get("profile_id")
    profile_id = uuid.UUID(profile_id_raw) if profile_id_raw else None
    data = await RecommendationEngineV1Product.get_feature(
        _actor(request), tenant_id, feature, profile_id=profile_id
    )
    return _json(data)


@require_api_auth
async def communication_hub_handler(request: web.Request) -> web.Response:
    from services.pg_communication_hub_v1 import CommunicationHubV1Product

    tenant_id = uuid.UUID(request.query.get("tenant_id", ""))
    hub = await CommunicationHubV1Product.get_hub(_actor(request), tenant_id)
    return _json(hub)


@require_api_auth
async def communication_hub_feature_handler(request: web.Request) -> web.Response:
    from services.pg_communication_hub_v1 import CommunicationHubV1Product

    tenant_id = uuid.UUID(request.query.get("tenant_id", ""))
    feature = request.match_info["feature"]
    conversation_id = request.query.get("conversation_id")
    data = await CommunicationHubV1Product.get_feature(
        _actor(request), tenant_id, feature, conversation_id=conversation_id
    )
    return _json(data)


@require_api_auth
async def ai_conversation_skills_handler(request: web.Request) -> web.Response:
    from services.pg_ai_conversation_skills_v1 import AiConversationSkillsV1Product

    tenant_id = uuid.UUID(request.query.get("tenant_id", ""))
    engine = await AiConversationSkillsV1Product.get_engine(_actor(request), tenant_id)
    return _json(engine)


@require_api_auth
async def ai_conversation_skills_feature_handler(request: web.Request) -> web.Response:
    from services.pg_ai_conversation_skills_v1 import AiConversationSkillsV1Product

    tenant_id = uuid.UUID(request.query.get("tenant_id", ""))
    feature = request.match_info["feature"]
    session_ref = request.query.get("session_ref", "demo-session")
    data = await AiConversationSkillsV1Product.get_feature(
        _actor(request), tenant_id, feature, session_ref=session_ref
    )
    return _json(data)


@require_api_auth
async def deal_pipeline_handler(request: web.Request) -> web.Response:
    from services.pg_deal_pipeline_v1 import DealPipelineV1

    tenant_id = uuid.UUID(request.query.get("tenant_id", ""))
    pipeline = await DealPipelineV1.get_pipeline(_actor(request), tenant_id)
    return _json(pipeline)


@require_api_auth
async def deal_pipeline_feature_handler(request: web.Request) -> web.Response:
    from services.pg_deal_pipeline_v1 import DealPipelineV1

    tenant_id = uuid.UUID(request.query.get("tenant_id", ""))
    feature = request.match_info["feature"]
    deal_id_raw = request.query.get("deal_id")
    deal_id = uuid.UUID(deal_id_raw) if deal_id_raw else None
    data = await DealPipelineV1.get_feature(
        _actor(request),
        tenant_id,
        feature,
        deal_id=deal_id,
        from_stage=request.query.get("from_stage"),
        to_stage=request.query.get("to_stage"),
    )
    return _json(data)


@require_api_auth
async def cross_posting_handler(request: web.Request) -> web.Response:
    from services.pg_cross_posting_v1 import CrossPostingV1

    tenant_id = uuid.UUID(request.query.get("tenant_id", ""))
    engine = await CrossPostingV1.get_engine(_actor(request), tenant_id)
    return _json(engine)


@require_api_auth
async def cross_posting_feature_handler(request: web.Request) -> web.Response:
    from services.pg_cross_posting_v1 import CrossPostingV1

    tenant_id = uuid.UUID(request.query.get("tenant_id", ""))
    feature = request.match_info["feature"]
    job_id_raw = request.query.get("job_id")
    job_id = uuid.UUID(job_id_raw) if job_id_raw else None
    data = await CrossPostingV1.get_feature(
        _actor(request),
        tenant_id,
        feature,
        job_id=job_id,
        content=request.query.get("content"),
    )
    return _json(data)


@require_api_auth
async def analytics_handler(request: web.Request) -> web.Response:
    from services.pg_analytics_v1 import AnalyticsV1

    tenant_id = uuid.UUID(request.query.get("tenant_id", ""))
    analytics = await AnalyticsV1.get_analytics(_actor(request), tenant_id)
    return _json(analytics)


@require_api_auth
async def analytics_feature_handler(request: web.Request) -> web.Response:
    from services.pg_analytics_v1 import AnalyticsV1

    tenant_id = uuid.UUID(request.query.get("tenant_id", ""))
    feature = request.match_info["feature"]
    data = await AnalyticsV1.get_feature(
        _actor(request),
        tenant_id,
        feature,
        export_format=request.query.get("format", "json"),
    )
    return _json(data)


async def auth_token_handler(request: web.Request) -> web.Response:
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        body = await request.json() if request.can_read_body else {}
        api_key = body.get("api_key")
    if not api_key:
        return web.json_response(
            {"error": "api_key_required", "api_version": "v1"},
            status=400,
        )
    try:
        token_data = await ApiGatewayEngineV1.exchange_api_key_for_jwt(api_key)
        return web.json_response({"data": token_data, "api_version": "v1"})
    except Exception as exc:
        return web.json_response(
            {"error": "authentication_failed", "message": str(exc), "api_version": "v1"},
            status=401,
        )


async def api_info_handler(request: web.Request) -> web.Response:
    return web.json_response({
        "name": "Public API Gateway",
        "version": "v1",
        "endpoints": [
            "/v1/deals",
            "/v1/partners",
            "/v1/pricing/calculate",
            "/v1/fx/rates",
            "/v1/vehicles",
            "/v1/inventory",
            "/v1/orders",
            "/v1/documents",
            "/v1/notifications",
            "/v1/dealer-portal",
            "/v1/dealer-portal/modules/{module}",
            "/v1/lead-marketplace",
            "/v1/lead-marketplace/features/{feature}",
            "/v1/ai-procurement-agent",
            "/v1/ai-procurement-agent/features/{feature}",
            "/v1/ai-advertising-agent",
            "/v1/ai-advertising-agent/features/{feature}",
            "/v1/ai-sales-agent",
            "/v1/ai-sales-agent/features/{feature}",
            "/v1/recommendation-engine",
            "/v1/recommendation-engine/features/{feature}",
            "/v1/communication-hub",
            "/v1/communication-hub/features/{feature}",
            "/v1/ai-conversation-skills",
            "/v1/ai-conversation-skills/features/{feature}",
            "/v1/deal-pipeline",
            "/v1/deal-pipeline/features/{feature}",
            "/v1/cross-posting",
            "/v1/cross-posting/features/{feature}",
            "/v1/analytics",
            "/v1/analytics/features/{feature}",
            "/v1/auth/token",
        ],
    })
