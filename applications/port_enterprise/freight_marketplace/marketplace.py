"""Freight marketplace and carrier management."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.port_enterprise.shared.exceptions import NotFoundError, ValidationError
from applications.port_enterprise.shared.store import PortEnterpriseStore, port_enterprise_store

CARRIER_TYPES = [
    "shipping",
    "rail",
    "truck",
    "air",
    "forwarder",
    "customs_broker",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class FreightMarketplace:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store

    def list_cargo(
        self,
        *,
        title: str,
        origin: str,
        destination: str,
        teu: float = 1.0,
        price: float = 0.0,
    ) -> dict[str, Any]:
        if not title:
            raise ValidationError("cargo listing title required")
        lid = _id("fm_cargo")
        return self.store.fm_cargo_listings.save(
            lid,
            {
                "listing_id": lid,
                "title": title,
                "origin": origin,
                "destination": destination,
                "teu": float(teu),
                "price": float(price),
                "status": "open",
                "created_at": _now(),
            },
        )

    def available_freight(self, *, corridor: str, capacity_teu: float) -> dict[str, Any]:
        if not corridor:
            raise ValidationError("corridor required")
        fid = _id("fm_avail")
        return self.store.fm_available.save(
            fid,
            {
                "freight_id": fid,
                "corridor": corridor,
                "capacity_teu": float(capacity_teu),
                "status": "available",
                "at": _now(),
            },
        )

    def transport_request(
        self,
        *,
        shipper: str,
        origin: str,
        destination: str,
        teu: float = 1.0,
    ) -> dict[str, Any]:
        if not shipper:
            raise ValidationError("shipper required")
        rid = _id("fm_req")
        return self.store.fm_requests.save(
            rid,
            {
                "request_id": rid,
                "shipper": shipper,
                "origin": origin,
                "destination": destination,
                "teu": float(teu),
                "status": "open",
                "created_at": _now(),
            },
        )

    def instant_match(self, *, request_id: str, carrier_id: str, score: float = 0.9) -> dict[str, Any]:
        if self.store.fm_requests.get(request_id) is None:
            raise NotFoundError("transport_request", request_id)
        mid = _id("fm_match")
        return self.store.fm_matches.save(
            mid,
            {
                "match_id": mid,
                "request_id": request_id,
                "carrier_id": carrier_id,
                "score": float(score),
                "matched": True,
                "at": _now(),
            },
        )

    def search(self, *, query: str, mode: str = "all") -> dict[str, Any]:
        if not query:
            raise ValidationError("search query required")
        sid = _id("fm_srch")
        hits = [
            item
            for item in self.store.fm_cargo_listings.list_all()
            if query.lower() in str(item.get("title", "")).lower()
            or query.lower() in str(item.get("origin", "")).lower()
            or query.lower() in str(item.get("destination", "")).lower()
        ]
        return self.store.fm_searches.save(
            sid,
            {
                "search_id": sid,
                "query": query,
                "mode": mode,
                "hits": len(hits),
                "results": hits[:20],
                "at": _now(),
            },
        )

    def analytics(self, *, period: str = "monthly") -> dict[str, Any]:
        aid = _id("fm_anl")
        return self.store.fm_analytics.save(
            aid,
            {
                "analytics_id": aid,
                "period": period,
                "listings": self.store.fm_cargo_listings.count(),
                "requests": self.store.fm_requests.count(),
                "matches": self.store.fm_matches.count(),
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "cargo_listings": self.store.fm_cargo_listings.count(),
            "available_freight": self.store.fm_available.count(),
            "requests": self.store.fm_requests.count(),
            "matches": self.store.fm_matches.count(),
        }


class CarrierManagement:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store

    def register(
        self,
        *,
        name: str,
        carrier_type: str,
        country: str = "",
        scac: str = "",
    ) -> dict[str, Any]:
        if not name:
            raise ValidationError("carrier name required")
        if carrier_type not in CARRIER_TYPES:
            raise ValidationError(f"carrier_type must be one of {CARRIER_TYPES}")
        cid = _id("fm_car")
        return self.store.fm_carriers.save(
            cid,
            {
                "carrier_id": cid,
                "name": name,
                "carrier_type": carrier_type,
                "country": country,
                "scac": scac,
                "rating": 0.0,
                "created_at": _now(),
            },
        )

    def rate(self, carrier_id: str, *, score: float, comment: str = "") -> dict[str, Any]:
        carrier = self.store.fm_carriers.get(carrier_id)
        if carrier is None:
            raise NotFoundError("carrier", carrier_id)
        score = float(score)
        if score < 0 or score > 5:
            raise ValidationError("rating score must be 0..5")
        carrier["rating"] = score
        self.store.fm_carriers.save(carrier_id, carrier)
        rid = _id("fm_rate")
        return self.store.fm_ratings.save(
            rid,
            {
                "rating_id": rid,
                "carrier_id": carrier_id,
                "score": score,
                "comment": comment,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        by_type: dict[str, int] = {t: 0 for t in CARRIER_TYPES}
        for c in self.store.fm_carriers.list_all():
            t = c.get("carrier_type", "")
            if t in by_type:
                by_type[t] += 1
        return {
            "carriers": self.store.fm_carriers.count(),
            "ratings": self.store.fm_ratings.count(),
            "by_type": by_type,
        }


class FreightExchange:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store

    def spot(self, *, corridor: str, teu: float, ask_price: float) -> dict[str, Any]:
        if not corridor:
            raise ValidationError("corridor required")
        sid = _id("fm_spot")
        return self.store.fm_spots.save(
            sid,
            {
                "spot_id": sid,
                "corridor": corridor,
                "teu": float(teu),
                "ask_price": float(ask_price),
                "status": "open",
                "created_at": _now(),
            },
        )

    def contract(
        self,
        *,
        shipper: str,
        carrier_id: str,
        corridor: str,
        rate: float,
        term_months: int = 12,
    ) -> dict[str, Any]:
        if self.store.fm_carriers.get(carrier_id) is None:
            raise NotFoundError("carrier", carrier_id)
        cid = _id("fm_ctr")
        return self.store.fm_contracts.save(
            cid,
            {
                "contract_id": cid,
                "shipper": shipper,
                "carrier_id": carrier_id,
                "corridor": corridor,
                "rate": float(rate),
                "term_months": int(term_months),
                "status": "active",
                "created_at": _now(),
            },
        )

    def tender(self, *, title: str, corridor: str, teu: float) -> dict[str, Any]:
        if not title:
            raise ValidationError("tender title required")
        tid = _id("fm_tnd")
        return self.store.fm_tenders.save(
            tid,
            {
                "tender_id": tid,
                "title": title,
                "corridor": corridor,
                "teu": float(teu),
                "status": "open",
                "created_at": _now(),
            },
        )

    def bid(self, *, tender_id: str, carrier_id: str, price: float) -> dict[str, Any]:
        if self.store.fm_tenders.get(tender_id) is None:
            raise NotFoundError("tender", tender_id)
        if self.store.fm_carriers.get(carrier_id) is None:
            raise NotFoundError("carrier", carrier_id)
        bid = _id("fm_bid")
        return self.store.fm_bids.save(
            bid,
            {
                "bid_id": bid,
                "tender_id": tender_id,
                "carrier_id": carrier_id,
                "price": float(price),
                "at": _now(),
            },
        )

    def auction(self, *, spot_id: str, start_price: float) -> dict[str, Any]:
        if self.store.fm_spots.get(spot_id) is None:
            raise NotFoundError("spot", spot_id)
        aid = _id("fm_auc")
        return self.store.fm_auctions.save(
            aid,
            {
                "auction_id": aid,
                "spot_id": spot_id,
                "start_price": float(start_price),
                "current_price": float(start_price),
                "status": "live",
                "at": _now(),
            },
        )

    def negotiate(self, *, subject_ref: str, offer: float, counter: float = 0.0) -> dict[str, Any]:
        nid = _id("fm_neg")
        return self.store.fm_negotiations.save(
            nid,
            {
                "negotiation_id": nid,
                "subject_ref": subject_ref,
                "offer": float(offer),
                "counter": float(counter),
                "at": _now(),
            },
        )

    def book(
        self,
        *,
        shipper: str,
        carrier_id: str,
        origin: str,
        destination: str,
        price: float,
    ) -> dict[str, Any]:
        if self.store.fm_carriers.get(carrier_id) is None:
            raise NotFoundError("carrier", carrier_id)
        bid = _id("fm_book")
        return self.store.fm_bookings.save(
            bid,
            {
                "booking_id": bid,
                "shipper": shipper,
                "carrier_id": carrier_id,
                "origin": origin,
                "destination": destination,
                "price": float(price),
                "status": "confirmed",
                "created_at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "spots": self.store.fm_spots.count(),
            "contracts": self.store.fm_contracts.count(),
            "tenders": self.store.fm_tenders.count(),
            "bids": self.store.fm_bids.count(),
            "bookings": self.store.fm_bookings.count(),
        }
