# Port ERP enterprise / network / production REST handlers — Sprint 9.8.

from __future__ import annotations

from aiohttp import web

from applications.port_erp import port_erp
from applications.port_erp.api.middleware import error_response, json_response
from applications.port_erp.enterprise.models import (
    DeploymentProfile,
    ExchangeOffer,
    IntegrationLink,
    IntegrationTarget,
    NetworkPartner,
    NetworkRoute,
    PartnerType,
    RegistryEntry,
    RegistryKind,
    TradeLane,
)
from applications.port_erp.shared.exceptions import NotFoundError, ValidationError


async def network_health_handler(_request: web.Request) -> web.Response:
    return json_response(
        {
            "global_network": port_erp.config.global_network,
            "application_version": port_erp.config.application_version,
            "metrics": port_erp.enterprise.network.metrics(),
            "partner_types": port_erp.enterprise.partners.partner_types(),
        }
    )


async def network_partners_list_handler(request: web.Request) -> web.Response:
    partner_type = request.rel_url.query.get("type")
    items = port_erp.enterprise.partners.list_partners(partner_type=partner_type)
    return json_response({"items": [p.to_dict() for p in items]})


async def network_partners_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        partner = port_erp.enterprise.partners.register(
            NetworkPartner(
                name=data.get("name", ""),
                partner_type=PartnerType(data.get("partner_type", PartnerType.PORT.value)),
                country=data.get("country", ""),
                region=data.get("region", ""),
                capabilities=list(data.get("capabilities") or []),
                capacity_teu=float(data.get("capacity_teu", 0) or 0),
                avg_price=float(data.get("avg_price", 0) or 0),
                reliability_score=float(data.get("reliability_score", 0.8) or 0.8),
                risk_score=float(data.get("risk_score", 0.2) or 0.2),
            )
        )
        return json_response(partner.to_dict(), status=201)
    except (ValidationError, ValueError) as exc:
        return error_response(str(exc), status=400)


async def network_discover_handler(request: web.Request) -> web.Response:
    q = request.rel_url.query
    partners = port_erp.enterprise.network.discover_partners(
        capability=q.get("capability", ""),
        region=q.get("region", ""),
    )
    return json_response({"items": [p.to_dict() for p in partners]})


async def network_routes_list_handler(_request: web.Request) -> web.Response:
    return json_response(
        {"items": [r.to_dict() for r in port_erp.enterprise.network.list_routes()]}
    )


