# Sprint 10.8 REST handlers — enterprise, network, partners, production, health.

from __future__ import annotations

from aiohttp import web

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.middleware import error_response, json_response
from applications.auto_marketplace.enterprise.models import (
    ConnectorKind,
    EnterpriseConnector,
    ExchangeOffer,
    NetworkListing,
    NetworkPartner,
    PartnerKind,
)
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError


def _connector_kind(value: str) -> ConnectorKind:
    try:
        return ConnectorKind(value or "erp")
    except ValueError as exc:
        raise ValidationError(f"invalid connector kind: {value}") from exc


def _partner_kind(value: str) -> PartnerKind:
    try:
        return PartnerKind(value or "dealer")
    except ValueError as exc:
        raise ValidationError(f"invalid partner kind: {value}") from exc


async def enterprise_health_handler(_request: web.Request) -> web.Response:
    return json_response(
        {
            "enterprise_engine": auto_marketplace.config.enterprise_engine,
            "global_network": auto_marketplace.config.global_network,
            "application_version": auto_marketplace.config.application_version,
            "production_ready": auto_marketplace.config.production_ready,
            "metrics": auto_marketplace.enterprise.metrics(),
        }
    )


async def enterprise_connectors_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            items = auto_marketplace.enterprise.connectors.list_connectors(kind=request.query.get("kind", ""))
            return json_response({"items": [c.to_dict() for c in items]})
        data = await request.json()
        if data.get("bootstrap"):
            items = auto_marketplace.enterprise.connectors.bootstrap_defaults()
            return json_response({"items": [c.to_dict() for c in items]}, status=201)
        connector = auto_marketplace.enterprise.connectors.register(
            EnterpriseConnector(
                name=data.get("name", ""),
                kind=_connector_kind(data.get("kind", "erp")),
                endpoint=data.get("endpoint", ""),
                metadata=dict(data.get("metadata") or {}),
            )
        )
        return json_response(connector.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def enterprise_ping_handler(request: web.Request) -> web.Response:
    try:
        return json_response(auto_marketplace.enterprise.connectors.ping(request.match_info["connector_id"]))
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def enterprise_cross_platform_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            return json_response(auto_marketplace.enterprise.cross_platform.status())
        data = await request.json()
        link = auto_marketplace.enterprise.cross_platform.link(
            target=data.get("target", ""),
            shared=list(data.get("shared") or []),
        )
        auto_marketplace.enterprise.monitoring.audit("cross_platform_link", data.get("actor", "system"))
        return json_response(link.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def network_health_handler(_request: web.Request) -> web.Response:
    return json_response(
        {
            "global_network": auto_marketplace.config.global_network,
            "metrics": auto_marketplace.enterprise.network.metrics(),
        }
    )


async def network_listings_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            max_price = request.query.get("max_price")
            items = auto_marketplace.enterprise.network.search(
                country=request.query.get("country", ""),
                region=request.query.get("region", ""),
                max_price=float(max_price) if max_price is not None else None,
                federated_only=request.query.get("federated") == "1",
            )
            return json_response({"items": [i.to_dict() for i in items]})
        data = await request.json()
        listing = auto_marketplace.enterprise.network.publish(
            NetworkListing(
                vehicle_id=data.get("vehicle_id", ""),
                vin=data.get("vin", ""),
                country=data.get("country", ""),
                region=data.get("region", ""),
                dealer_id=data.get("dealer_id", ""),
                price=float(data.get("price", 0) or 0),
                currency=data.get("currency", "USD"),
                federated=bool(data.get("federated")),
            )
        )
        return json_response(listing.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def network_exchange_handler(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        offer = auto_marketplace.enterprise.exchange.create_offer(
            ExchangeOffer(
                from_partner_id=data.get("from_partner_id", ""),
                to_partner_id=data.get("to_partner_id", ""),
                vehicle_id=data.get("vehicle_id", ""),
                price=float(data.get("price", 0) or 0),
                currency=data.get("currency", "USD"),
            )
        )
        return json_response(offer.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def partners_handler(request: web.Request) -> web.Response:
    try:
        if request.method == "GET":
            items = auto_marketplace.enterprise.partners.list_partners(
                kind=request.query.get("kind", ""),
                country=request.query.get("country", ""),
            )
            return json_response({"items": [p.to_dict() for p in items]})
        data = await request.json()
        partner = auto_marketplace.enterprise.partners.register(
            NetworkPartner(
                name=data.get("name", ""),
                kind=_partner_kind(data.get("kind", "dealer")),
                country=data.get("country", ""),
                region=data.get("region", ""),
                rating=float(data.get("rating", 0) or 0),
            )
        )
        return json_response(partner.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def production_health_handler(_request: web.Request) -> web.Response:
    return json_response(
        {
            "application_version": auto_marketplace.config.application_version,
            "production_ready": auto_marketplace.config.production_ready,
            "release": auto_marketplace.enterprise.release.certify(),
            "metrics": auto_marketplace.enterprise.production.metrics(),
        }
    )


async def production_validate_handler(_request: web.Request) -> web.Response:
    report = auto_marketplace.enterprise.production.generate_report()
    return json_response(report.to_dict())


async def production_manifest_handler(_request: web.Request) -> web.Response:
    return json_response(auto_marketplace.enterprise.production.release_manifest())


async def production_preflight_handler(request: web.Request) -> web.Response:
    from applications.auto_marketplace.config import DEFAULT_CONFIG

    version = request.query.get("version", DEFAULT_CONFIG.application_version)
    return json_response(auto_marketplace.enterprise.deployment.preflight(version=version))


async def production_rollback_handler(_request: web.Request) -> web.Response:
    return json_response(auto_marketplace.enterprise.deployment.rollback_procedure())


async def health_deep_handler(_request: web.Request) -> web.Response:
    return json_response(auto_marketplace.enterprise.health.deep())


async def health_ready_handler(_request: web.Request) -> web.Response:
    return json_response(auto_marketplace.enterprise.health.ready())


async def health_live_handler(_request: web.Request) -> web.Response:
    return json_response(auto_marketplace.enterprise.health.live())
