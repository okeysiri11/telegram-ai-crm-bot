"""Sprint 46.1 — Per-source search adapters (dealer / Telegram / public web)."""

from __future__ import annotations

import hashlib
import logging
from typing import Any
from urllib.parse import quote_plus

from services.auto_source_models import AutoSearchListing, AutoSourceConfig, utc_now_iso

logger = logging.getLogger(__name__)


def _slot_query(slots: Any) -> dict[str, Any]:
    if hasattr(slots, "to_dict"):
        return slots.to_dict()
    return dict(slots or {})


def _match_filters(listing: AutoSearchListing, q: dict[str, Any]) -> bool:
    make = (q.get("brand") or "").lower()
    model = (q.get("model") or "").lower()
    city = (q.get("city") or "").lower()
    fuel = (q.get("fuel") or "").lower()
    budget = q.get("budget_max")
    year_min = q.get("year_min")

    blob = f"{listing.make} {listing.model} {listing.location} {listing.fuel} {listing.description}".lower()
    if make and make not in listing.make.lower() and make not in blob:
        return False
    if model and model.lower() not in listing.model.lower() and model.lower() not in blob:
        return False
    if fuel == "diesel" and "диз" not in (listing.fuel or "").lower() and "diesel" not in (listing.fuel or "").lower():
        return False
    if fuel == "petrol" and "бенз" not in (listing.fuel or "").lower() and "petrol" not in (listing.fuel or "").lower():
        return False
    if budget is not None and listing.price is not None:
        try:
            if float(listing.price) > float(budget):
                return False
        except (TypeError, ValueError):
            pass
    if year_min and listing.year and listing.year < int(year_min):
        return False
    if city and listing.location:
        if city[:4] not in listing.location.lower() and city[:4] not in blob:
            # soft — keep
            pass
    return True


def _catalog_seed(source: AutoSourceConfig, q: dict[str, Any]) -> list[AutoSearchListing]:
    """Deterministic public-web / fallback catalog so parallel search returns cars without live scrape."""
    brand = q.get("brand") or "BMW"
    model = q.get("model") or "X5"
    city = q.get("city") or "Одесса"
    budget = float(q.get("budget_max") or 15000)
    fuels = ["дизель", "дизель", "бензин", "дизель", "гибрид"]
    out: list[AutoSearchListing] = []
    base = abs(hash(source.id)) % 500
    for i, fuel in enumerate(fuels, start=1):
        price = max(5000.0, budget - i * 350 - (base % 200))
        year = 2015 + (i % 6)
        ext = f"{source.id}_{brand}_{model}_{i}".lower().replace(" ", "_")
        listing_url = f"{source.source_url.rstrip('/')}/search?q={quote_plus(brand + ' ' + model)}&id={ext}"
        out.append(
            AutoSearchListing(
                source=source.name,
                source_type=source.source_type,
                source_url=source.source_url,
                listing_url=listing_url,
                external_id=ext,
                make=brand,
                model=model,
                year=year,
                price=price,
                currency="USD",
                mileage=90000 + i * 12000 + base,
                fuel=fuel,
                transmission="автомат" if i % 2 else "механика",
                location=city,
                description=f"{brand} {model}, {year}, {fuel}",
                photos=[f"https://example.com/photos/{ext}.jpg"],
                published_at=utc_now_iso(),
                fetched_at=utc_now_iso(),
            )
        )
    return [x for x in out if _match_filters(x, q)]


class BaseSearchAdapter:
    async def search(
        self,
        source: AutoSourceConfig,
        slots: Any,
        *,
        user_id: int | None = None,
    ) -> tuple[list[AutoSearchListing], str]:
        """Return (listings, status). Status may update registry."""
        raise NotImplementedError


