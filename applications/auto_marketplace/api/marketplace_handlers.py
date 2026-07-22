# Sprint 10.2 REST handlers — marketplace, VIN, history, dealers, verification, pricing.

from __future__ import annotations

from aiohttp import web

from applications.auto_marketplace import auto_marketplace
from applications.auto_marketplace.api.middleware import error_response, json_response
from applications.auto_marketplace.marketplace.models import (
    AuctionLot,
    DealerNetworkProfile,
    DealerTier,
    MarketplaceChannel,
    MarketplaceListing,
    OwnershipTransfer,
)
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.models import Dealer


async def marketplace_health_handler(_request: web.Request) -> web.Response:
    return json_response(
        {
            "application_version": auto_marketplace.config.application_version,
            "overview": auto_marketplace.marketplace.marketplace.overview(),
            "metrics": auto_marketplace.marketplace.metrics(),
        }
    )


async def marketplace_listings_handler(request: web.Request) -> web.Response:
    if request.method == "GET":
        q = request.rel_url.query
        items = auto_marketplace.marketplace.listings.list_listings(
            channel=q.get("channel"),
            status=q.get("status"),
            dealer_id=q.get("dealer_id", ""),
            region=q.get("region", ""),
        )
        return json_response({"items": [i.to_dict() for i in items]})
    data = await request.json()
    try:
        listing = auto_marketplace.marketplace.create_listing(
            MarketplaceListing(
                vehicle_id=data.get("vehicle_id", ""),
                seller_id=data.get("seller_id", ""),
                dealer_id=data.get("dealer_id", ""),
                channel=MarketplaceChannel(data.get("channel", MarketplaceChannel.RETAIL.value)),
                title=data.get("title", ""),
                price=float(data.get("price", 0) or 0),
                currency=data.get("currency", "USD"),
                region=data.get("region", ""),
                vin=data.get("vin", ""),
                media_ids=list(data.get("media_ids") or []),
                metadata=dict(data.get("metadata") or {}),
            )
        )
        return json_response(listing.to_dict(), status=201)
    except (ValidationError, ValueError) as exc:
        return error_response(str(exc), status=400)


