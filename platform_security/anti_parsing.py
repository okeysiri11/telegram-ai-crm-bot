# Anti-parsing / anti-scraping protection — Sprint 32.4.
# Platform-layer only; verticals must call this, not reimplement.

from __future__ import annotations

import hashlib
import time
from collections import defaultdict
from typing import Any


class AntiParsingProtection:
    """Bot / crawler / scraping detection with adaptive rate signals."""

    PROTECTED_SURFACES = (
        "enterprise_city",
        "knowledge_base",
        "api",
        "marketplace",
    )

    def __init__(self) -> None:
        self._hits: dict[str, list[float]] = defaultdict(list)
        self._blocked = 0
        self._challenged = 0
        self._window = 60.0
        self._soft_limit = 60
        self._hard_limit = 120

    def reset(self) -> None:
        self._hits.clear()
        self._blocked = 0
        self._challenged = 0

    def fingerprint(self, *, ip: str, ua: str, path: str) -> str:
        raw = f"{ip}|{ua}|{path}".encode()
        return hashlib.sha256(raw).hexdigest()[:24]

    def analyze(
        self,
        *,
        ip: str,
        user_agent: str = "",
        path: str = "/",
        surface: str = "api",
        session_token: str | None = None,
    ) -> dict[str, Any]:
        ua = (user_agent or "").lower()
        reasons: list[str] = []
        bot_markers = ("bot", "crawler", "spider", "scrapy", "httpclient", "python-requests", "curl/")
        if any(m in ua for m in bot_markers):
            reasons.append("crawler_ua")
        if not ua:
            reasons.append("missing_ua")
        if surface not in self.PROTECTED_SURFACES:
            surface = "api"

        fp = self.fingerprint(ip=ip, ua=user_agent, path=path)
        now = time.time()
        bucket = [t for t in self._hits[fp] if now - t < self._window]
        bucket.append(now)
        self._hits[fp] = bucket
        count = len(bucket)

        challenge = False
        blocked = False
        if count > self._hard_limit or "crawler_ua" in reasons:
            blocked = True
            self._blocked += 1
            reasons.append("rate_hard_limit" if count > self._hard_limit else "bot_detected")
        elif count > self._soft_limit:
            challenge = True
            self._challenged += 1
            reasons.append("adaptive_challenge")

        session_ok = True
        if session_token is not None and not session_token:
            session_ok = False
            reasons.append("session_integrity")
            blocked = True
            self._blocked += 1

        return {
            "ok": not blocked,
            "challenge": challenge,
            "fingerprint": fp,
            "request_count": count,
            "surface": surface,
            "reasons": reasons,
            "session_integrity": session_ok,
            "behavior": "suspicious" if reasons else "normal",
        }

    def analytics(self) -> dict[str, Any]:
        return {
            "blocked": self._blocked,
            "challenged": self._challenged,
            "tracked_fingerprints": len(self._hits),
            "protected_surfaces": list(self.PROTECTED_SURFACES),
        }

    def capabilities(self) -> dict[str, Any]:
        return {
            "bot_detection": True,
            "crawler_detection": True,
            "scraping_detection": True,
            "behavior_analysis": True,
            "request_fingerprinting": True,
            "adaptive_rate_limiting": True,
            "dynamic_challenge": True,
            "session_integrity": True,
            "access_pattern_analysis": True,
            "surfaces": list(self.PROTECTED_SURFACES),
        }
