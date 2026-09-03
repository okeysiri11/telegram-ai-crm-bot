"""Canonical FX market intelligence facade — Web and Telegram must call this."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import math
import time

from services.fx_market_intel.consensus import build_consensus
from services.fx_market_intel.correlation import eurusd_dxy_correlation
from services.fx_market_intel.fair_economy_macro import FairEconomyMacroProvider
from services.fx_market_intel.macro import empty_calendar_state, normalize_macro_event
from services.fx_market_intel.memory import list_analyses, performance_metrics
from services.fx_market_intel.news import dedupe_articles, normalize_article
from services.fx_market_intel.persistence import (
    get_history_detail,
    list_history,
    persist_full_analysis,
    persist_macro_events,
    persist_news_items,
)
from services.fx_market_intel.providers import (
    MacroCalendarProvider,
    MarketDataProvider,
    NewsProvider,
    NullMarketDataProvider,
)
from services.fx_market_intel.rss_news import CuratedRssNewsProvider
from services.fx_market_intel.signals import SIGNAL_STATUSES, assert_no_trade_execution, create_signal
from services.fx_market_intel.symbols import CORE_INSTRUMENTS, normalize_symbol
from services.fx_market_intel.technical import compute_indicators
from services.fx_market_intel.candle_feed import cached_quote, get_candles
from services.fx_market_intel.yahoo_feed import (
    DXY_SUPPORTED_TIMEFRAMES,
    SUPPORTED_TIMEFRAMES,
    EurUsdMarketQuoteProvider,
    YahooQuoteProvider,
)

ANALYSIS_PRESETS = [
    {
        "id": "morning",
        "name": "Утренний обзор",
        "instruments": ["EUR/USD", "DXY"],
        "sections": {
            "technical": True,
            "dxy": True,
            "macro": True,
            "news": True,
            "europe": True,
            "us": True,
            "asia": False,
        },
    },
    {
        "id": "pre_europe",
        "name": "Перед Европой",
        "instruments": ["EUR/USD", "DXY"],
        "sections": {
            "technical": True,
            "dxy": True,
            "macro": True,
            "news": True,
            "europe": True,
            "us": False,
            "asia": False,
        },
    },
    {
        "id": "pre_us",
        "name": "Перед США",
        "instruments": ["EUR/USD", "DXY"],
        "sections": {
            "technical": True,
            "dxy": True,
            "macro": True,
            "news": True,
            "europe": False,
            "us": True,
            "asia": False,
        },
    },
    {
        "id": "pre_trade",
        "name": "Перед торговлей",
        "instruments": ["EUR/USD", "DXY"],
        "sections": {
            "technical": True,
            "dxy": True,
            "macro": True,
            "news": False,
            "europe": True,
            "us": True,
            "asia": False,
        },
    },
    {
        "id": "event",
        "name": "Событийный анализ",
        "instruments": ["EUR/USD", "DXY"],
        "sections": {
            "technical": False,
            "dxy": True,
            "macro": True,
            "news": True,
            "europe": True,
            "us": True,
            "asia": False,
        },
    },
    {
        "id": "evening",
        "name": "Вечерний обзор",
        "instruments": ["EUR/USD", "DXY"],
        "sections": {
            "technical": True,
            "dxy": True,
            "macro": True,
            "news": True,
            "europe": True,
            "us": True,
            "asia": False,
        },
    },
]

SPECIALISTS = [
    {"id": "eurusd_structure", "name": "EUR/USD Structure Agent", "instruments": ["EUR/USD"]},
    {"id": "dxy", "name": "DXY Agent", "instruments": ["DXY"]},
    {"id": "technical", "name": "Technical Agent", "instruments": ["EUR/USD", "DXY"]},
    {"id": "macro", "name": "Macro Agent", "instruments": ["EUR/USD", "DXY"]},
    {"id": "news", "name": "News Agent", "instruments": ["EUR/USD", "DXY"]},
    {"id": "europe", "name": "Europe Session Agent", "instruments": ["EUR/USD"]},
    {"id": "us", "name": "US Session Agent", "instruments": ["EUR/USD", "DXY"]},
    {"id": "risk", "name": "Risk Agent", "instruments": ["EUR/USD", "DXY"]},
    {"id": "chief", "name": "Chief Analyst", "instruments": ["EUR/USD", "DXY"]},
]

_DIR_RU = {
    "BUY_BIAS": "Склонность к покупке",
    "SELL_BIAS": "Склонность к продаже",
    "WATCH_BUY": "Склонность к покупке",
    "WATCH_SELL": "Склонность к продаже",
    "NEUTRAL": "Нейтрально",
    "WAIT": "Ждать",
    "HIGH_RISK": "Ждать",
    "NO_SIGNAL": "Ждать",
    "BULLISH": "Склонность к покупке",
    "BEARISH": "Склонность к продаже",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _signal_ru(status: str) -> str:
    return {
        "BUY_BIAS": "Склонность к покупке",
        "SELL_BIAS": "Склонность к продаже",
        "WATCH_BUY": "Наблюдать покупку",
        "WATCH_SELL": "Наблюдать продажу",
        "WAIT": "Ждать",
        "HIGH_RISK": "Высокий риск",
        "NO_SIGNAL": "Нет сигнала",
        "NEUTRAL": "Ждать",
        "EXPIRED": "Истёк",
    }.get(status, status)


LIVE_MAX_AGE_SEC = 15 * 60


def _finite_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        n = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(n):
        return None
    return n


def classify_fx_quote_status(quote: dict[str, Any]) -> str:
    """Honest live/delayed/error. Never treat fetch-clock as market time."""
    price = _finite_float(quote.get("price") if quote.get("price") is not None else quote.get("mid"))
    raw = str(quote.get("status") or "")
    if price is None:
        return "error"
    if raw in {"error", "not_connected", "needs_config"}:
        return "error" if raw == "error" else raw
    provider = str(quote.get("provider") or quote.get("source") or "")
    freshness = str(quote.get("freshness") or "")
    if "nbu" in provider.lower() or "nbu" in freshness.lower():
        return "delayed"
    market_time = quote.get("market_time")
    try:
        market_unix = float(market_time) if market_time is not None else None
    except (TypeError, ValueError):
        market_unix = None
    if market_unix is None:
        return "delayed"
    age = time.time() - market_unix
    if -60 <= age <= LIVE_MAX_AGE_SEC:
        return "live"
    return "delayed"


def normalize_public_quote(quote: dict[str, Any]) -> dict[str, Any]:
    """Additive public quote shape. Existing mid/bid/ask/source fields stay."""
    out = dict(quote)
    price = _finite_float(out.get("mid") if out.get("mid") is not None else out.get("price"))
    out["price"] = price
    market_time = out.get("market_time")
    try:
        market_unix = float(market_time) if market_time is not None else None
    except (TypeError, ValueError):
        market_unix = None
    out["timestamp"] = int(market_unix * 1000) if market_unix else None
    out["status"] = classify_fx_quote_status({**out, "price": price})
    return out


class FxMarketIntelService:
    def __init__(
        self,
        eurusd_provider: MarketDataProvider | None = None,
        dxy_provider: MarketDataProvider | None = None,
        news_provider: NewsProvider | None = None,
        macro_provider: MacroCalendarProvider | None = None,
    ) -> None:
        self.eurusd = eurusd_provider or EurUsdMarketQuoteProvider()
        self.dxy = dxy_provider or YahooQuoteProvider(instrument="DXY")
        self.news = news_provider or CuratedRssNewsProvider()
        self.macro = macro_provider or FairEconomyMacroProvider()
        self._signals: list[dict[str, Any]] = []
        self._scheduler_wired = True  # jobs registered in pg_scheduler_engine

    async def connection_health(self) -> dict[str, Any]:
        e = await self.eurusd.status()
        d = await self.dxy.status()
        n = await self.news.status()
        m = await self.macro.status()
        return {
            "quotes": e,
            "dxy": d,
            "tradingview": {
                "status": "partial",
                "label": "TradingView",
                "message": "EUR/USD и DXY: нативный Lightweight Charts (Yahoo). TradingView не используется.",
            },
            "news": n,
            "macro_calendar": m,
            "ai_analysis": {
                "status": "configured",
                "label": "AI-анализ",
                "message": "Консенсус специалистов по доступным данным",
            },
            "scheduler": {
                "status": "connected" if self._scheduler_wired else "not_connected",
                "label": "Расписание",
                "message": "Профили анализа в планировщике платформы"
                if self._scheduler_wired
                else "Автодоставка не настроена",
            },
            "notifications": {
                "status": "needs_config",
                "label": "Уведомления",
                "message": "Требуется настройка канала",
            },
            "persistence": {
                "status": "configured",
                "label": "Хранение анализов",
                "message": "Postgres fx_mi_* (fallback: память процесса)",
            },
        }

    async def quote(self, symbol: str) -> dict[str, Any]:
        sym = normalize_symbol(symbol)
        if sym == "DXY":
            async def _dxy() -> dict[str, Any]:
                q = await self.dxy.get_quote("DXY")
                q.setdefault("provider", getattr(self.dxy, "id", "yahoo_dxy"))
                return q

            return await cached_quote("DXY", _dxy)
        if sym == "EUR/USD":
            async def _eur() -> dict[str, Any]:
                q = await self.eurusd.get_quote("EUR/USD")
                q.setdefault("provider", getattr(self.eurusd, "id", "yahoo_eurusd"))
                return normalize_public_quote(q)

            return await cached_quote("EUR/USD", _eur)
        return await NullMarketDataProvider().get_quote(sym)

    async def candles(self, symbol: str, timeframe: str = "1H") -> dict[str, Any]:
        return await get_candles(symbol, timeframe)

    async def desk_snapshot(self, tenant_id: str = "default") -> dict[str, Any]:
        eurusd = await self.quote("EUR/USD")
        dxy = await self.quote("DXY")
        health = await self.connection_health()
        e_bars = await get_candles("EUR/USD", "1H")
        d_bars = await get_candles("DXY", "1H")
        e_closes = [b["c"] for b in (e_bars.get("bars") or [])[-40:]]
        d_closes = [b["c"] for b in (d_bars.get("bars") or [])[-40:]]
        corr = eurusd_dxy_correlation(e_closes, d_closes)
        return {
            "core_instruments": list(CORE_INSTRUMENTS),
            "eurusd": eurusd,
            "dxy": dxy,
            "correlation": corr,
            "health": health,
            "analysis_presets": ANALYSIS_PRESETS,
            "specialists": SPECIALISTS,
            "signals": await self.list_signals(tenant_id),
            "scheduler_message": health["scheduler"]["message"],
            "disclaimer": "AI-анализ, не является гарантией результата.",
            "tradingview": {
                "EUR/USD": None,
                "DXY": None,
                "EURUSD_note_ru": "EUR/USD рендерится нативным Lightweight Charts по барам Yahoo (EURUSD=X), не через FX:EURUSD.",
                "DXY_note_ru": "DXY рендерится нативным Lightweight Charts по барам Yahoo (DX-Y.NYB), не через TVC:DXY.",
            },
            "eurusd_chart": {
                "engine": "ados_lightweight_charts",
                "endpoint": "/api/crypto-mi/v1/fx-intel/candles?symbol=EUR/USD",
                "provider": "yahoo",
                "yahoo_symbol": "EURUSD=X",
                "supported_timeframes": list(SUPPORTED_TIMEFRAMES),
            },
            "dxy_chart": {
                "engine": "ados_lightweight_charts",
                "endpoint": "/api/crypto-mi/v1/fx-intel/candles?symbol=DXY",
                "provider": "yahoo",
                "yahoo_symbol": "DX-Y.NYB",
                "supported_timeframes": list(DXY_SUPPORTED_TIMEFRAMES),
            },
        }

    def technical(self, bars: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        return compute_indicators(bars or [])

    async def technical_live(self, symbol: str = "EUR/USD", timeframe: str = "1H") -> dict[str, Any]:
        pack = await get_candles(symbol, timeframe)
        ind = compute_indicators(pack.get("bars") or [])
        return {**ind, "symbol": symbol, "timeframe": timeframe, "bars_status": pack.get("status"), "source": pack.get("source")}

    def correlation(self, eurusd_closes: list[float], dxy_closes: list[float]) -> dict[str, Any]:
        return eurusd_dxy_correlation(eurusd_closes, dxy_closes)

    async def news_feed(self, instruments: list[str] | None = None, filter_key: str | None = None) -> dict[str, Any]:
        status = await self.news.status()
        items = await self.news.fetch(instruments=instruments or ["EUR/USD", "DXY"], limit=40)
        deduped = dedupe_articles(items)
        await persist_news_items(deduped)
        fk = (filter_key or "Все").strip()
        if fk and fk != "Все":
            fl = fk.lower()
            filtered = []
            for a in deduped:
                blob = " ".join(
                    [
                        str(a.get("title") or ""),
                        " ".join(a.get("topics") or []),
                        " ".join(a.get("instruments") or []),
                        str(a.get("region") or ""),
                        str(a.get("source") or ""),
                    ]
                ).lower()
                if fl in blob or fk in (a.get("instruments") or []) or fk in (a.get("topics") or []):
                    filtered.append(a)
            deduped = filtered
        return {"provider": status, "items": deduped, "count": len(deduped), "filter": fk}

    def ingest_news(self, articles: list[dict[str, Any]]) -> dict[str, Any]:
        items = dedupe_articles([normalize_article(a) for a in articles])
        return {"items": items, "count": len(items)}

    async def macro_calendar(self) -> dict[str, Any]:
        status = await self.macro.status()
        raw = await self.macro.list_events()
        events = []
        for e in raw:
            ev = normalize_macro_event(e)
            if e.get("title"):
                ev["title"] = e["title"]
            if e.get("external_key"):
                ev["external_key"] = e["external_key"]
            events.append(ev)
        await persist_macro_events(raw)
        if status.get("status") != "connected":
            base = empty_calendar_state()
            base["provider"] = status
            return base
        return {"status": "connected", "provider": status, "events": events, "message": "OK"}

    def _vote_from_ta(self, ta: dict[str, Any]) -> tuple[str, float]:
        if ta.get("status") != "ok":
            return "WAIT", 0.2
        return str(ta.get("bias") or "NEUTRAL"), 0.55 if ta.get("bias") != "NEUTRAL" else 0.4

    def _dxy_vote(self, dxy_q: dict[str, Any], dxy_ta: dict[str, Any], corr: dict[str, Any]) -> tuple[str, float]:
        if dxy_q.get("status") != "connected":
            return "WAIT", 0.15
        bias = dxy_ta.get("bias") if dxy_ta.get("status") == "ok" else "NEUTRAL"
        # Strong DXY often pressures EUR/USD
        if bias == "WATCH_BUY":
            return "WATCH_SELL", 0.55  # DXY up → EUR/USD watch sell
        if bias == "WATCH_SELL":
            return "WATCH_BUY", 0.55
        coef = corr.get("coefficient")
        if coef is not None and coef < -0.3:
            return "NEUTRAL", 0.45
        return "NEUTRAL", 0.35

    def _macro_vote(self, events: list[dict[str, Any]]) -> tuple[str, float, list[str]]:
        if not events:
            return "WAIT", 0.2, ["Макрокалендарь без релевантных событий"]
        soon = []
        for e in events:
            if str(e.get("importance") or "").lower() in {"high", "высокий"}:
                soon.append(str(e.get("title") or e.get("event")))
        if soon:
            return "HIGH_RISK", 0.5, soon[:5]
        return "NEUTRAL", 0.4, []

    def _news_vote(self, items: list[dict[str, Any]]) -> tuple[str, float, list[str]]:
        if not items:
            return "WAIT", 0.2, ["Нет свежих новостей"]
        score = 0
        notes = []
        for a in items[:8]:
            assess = str(a.get("ai_assessment") or a.get("sentiment") or "")
            if "Положительно для EUR/USD" in assess:
                score += 1
                notes.append(a.get("title"))
            elif "Негативно для EUR/USD" in assess or "Поддерживает DXY" in assess:
                score -= 1
                notes.append(a.get("title"))
            elif "Давит на DXY" in assess:
                score += 1
        if score >= 2:
            return "WATCH_BUY", 0.45, [str(n) for n in notes[:3]]
        if score <= -2:
            return "WATCH_SELL", 0.45, [str(n) for n in notes[:3]]
        return "NEUTRAL", 0.35, []

    def _session_vote(self, which: str = "both") -> tuple[str, float]:
        hour = datetime.now(timezone.utc).hour
        # Europe ~7-16 UTC, US ~13-21 UTC
        if which == "europe":
            if 7 <= hour < 16:
                return "WATCH_BUY" if hour < 12 else "NEUTRAL", 0.4
            return "WAIT", 0.25
        if which == "us":
            if 13 <= hour < 21:
                return "NEUTRAL", 0.4
            return "WAIT", 0.25
        if 7 <= hour < 21:
            return "NEUTRAL", 0.35
        return "WAIT", 0.25

    def _risk_vote(
        self,
        *,
        missing: list[str],
        macro_vote: str,
        atr: float | None,
        disagreement_hint: float = 0.0,
    ) -> tuple[str, float, str]:
        if macro_vote == "HIGH_RISK" or len(missing) >= 3:
            return "WAIT", 0.75, "Повышенный риск: пропуски данных или макро-событие"
        if atr is not None and atr > 0.005:
            return "WAIT", 0.55, "Повышенная волатильность (ATR)"
        if disagreement_hint > 0.6:
            return "NEUTRAL", 0.45, "Разногласие специалистов"
        return "NEUTRAL", 0.4, "Риск умеренный"

    async def run_full_analysis(
        self,
        *,
        preset_id: str = "morning",
        tenant_id: str = "default",
        timeframe: str = "1H",
        user_id: str | None = None,
    ) -> dict[str, Any]:
        preset = next((p for p in ANALYSIS_PRESETS if p["id"] == preset_id), ANALYSIS_PRESETS[0])
        sections = preset.get("sections") or {}
        missing: list[str] = []

        eurusd = await self.quote("EUR/USD")
        dxy = await self.quote("DXY")
        if eurusd.get("status") != "connected":
            missing.append(f"EUR/USD: {eurusd.get('message')}")
        if dxy.get("status") != "connected":
            missing.append(f"DXY: {dxy.get('message')}")

        e_pack = await get_candles("EUR/USD", timeframe) if sections.get("technical", True) else {"bars": [], "status": "skipped"}
        d_pack = await get_candles("DXY", timeframe) if sections.get("dxy", True) else {"bars": [], "status": "skipped"}
        if sections.get("technical", True) and e_pack.get("status") not in {"connected", "ok", "delayed"}:
            missing.append(f"Бары EUR/USD: {e_pack.get('message')}")
        if sections.get("dxy", True) and d_pack.get("status") not in {"connected", "ok", "delayed"}:
            missing.append(f"Бары DXY: {d_pack.get('message')}")

        e_ta = compute_indicators(e_pack.get("bars") or [])
        d_ta = compute_indicators(d_pack.get("bars") or [])
        e_closes = [b["c"] for b in (e_pack.get("bars") or [])[-60:]]
        d_closes = [b["c"] for b in (d_pack.get("bars") or [])[-60:]]
        corr = eurusd_dxy_correlation(e_closes, d_closes)

        news_items: list[dict[str, Any]] = []
        if sections.get("news", True):
            feed = await self.news_feed(["EUR/USD", "DXY"])
            news_items = feed.get("items") or []
            if feed.get("provider", {}).get("status") != "connected":
                missing.append(f"Новости: {feed.get('provider', {}).get('message')}")

        macro_events: list[dict[str, Any]] = []
        if sections.get("macro", True):
            cal = await self.macro_calendar()
            macro_events = cal.get("events") or []
            if cal.get("status") != "connected":
                missing.append(f"Календарь: {cal.get('message')}")

        tech_vote, tech_c = self._vote_from_ta(e_ta)
        dxy_vote, dxy_c = self._dxy_vote(dxy, d_ta, corr)
        macro_vote, macro_c, macro_risks = self._macro_vote(macro_events)
        news_vote, news_c, news_notes = self._news_vote(news_items)
        eu_vote, eu_c = self._session_vote("europe")
        us_vote, us_c = self._session_vote("us")
        session_vote, session_c = self._session_vote("both")

        # Confidence haircut for missing sources
        haircut = max(0.35, 1.0 - 0.08 * len(missing))

        atr_val = e_ta.get("atr")
        try:
            atr_f = float(atr_val) if atr_val is not None else None
        except Exception:
            atr_f = None
        risk_vote, risk_c, risk_note = self._risk_vote(
            missing=missing,
            macro_vote=macro_vote,
            atr=atr_f,
        )

        agent_outputs = [
            {"agent_id": "technical", "agent_name": "Technical Agent", "vote": tech_vote, "confidence": round(tech_c * haircut, 3), "summary": e_ta.get("message")},
            {"agent_id": "dxy", "agent_name": "DXY Agent", "vote": dxy_vote, "confidence": round(dxy_c * haircut, 3), "summary": dxy.get("message")},
            {"agent_id": "macro", "agent_name": "Macro Agent", "vote": macro_vote, "confidence": round(macro_c * haircut, 3), "summary": "; ".join(macro_risks) or "OK"},
            {"agent_id": "news", "agent_name": "News Agent", "vote": news_vote, "confidence": round(news_c * haircut, 3), "summary": "; ".join(news_notes[:2]) or "OK"},
            {"agent_id": "europe", "agent_name": "Europe Session Agent", "vote": eu_vote, "confidence": round(eu_c * haircut, 3), "summary": "Сессия Европы"},
            {"agent_id": "us", "agent_name": "US Session Agent", "vote": us_vote, "confidence": round(us_c * haircut, 3), "summary": "Сессия США"},
            {"agent_id": "session", "agent_name": "Session Agent", "vote": session_vote, "confidence": round(session_c * haircut, 3), "summary": "Комбинированная сессия"},
            {"agent_id": "risk", "agent_name": "Risk Agent", "vote": risk_vote, "confidence": round(risk_c * haircut, 3), "summary": risk_note},
            {"agent_id": "eurusd_structure", "agent_name": "EUR/USD Structure Agent", "vote": tech_vote, "confidence": round(tech_c * haircut, 3), "summary": f"Trend={e_ta.get('trend')}"},
            {"agent_id": "chief", "agent_name": "Chief Analyst", "vote": "PENDING", "confidence": 0.0, "summary": "Формирует консенсус"},
        ]

        sources_map = {
            "eurusd": eurusd.get("source"),
            "dxy": dxy.get("source"),
            "bars": e_pack.get("source"),
            "news": getattr(self.news, "label", "Новости"),
            "macro": getattr(self.macro, "label", "Календарь"),
        }
        key_reasons = [
            f"Technical Agent: {tech_vote}",
            f"DXY Agent: {dxy_vote}",
            f"Macro Agent: {macro_vote}",
            f"News Agent: {news_vote}",
            f"Session Agent: {session_vote}",
            f"Risk Agent: {risk_vote}",
        ]
        consensus = build_consensus(
            technical_vote=tech_vote,
            dxy_vote=dxy_vote,
            macro_vote=macro_vote if macro_vote != "HIGH_RISK" else "WAIT",
            news_vote=news_vote,
            session_vote=session_vote,
            risk_vote=risk_vote,
            confidences={
                "technical": tech_c * haircut,
                "dxy": dxy_c * haircut,
                "macro": macro_c * haircut,
                "news": news_c * haircut,
                "session": session_c * haircut,
                "risk": risk_c * haircut,
            },
            risks=missing + macro_risks,
            data_gaps=missing,
            key_reasons=key_reasons,
            sources=sources_map,
            invalidation=f"Пробой {e_ta.get('support')}" if e_ta.get("support") else "Нет подтверждения структуры",
        )
        # Update chief vote to final bias
        for a in agent_outputs:
            if a["agent_id"] == "chief":
                a["vote"] = consensus.get("final_result") or consensus.get("overall_direction")
                a["confidence"] = consensus.get("overall_confidence")
                a["summary"] = "Консенсус специалистов"

        direction = consensus.get("final_result") or consensus.get("overall_direction")
        confidence = float(consensus["overall_confidence"])
        conf_pct = int(round(confidence * 100))

        regime = "range"
        if e_ta.get("trend") == "up":
            regime = "trend_up"
        elif e_ta.get("trend") == "down":
            regime = "trend_down"
        if macro_vote == "HIGH_RISK":
            regime = "event_risk"

        display = {
            "instrument": "EUR/USD",
            "final_result": consensus.get("final_result") or direction,
            "direction": direction,
            "direction_ru": _DIR_RU.get(str(consensus.get("final_result") or direction), "Недостаточно данных"),
            "overall_summary": _DIR_RU.get(str(consensus.get("final_result") or direction), "Недостаточно данных"),
            "confidence": confidence,
            "confidence_pct": conf_pct,
            "bullish_score": consensus.get("bullish_score"),
            "bearish_score": consensus.get("bearish_score"),
            "neutral_score": consensus.get("neutral_score"),
            "key_reasons": consensus.get("key_reasons") or [],
            "data_gaps": consensus.get("data_gaps") or missing,
            "what_changed": [
                f"EUR/USD mid={eurusd.get('mid')}",
                f"DXY mid={dxy.get('mid')}",
                f"Корреляция={corr.get('correlation') if isinstance(corr, dict) else corr}",
            ],
            "market_regime": regime,
            "eurusd_state": {"quote": eurusd, "technical": {k: e_ta.get(k) for k in ("trend", "rsi", "status")}, "mid": eurusd.get("mid")},
            "dxy_state": {"vote": dxy_vote, "quote": dxy, "technical": {k: d_ta.get(k) for k in ("trend", "rsi", "ema_fast", "ema_slow", "support", "resistance", "status")}, "mid": dxy.get("mid")},
            "dxy_factor": {"vote": dxy_vote, "quote": dxy, "technical": {k: d_ta.get(k) for k in ("trend", "rsi", "ema_fast", "ema_slow", "support", "resistance", "status")}},
            "technical_factor": {k: e_ta.get(k) for k in ("trend", "ema_fast", "ema_slow", "rsi", "macd", "macd_signal", "atr", "bollinger", "support", "resistance", "status")},
            "macro_factor": {"vote": macro_vote, "risks": macro_risks, "events_count": len(macro_events)},
            "news_factor": {"vote": news_vote, "notes": news_notes[:3], "items_count": len(news_items)},
            "correlation_factor": corr if isinstance(corr, dict) else {"correlation": corr},
            "risk_factor": {"vote": risk_vote, "note": risk_note, "confidence": round(risk_c * haircut, 3)},
            "session_factor": {"vote": session_vote, "europe": eu_vote, "us": us_vote, "confidence": round(session_c * haircut, 3)},
            "support": e_ta.get("support"),
            "resistance": e_ta.get("resistance"),
            "nearest_risks": (macro_risks or missing)[:5],
            "upside_scenario": f"Рост при удержании выше {e_ta.get('support')} и ослаблении DXY"
            if e_ta.get("support")
            else "Недостаточно данных для сценария роста",
            "downside_scenario": f"Снижение при потере {e_ta.get('support')} и росте DXY"
            if e_ta.get("support")
            else "Недостаточно данных для сценария снижения",
            "invalidation": consensus.get("invalidation"),
            "sources": sources_map,
            "generated_at": _now_iso(),
            "missing_sources": missing,
            "timeframe": timeframe,
            "preset": preset,
            "agent_votes_panel": agent_outputs,
            "consensus": consensus,
            "disclaimer": "AI-анализ, не является гарантией результата.",
        }

        sig_status = direction if direction in SIGNAL_STATUSES else "NO_SIGNAL"
        if missing and confidence < 0.25:
            sig_status = "NO_SIGNAL"
        signal = create_signal(
            instrument="EUR/USD",
            timeframe=timeframe,
            signal=sig_status,
            confidence=confidence,
            reasons=(news_notes[:2] or macro_risks[:2] or ["Консенсус специалистов по доступным данным"]),
            support=e_ta.get("support"),
            resistance=e_ta.get("resistance"),
            entry_zone=f"{e_ta.get('support')}–{e_ta.get('resistance')}" if e_ta.get("support") and e_ta.get("resistance") else None,
            invalidation=str(consensus.get("invalidation") or ""),
            agent_votes=[{"agent": a["agent_name"], "vote": a["vote"]} for a in agent_outputs],
            risk_events=missing + macro_risks,
            tenant_id=tenant_id,
        )
        signal["price_at_signal"] = eurusd.get("mid")
        signal["status_ru"] = _signal_ru(signal["status"])
        signal["analysis_link"] = None
        assert_no_trade_execution(signal)

        result = {
            "ok": True,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "preset_id": preset_id,
            "analysis_type": preset.get("name") or preset_id,
            "analysis": {
                "instrument": "EUR/USD",
                "agent": "Chief Analyst",
                "direction": direction,
                "final_result": consensus.get("final_result") or direction,
                "confidence": confidence,
                "bullish_score": consensus.get("bullish_score"),
                "bearish_score": consensus.get("bearish_score"),
                "neutral_score": consensus.get("neutral_score"),
                "key_reasons": consensus.get("key_reasons"),
                "data_gaps": consensus.get("data_gaps") or missing,
                "sources": sources_map,
                "horizon": "intraday",
                "price_at_analysis": eurusd.get("mid"),
                "dxy_at_analysis": dxy.get("mid"),
                "market_regime": regime,
            },
            "consensus": consensus,
            "signal": signal,
            "agent_outputs": agent_outputs,
            "market_snapshot": eurusd,
            "display": display,
            "missing_sources": missing,
            "technical": {"EUR/USD": e_ta, "DXY": d_ta},
            "correlation": corr,
            "disclaimer": "AI-анализ, не является гарантией результата.",
        }
        result = await persist_full_analysis(result)
        try:
            from services.fx_market_intel.schedule import record_last_run
            record_last_run(
                tenant_id,
                preset_id,
                result=str(consensus.get("final_result") or direction),
                confidence=float(confidence),
            )
        except Exception:
            pass
        if result.get("analysis", {}).get("analysis_run_id"):
            signal["analysis_run_id"] = result["analysis"]["analysis_run_id"]
            signal["analysis_link"] = result["analysis"]["analysis_run_id"]
        self._signals.insert(0, signal)
        self._signals = self._signals[:100]
        return result

    async def run_specialist(
        self,
        *,
        specialist_id: str,
        tenant_id: str = "default",
        bars: list[dict[str, Any]] | None = None,
        timeframe: str = "1H",
    ) -> dict[str, Any]:
        if specialist_id == "chief" or specialist_id in {p["id"] for p in ANALYSIS_PRESETS}:
            preset = specialist_id if specialist_id in {p["id"] for p in ANALYSIS_PRESETS} else "morning"
            return await self.run_full_analysis(preset_id=preset, tenant_id=tenant_id, timeframe=timeframe)

        spec = next((s for s in SPECIALISTS if s["id"] == specialist_id), None)
        if not spec:
            return {"ok": False, "error": "unknown_specialist"}

        # Single-agent run still goes through shared pipeline data, then persists as focused run
        full = await self.run_full_analysis(preset_id="pre_trade", tenant_id=tenant_id, timeframe=timeframe)
        agent = next((a for a in full.get("agent_outputs") or [] if a["agent_id"] == specialist_id), None)
        if specialist_id == "eurusd_structure":
            agent = next((a for a in full.get("agent_outputs") or [] if a["agent_id"] == "eurusd_structure"), agent)
        display = full.get("display") or {}
        return {
            "ok": True,
            "specialist": spec,
            "analysis": {
                **(full.get("analysis") or {}),
                "agent": spec["name"],
                "direction": (agent or {}).get("vote") or display.get("direction"),
                "confidence": (agent or {}).get("confidence") or display.get("confidence"),
            },
            "consensus": full.get("consensus") if specialist_id == "chief" else None,
            "signal": full.get("signal"),
            "agent_output": agent,
            "display": display,
            "dependency_gaps": full.get("missing_sources") or [],
            "technical": full.get("technical"),
            "persistence": full.get("persistence"),
            "disclaimer": "AI-анализ, не является гарантией результата.",
        }

    async def list_signals(self, tenant_id: str = "default") -> list[dict[str, Any]]:
        # Prefer durable rows
        try:
            from database.session import get_session
            from repositories.fx_market_intel_repository import FxMarketIntelRepository

            async with get_session() as session:
                repo = FxMarketIntelRepository(session)
                rows = await repo.list_signals(tenant_id, limit=50)
                if rows:
                    out = []
                    now = datetime.now(timezone.utc)
                    for r in rows:
                        status = r.status
                        if r.expires_at and r.expires_at < now:
                            status = "EXPIRED"
                        payload = dict(r.payload or {})
                        payload.update(
                            {
                                "signal_id": r.signal_key,
                                "instrument": r.instrument,
                                "timeframe": r.timeframe,
                                "signal": r.signal,
                                "confidence": r.confidence,
                                "price_at_signal": r.price_at_signal,
                                "entry_zone": r.entry_zone,
                                "invalidation": r.invalidation,
                                "reasons": r.reasons or [],
                                "status": status,
                                "status_ru": _signal_ru(status),
                                "timestamp": r.created_at.isoformat() if r.created_at else None,
                                "analysis_run_id": r.analysis_run_id,
                                "analytics_only": True,
                                "trade_execution": False,
                            }
                        )
                        out.append(payload)
                    return out
        except Exception:
            pass
        return [s for s in self._signals if s.get("tenant_id") in ("", tenant_id, "default")]

    async def memory(self, tenant_id: str = "default") -> dict[str, Any]:
        history = await list_history(tenant_id)
        return {
            "analyses": history or list_analyses(tenant_id),
            "metrics": performance_metrics(tenant_id),
        }

    async def history(self, tenant_id: str = "default", limit: int = 50) -> dict[str, Any]:
        return {"items": await list_history(tenant_id, limit=limit)}

    async def history_detail(self, run_id: str, tenant_id: str = "default") -> dict[str, Any]:
        detail = await get_history_detail(run_id, tenant_id)
        if not detail:
            return {"ok": False, "error": "not_found"}
        return {"ok": True, **detail}

    def format_telegram_quote(self, quote: dict[str, Any]) -> str:
        sym = quote.get("symbol", "")
        if quote.get("mid"):
            return (
                f"{sym}: {quote['mid']}\n"
                f"Источник: {quote.get('source')}\n"
                f"Данные: {quote.get('fetched_at')}"
            )
        return f"{sym}: нет данных\n{quote.get('message') or quote.get('status')}"

    async def telegram_brief(self, command: str, tenant_id: str = "telegram") -> str:
        """Same backend path as Web — no duplicated analysis logic."""
        cmd = (command or "").strip().lower()
        lines = ["AI-анализ, не является гарантией результата."]
        if cmd in {"dxy", "dxy сейчас"} or cmd.endswith("dxy") and "новост" not in cmd:
            q = await self.quote("DXY")
            lines.append(self.format_telegram_quote(q))
            return "\n".join(lines)
        if cmd in {"eurusd", "eur/usd", "eur/usd сейчас"} or ("eur" in cmd and "новост" not in cmd and "анализ" not in cmd and "утр" not in cmd):
            q = await self.quote("EUR/USD")
            lines.append(self.format_telegram_quote(q))
            return "\n".join(lines)
        if "календар" in cmd:
            cal = await self.macro_calendar()
            lines.append(f"Календарь: {cal.get('provider', {}).get('label') or cal.get('status')}")
            for e in (cal.get("events") or [])[:5]:
                lines.append(f"• {e.get('title') or e.get('event')} · {e.get('scheduled_at')}")
            if not cal.get("events"):
                lines.append(cal.get("message") or "Событий нет")
            return "\n".join(lines)
        if "сигнал" in cmd:
            sigs = await self.list_signals(tenant_id)
            if not sigs:
                lines.append("Сигналов пока нет. Запустите анализ.")
            else:
                s = sigs[0]
                lines.append(
                    f"{s.get('instrument')} · {s.get('status_ru') or s.get('signal')} · "
                    f"уверенность {int(round(float(s.get('confidence') or 0)*100))}%"
                )
                lines.append(f"Цена сигнала: {s.get('price_at_signal')}")
                lines.append(f"Анализ: {s.get('analysis_run_id') or '—'}")
            return "\n".join(lines)
        if "новост" in cmd:
            feed = await self.news_feed(["EUR/USD"])
            lines.append(f"Источник: {(feed.get('provider') or {}).get('label')}")
            if not feed["items"]:
                lines.append("Новости недоступны")
            else:
                for a in feed["items"][:3]:
                    lines.append(f"• {a['title']}")
                    lines.append(f"  {a.get('ai_assessment') or a.get('sentiment') or 'Нейтрально'}")
            return "\n".join(lines)
        # morning / now analysis
        preset = "morning" if "утр" in cmd else "pre_trade"
        result = await self.run_full_analysis(preset_id=preset, tenant_id=tenant_id)
        d = result.get("display") or {}
        c = result.get("consensus") or {}
        lines.append(f"Направление: {d.get('direction_ru') or c.get('overall_direction')}")
        lines.append(f"Уверенность: {d.get('confidence_pct', int(round(float(c.get('overall_confidence') or 0)*100)))}%")
        lines.append(f"Анализ: {d.get('generated_at')}")
        eurusd = (result.get("market_snapshot") or {})
        lines.append(f"Котировка: {eurusd.get('mid')} · {eurusd.get('source')} · {eurusd.get('fetched_at')}")
        risks = d.get("nearest_risks") or result.get("missing_sources") or []
        if risks:
            lines.append("Риск: " + str(risks[0]))
        return "\n".join(lines)


_SERVICE: FxMarketIntelService | None = None


def get_fx_market_intel() -> FxMarketIntelService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = FxMarketIntelService()
    return _SERVICE


def reset_fx_market_intel_for_tests() -> None:
    global _SERVICE
    _SERVICE = None
