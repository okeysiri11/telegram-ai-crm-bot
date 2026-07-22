"""Seller AI Suite facade — Sprint 13.5."""

from __future__ import annotations

from typing import Any

from applications.auto_marketplace.config import DEFAULT_CONFIG
from applications.auto_marketplace.seller_ai.auction import AuctionPlatform
from applications.auto_marketplace.seller_ai.pricing import AIPricing
from applications.auto_marketplace.seller_ai.seller import SellerAI
from applications.auto_marketplace.seller_ai.services import (
    BusinessIntelligence,
    GlobalAutomotiveNetwork,
    MatchingEngine,
    SellerDashboard,
)
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class SellerAISuite:
    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self.store = store or marketplace_store
        self.seller = SellerAI(self.store)
        self.auctions = AuctionPlatform(self.store)
        self.pricing = AIPricing(self.store)
        self.network = GlobalAutomotiveNetwork(self.store)
        self.matching = MatchingEngine(self.store)
        self.bi = BusinessIntelligence(self.store)
        self.dashboard = SellerDashboard(self.store)

    def bootstrap(self) -> dict[str, Any]:
        seller = self.seller.create_seller(name="Prime Export Motors", seller_type="dealership", region="EU")
        listing = self.seller.create_listing(
            seller_id=seller["seller_id"],
            vin="WVWZZZ1JZXW000001",
            make="Volkswagen",
            model="Golf",
            year=2020,
            ask_price=18500,
            photos=["front.jpg", "side.jpg", "interior.jpg"],
        )
        copy = self.seller.generate_listing_copy(listing["listing_id"])
        position = self.seller.analyze_market_position(listing_id=listing["listing_id"], market_avg=18000, demand_index=0.7)
        quote = self.pricing.quote(vin=listing["vin"], make="Volkswagen", model="Golf", year=2020, mileage=45000, base_market=18000)
        auction = self.auctions.create_auction(listing_id=listing["listing_id"], mode="timed", reserve_price=16000, start_price=15000)
        self.auctions.place_bid(auction_id=auction["auction_id"], bidder_id="buyer_1", amount=15500, proxy_max=17000)
        self.auctions.place_bid(auction_id=auction["auction_id"], bidder_id="buyer_2", amount=16200)
        closed = self.auctions.close_auction(auction["auction_id"])
        dealer = self.network.register_dealer(name="Tokyo Auto Trade", country="JP", role="exporter")
        trade = self.network.publish_trade_listing(
            direction="export",
            vin=listing["vin"],
            origin_country="DE",
            destination_country="JP",
            price=19000,
        )
        self.network.add_shipping_route(origin="DE", destination="JP", carrier="Ocean Auto")
        self.network.country_regulations("JP")
        match = self.matching.match(buyer_region="JP", make="Volkswagen", budget=20000)
        bi = self.bi.report(report_type="auction")
        board = self.dashboard.render(dashboard_type="marketplace")
        return {
            "bootstrap": True,
            "seller_id": seller["seller_id"],
            "listing_id": listing["listing_id"],
            "copy_id": copy["copy_id"],
            "analysis_id": position["analysis_id"],
            "quote_id": quote["quote_id"],
            "auction_id": auction["auction_id"],
            "auction_status": closed["status"],
            "network_dealer_id": dealer["network_dealer_id"],
            "trade_id": trade["trade_id"],
            "match_id": match["match_id"],
            "report_id": bi["report_id"],
            "dashboard_id": board["dashboard_id"],
            "version": DEFAULT_CONFIG.application_version,
        }

    def status(self) -> dict[str, Any]:
        return {
            "seller": self.seller.status(),
            "auctions": self.auctions.status(),
            "pricing": self.pricing.status(),
            "network": self.network.status(),
            "matching": self.matching.status(),
            "bi": self.bi.status(),
            "dashboard": self.dashboard.status(),
        }


seller_ai = SellerAISuite()
