"""Sprint 46.1 — Normalized auto search listing schema."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class AutoSearchListing:
    source: str
    source_type: str  # dealer_warehouse | telegram_channel | public_web | dealer_source
    source_url: str
    listing_url: str
    external_id: str
    make: str
    model: str
    year: int | None = None
    price: float | None = None
    currency: str = "USD"
    mileage: int | None = None
    fuel: str | None = None
    transmission: str | None = None
    location: str | None = None
    description: str | None = None
    photos: list[str] = field(default_factory=list)
    published_at: str | None = None
    fetched_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        # Client card aliases (no adapter/source IDs required on UI)
        d["brand"] = self.make
        d["title"] = f"{self.make} {self.model}".strip()
        d["city"] = self.location
        d["url"] = self.listing_url
        d["link"] = self.listing_url
        d["price_usd"] = self.price if self.currency.upper() == "USD" else self.price
        d["id"] = self.external_id
        return d


@dataclass
class AutoSourceConfig:
    id: str
    name: str
    source_type: str
    source_url: str
    enabled: bool = True
    priority: int = 50
    status: str = "active"  # active | unavailable | requires_configuration
    category: str = "extra"  # warehouse | telegram | websites | extra
    owner_added: bool = False
    searchable: bool = True
    region: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
