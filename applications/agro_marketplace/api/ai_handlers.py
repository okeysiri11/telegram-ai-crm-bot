# AI / Recommendations / Forecast / Knowledge / Assistant API handlers — Sprint 8.4.

from __future__ import annotations

from aiohttp import web

from applications.agro_marketplace import agro_marketplace
from applications.agro_marketplace.api.middleware import error_response, json_response
from applications.agro_marketplace.ai.models import ForecastKind, KnowledgeArticle, KnowledgeKind
from applications.agro_marketplace.shared.exceptions import NotFoundError


async def ai_health_handler(_request: web.Request) -> web.Response:
    return json_response(
        {
            "agro_ai": agro_marketplace.config.agro_ai,
            "application_version": agro_marketplace.config.application_version,
            "metrics": agro_marketplace.agro_ai.metrics(),
            "analytics": agro_marketplace.analytics.ai_insights(),
        }
    )


async def ai_agents_list_handler(_request: web.Request) -> web.Response:
    return json_response({"items": [a.to_dict() for a in agro_marketplace.agro_ai.agents.list_agents()]})


async def ai_agent_invoke_handler(request: web.Request) -> web.Response:
    data = await request.json()
    agent_type = request.match_info.get("agent_type") or data.get("agent_type", "farmer_assistant")
    try:
        invocation = await agro_marketplace.agro_ai.agents.invoke(
            agent_type,
            data.get("message", ""),
            user_id=data.get("user_id", ""),
            context=data.get("context"),
        )
        return json_response(invocation.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def recommendations_products_handler(request: web.Request) -> web.Response:
    budget = request.query.get("budget")
    rec = await agro_marketplace.agro_ai.recommendations.recommend_products(
        buyer_id=request.query.get("buyer_id", ""),
        budget=float(budget) if budget else None,
    )
    return json_response(rec.to_dict())


async def recommendations_buyers_handler(request: web.Request) -> web.Response:
    rec = await agro_marketplace.agro_ai.recommendations.recommend_buyers(request.match_info["offer_id"])
    return json_response(rec.to_dict())


async def recommendations_suppliers_handler(request: web.Request) -> web.Response:
    rec = await agro_marketplace.agro_ai.recommendations.recommend_suppliers(request.match_info["request_id"])
    return json_response(rec.to_dict())


async def recommendations_contracts_handler(request: web.Request) -> web.Response:
    rec = await agro_marketplace.agro_ai.recommendations.recommend_contracts(request.match_info["order_id"])
    return json_response(rec.to_dict())


async def recommendations_opportunities_handler(_request: web.Request) -> web.Response:
    rec = await agro_marketplace.agro_ai.recommendations.detect_trade_opportunities()
    return json_response(rec.to_dict())


async def recommendations_inventory_handler(request: web.Request) -> web.Response:
    return json_response(
        agro_marketplace.agro_ai.recommendations.inventory_optimization(
            warehouse_id=request.query.get("warehouse_id", "")
        )
    )


async def recommendations_warehouse_handler(_request: web.Request) -> web.Response:
    return json_response(agro_marketplace.agro_ai.recommendations.warehouse_optimization())


async def forecast_price_handler(request: web.Request) -> web.Response:
    data = await request.json() if request.method == "POST" else {}
    subject = data.get("subject") or request.query.get("subject", "")
    if not subject:
        return error_response("subject is required", status=400)
    result = await agro_marketplace.agro_ai.forecasting.forecast_price(
        subject,
        region=data.get("region") or request.query.get("region", ""),
        horizon_days=int(data.get("horizon_days") or request.query.get("horizon_days", 30)),
        base_price=float(data["base_price"]) if data.get("base_price") is not None else None,
    )
    return json_response(result.to_dict())


async def forecast_demand_handler(request: web.Request) -> web.Response:
    data = await request.json() if request.method == "POST" else {}
    subject = data.get("subject") or request.query.get("subject", "")
    if not subject:
        return error_response("subject is required", status=400)
    result = await agro_marketplace.agro_ai.forecasting.forecast_demand(
        subject,
        region=data.get("region") or request.query.get("region", ""),
        horizon_days=int(data.get("horizon_days") or request.query.get("horizon_days", 30)),
    )
    return json_response(result.to_dict())


async def forecast_supply_handler(request: web.Request) -> web.Response:
    data = await request.json() if request.method == "POST" else {}
    subject = data.get("subject") or request.query.get("subject", "")
    if not subject:
        return error_response("subject is required", status=400)
    result = await agro_marketplace.agro_ai.forecasting.forecast_supply(
        subject,
        region=data.get("region") or request.query.get("region", ""),
    )
    return json_response(result.to_dict())


async def forecast_harvest_handler(request: web.Request) -> web.Response:
    data = await request.json() if request.method == "POST" else {}
    subject = data.get("subject") or request.query.get("subject", "")
    if not subject:
        return error_response("subject is required", status=400)
    result = await agro_marketplace.agro_ai.forecasting.forecast_harvest(
        subject,
        region=data.get("region") or request.query.get("region", ""),
    )
    return json_response(result.to_dict())


async def forecast_season_handler(request: web.Request) -> web.Response:
    data = await request.json() if request.method == "POST" else {}
    crop = data.get("crop") or request.query.get("crop", "")
    if not crop:
        return error_response("crop is required", status=400)
    result = await agro_marketplace.agro_ai.forecasting.season_plan(
        crop,
        region=data.get("region") or request.query.get("region", ""),
    )
    return json_response(result.to_dict())


async def forecast_risk_handler(request: web.Request) -> web.Response:
    data = await request.json() if request.method == "POST" else {}
    subject = data.get("subject") or request.query.get("subject", "")
    if not subject:
        return error_response("subject is required", status=400)
    result = await agro_marketplace.agro_ai.forecasting.estimate_risk(
        subject,
        region=data.get("region") or request.query.get("region", ""),
    )
    return json_response(result.to_dict())


async def forecast_list_handler(request: web.Request) -> web.Response:
    kind = request.query.get("kind")
    items = agro_marketplace.agro_ai.forecasting.list_forecasts(
        kind=ForecastKind(kind) if kind else None
    )
    return json_response({"items": [f.to_dict() for f in items]})


async def knowledge_search_handler(request: web.Request) -> web.Response:
    kind = request.query.get("kind")
    items = agro_marketplace.agro_ai.knowledge.search(
        request.query.get("q", ""),
        kind=KnowledgeKind(kind) if kind else None,
    )
    return json_response({"items": items})


async def knowledge_taxonomy_handler(_request: web.Request) -> web.Response:
    return json_response({"items": agro_marketplace.agro_ai.knowledge.crop_taxonomy()})


async def knowledge_seasonality_handler(request: web.Request) -> web.Response:
    return json_response(
        {
            "items": agro_marketplace.agro_ai.knowledge.seasonality(
                crop=request.query.get("crop", ""),
                region=request.query.get("region", ""),
            )
        }
    )


async def knowledge_export_handler(request: web.Request) -> web.Response:
    return json_response(
        {"items": agro_marketplace.agro_ai.knowledge.export_regulations(request.query.get("q", "export"))}
    )


async def knowledge_add_handler(request: web.Request) -> web.Response:
    data = await request.json()
    article = agro_marketplace.agro_ai.knowledge.add_article(
        KnowledgeArticle(
            kind=KnowledgeKind(data.get("kind", "general")),
            title=data.get("title", ""),
            body=data.get("body", ""),
            tags=list(data.get("tags", [])),
            region=data.get("region", ""),
            crop=data.get("crop", ""),
        )
    )
    return json_response(article.to_dict(), status=201)


async def assistant_ask_handler(request: web.Request) -> web.Response:
    data = await request.json()
    result = await agro_marketplace.agro_ai.assistant.ask(
        data.get("message", ""),
        user_id=data.get("user_id", ""),
        role=data.get("role", ""),
        context=data.get("context"),
    )
    return json_response(result)


async def pricing_ai_estimate_handler(request: web.Request) -> web.Response:
    try:
        result = await agro_marketplace.agro_ai.pricing_ai.estimate_price(request.match_info["product_id"])
        return json_response(result)
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def crop_ai_advise_handler(request: web.Request) -> web.Response:
    crop = request.match_info.get("crop") or request.query.get("crop", "")
    if not crop:
        return error_response("crop is required", status=400)
    return json_response(
        agro_marketplace.agro_ai.crop_ai.advise(crop, region=request.query.get("region", ""))
    )


async def market_ai_snapshot_handler(request: web.Request) -> web.Response:
    data = await request.json() if request.method == "POST" else {}
    subject = data.get("subject") or request.query.get("subject", "")
    if not subject:
        return error_response("subject is required", status=400)
    result = await agro_marketplace.agro_ai.market_ai.market_snapshot(
        subject,
        region=data.get("region") or request.query.get("region", ""),
    )
    return json_response(result)


async def workflow_qualify_lead_handler(request: web.Request) -> web.Response:
    try:
        result = await agro_marketplace.agro_ai.workflow.qualify_lead(request.match_info["lead_id"])
        return json_response(result)
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def workflow_auto_match_handler(_request: web.Request) -> web.Response:
    return json_response(await agro_marketplace.agro_ai.workflow.auto_match_offers())


async def workflow_negotiation_handler(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except Exception:
        body = {}
    try:
        result = await agro_marketplace.agro_ai.workflow.assist_negotiation(
            request.match_info["negotiation_id"],
            target_price=float(body.get("target_price", 0)),
        )
        return json_response(result)
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def workflow_opportunities_handler(_request: web.Request) -> web.Response:
    return json_response(await agro_marketplace.agro_ai.workflow.detect_opportunities())


async def workflow_executive_report_handler(request: web.Request) -> web.Response:
    data = {}
    if request.method == "POST":
        try:
            data = await request.json()
        except Exception:
            data = {}
    report = await agro_marketplace.agro_ai.workflow.executive_report(
        title=data.get("title", "Agro Executive Report")
    )
    return json_response(report.to_dict(), status=201)


async def workflow_tasks_handler(_request: web.Request) -> web.Response:
    return json_response({"items": [t.to_dict() for t in agro_marketplace.agro_ai.workflow.list_tasks()]})
