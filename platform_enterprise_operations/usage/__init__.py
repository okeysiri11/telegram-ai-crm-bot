"""Usage Analytics — Sprint 23.0."""

from __future__ import annotations

from typing import Any


class UsageAnalytics:
    def summarize(self, *, events: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        events = list(events or [])
        counts: dict[str, int] = {}
        durations: list[float] = []
        errors = 0
        incomplete = 0
        ai_recs: dict[str, int] = {}
        for e in events:
            feat = str(e.get("feature") or "unknown")
            counts[feat] = counts.get(feat, 0) + 1
            if e.get("duration_ms") is not None:
                durations.append(float(e["duration_ms"]))
            if e.get("error"):
                errors += 1
            if e.get("incomplete"):
                incomplete += 1
            if e.get("ai_recommendation"):
                rec = str(e["ai_recommendation"])
                ai_recs[rec] = ai_recs.get(rec, 0) + 1
        sorted_feats = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        avg = round(sum(durations) / len(durations), 2) if durations else 0.0
        return {
            "most_used": [f for f, _ in sorted_feats[:5]],
            "rarely_used": [f for f, _ in sorted_feats[-3:]] if sorted_feats else [],
            "avg_operation_ms": avg,
            "user_errors": errors,
            "incomplete_flows": incomplete,
            "popular_ai_recommendations": sorted(ai_recs.items(), key=lambda x: x[1], reverse=True)[:5],
            "event_count": len(events),
        }
