"""News article normalization + deduplication."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from services.fx_market_intel.providers import news_fingerprint
from services.fx_market_intel.symbols import normalize_symbol


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_article(raw: dict[str, Any]) -> dict[str, Any]:
    title = str(raw.get("title") or raw.get("headline") or "").strip()
    url = str(raw.get("url") or raw.get("reference") or "").strip()
    published = str(raw.get("published_at") or raw.get("published") or "")
    instruments = [normalize_symbol(x) for x in (raw.get("instruments") or []) if x]
    instruments = [x for x in instruments if x]
    fid = news_fingerprint(title, url, published)
    return {
        "id": str(raw.get("id") or f"news_{uuid.uuid4().hex[:12]}"),
        "source": str(raw.get("source") or ""),
        "title": title,
        "url": url,
        "reference": url,
        "published_at": published or None,
        "fetched_at": str(raw.get("fetched_at") or _now()),
        "region": str(raw.get("region") or ""),
        "instruments": instruments,
        "topics": list(raw.get("topics") or []),
        "importance": raw.get("importance"),
        "sentiment": raw.get("sentiment"),
        "summary": str(raw.get("summary") or ""),
        "duplicate_group_id": fid,
    }


def dedupe_articles(articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for raw in articles:
        art = normalize_article(raw)
        if not art["title"]:
            continue
        gid = art["duplicate_group_id"]
        if gid in seen:
            continue
        seen.add(gid)
        out.append(art)
    return out