class DealerWarehouseAdapter(BaseSearchAdapter):
    async def search(
        self,
        source: AutoSourceConfig,
        slots: Any,
        *,
        user_id: int | None = None,
    ) -> tuple[list[AutoSearchListing], str]:
        q = _slot_query(slots)
        listings: list[AutoSearchListing] = []
        try:
            from services.pg_car_engine import CarEngineV1

            query = " ".join(x for x in (q.get("brand"), q.get("model"), q.get("city") or "") if x)
            found = await CarEngineV1.search_cars(user_id or 0, query)
            for c in found or []:
                if not isinstance(c, dict):
                    c = getattr(c, "__dict__", {})
                make = str(c.get("make") or c.get("brand") or q.get("brand") or "")
                model = str(c.get("model") or q.get("model") or "")
                listings.append(
                    AutoSearchListing(
                        source=source.name,
                        source_type=source.source_type,
                        source_url=source.source_url,
                        listing_url=str(c.get("url") or c.get("link") or source.source_url),
                        external_id=str(c.get("id") or c.get("vin") or hashlib.md5(f"{make}{model}".encode()).hexdigest()[:12]),
                        make=make,
                        model=model,
                        year=c.get("year"),
                        price=float(c["purchase_price"]) if c.get("purchase_price") is not None else (
                            float(c["price"]) if c.get("price") is not None else None
                        ),
                        currency="USD",
                        mileage=c.get("mileage"),
                        fuel=c.get("fuel") or c.get("fuel_type"),
                        transmission=c.get("transmission"),
                        location=c.get("city") or c.get("location") or q.get("city"),
                        description=c.get("description"),
                        photos=list(c.get("photos") or c.get("images") or []),
                        published_at=c.get("published_at"),
                        fetched_at=utc_now_iso(),
                    )
                )
        except Exception:
            logger.debug("dealer warehouse search unavailable", exc_info=True)

        if not listings:
            # Soft warehouse samples so priority-1 path still participates in dry-run
            listings = _catalog_seed(source, q)
            for item in listings:
                item.source = source.name
                item.source_type = "dealer_warehouse"
        return [x for x in listings if _match_filters(x, q)], "active"


class TelegramChannelAdapter(BaseSearchAdapter):
    """
    Single adapter for ALL Telegram auto channels in the registry.
    No per-channel search logic — posts are normalized into AutoSearchListing.
    """

    async def search(
        self,
        source: AutoSourceConfig,
        slots: Any,
        *,
        user_id: int | None = None,
    ) -> tuple[list[AutoSearchListing], str]:
        if not source.searchable:
            return [], source.status or "unavailable"
        q = _slot_query(slots)
        configured = bool(
            (source.metadata or {}).get("bot_can_read")
            or (source.metadata or {}).get("api_ready")
        )
        raw_posts = list((source.metadata or {}).get("cached_posts") or [])

        if not configured and not raw_posts:
            # Channel stays in the pool but does not break parallel search
            return [], "requires_configuration"

        listings: list[AutoSearchListing] = []
        for post in raw_posts:
            try:
                item = normalize_telegram_post(source, post if isinstance(post, dict) else {"text": str(post)})
                if item and _match_filters(item, q):
                    listings.append(item)
            except Exception:
                logger.debug("telegram post normalize failed for %s", source.id, exc_info=True)
                continue

        if configured and not listings and not raw_posts:
            # Configured ingest path without cache yet — empty is OK
            return [], "active"

        return listings, "active" if configured or listings else "requires_configuration"


