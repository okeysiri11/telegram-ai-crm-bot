"""Ranking — re-rank retrieval candidates."""

from __future__ import annotations

from typing import Any


class RankingEngine:
    def rerank(self, *, candidates: list[dict[str, Any]], query: str) -> list[dict[str, Any]]:
        q = query.lower()
        scored = []
        for c in candidates:
            text = (c.get("text") or "").lower()
            boost = 0.1 if any(tok in text for tok in q.split()) else 0.0
            score = float(c.get("score", 0)) + boost
            scored.append({**c, "score": score, "reranked": True})
        return sorted(scored, key=lambda x: x.get("score", 0), reverse=True)
