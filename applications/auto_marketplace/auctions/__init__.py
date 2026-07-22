from applications.auto_marketplace.auctions.engine import AuctionsEngine, auctions_engine

__all__ = [
    "AuctionsEngine",
    "auctions_engine",
    "CommercialAuctionEngine",
    "commercial_auction_engine",
]


def __getattr__(name: str):
    if name in {"CommercialAuctionEngine", "commercial_auction_engine"}:
        from applications.auto_marketplace.auctions.commercial import (
            CommercialAuctionEngine,
            commercial_auction_engine,
        )

        return CommercialAuctionEngine if name == "CommercialAuctionEngine" else commercial_auction_engine
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
