"""Global network, matching, BI, dashboards — Sprint 13.5."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.auto_marketplace.shared.exceptions import ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store

DASHBOARD_TYPES = ["marketplace", "auction", "global_sales", "international_trade"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class GlobalAutomotiveNetwork:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store

    def register_dealer(
        self,
        *,
        name: str,
        country: str,
        role: str = "dealer",
    ) -> dict[str, Any]:
        if not name or not country:
            raise ValidationError("name and country required")
        if role not in ("dealer", "exporter", "importer", "shipper", "customs_broker"):
            raise ValidationError("invalid role")
        did = _id("sai_gdeal")
        dealer = {
            "network_dealer_id": did,
            "name": name,
            "country": country.upper(),
            "role": role,
            "status": "active",
            "registered_at": _now(),
        }
        return self.store.sa_network_dealers.save(did, dealer)

    def publish_trade_listing(
        self,
        *,
        direction: str,
        vin: str,
        origin_country: str,
        destination_country: str = "",
        price: float = 0.0,
    ) -> dict[str, Any]:
        if direction not in ("export", "import"):
            raise ValidationError("direction must be export or import")
        tid = _id("sai_trade")
        item = {
            "trade_id": tid,
            "direction": direction,
            "vin": (vin or "").strip().upper(),
            "origin_country": origin_country.upper(),
            "destination_country": (destination_country or "").upper(),
            "price": float(price),
            "shipping_available": True,
            "customs_support": True,
            "compliance": {"status": "review", "notes": "check local regulations"},
            "created_at": _now(),
        }
        return self.store.sa_trade_listings.save(tid, item)

    def add_shipping_route(self, *, origin: str, destination: str, carrier: str = "") -> dict[str, Any]:
        rid = _id("sai_ship")
        route = {
            "route_id": rid,
            "origin": origin.upper(),
            "destination": destination.upper(),
            "carrier": carrier or "global-auto-logistics",
            "status": "active",
            "created_at": _now(),
        }
        return self.store.sa_shipping_routes.save(rid, route)

    def country_regulations(self, country: str) -> dict[str, Any]:
        country = (country or "").upper()
        rid = _id("sai_reg")
        record = {
            "regulation_id": rid,
            "country": country,
            "import_duty_pct": 10.0 if country not in ("EU", "DE", "FR") else 0.0,
            "emissions_standard": "Euro 6" if country.startswith("E") or country in ("DE", "FR", "IT") else "local",
            "compliance_checklist": ["title", "vin_check", "customs_declaration"],
            "at": _now(),
        }
        return self.store.sa_regulations.save(rid, record)

    def status(self) -> dict[str, Any]:
        return {
            "dealers": self.store.sa_network_dealers.count(),
            "trade_listings": self.store.sa_trade_listings.count(),
            "shipping_routes": self.store.sa_shipping_routes.count(),
            "regulations": self.store.sa_regulations.count(),
        }


class MatchingEngine:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store

    def match(
        self,
        *,
        buyer_region: str = "",
        make: str = "",
        budget: float = 0.0,
    ) -> dict[str, Any]:
        listings = self.store.sa_listings.list_all()
        candidates = []
        for item in listings:
            if make and (item.get("make") or "").lower() != make.lower():
                continue
            if budget and float(item.get("ask_price") or 0) > float(budget):
                continue
            candidates.append(item)
        dealers = self.store.sa_network_dealers.list_all()
        if buyer_region:
            dealers = [d for d in dealers if d.get("country", "").upper() == buyer_region.upper() or d.get("country") == "EU"]
        rid = _id("sai_match")
        result = {
            "match_id": rid,
            "buyer_region": buyer_region,
            "make": make,
            "budget": budget,
            "listing_matches": [c["listing_id"] for c in candidates[:10]],
            "dealer_matches": [d["network_dealer_id"] for d in dealers[:10]],
            "demand_forecast": max(3, len(candidates) + 2),
            "supply_forecast": max(1, self.store.sa_listings.count()),
            "at": _now(),
        }
        return self.store.sa_matches.save(rid, result)

    def status(self) -> dict[str, Any]:
        return {"matches": self.store.sa_matches.count()}


class BusinessIntelligence:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store

    def report(self, *, report_type: str = "market") -> dict[str, Any]:
        allowed = ("market", "country", "brand", "dealer", "auction", "revenue")
        if report_type not in allowed:
            raise ValidationError(f"report_type must be one of {allowed}")
        listings = self.store.sa_listings.list_all()
        auctions = self.store.sa_auctions.list_all()
        trades = self.store.sa_trade_listings.list_all()
        if report_type == "market":
            metrics: dict[str, Any] = {
                "listings": len(listings),
                "avg_ask": round(sum(float(l.get("ask_price") or 0) for l in listings) / max(1, len(listings)), 2),
            }
        elif report_type == "country":
            by_country: dict[str, int] = {}
            for d in self.store.sa_network_dealers.list_all():
                c = d.get("country", "XX")
                by_country[c] = by_country.get(c, 0) + 1
            metrics = {"dealers_by_country": by_country}
        elif report_type == "brand":
            brands: dict[str, int] = {}
            for l in listings:
                b = l.get("make", "Unknown")
                brands[b] = brands.get(b, 0) + 1
            metrics = {"listings_by_brand": brands}
        elif report_type == "dealer":
            metrics = {"network_dealers": self.store.sa_network_dealers.count(), "sellers": self.store.sa_sellers.count()}
        elif report_type == "auction":
            metrics = {
                "auctions": len(auctions),
                "sold": len([a for a in auctions if a.get("status") == "sold"]),
                "bids": sum(len(a.get("bids") or []) for a in auctions),
            }
        else:
            revenue = sum(float(a.get("current_bid") or 0) for a in auctions if a.get("status") == "sold")
            revenue += sum(float(t.get("price") or 0) for t in trades)
            metrics = {"estimated_revenue": round(revenue, 2), "trade_listings": len(trades)}
        rid = _id("sai_bi")
        report = {
            "report_id": rid,
            "report_type": report_type,
            "metrics": metrics,
            "generated_at": _now(),
        }
        return self.store.sa_bi_reports.save(rid, report)

    def status(self) -> dict[str, Any]:
        return {"reports": self.store.sa_bi_reports.count()}


class SellerDashboard:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store
        self.types = list(DASHBOARD_TYPES)

    def render(self, *, dashboard_type: str) -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        if dashboard_type == "marketplace":
            widgets: dict[str, Any] = {
                "sellers": self.store.sa_sellers.count(),
                "listings": self.store.sa_listings.count(),
            }
        elif dashboard_type == "auction":
            widgets = {
                "auctions": self.store.sa_auctions.count(),
                "open": len([a for a in self.store.sa_auctions.list_all() if a.get("status") == "open"]),
            }
        elif dashboard_type == "global_sales":
            widgets = {
                "network_dealers": self.store.sa_network_dealers.count(),
                "matches": self.store.sa_matches.count(),
            }
        else:
            widgets = {
                "trade_listings": self.store.sa_trade_listings.count(),
                "shipping_routes": self.store.sa_shipping_routes.count(),
                "regulations": self.store.sa_regulations.count(),
            }
        did = _id("sai_dash")
        board = {
            "dashboard_id": did,
            "dashboard_type": dashboard_type,
            "widgets": widgets,
            "rendered_at": _now(),
        }
        return self.store.sa_dashboards.save(did, board)

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.sa_dashboards.count(), "types": self.types}