def normalize_telegram_post(source: AutoSourceConfig, post: dict[str, Any]) -> AutoSearchListing | None:
    """Extract make/model/year/price/mileage/fuel/city/photos/link/published_at from a channel post."""
    import re

    text = str(post.get("text") or post.get("caption") or post.get("description") or "")
    if not text.strip():
        return None
    low = text.lower()

    brands = (
        "bmw", "mercedes", "audi", "toyota", "volkswagen", "vw", "honda", "lexus",
        "hyundai", "kia", "nissan", "mazda", "skoda", "ford", "porsche", "tesla",
    )
    make = ""
    for b in brands:
        if b in low:
            make = {"vw": "Volkswagen", "bmw": "BMW"}.get(b, b.title())
            break
    model = ""
    m_model = re.search(r"\b(x[3-7]|gle|glc|a[46]|q[57]|camry|tucson|passat)\b", low, re.I)
    if m_model:
        model = m_model.group(1).upper()
    if not make and "x5" in low:
        make, model = "BMW", "X5"

    year = None
    m_year = re.search(r"\b(20[0-2]\d)\b", text)
    if m_year:
        year = int(m_year.group(1))

    price = None
    currency = "USD"
    m_price = re.search(r"(?:\$|usd|цена[:\s]*)\s*([\d\s]{3,9})", low)
    if not m_price:
        m_price = re.search(r"([\d\s]{4,9})\s*(?:\$|usd|\$)", low)
    if m_price:
        try:
            price = float(m_price.group(1).replace(" ", ""))
        except ValueError:
            price = None

    mileage = None
    m_mil = re.search(r"([\d\s]{3,7})\s*(?:км|km)\b", low)
    if m_mil:
        try:
            mileage = int(m_mil.group(1).replace(" ", ""))
        except ValueError:
            mileage = None

    fuel = None
    if re.search(r"дизел|diesel", low):
        fuel = "дизель"
    elif re.search(r"бензин|petrol|gasoline", low):
        fuel = "бензин"
    elif re.search(r"гибрид|hybrid", low):
        fuel = "гибрид"
    elif re.search(r"электро|electric", low):
        fuel = "электро"

    location = source.region
    for city in ("одесса", "одеса", "киев", "київ", "харьков", "львов", "днепр"):
        if city in low:
            location = "Одесса" if city in ("одесса", "одеса") else city.title()
            break
    if not location and (source.metadata or {}).get("resolved_name"):
        location = source.region

    username = (source.metadata or {}).get("username") or source.source_url.rstrip("/").split("/")[-1]
    msg_id = post.get("message_id") or post.get("id") or abs(hash(text)) % 10_000_000
    listing_url = str(post.get("url") or post.get("link") or f"https://t.me/{username}/{msg_id}")
    photos = list(post.get("photos") or post.get("images") or [])
    if post.get("photo"):
        photos.append(str(post["photo"]))

    published_at = post.get("published_at") or post.get("date") or post.get("created_at")

    if not make and not model:
        # Keep generic car posts searchable via description match
        make = make or "Авто"
        model = model or "—"

    return AutoSearchListing(
        source=source.name,
        source_type="telegram_channel",
        source_url=source.source_url,
        listing_url=listing_url,
        external_id=f"{source.id}_{msg_id}",
        make=make,
        model=model,
        year=year,
        price=price,
        currency=currency,
        mileage=mileage,
        fuel=fuel,
        transmission=post.get("transmission"),
        location=location,
        description=text[:500],
        photos=photos,
        published_at=str(published_at) if published_at else None,
        fetched_at=utc_now_iso(),
    )


class PublicWebAdapter(BaseSearchAdapter):
    """Public automotive sites — use connector stubs when present, else catalog seed."""

    async def search(
        self,
        source: AutoSourceConfig,
        slots: Any,
        *,
        user_id: int | None = None,
    ) -> tuple[list[AutoSearchListing], str]:
        q = _slot_query(slots)
        adapter_key = (source.metadata or {}).get("adapter") or source.id
        try:
            from connectors.automotive_marketplace_connectors import get_connector
            from database.models.automotive_marketplace import ConnectorType

            type_map = {
                "autoria": ConnectorType.AUTORIA.value,
                "olx_auto": ConnectorType.OLX_AUTO.value,
            }
            ctype = type_map.get(str(adapter_key))
            if ctype:
                connector = get_connector(ctype)
                raw = await connector.fetch_listings(None, limit=20)
                if raw:
                    listings = []
                    for row in raw:
                        listings.append(
                            AutoSearchListing(
                                source=source.name,
                                source_type="public_web",
                                source_url=source.source_url,
                                listing_url=source.source_url,
                                external_id=row.external_id,
                                make=row.make,
                                model=row.model,
                                year=row.year,
                                price=float(row.price) if row.price is not None else None,
                                currency=row.currency or "USD",
                                mileage=row.mileage,
                                fuel=row.fuel_type,
                                transmission=row.transmission,
                                location=row.location or q.get("city"),
                                description=None,
                                photos=list(row.images or []),
                                fetched_at=utc_now_iso(),
                            )
                        )
                    filtered = [x for x in listings if _match_filters(x, q)]
                    if filtered:
                        return filtered, "active"
        except Exception:
            logger.debug("public web connector path failed for %s", source.id, exc_info=True)

        return _catalog_seed(source, q), "active"


class GenericOwnerWebAdapter(BaseSearchAdapter):
    async def search(
        self,
        source: AutoSourceConfig,
        slots: Any,
        *,
        user_id: int | None = None,
    ) -> tuple[list[AutoSearchListing], str]:
        return _catalog_seed(source, _slot_query(slots)), "active"


def resolve_adapter(source: AutoSourceConfig) -> BaseSearchAdapter:
    if source.source_type == "dealer_warehouse":
        return DealerWarehouseAdapter()
    if source.source_type == "telegram_channel":
        return TelegramChannelAdapter()
    if source.source_type == "public_web":
        return PublicWebAdapter()
    return GenericOwnerWebAdapter()
