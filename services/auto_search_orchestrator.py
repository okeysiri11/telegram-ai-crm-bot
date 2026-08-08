"""Sprint 46.1 — Auto Search Orchestrator (parallel multi-source search)."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from services.auto_search_adapters import resolve_adapter
from services.auto_source_models import AutoSearchListing, AutoSourceConfig
from services.auto_source_registry import auto_source_registry

logger = logging.getLogger(__name__)

# Priority bands (ranking weight only — never excludes enabled sources)
PRIORITY_WEIGHT = {
    "dealer_warehouse": 1000,
    "telegram_channel": 800,
    "dealer_source": 600,
    "public_web": 400,
}


class AutoSearchOrchestrator:
    """
    CLIENT QUERY → Conversation → slots → here:

    parallel:
      A. dealer / telegram sources
      B. public web (AUTO.RIA / OLX / RST / …)

    → normalize → dedupe → rank → cards
    """

    def __init__(self, registry=auto_source_registry) -> None:
        self.registry = registry

    async def search(
        self,
        slots: Any,
        *,
        user_id: int | None = None,
        settings: dict[str, Any] | None = None,
        mode: str = "fast",
    ) -> dict[str, Any]:
        settings = settings or {}
        preferred = set(settings.get("preferred_sources") or [])
        excluded = set(settings.get("excluded_sources") or [])
        sources = [
            s
            for s in self.registry.list_enabled()
            if s.id not in excluded
        ]
        if not sources:
            return {"listings": [], "by_source": {}, "statuses": {}, "sources_queried": []}

        async def _one(src: AutoSourceConfig) -> tuple[str, list[AutoSearchListing], str]:
            adapter = resolve_adapter(src)
            try:
                items, status = await adapter.search(src, slots, user_id=user_id)
                if status != src.status:
                    self.registry.set_status(src.id, status)
                return src.id, items, status
            except Exception:
                logger.warning("source %s failed", src.id, exc_info=True)
                self.registry.set_status(src.id, "unavailable")
                return src.id, [], "unavailable"

        results = await asyncio.gather(*[_one(s) for s in sources])
        by_source: dict[str, list[dict[str, Any]]] = {}
        statuses: dict[str, str] = {}
        merged: list[AutoSearchListing] = []
        for sid, items, status in results:
            statuses[sid] = status
            by_source[sid] = [x.to_dict() for x in items]
            merged.extend(items)

        normalized = self._normalize(merged)
        deduped = self._dedupe(normalized)
        ranked = self._rank(deduped, sources, preferred=preferred)

        limit = int(settings.get("max_results", 7))
        if mode == "fast":
            limit = min(limit, 7)
        elif mode == "deep":
            limit = max(limit, 15)

        cards = [x.to_dict() for x in ranked[:limit]]
        return {
            "listings": cards,
            "by_source": by_source,
            "statuses": statuses,
            "sources_queried": [s.id for s in sources],
            "total_raw": len(merged),
            "total_deduped": len(deduped),
        }

    def _normalize(self, items: list[AutoSearchListing]) -> list[AutoSearchListing]:
        out: list[AutoSearchListing] = []
        for it in items:
            it.make = (it.make or "").strip()
            it.model = (it.model or "").strip()
            if it.fuel:
                low = it.fuel.lower()
                if "диз" in low or "diesel" in low:
                    it.fuel = "дизель"
                elif "бенз" in low or "petrol" in low or "gas" in low:
                    it.fuel = "бензин"
                elif "гибр" in low or "hybrid" in low:
                    it.fuel = "гибрид"
                elif "элект" in low or "electric" in low:
                    it.fuel = "электро"
            out.append(it)
        return out

    def _dedupe(self, items: list[AutoSearchListing]) -> list[AutoSearchListing]:
        seen: set[str] = set()
        out: list[AutoSearchListing] = []
        for it in items:
            key = "|".join(
                [
                    (it.make or "").lower(),
                    (it.model or "").lower(),
                    str(it.year or ""),
                    str(int(it.price) if it.price is not None else ""),
                    (it.location or "").lower()[:8],
                    str(it.mileage or ""),
                ]
            )
            if key in seen:
                continue
            seen.add(key)
            out.append(it)
        return out

    def _rank(
        self,
        items: list[AutoSearchListing],
        sources: list[AutoSourceConfig],
        *,
        preferred: set[str],
    ) -> list[AutoSearchListing]:
        prio = {s.name: s.priority for s in sources}

        def score(it: AutoSearchListing) -> tuple:
            type_w = PRIORITY_WEIGHT.get(it.source_type, 100)
            # Lower registry priority number → higher score
            reg_priority = prio.get(getattr(it, "source", ""), 50)
            reg_p = 100 - min(99, int(reg_priority))
            src_name = getattr(it, "source", "") or ""
            src_url = getattr(it, "source_url", "") or ""
            pref = 50 if src_name in preferred or any(p in src_url for p in preferred) else 0
            price = -(it.price or 0)
            year = it.year or 0
            return (type_w + reg_p + pref, year, price)

        return sorted(items, key=score, reverse=True)


auto_search_orchestrator = AutoSearchOrchestrator()
