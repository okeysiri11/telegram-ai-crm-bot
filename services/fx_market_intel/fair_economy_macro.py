"""Macro calendar via public FairEconomy / ForexFactory weekly JSON."""

from __future__ import annotations

import hashlib
from typing import Any

import aiohttp

from services.fx_market_intel.macro import normalize_macro_event
from services.fx_market_intel.providers import MacroCalendarProvider, _now

CALENDAR_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
_HEADERS = {"User-Agent": "ADOS-FX-Intel/50.1"}

_TITLE_MAP = (
    ("interest rate", "fed_rate"),
    ("fed", "fed_rate"),
    ("ecb", "ecb_rate"),
    ("cpi", "cpi"),
    ("pce", "pce"),
    ("nonfarm", "nfp"),
    ("nfp", "nfp"),
    ("payroll", "nfp"),
    ("gdp", "gdp"),
    ("pmi", "pmi"),
    ("unemployment", "unemployment"),
    ("employment", "employment"),
    ("speech", "cb_speech"),
    ("fomc", "cb_speech"),
)


def _classify(title: str, country: str) -> str:
    t = (title or "").lower()
    c = (country or "").upper()
    for needle, et in _TITLE_MAP:
        if needle in t:
            if et == "fed_rate" and c in ("EUR", "EMU", "EU"):
                return "ecb_rate"
            if et == "ecb_rate" and c in ("USD", "USA", "US"):
                return "fed_rate"
            return et
    return "employment" if "job" in t else "unknown"


class FairEconomyMacroProvider(MacroCalendarProvider):
    id = "faireconomy_ff"
    label = "Экономический календарь (FairEconomy)"

    def __init__(self) -> None:
        self._last_error: str | None = None

    async def status(self) -> dict[str, Any]:
        events = await self.list_events()
        if events:
            return {
                "status": "connected",
                "label": self.label,
                "message": f"Событий на неделю: {len(events)}",
                "last_update": _now(),
            }
        return {
            "status": "error" if self._last_error else "not_connected",
            "label": self.label,
            "message": self._last_error or "Календарь пуст",
            "last_update": _now(),
        }

    async def list_events(self) -> list[dict[str, Any]]:
        try:
            timeout = aiohttp.ClientTimeout(total=20)
            async with aiohttp.ClientSession(timeout=timeout, headers=_HEADERS) as session:
                async with session.get(CALENDAR_URL) as resp:
                    if resp.status != 200:
                        self._last_error = f"Calendar HTTP {resp.status}"
                        return []
                    data = await resp.json(content_type=None)
        except Exception as exc:
            self._last_error = str(exc)
            return []
        if not isinstance(data, list):
            return []
        out: list[dict[str, Any]] = []
        for raw in data:
            title = str(raw.get("title") or "")
            country = str(raw.get("country") or "")
            # Focus USD/EUR relevance; keep High/Medium broadly
            if country.upper() not in {"USD", "EUR", "EMU", "EU", "USA", "US", "DEU", "DE", "GBP", "JPY"}:
                continue
            et = _classify(title, country)
            scheduled = raw.get("date")
            key_src = f"{title}|{country}|{scheduled}"
            external_key = hashlib.sha256(key_src.encode()).hexdigest()[:24]
            impact = str(raw.get("impact") or "Low")
            affected = ["EUR/USD", "DXY"] if country.upper() in {"USD", "EUR", "EMU", "EU", "USA", "US"} else ["EUR/USD"]
            ev = normalize_macro_event(
                {
                    "event": et,
                    "country": country,
                    "region": country,
                    "scheduled_at": scheduled,
                    "actual": raw.get("actual"),
                    "forecast": raw.get("forecast"),
                    "previous": raw.get("previous"),
                    "importance": impact.lower(),
                    "affected_instruments": affected,
                    "status": "released" if raw.get("actual") not in (None, "") else "scheduled",
                    "title": title,
                    "external_key": external_key,
                }
            )
            ev["title"] = title
            ev["external_key"] = external_key
            out.append(ev)
        out.sort(key=lambda e: str(e.get("scheduled_at") or ""))
        return out
