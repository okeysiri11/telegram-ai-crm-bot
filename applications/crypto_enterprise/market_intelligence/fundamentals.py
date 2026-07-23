"""Sentiment, fundamental, and macro intelligence."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.crypto_enterprise.shared.exceptions import ValidationError
from applications.crypto_enterprise.shared.store import CryptoEnterpriseStore, crypto_enterprise_store

SENTIMENT_LABELS = ["bullish", "bearish", "neutral"]
MACRO_TYPES = [
    "fed",
    "inflation",
    "interest_rate",
    "employment",
    "gdp",
    "global",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class SentimentIntelligence:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store

    def market_index(self, *, score: float, label: str = "") -> dict[str, Any]:
        score = float(score)
        if score < 0 or score > 100:
            raise ValidationError("score must be 0..100")
        if not label:
            label = "bullish" if score >= 60 else "bearish" if score <= 40 else "neutral"
        if label not in SENTIMENT_LABELS:
            raise ValidationError(f"label must be one of {SENTIMENT_LABELS}")
        sid = _id("mi_sent")
        return self.store.mi_sentiment_index.save(
            sid,
            {"index_id": sid, "score": score, "label": label, "at": _now()},
        )

    def fear_greed(self, *, value: int) -> dict[str, Any]:
        value = int(value)
        if value < 0 or value > 100:
            raise ValidationError("value must be 0..100")
        fid = _id("mi_fg")
        band = (
            "extreme_fear"
            if value <= 25
            else "fear"
            if value <= 45
            else "neutral"
            if value < 55
            else "greed"
            if value < 75
            else "extreme_greed"
        )
        return self.store.mi_fear_greed.save(
            fid,
            {"fg_id": fid, "value": value, "band": band, "at": _now()},
        )

    def classify(self, *, text: str, label: str, confidence: float) -> dict[str, Any]:
        if label not in SENTIMENT_LABELS:
            raise ValidationError(f"label must be one of {SENTIMENT_LABELS}")
        confidence = float(confidence)
        if confidence < 0 or confidence > 1:
            raise ValidationError("confidence must be 0..1")
        cid = _id("mi_scls")
        return self.store.mi_sentiment_class.save(
            cid,
            {
                "classification_id": cid,
                "text": text[:240],
                "label": label,
                "confidence": confidence,
                "at": _now(),
            },
        )

    def history(self, *, points: list[dict[str, Any]]) -> dict[str, Any]:
        if not points:
            raise ValidationError("points required")
        hid = _id("mi_shist")
        return self.store.mi_sentiment_history.save(
            hid,
            {"history_id": hid, "points": points, "at": _now()},
        )

    def trend(self, *, direction: str, strength: float) -> dict[str, Any]:
        if direction not in ("up", "down", "flat"):
            raise ValidationError("direction must be up|down|flat")
        tid = _id("mi_strend")
        return self.store.mi_sentiment_trend.save(
            tid,
            {
                "trend_id": tid,
                "direction": direction,
                "strength": float(strength),
                "at": _now(),
            },
        )

    def regional(self, *, region: str, score: float, label: str) -> dict[str, Any]:
        if label not in SENTIMENT_LABELS:
            raise ValidationError(f"label must be one of {SENTIMENT_LABELS}")
        rid = _id("mi_sreg")
        return self.store.mi_sentiment_regional.save(
            rid,
            {
                "regional_id": rid,
                "region": region,
                "score": float(score),
                "label": label,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "index": self.store.mi_sentiment_index.count(),
            "fear_greed": self.store.mi_fear_greed.count(),
            "classifications": self.store.mi_sentiment_class.count(),
            "trends": self.store.mi_sentiment_trend.count(),
        }


class FundamentalIntelligence:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store

    def register_project(self, *, name: str, symbol: str, category: str = "protocol") -> dict[str, Any]:
        if not name or not symbol:
            raise ValidationError("name and symbol required")
        pid = _id("mi_proj")
        return self.store.mi_projects.save(
            pid,
            {
                "project_id": pid,
                "name": name,
                "symbol": symbol.upper(),
                "category": category,
                "at": _now(),
            },
        )

    def token_fundamentals(self, *, symbol: str, market_cap: float, fdv: float, holders: int) -> dict[str, Any]:
        tid = _id("mi_tfund")
        return self.store.mi_token_fundamentals.save(
            tid,
            {
                "fundamentals_id": tid,
                "symbol": symbol.upper(),
                "market_cap": float(market_cap),
                "fdv": float(fdv),
                "holders": int(holders),
                "at": _now(),
            },
        )

    def unlock_calendar(self, *, symbol: str, unlocks: list[dict[str, Any]]) -> dict[str, Any]:
        if not unlocks:
            raise ValidationError("unlocks required")
        uid = _id("mi_unlk")
        return self.store.mi_unlocks.save(
            uid,
            {"calendar_id": uid, "symbol": symbol.upper(), "unlocks": unlocks, "at": _now()},
        )

    def tokenomics(self, *, symbol: str, circulating_pct: float, inflation_pct: float) -> dict[str, Any]:
        tid = _id("mi_tomo")
        return self.store.mi_tokenomics.save(
            tid,
            {
                "tokenomics_id": tid,
                "symbol": symbol.upper(),
                "circulating_pct": float(circulating_pct),
                "inflation_pct": float(inflation_pct),
                "at": _now(),
            },
        )

    def developer_activity(self, *, symbol: str, commits_30d: int, contributors: int) -> dict[str, Any]:
        did = _id("mi_dev")
        return self.store.mi_dev_activity.save(
            did,
            {
                "activity_id": did,
                "symbol": symbol.upper(),
                "commits_30d": int(commits_30d),
                "contributors": int(contributors),
                "at": _now(),
            },
        )

    def github_activity(self, *, repo: str, stars: int, forks: int, open_issues: int) -> dict[str, Any]:
        gid = _id("mi_gh")
        return self.store.mi_github.save(
            gid,
            {
                "github_id": gid,
                "repo": repo,
                "stars": int(stars),
                "forks": int(forks),
                "open_issues": int(open_issues),
                "at": _now(),
            },
        )

    def partnership(self, *, project: str, partner: str, kind: str = "strategic") -> dict[str, Any]:
        pid = _id("mi_part")
        return self.store.mi_partnerships.save(
            pid,
            {
                "partnership_id": pid,
                "project": project,
                "partner": partner,
                "kind": kind,
                "at": _now(),
            },
        )

    def protocol_update(self, *, protocol: str, version: str, summary: str) -> dict[str, Any]:
        uid = _id("mi_pupd")
        return self.store.mi_protocol_updates.save(
            uid,
            {
                "update_id": uid,
                "protocol": protocol,
                "version": version,
                "summary": summary,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "projects": self.store.mi_projects.count(),
            "fundamentals": self.store.mi_token_fundamentals.count(),
            "unlocks": self.store.mi_unlocks.count(),
            "github": self.store.mi_github.count(),
        }


class MacroIntelligence:
    def __init__(self, store: CryptoEnterpriseStore | None = None) -> None:
        self.store = store or crypto_enterprise_store

    def event(self, *, event_type: str, title: str, scheduled_at: str, impact: str = "high") -> dict[str, Any]:
        if event_type not in MACRO_TYPES:
            raise ValidationError(f"event_type must be one of {MACRO_TYPES}")
        if not title:
            raise ValidationError("title required")
        eid = _id("mi_macro")
        return self.store.mi_macro_events.save(
            eid,
            {
                "event_id": eid,
                "event_type": event_type,
                "title": title,
                "scheduled_at": scheduled_at,
                "impact": impact,
                "at": _now(),
            },
        )

    def fed(self, *, title: str, scheduled_at: str) -> dict[str, Any]:
        return self.event(event_type="fed", title=title, scheduled_at=scheduled_at)

    def inflation(self, *, title: str, scheduled_at: str) -> dict[str, Any]:
        return self.event(event_type="inflation", title=title, scheduled_at=scheduled_at)

    def interest_rate(self, *, title: str, scheduled_at: str) -> dict[str, Any]:
        return self.event(event_type="interest_rate", title=title, scheduled_at=scheduled_at)

    def employment(self, *, title: str, scheduled_at: str) -> dict[str, Any]:
        return self.event(event_type="employment", title=title, scheduled_at=scheduled_at)

    def gdp(self, *, title: str, scheduled_at: str) -> dict[str, Any]:
        return self.event(event_type="gdp", title=title, scheduled_at=scheduled_at)

    def global_macro(self, *, title: str, scheduled_at: str) -> dict[str, Any]:
        return self.event(event_type="global", title=title, scheduled_at=scheduled_at)

    def status(self) -> dict[str, Any]:
        return {"events": self.store.mi_macro_events.count(), "types": list(MACRO_TYPES)}