async def network_routes_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        route = port_erp.enterprise.network.register_route(
            NetworkRoute(
                name=data.get("name", ""),
                origin=data.get("origin", ""),
                destination=data.get("destination", ""),
                carrier_id=data.get("carrier_id", ""),
                mode=data.get("mode", "sea"),
                price=float(data.get("price", 0) or 0),
                currency=data.get("currency", "USD"),
                capacity_teu=float(data.get("capacity_teu", 0) or 0),
                eta_hours=float(data.get("eta_hours", 0) or 0),
                risk_score=float(data.get("risk_score", 0.2) or 0.2),
            )
        )
        return json_response(route.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def network_lanes_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        lane = port_erp.enterprise.network.register_lane(
            TradeLane(
                name=data.get("name", ""),
                origin_port=data.get("origin_port", ""),
                destination_port=data.get("destination_port", ""),
                modes=list(data.get("modes") or ["sea"]),
                distance_nm=float(data.get("distance_nm", 0) or 0),
                transit_days=float(data.get("transit_days", 0) or 0),
                risk_level=data.get("risk_level", "low"),
            )
        )
        return json_response(lane.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def network_recommend_handler(request: web.Request) -> web.Response:
    data = await request.json()
    items = port_erp.enterprise.network.recommend_carriers(
        origin=data.get("origin", ""),
        destination=data.get("destination", ""),
        limit=int(data.get("limit", 5) or 5),
    )
    return json_response({"items": items})


async def network_compare_handler(request: web.Request) -> web.Response:
    data = await request.json()
    origin = data.get("origin", "")
    destination = data.get("destination", "")
    return json_response(
        {
            "prices": port_erp.enterprise.network.compare_prices(origin=origin, destination=destination),
            "capacity": port_erp.enterprise.network.compare_capacity(
                origin=origin, destination=destination
            ),
            "eta": port_erp.enterprise.network.optimize_eta(origin=origin, destination=destination),
            "risk": port_erp.enterprise.network.analyze_risk(origin=origin, destination=destination),
        }
    )


async def network_recommendations_handler(request: web.Request) -> web.Response:
    region = request.rel_url.query.get("region", "")
    return json_response(
        {"items": port_erp.enterprise.network.trade_recommendations(region=region)}
    )


async def integration_health_handler(_request: web.Request) -> web.Response:
    return json_response(
        {
            "enterprise_engine": port_erp.config.enterprise_engine,
            "application_version": port_erp.config.application_version,
            "targets": port_erp.enterprise.integration.targets(),
            "matrix": port_erp.enterprise.integration.status_matrix(),
        }
    )


async def integration_bootstrap_handler(_request: web.Request) -> web.Response:
    return json_response(port_erp.enterprise.enterprise.bootstrap(), status=201)


async def integration_list_handler(_request: web.Request) -> web.Response:
    return json_response(
        {"items": [l.to_dict() for l in port_erp.enterprise.integration.list_links()]}
    )


async def integration_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        link = port_erp.enterprise.integration.register(
            IntegrationLink(
                target=IntegrationTarget(data.get("target", IntegrationTarget.CRM.value)),
                endpoint=data.get("endpoint", ""),
                metadata=dict(data.get("metadata") or {}),
            )
        )
        return json_response(link.to_dict(), status=201)
    except (ValidationError, ValueError) as exc:
        return error_response(str(exc), status=400)


async def integration_connect_handler(request: web.Request) -> web.Response:
    link_id = request.match_info["link_id"]
    try:
        link = port_erp.enterprise.integration.connect(link_id)
        return json_response(link.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def global_health_handler(_request: web.Request) -> web.Response:
    return json_response(
        {
            "global_network": port_erp.config.global_network,
            "application_version": port_erp.config.application_version,
            "registry": port_erp.enterprise.registry.summary(),
            "kinds": port_erp.enterprise.registry.kinds(),
            "executive": port_erp.enterprise.analytics.executive_report(),
        }
    )


async def global_registry_list_handler(request: web.Request) -> web.Response:
    kind = request.rel_url.query.get("kind")
    items = port_erp.enterprise.registry.list_entries(kind=kind)
    return json_response({"items": [e.to_dict() for e in items]})


async def global_registry_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        entry = port_erp.enterprise.registry.register(
            RegistryEntry(
                kind=RegistryKind(data.get("kind", RegistryKind.COMPANY.value)),
                external_id=data.get("external_id", ""),
                name=data.get("name", ""),
                region=data.get("region", ""),
                attributes=dict(data.get("attributes") or {}),
            )
        )
        return json_response(entry.to_dict(), status=201)
    except (ValidationError, ValueError) as exc:
        return error_response(str(exc), status=400)


async def global_exchange_list_handler(_request: web.Request) -> web.Response:
    return json_response(
        {"items": [o.to_dict() for o in port_erp.enterprise.exchange.list_offers()]}
    )


async def global_exchange_publish_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        offer = port_erp.enterprise.exchange.publish(
            ExchangeOffer(
                partner_id=data.get("partner_id", ""),
                origin=data.get("origin", ""),
                destination=data.get("destination", ""),
                capacity_teu=float(data.get("capacity_teu", 0) or 0),
                price=float(data.get("price", 0) or 0),
                currency=data.get("currency", "USD"),
                valid_until=float(data.get("valid_until", 0) or 0),
            )
        )
        return json_response(offer.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def global_dashboard_handler(_request: web.Request) -> web.Response:
    return json_response(port_erp.enterprise.analytics.executive_report())


async def production_health_handler(_request: web.Request) -> web.Response:
    return json_response(
        {
            "application_version": port_erp.config.application_version,
            "enterprise_engine": port_erp.config.enterprise_engine,
            "global_network": port_erp.config.global_network,
            "health": port_erp.enterprise.health.probe(),
            "steps": port_erp.enterprise.deployment.steps(),
        }
    )


async def production_readiness_handler(_request: web.Request) -> web.Response:
    return json_response(port_erp.enterprise.production.readiness())


async def production_verify_handler(_request: web.Request) -> web.Response:
    report = port_erp.enterprise.production.verify_release()
    return json_response(report.to_dict(), status=201)


async def production_benchmark_handler(_request: web.Request) -> web.Response:
    return json_response(port_erp.enterprise.production.performance_benchmark())


async def production_profile_handler(request: web.Request) -> web.Response:
    if request.method == "GET":
        return json_response(
            {"items": [p.to_dict() for p in port_erp.enterprise.deployment.list_profiles()]}
        )
    data = await request.json()
    try:
        profile = port_erp.enterprise.deployment.save_profile(
            DeploymentProfile(
                name=data.get("name", "production"),
                environment=data.get("environment", "production"),
                replicas=int(data.get("replicas", 1) or 1),
                region=data.get("region", "global"),
                feature_flags=dict(data.get("feature_flags") or {}),
            )
        )
        return json_response(profile.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def enterprise_health_handler(_request: web.Request) -> web.Response:
    return json_response(
        {
            "enterprise_engine": port_erp.config.enterprise_engine,
            "application_version": port_erp.config.application_version,
            "connectors": port_erp.enterprise.enterprise.connectors(),
            "metrics": port_erp.enterprise.metrics(),
            "matrix": port_erp.enterprise.enterprise.matrix(),
        }
    )


async def enterprise_bootstrap_handler(_request: web.Request) -> web.Response:
    return json_response(port_erp.enterprise.enterprise.bootstrap(), status=201)