async def marketplace_publish_handler(request: web.Request) -> web.Response:
    listing_id = request.match_info["listing_id"]
    try:
        listing = auto_marketplace.marketplace.publish_listing(listing_id)
        return json_response(listing.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def marketplace_browse_handler(request: web.Request) -> web.Response:
    q = request.rel_url.query
    items = auto_marketplace.marketplace.marketplace.browse(
        channel=q.get("channel", ""),
        region=q.get("region", ""),
    )
    return json_response({"items": [i.to_dict() for i in items]})


async def marketplace_auctions_handler(request: web.Request) -> web.Response:
    if request.method == "GET":
        return json_response(
            {"items": [a.to_dict() for a in auto_marketplace.marketplace.auctions.list_active()]}
        )
    data = await request.json()
    try:
        lot = auto_marketplace.marketplace.auctions.create(
            AuctionLot(
                listing_id=data.get("listing_id", ""),
                start_price=float(data.get("start_price", 0) or 0),
                reserve_price=float(data.get("reserve_price", 0) or 0),
                currency=data.get("currency", "USD"),
                ends_at=float(data.get("ends_at", 0) or 0),
            )
        )
        return json_response(lot.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def marketplace_bid_handler(request: web.Request) -> web.Response:
    auction_id = request.match_info["auction_id"]
    data = await request.json()
    try:
        lot = auto_marketplace.marketplace.auctions.place_bid(
            auction_id,
            data.get("bidder_id", ""),
            float(data.get("amount", 0) or 0),
        )
        return json_response(lot.to_dict())
    except (NotFoundError, ValidationError) as exc:
        status = 404 if isinstance(exc, NotFoundError) else 400
        return error_response(str(exc), status=status)


async def vin_health_handler(_request: web.Request) -> web.Response:
    return json_response(
        {
            "vin_engine": auto_marketplace.config.vin_engine,
            "application_version": auto_marketplace.config.application_version,
            "metrics": auto_marketplace.marketplace.vin.metrics(),
        }
    )


async def vin_decode_handler(request: web.Request) -> web.Response:
    data = await request.json()
    result = auto_marketplace.marketplace.vin.decode(data.get("vin", ""))
    return json_response(result.to_dict(), status=200 if result.valid else 400)


async def vin_get_handler(request: web.Request) -> web.Response:
    vin = request.match_info["vin"]
    result = auto_marketplace.marketplace.vin.get(vin) or auto_marketplace.marketplace.vin.decode(vin)
    return json_response(result.to_dict())


async def history_health_handler(_request: web.Request) -> web.Response:
    return json_response(
        {
            "application_version": auto_marketplace.config.application_version,
            "metrics": auto_marketplace.marketplace.history.metrics(),
        }
    )


async def history_get_handler(request: web.Request) -> web.Response:
    vin = request.match_info["vin"]
    try:
        record = auto_marketplace.marketplace.history.get(vin)
        return json_response(record.to_dict())
    except NotFoundError:
        record = auto_marketplace.marketplace.history.get_or_create(vin=vin)
        return json_response(record.to_dict())


async def history_event_handler(request: web.Request) -> web.Response:
    vin = request.match_info["vin"]
    data = await request.json()
    event = data.get("event", "")
    try:
        engine = auto_marketplace.marketplace.history
        if event == "ownership":
            record = engine.add_ownership(vin, data.get("owner", ""), from_date=data.get("from", ""), to_date=data.get("to", ""))
        elif event == "registration":
            record = engine.add_registration(vin, data.get("region", ""), plate=data.get("plate", ""))
        elif event == "mileage":
            record = engine.add_mileage(vin, int(data.get("mileage_km", 0) or 0), source=data.get("source", "odometer"))
        elif event == "claim":
            record = engine.add_claim(vin, float(data.get("amount", 0) or 0), description=data.get("description", ""))
        elif event == "accident":
            record = engine.add_accident(vin, data.get("severity", "minor"), description=data.get("description", ""))
        elif event == "repair":
            record = engine.add_repair(vin, data.get("description", ""), cost=float(data.get("cost", 0) or 0))
        elif event == "service":
            record = engine.add_service(vin, data.get("description", ""), mileage_km=int(data.get("mileage_km", 0) or 0))
        elif event == "import_export":
            record = engine.add_import_export(vin, data.get("direction", "import"), data.get("country", ""))
        elif event == "theft":
            record = engine.set_theft_status(vin, data.get("status", "clear"))
        elif event == "lien":
            record = engine.set_lien_status(vin, data.get("status", "clear"))
        elif event == "inspection":
            record = engine.add_inspection(vin, float(data.get("score", 0) or 0), findings=list(data.get("findings") or []))
        else:
            return error_response("unknown history event", status=400)
        return json_response(record.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def dealers_network_list_handler(request: web.Request) -> web.Response:
    q = request.rel_url.query
    items = auto_marketplace.marketplace.dealers.list_profiles(
        region=q.get("region", ""),
        verified_only=q.get("verified_only", "false") == "true",
    )
    return json_response({"items": [p.to_dict() for p in items]})


async def dealers_network_create_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        # Ensure base dealer exists
        dealer_id = data.get("dealer_id", "")
        if not dealer_id:
            dealer = auto_marketplace.dealers.create_dealer(
                Dealer(name=data.get("name", ""), email=data.get("email", ""), phone=data.get("phone", ""))
            )
            dealer_id = dealer.dealer_id
        profile = auto_marketplace.marketplace.dealers.register_profile(
            DealerNetworkProfile(
                dealer_id=dealer_id,
                name=data.get("name", ""),
                region=data.get("region", ""),
                tier=DealerTier(data.get("tier", DealerTier.STANDARD.value)),
                branches=list(data.get("branches") or []),
                managers=list(data.get("managers") or []),
            )
        )
        return json_response(profile.to_dict(), status=201)
    except (ValidationError, ValueError) as exc:
        return error_response(str(exc), status=400)


async def dealers_verify_handler(request: web.Request) -> web.Response:
    dealer_id = request.match_info["dealer_id"]
    try:
        data = await request.json()
    except Exception:
        data = {}
    try:
        tier = DealerTier(data.get("tier", DealerTier.VERIFIED.value))
        profile = auto_marketplace.marketplace.dealers.verify(dealer_id, tier=tier)
        return json_response(profile.to_dict())
    except (NotFoundError, ValueError) as exc:
        status = 404 if isinstance(exc, NotFoundError) else 400
        return error_response(str(exc), status=status)


async def dealers_rate_handler(request: web.Request) -> web.Response:
    dealer_id = request.match_info["dealer_id"]
    data = await request.json()
    try:
        profile = auto_marketplace.marketplace.dealers.rate(dealer_id, float(data.get("rating", 0) or 0))
        return json_response(profile.to_dict())
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def dealers_analytics_handler(request: web.Request) -> web.Response:
    dealer_id = request.match_info["dealer_id"]
    try:
        auto_marketplace.marketplace.dealers.sync_inventory(dealer_id)
        return json_response(auto_marketplace.marketplace.dealers.analytics(dealer_id))
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def dealers_assign_lead_handler(request: web.Request) -> web.Response:
    dealer_id = request.match_info["dealer_id"]
    data = await request.json()
    try:
        assignment = auto_marketplace.marketplace.dealers.assign_lead(
            dealer_id,
            data.get("lead_id", ""),
            manager_id=data.get("manager_id", ""),
        )
        return json_response(assignment, status=201)
    except NotFoundError as exc:
        return error_response(str(exc), status=404)


async def verification_health_handler(_request: web.Request) -> web.Response:
    return json_response(
        {
            "application_version": auto_marketplace.config.application_version,
            "metrics": auto_marketplace.marketplace.verification.metrics(),
        }
    )


async def verification_run_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        report = auto_marketplace.marketplace.verification.verify_listing(
            listing_id=data.get("listing_id", ""),
            vehicle_id=data.get("vehicle_id", ""),
            vin=data.get("vin", ""),
            photo_count=int(data.get("photo_count", 0) or 0),
            media_urls=list(data.get("media_urls") or []),
        )
        return json_response(report.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def pricing_health_handler(_request: web.Request) -> web.Response:
    return json_response(
        {
            "application_version": auto_marketplace.config.application_version,
            "metrics": auto_marketplace.marketplace.valuation.metrics(),
        }
    )


async def pricing_value_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        valuation = auto_marketplace.marketplace.valuation.value_vehicle(
            vehicle_id=data.get("vehicle_id", ""),
            vin=data.get("vin", ""),
            year=int(data.get("year", 2020) or 2020),
            mileage_km=int(data.get("mileage_km", 50000) or 50000),
            base_price=float(data.get("base_price", 0) or 0),
            currency=data.get("currency", "USD"),
        )
        return json_response(valuation.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)


async def ownership_transfer_handler(request: web.Request) -> web.Response:
    data = await request.json()
    try:
        transfer = auto_marketplace.marketplace.ownership.transfer(
            OwnershipTransfer(
                vin=data.get("vin", ""),
                from_owner=data.get("from_owner", ""),
                to_owner=data.get("to_owner", ""),
                region=data.get("region", ""),
                notes=data.get("notes", ""),
            )
        )
        return json_response(transfer.to_dict(), status=201)
    except ValidationError as exc:
        return error_response(str(exc), status=400)
