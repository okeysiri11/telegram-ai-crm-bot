"""Chief Market Analyst — weighted structured consensus (not text concat)."""

from __future__ import annotations

from typing import Any

# Configurable defaults — not historically optimized.
DEFAULT_WEIGHTS = {
    "technical": 0.22,
    "dxy": 0.18,
    "macro": 0.18,
    "news": 0.14,
    "session": 0.14,
    "risk": 0.14,
}

_DIR_SCORE = {
    "BUY_BIAS": 1.0,
    "WATCH_BUY": 1.0,
    "bullish": 1.0,
    "BUY": 1.0,
    "SELL_BIAS": -1.0,
    "WATCH_SELL": -1.0,
    "bearish": -1.0,
    "SELL": -1.0,
    "NEUTRAL": 0.0,
    "WAIT": 0.0,
    "HIGH_RISK": 0.0,
    "NO_SIGNAL": 0.0,
}

FINAL_BIASES = {"BUY_BIAS", "SELL_BIAS", "NEUTRAL", "WAIT"}


def _vote_score(vote: str | None) -> float:
    if not vote:
        return 0.0
    return _DIR_SCORE.get(str(vote), 0.0)


def _normalize_vote(vote: str | None) -> str:
    v = str(vote or "NEUTRAL")
    if v in {"WATCH_BUY", "BUY", "bullish", "BULLISH"}:
        return "BUY_BIAS"
    if v in {"WATCH_SELL", "SELL", "bearish", "BEARISH"}:
        return "SELL_BIAS"
    if v in {"HIGH_RISK", "NO_SIGNAL"}:
        return "WAIT"
    if v in FINAL_BIASES:
        return v
    return "NEUTRAL"


def build_consensus(
    *,
    technical_vote: str = "NEUTRAL",
    dxy_vote: str = "NEUTRAL",
    macro_vote: str = "NEUTRAL",
    news_vote: str = "NEUTRAL",
    session_vote: str = "NEUTRAL",
    risk_vote: str = "NEUTRAL",
    confidences: dict[str, float] | None = None,
    weights: dict[str, float] | None = None,
    risks: list[str] | None = None,
    invalidation: str | None = None,
    key_reasons: list[str] | None = None,
    data_gaps: list[str] | None = None,
    sources: dict[str, Any] | None = None,
) -> dict[str, Any]:
    w = {**DEFAULT_WEIGHTS, **(weights or {})}
    conf = confidences or {}
    parts = {
        "technical": (_vote_score(technical_vote), float(conf.get("technical", 0.5)), w.get("technical", 0.2)),
        "dxy": (_vote_score(dxy_vote), float(conf.get("dxy", 0.5)), w.get("dxy", 0.18)),
        "macro": (_vote_score(macro_vote), float(conf.get("macro", 0.5)), w.get("macro", 0.18)),
        "news": (_vote_score(news_vote), float(conf.get("news", 0.5)), w.get("news", 0.14)),
        "session": (_vote_score(session_vote), float(conf.get("session", 0.5)), w.get("session", 0.14)),
        "risk": (_vote_score(risk_vote), float(conf.get("risk", 0.5)), w.get("risk", 0.14)),
    }
    num = sum(score * c * wt for score, c, wt in parts.values())
    den = sum(c * wt for _, c, wt in parts.values()) or 1.0
    weighted = num / den

    bullish = 0.0
    bearish = 0.0
    neutral = 0.0
    for score, c, wt in parts.values():
        mass = c * wt
        if score > 0.05:
            bullish += mass * score
        elif score < -0.05:
            bearish += mass * abs(score)
        else:
            neutral += mass
    total_mass = bullish + bearish + neutral or 1.0
    bullish_score = round(100.0 * bullish / total_mass, 2)
    bearish_score = round(100.0 * bearish / total_mass, 2)
    neutral_score = round(100.0 * neutral / total_mass, 2)

    votes = [technical_vote, dxy_vote, macro_vote, news_vote, session_vote, risk_vote]
    unique = {str(v) for v in votes if v}
    disagreement = max(0.0, min(1.0, (len(unique) - 1) / max(1, len(parts) - 1)))

    gaps = list(data_gaps or risks or [])
    if risk_vote in {"WAIT", "HIGH_RISK"} or (macro_vote == "HIGH_RISK"):
        final = "WAIT"
    elif gaps and abs(weighted) < 0.15:
        final = "WAIT"
    elif weighted > 0.25:
        final = "BUY_BIAS"
    elif weighted < -0.25:
        final = "SELL_BIAS"
    else:
        final = "NEUTRAL"

    # Legacy alias for callers still reading overall_direction as WATCH_*
    legacy = {
        "BUY_BIAS": "WATCH_BUY",
        "SELL_BIAS": "WATCH_SELL",
        "NEUTRAL": "NEUTRAL",
        "WAIT": "WAIT",
    }.get(final, final)

    overall_confidence = max(0.0, min(1.0, abs(weighted) * (1 - 0.5 * disagreement)))
    if final == "WAIT":
        overall_confidence = min(overall_confidence, 0.4)

    reasons = list(key_reasons or [])
    if not reasons:
        reasons = [f"Технический: {_normalize_vote(technical_vote)}", f"DXY: {_normalize_vote(dxy_vote)}"]
        if macro_vote:
            reasons.append(f"Макро: {_normalize_vote(macro_vote)}")

    return {
        "technical_vote": technical_vote,
        "dxy_vote": dxy_vote,
        "macro_vote": macro_vote,
        "news_vote": news_vote,
        "session_vote": session_vote,
        "risk_vote": risk_vote,
        "final_result": final,
        "overall_direction": legacy,
        "bias": final,
        "overall_confidence": round(overall_confidence, 3),
        "confidence": round(overall_confidence, 3),
        "bullish_score": bullish_score,
        "bearish_score": bearish_score,
        "neutral_score": neutral_score,
        "disagreement_score": round(disagreement, 3),
        "weighted_score": round(weighted, 4),
        "weights_used": w,
        "key_reasons": reasons[:8],
        "data_gaps": gaps[:12],
        "sources": sources or {},
        "risks": risks or [],
        "invalidation": invalidation,
        "disclaimer": "AI-анализ, не является гарантией результата.",
    }
