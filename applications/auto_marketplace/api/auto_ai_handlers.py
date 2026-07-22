# Sprint 10.3 REST handlers — Auto AI, recommendations, pricing-ai, inspection, forecast, assistant.

from __future__ import annotations

from aiohttp import web

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.middleware import error_response, json_response
from applications.auto_marketplace.shared.exceptions import ValidationError


async def auto_ai_health_handler(_request: web.Request) -> web.Response:
    return json_response(
        {
            "auto_ai_engine": auto_marketplace.config.auto_ai_engine,
            "recommendation_engine": auto_marketplace.config.recommendation_engine,
            "application_version": auto_marketplace.config.application_version,
            "metrics": auto_marketplace.auto_ai.metrics(),
        }
    )


async def recommendations_health_handler(_request: web.Request) -> web.Response:
    return json_response(
        {
            "recommendation_engine": auto_marketplace.config.recommendation_engine,
            "metrics": auto_marketplace.auto_ai.recommendations.metrics(),
        }
    )


async def recommendations_personal_handler(request: web.Request) -> web.Response:
    data = await request.json()
    items = auto_marketplace.auto_ai.recommendations.personal(
        data.get("buyer_id", ""),
        data.get("preferences") or {},
        limit=int(data.get("limit", 5) or 5),
    )
    return json_response({"items": [i.to_dict() for i in items]})


async def recommendations_similar_handler(request: web.Request) -> web.Response:
    data = await request.json()
    items = auto_marketplace.auto_ai.recommendations.similar(
        data.get("vehicle_id", ""),
        limit=int(data.get("limit", 5) or 5),
    )
    return json_response({"items": [i.to_dict() for i in items]})


async def recommendations_alternatives_handler(request: web.Request) -> web.Response:
    data = await request.json()
    items = auto_marketplace.auto_ai.recommendations.alternatives(
        data.get("vehicle_id", ""),
        limit=int(data.get("limit", 5) or 5),
    )
    return json_response({"items": [i.to_dict() for i in items]})


async def recommendations_budget_handler(request: web.Request) -> web.Response:
    data = await request.json()
    items = auto_marketplace.auto_ai.recommendations.budget_optimize(
        data.get("buyer_id", ""),
        float(data.get("budget", 0) or 0),
        limit=int(data.get("limit", 5) or 5),
    )
    return json_response({"items": [i.to_dict() for i in items]})


async def recommendations_ownership_handler(request: web.Request) -> web.Response:
    data = await request.json()
    item = auto_marketplace.auto_ai.recommendations.ownership_cost(data.get("vehicle_id", ""))
    return json_response(item.to_dict())


async def recommendations_family_handler(request: web.Request) -> web.Response:
    data = await request.json()
    items = auto_marketplace.auto_ai.recommendations.family(
        data.get("buyer_id", ""),
        seats=int(data.get("seats", 5) or 5),
        limit=int(data.get("limit", 5) or 5),
    )
    return json_response({"items": [i.to_dict() for i in items]})


async def recommendations_commercial_handler(request: web.Request) -> web.Response:
    data = await request.json()
    items = auto_marketplace.auto_ai.recommendations.commercial(
        data.get("buyer_id", ""),
        limit=int(data.get("limit", 5) or 5),
    )
    return json_response({"items": [i.to_dict() for i in items]})


async def recommendations_fleet_handler(request: web.Request) -> web.Response:
    data = await request.json()
    items = auto_marketplace.auto_ai.recommendations.fleet(
        data.get("buyer_id", ""),
        fleet_size=int(data.get("fleet_size", 5) or 5),
        limit=int(data.get("limit", 5) or 5),
    )
    return json_response({"items": [i.to_dict() for i in items]})


async def pricing_ai_health_handler(_request: web.Request) -> web.Response:
    return json_response(
        {
            "application_version": auto_marketplace.config.application_version,
            "metrics": auto_marketplace.auto_ai.pricing_ai.metrics(),
        }
    )


async def pricing_ai_analyze_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        insight = auto_marketplace.auto_ai.pricing_ai.analyze(
            vehicle_id=data.get("vehicle_id", ""),
            vin=data.get("vin", ""),
            year=int(data.get("year", 2020) or 2020),
            mileage_km=int(data.get("mileage_km", 50000) or 50000),
            base_price=float(data.get("base_price", 0) or 0),
            currency=data.get("currency", "USD"),
        )
        return json_response(insight.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def inspection_ai_health_handler(_request: web.Request) -> web.Response:
    return json_response(
        {
            "application_version": auto_marketplace.config.application_version,
            "metrics": auto_marketplace.auto_ai.inspection_ai.metrics(),
        }
    )


async def inspection_ai_analyze_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        result = auto_marketplace.auto_ai.inspection_ai.analyze(
            vehicle_id=data.get("vehicle_id", ""),
            photo_urls=list(data.get("photo_urls") or []),
            hints=dict(data.get("hints") or {}),
        )
        return json_response(result.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def forecast_health_handler(_request: web.Request) -> web.Response:
    return json_response(
        {
            "application_version": auto_marketplace.config.application_version,
            "metrics": auto_marketplace.auto_ai.forecasting.metrics(),
        }
    )


async def forecast_vehicle_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        result = auto_marketplace.auto_ai.forecasting.forecast(
            vehicle_id=data.get("vehicle_id", ""),
            vin=data.get("vin", ""),
            year=int(data.get("year", 2020) or 2020),
            mileage_km=int(data.get("mileage_km", 50000) or 50000),
            base_price=float(data.get("base_price", 0) or 0),
            horizon_months=int(data.get("horizon_months", 12) or 12),
            currency=data.get("currency", "USD"),
        )
        return json_response(result.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def assistant_health_handler(_request: web.Request) -> web.Response:
    return json_response(
        {
            "application_version": auto_marketplace.config.application_version,
            "metrics": auto_marketplace.auto_ai.assistant.metrics(),
        }
    )


async def assistant_ask_handler(request: web.Request) -> web.Response:
    data = await request.json()
    reply = auto_marketplace.auto_ai.assistant.ask(
        data.get("query", ""),
        session_id=data.get("session_id", ""),
        budget=float(data["budget"]) if data.get("budget") is not None else None,
    )
    return json_response(reply.to_dict(), status=201)


async def knowledge_card_handler(request: web.Request) -> web.Response:
    data = await request.json()
    card = auto_marketplace.auto_ai.knowledge.ensure_default(
        data.get("make", ""),
        data.get("model", ""),
        int(data.get("year", 2020) or 2020),
    )
    return json_response(card.to_dict(), status=201)
