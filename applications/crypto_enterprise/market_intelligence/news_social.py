"""News and social intelligence."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.crypto_enterprise.shared.exceptions import ValidationError
from applications.crypto_enterprise.shared.store import CryptoEnterpriseStore, crypto_enterprise_store

NEWS_CLASSES = ["general", "breaking", "etf", "exchange", "project", "macro", "regulatory"]
SOCIAL_SOURCES = ["x", "telegram", "reddit", "youtube", "discord"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class NewsIntelligence:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store

    def aggregate(self, *, source: str, headline: str, url: str = "") -> dict[str, Any]:
        if not source or not headline:
            raise ValidationError("source and headline required")
        nid = _id("mi_news")
        return self.store.mi_news_feed.save(
            nid,
            {
                "news_id": nid,
                "source": source,
                "headline": headline,
                "url": url,
                "at": _now(),
            },
        )

    def classify(self, *, news_id: str, category: str) -> dict[str, Any]:
        if category not in NEWS_CLASSES:
            raise ValidationError(f"category must be one of {NEWS_CLASSES}")
        if self.store.mi_news_feed.get(news_id) is None:
            raise ValidationError("news_id not found")
        cid = _id("mi_ncls")
        return self.store.mi_news_class.save(
            cid,
            {
                "classification_id": cid,
                "news_id": news_id,
                "category": category,
                "at": _now(),
            },
        )

    def breaking(self, *, headline: str, severity: float) -> dict[str, Any]:
        severity = float(severity)
        if severity < 0 or severity > 1:
            raise ValidationError("severity must be 0..1")
        bid = _id("mi_break")
        return self.store.mi_breaking.save(
            bid,
            {
                "breaking_id": bid,
                "headline": headline,
                "severity": severity,
                "detected": severity >= 0.7,
                "at": _now(),
            },
        )

    def economic_calendar(self, *, events: list[dict[str, Any]]) -> dict[str, Any]:
        if not events:
            raise ValidationError("events required")
        eid = _id("mi_econ")
        return self.store.mi_econ_calendar.save(
            eid,
            {"calendar_id": eid, "events": events, "at": _now()},
        )

    def crypto_events(self, *, events: list[dict[str, Any]]) -> dict[str, Any]:
        if not events:
            raise ValidationError("events required")
        eid = _id("mi_cevt")
        return self.store.mi_crypto_events.save(
            eid,
            {"calendar_id": eid, "events": events, "at": _now()},
        )

    def etf_news(self, *, ticker: str, headline: str) -> dict[str, Any]:
        if not ticker or not headline:
            raise ValidationError("ticker and headline required")
        eid = _id("mi_etf")
        return self.store.mi_etf_news.save(
            eid,
            {"etf_news_id": eid, "ticker": ticker.upper(), "headline": headline, "at": _now()},
        )

    def exchange_announcement(self, *, exchange: str, title: str) -> dict[str, Any]:
        if not exchange or not title:
            raise ValidationError("exchange and title required")
        aid = _id("mi_xann")
        return self.store.mi_exchange_ann.save(
            aid,
            {"announcement_id": aid, "exchange": exchange.lower(), "title": title, "at": _now()},
        )

    def project_announcement(self, *, project: str, title: str) -> dict[str, Any]:
        if not project or not title:
            raise ValidationError("project and title required")
        pid = _id("mi_pann")
        return self.store.mi_project_ann.save(
            pid,
            {"announcement_id": pid, "project": project, "title": title, "at": _now()},
        )

    def status(self) -> dict[str, Any]:
        return {
            "feed": self.store.mi_news_feed.count(),
            "breaking": self.store.mi_breaking.count(),
            "etf": self.store.mi_etf_news.count(),
            "exchange_ann": self.store.mi_exchange_ann.count(),
        }


class SocialIntelligence:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store

    def analyze_source(self, *, source: str, handle: str, mentions: int, engagement: float) -> dict[str, Any]:
        if source not in SOCIAL_SOURCES:
            raise ValidationError(f"source must be one of {SOCIAL_SOURCES}")
        if not handle:
            raise ValidationError("handle required")
        sid = _id("mi_soc")
        return self.store.mi_social.save(
            sid,
            {
                "analysis_id": sid,
                "source": source,
                "handle": handle,
                "mentions": int(mentions),
                "engagement": float(engagement),
                "at": _now(),
            },
        )

    def influencer(self, *, handle: str, platform: str, followers: int, influence_score: float) -> dict[str, Any]:
        iid = _id("mi_infl")
        return self.store.mi_influencers.save(
            iid,
            {
                "influencer_id": iid,
                "handle": handle,
                "platform": platform,
                "followers": int(followers),
                "influence_score": float(influence_score),
                "at": _now(),
            },
        )

    def trending(self, *, topics: list[str]) -> dict[str, Any]:
        if not topics:
            raise ValidationError("topics required")
        tid = _id("mi_trend")
        return self.store.mi_trending.save(
            tid,
            {"trend_id": tid, "topics": topics, "at": _now()},
        )

    def hashtags(self, *, tags: list[str], volume: int) -> dict[str, Any]:
        if not tags:
            raise ValidationError("tags required")
        hid = _id("mi_hash")
        return self.store.mi_hashtags.save(
            hid,
            {"hashtag_id": hid, "tags": tags, "volume": int(volume), "at": _now()},
        )

    def status(self) -> dict[str, Any]:
        return {
            "social": self.store.mi_social.count(),
            "influencers": self.store.mi_influencers.count(),
            "trending": self.store.mi_trending.count(),
        }
