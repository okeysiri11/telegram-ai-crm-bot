"""Curated allowlisted RSS news — Fed + ECB. No arbitrary URL fetching."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import urlparse

import aiohttp

from services.fx_market_intel.news import normalize_article
from services.fx_market_intel.providers import NewsProvider, _now

ALLOWED_HOSTS = frozenset({
    "www.federalreserve.gov",
    "federalreserve.gov",
    "www.ecb.europa.eu",
    "ecb.europa.eu",
})

FEEDS = (
    {
        "source": "Federal Reserve",
        "url": "https://www.federalreserve.gov/feeds/press_all.xml",
        "region": "US",
        "topics": ["Fed", "USD", "Макро"],
        "instruments": ["DXY", "EUR/USD"],
    },
    {
        "source": "ECB",
        "url": "https://www.ecb.europa.eu/rss/press.html",
        "region": "EU",
        "topics": ["ECB", "EUR", "Макро"],
        "instruments": ["EUR/USD", "DXY"],
    },
)

_HEADERS = {"User-Agent": "ADOS-FX-Intel/50.1"}


def _host_ok(url: str) -> bool:
    try:
        host = urlparse(url).hostname or ""
        return host.lower() in ALLOWED_HOSTS
    except Exception:
        return False


def assess_news_impact(title: str, source: str = "") -> str:
    """Heuristic AI-оценка — never confident trade advice from weak headlines."""
    t = (title or "").lower()
    if not t or len(t) < 12:
        return "Недостаточно данных"
    hawkish = any(x in t for x in ("hike", "tightening", "higher rates", "inflation rises", "hawkish"))
    dovish = any(x in t for x in ("cut", "easing", "dovish", "lower rates", "stimulus"))
    usd_pos = any(x in t for x in ("strong dollar", "usd strength", "dollar index"))
    eur_pos = any(x in t for x in ("euro strength", "eur/", "stronger euro"))
    fed = "fed" in t or "federal reserve" in t or source.lower().startswith("federal")
    ecb = "ecb" in t or "european central" in t or source.upper() == "ECB"
    # Weak administrative/bank M&A noise → insufficient
    if any(x in t for x in ("application by", "appoints", "bancorp", "banknotes", "app to incorporate")):
        return "Нейтрально"
    if hawkish and (fed or "usd" in t):
        return "Поддерживает DXY"
    if dovish and (fed or "usd" in t):
        return "Давит на DXY"
    if hawkish and ecb:
        return "Положительно для EUR/USD"
    if dovish and ecb:
        return "Негативно для EUR/USD"
    if usd_pos:
        return "Поддерживает DXY"
    if eur_pos:
        return "Положительно для EUR/USD"
    if fed or ecb or "monetary policy" in t or "inflation" in t or "rates" in t:
        return "Нейтрально"
    return "Недостаточно данных"


def _parse_rss(xml_text: str, meta: dict[str, Any]) -> list[dict[str, Any]]:
    root = ET.fromstring(xml_text)
    items: list[dict[str, Any]] = []
    for item in root.findall("./channel/item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or item.findtext("guid") or "").strip()
        # CDATA may leave wrappers already stripped by ET
        link = re.sub(r"^<!\[CDATA\[|\]\]>$", "", link).strip()
        if not title or not _host_ok(link):
            continue
        pub = item.findtext("pubDate") or ""
        published_at = None
        try:
            if pub:
                published_at = parsedate_to_datetime(pub).astimezone(timezone.utc).isoformat()
        except Exception:
            published_at = None
        assessment = assess_news_impact(title, meta["source"])
        art = normalize_article(
            {
                "source": meta["source"],
                "title": title,
                "url": link,
                "published_at": published_at,
                "region": meta["region"],
                "instruments": meta["instruments"],
                "topics": meta["topics"],
                "importance": "medium",
                "sentiment": assessment,
                "summary": title,
                "ai_assessment": assessment,
            }
        )
        art["ai_assessment"] = assessment
        items.append(art)
    return items


class CuratedRssNewsProvider(NewsProvider):
    id = "rss_fed_ecb"
    label = "Fed + ECB (RSS)"

    async def status(self) -> dict[str, Any]:
        try:
            items = await self.fetch(instruments=["EUR/USD", "DXY"], limit=3)
            if not items:
                return {
                    "status": "error",
                    "label": self.label,
                    "message": "Лента пуста или недоступна",
                    "last_update": _now(),
                }
            return {
                "status": "connected",
                "label": self.label,
                "message": f"Загружено источников: {len(FEEDS)}",
                "last_update": _now(),
            }
        except Exception as exc:
            return {
                "status": "error",
                "label": self.label,
                "message": str(exc),
                "last_update": _now(),
            }

    async def fetch(self, *, instruments: list[str], limit: int = 20) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        timeout = aiohttp.ClientTimeout(total=25)
        async with aiohttp.ClientSession(timeout=timeout, headers=_HEADERS) as session:
            for feed in FEEDS:
                if not _host_ok(feed["url"]):
                    continue
                try:
                    async with session.get(feed["url"]) as resp:
                        if resp.status != 200:
                            continue
                        text = await resp.text()
                    out.extend(_parse_rss(text, feed))
                except Exception:
                    continue
        # Prefer instrument filter if provided
        want = {i.upper() for i in instruments} if instruments else set()
        if want:
            filtered = [
                a
                for a in out
                if want.intersection({str(x).upper() for x in (a.get("instruments") or [])})
                or want.intersection({str(x).upper() for x in (a.get("topics") or [])})
            ]
            if filtered:
                out = filtered
        out.sort(key=lambda a: a.get("published_at") or "", reverse=True)
        return out[:limit]
