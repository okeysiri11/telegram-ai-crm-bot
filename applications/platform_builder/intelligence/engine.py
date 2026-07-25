"""Visual Intelligence Engine & Enterprise Visual Analytics — Sprint 29.10.

Analyzes visual activity and provides intelligent visual insights.
Never changes business logic. Never generates business events.
Analyzes verified platform events and produces visual recommendations.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.platform_builder.intelligence.catalogs import (
    ANOMALY_TYPES,
    ATTENTION_RECOMMENDATIONS,
    EXECUTIVE_INSIGHTS,
    HEATMAP_TYPES,
    HEALTH_INDICES,
    INTELLIGENCE_COMPONENTS,
    PATTERN_TYPES,
    PREDICTIVE_APIS,
    TREND_TYPES,
    UI_SURFACES,
    WIZARD_STEPS,
    full_catalog,
)
from applications.platform_builder.shared.exceptions import NotFoundError, ValidationError
from applications.platform_builder.shared.store import PlatformBuilderStore, platform_builder_store
from applications.platform_builder.team_map.engine import VisualEventBus


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


class PatternEngine:
    """Detect visual activity patterns from verified bus events."""

    def detect(self, events: list[dict[str, Any]]) -> dict[str, Any]:
        by_channel: dict[str, int] = {}
        by_type: dict[str, int] = {}
        for e in events:
            ch = e.get("channel") or "unknown"
            et = e.get("event_type") or "unknown"
            by_channel[ch] = by_channel.get(ch, 0) + 1
            by_type[et] = by_type.get(et, 0) + 1
        patterns = {
            "Activity Trends": {
                "total_events": len(events),
                "channels": by_channel,
                "direction": "up" if len(events) >= 3 else "flat",
            },
            "Workflow Patterns": {
                "count": by_channel.get("Workflow Events", 0) + by_channel.get("Task Events", 0),
                "dominant": max(
                    (
                        (k, v)
                        for k, v in by_type.items()
                        if "workflow" in k or "task" in k
                    ),
                    key=lambda x: x[1],
                    default=("none", 0),
                )[0],
            },
            "Knowledge Patterns": {
                "count": by_channel.get("Knowledge Events", 0),
            },
            "Department Patterns": {
                "count": sum(1 for t in by_type if "department" in t),
            },
            "AI Collaboration Patterns": {
                "count": by_channel.get("AI Events", 0),
                "signal": "active" if by_channel.get("AI Events", 0) >= 2 else "quiet",
            },
            "Organization Growth Patterns": {
                "count": by_channel.get("Organization Events", 0),
            },
        }
        return {
            "patterns": patterns,
            "pattern_names": list(PATTERN_TYPES),
            "event_count": len(events),
            "changes_business_logic": False,
            "generates_business_events": False,
            "ready": True,
        }


class InsightEngine:
    def executive(self, events: list[dict[str, Any]], patterns: dict[str, Any]) -> dict[str, Any]:
        by_channel = patterns.get("Activity Trends", {}).get("channels") or {}
        total = len(events)
        insights = {
            "Daily Overview": {
                "events_today": total,
                "top_channel": max(by_channel.items(), key=lambda x: x[1], default=("none", 0))[0],
            },
            "Weekly Summary": {
                "events": total,
                "channels_active": len(by_channel),
            },
            "Monthly Growth": {
                "growth_signal": patterns.get("Organization Growth Patterns", {}).get("count", 0),
            },
            "Organization Health": {
                "score": _clamp(0.55 + by_channel.get("Organization Events", 0) * 0.05),
            },
            "Department Performance": {
                "score": _clamp(0.5 + patterns.get("Department Patterns", {}).get("count", 0) * 0.08),
            },
            "AI Productivity": {
                "score": _clamp(0.5 + by_channel.get("AI Events", 0) * 0.06),
                "events": by_channel.get("AI Events", 0),
            },
            "Knowledge Health": {
                "score": _clamp(0.5 + by_channel.get("Knowledge Events", 0) * 0.07),
            },
        }
        return {
            "insights": insights,
            "insight_names": list(EXECUTIVE_INSIGHTS),
            "generates_business_events": False,
            "ready": True,
        }


class RecommendationEngine:
    def recommend(
        self,
        events: list[dict[str, Any]],
        anomalies: dict[str, Any],
        patterns: dict[str, Any],
    ) -> dict[str, Any]:
        by_channel = patterns.get("Activity Trends", {}).get("channels") or {}
        recommendations = {
            "Critical Departments": {
                "priority": "high" if anomalies["detected"].get("Resource Imbalance") else "medium",
                "reason": "Visual activity imbalance across organization channels",
                "visual_only": True,
            },
            "Important Workflows": {
                "priority": "high" if by_channel.get("Workflow Events", 0) >= 2 else "medium",
                "reason": "Elevated workflow visual traffic",
                "visual_only": True,
            },
            "Priority Documents": {
                "priority": "medium",
                "reason": "Document-related knowledge events present" if by_channel.get("Knowledge Events") else "No document heat",
                "visual_only": True,
            },
            "Executive Alerts": {
                "priority": "high" if any(anomalies["detected"].values()) else "low",
                "items": [k for k, v in anomalies["detected"].items() if v],
                "visual_only": True,
            },
            "Key Decisions": {
                "priority": "medium",
                "reason": "Decision-like event types in feed",
                "visual_only": True,
            },
            "High Impact Events": {
                "priority": "high" if len(events) >= 5 else "medium",
                "event_ids": [e.get("event_id") for e in events[:5]],
                "visual_only": True,
            },
        }
        return {
            "recommendations": recommendations,
            "recommendation_names": list(ATTENTION_RECOMMENDATIONS),
            "changes_business_logic": False,
            "generates_business_events": False,
            "produces_visual_recommendations_only": True,
            "ready": True,
        }


class AnalyticsRegistry:
    def __init__(self, store: PlatformBuilderStore) -> None:
        self.store = store

    def save_snapshot(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        sid = snapshot.get("analytics_id") or _id("vana")
        snapshot["analytics_id"] = sid
        snapshot["registered_at"] = _now()
        self.store.analytics_snapshots.save(sid, snapshot)
        return snapshot

    def list_snapshots(self) -> dict[str, Any]:
        items = self.store.analytics_snapshots.list_all()
        return {"snapshots": items, "count": len(items), "ready": True, "operational": True}


class VisualIntelligenceEngine:
    """Enterprise Visual Intelligence — analytics/recommendations only."""

    def __init__(
        self,
        store: PlatformBuilderStore | None = None,
        bus: VisualEventBus | None = None,
    ) -> None:
        self.store = store or platform_builder_store
        self.bus = bus or VisualEventBus(self.store)
        self.patterns = PatternEngine()
        self.insights = InsightEngine()
        self.recommendations = RecommendationEngine()
        self.analytics = AnalyticsRegistry(self.store)

    def catalog(self) -> dict[str, Any]:
        return {
            "ready": True,
            "operational": True,
            "version": "1.0.0",
            "sprint": "29.10",
            "visual_intelligence_engine_ready": True,
            "insight_engine_ready": True,
            "analytics_ready": True,
            "recommendation_engine_ready": True,
            "health_index_ready": True,
            "changes_business_logic": False,
            "generates_business_events": False,
            "analyzes_verified_events_only": True,
            "autonomous_business_decisions": False,
            **full_catalog(),
        }

    def status(self) -> dict[str, Any]:
        return {
            "ready": True,
            "operational": True,
            "version": "1.0.0",
            "sprint": "29.10",
            "changes_business_logic": False,
            "generates_business_events": False,
            "analyzes_verified_events_only": True,
            "autonomous_business_decisions": False,
            "components": list(INTELLIGENCE_COMPONENTS),
            "engines": len(self.store.intelligence_engines.list_all()),
            "snapshots": len(self.store.analytics_snapshots.list_all()),
        }

    def _events(self, limit: int = 200) -> list[dict[str, Any]]:
        return list(self.bus.poll(limit=limit).get("events") or [])

    # Step 1
    def engine_overview(self) -> dict[str, Any]:
        return {
            "title": "Visual Intelligence Engine",
            "components": list(INTELLIGENCE_COMPONENTS),
            "analytics": self.analytics.list_snapshots(),
            "changes_business_logic": False,
            "generates_business_events": False,
            "ready": True,
        }

    # Step 2
    def pattern_detection(self) -> dict[str, Any]:
        return self.patterns.detect(self._events())

    # Step 3
    def anomaly_detection(self) -> dict[str, Any]:
        events = self._events()
        by_channel: dict[str, int] = {}
        for e in events:
            ch = e.get("channel") or "unknown"
            by_channel[ch] = by_channel.get(ch, 0) + 1
        ai = by_channel.get("AI Events", 0)
        wf = by_channel.get("Workflow Events", 0)
        task = by_channel.get("Task Events", 0)
        kn = by_channel.get("Knowledge Events", 0)
        org = by_channel.get("Organization Events", 0)
        detected = {
            "Inactive AI": ai == 0 and len(events) > 0,
            "Workflow Bottlenecks": wf > 0 and task == 0,
            "Queue Congestion": task >= 4,
            "Knowledge Gaps": kn == 0 and len(events) >= 3,
            "Communication Delays": ai >= 1 and org == 0 and len(events) >= 4,
            "Resource Imbalance": max(by_channel.values(), default=0) >= 5 and len(by_channel) <= 2,
            "Unusual Activity": len(events) >= 12,
        }
        return {
            "anomalies": ANOMALY_TYPES,
            "detected": detected,
            "active": [k for k, v in detected.items() if v],
            "count": sum(1 for v in detected.values() if v),
            "changes_business_logic": False,
            "generates_business_events": False,
            "ready": True,
        }

    # Step 4
    def attention_recommendations(self) -> dict[str, Any]:
        events = self._events()
        patterns = self.patterns.detect(events)
        anomalies = self.anomaly_detection()
        return self.recommendations.recommend(events, anomalies, patterns["patterns"])

    # Step 5
    def executive_insights(self) -> dict[str, Any]:
        events = self._events()
        patterns = self.patterns.detect(events)
        return self.insights.executive(events, patterns["patterns"])

    # Step 6
    def visual_heatmaps(self) -> dict[str, Any]:
        events = self._events()
        by_channel: dict[str, int] = {}
        for e in events:
            ch = e.get("channel") or "unknown"
            by_channel[ch] = by_channel.get(ch, 0) + 1
        max_c = max(by_channel.values(), default=1) or 1
        cells = {
            ch: {"count": n, "intensity": round(n / max_c, 2)} for ch, n in by_channel.items()
        }
        heatmaps = {
            "Activity Heatmap": {"cells": cells, "ready": True},
            "Department Heatmap": {
                "cells": {k: v for k, v in cells.items() if "Organization" in k},
                "ready": True,
            },
            "Knowledge Heatmap": {
                "cells": {k: v for k, v in cells.items() if "Knowledge" in k},
                "ready": True,
            },
            "Workflow Heatmap": {
                "cells": {k: v for k, v in cells.items() if "Workflow" in k or "Task" in k},
                "ready": True,
            },
            "Organization Heatmap": {
                "cells": {k: v for k, v in cells.items() if "Organization" in k},
                "ready": True,
            },
            "Future AI City Heatmap": {
                "ready": True,
                "planned": True,
                "note": "Foundation for AI City spatial heatmaps",
            },
        }
        return {
            "heatmaps": heatmaps,
            "heatmap_names": list(HEATMAP_TYPES),
            "ready": True,
        }

    # Step 7
    def trend_engine(self) -> dict[str, Any]:
        events = self._events()
        patterns = self.patterns.detect(events)["patterns"]
        by_channel = patterns.get("Activity Trends", {}).get("channels") or {}
        trends = {
            "Growth Trends": {
                "direction": patterns.get("Activity Trends", {}).get("direction"),
                "organization_events": by_channel.get("Organization Events", 0),
            },
            "Performance Trends": {
                "workflow_load": by_channel.get("Workflow Events", 0) + by_channel.get("Task Events", 0),
            },
            "Knowledge Evolution": {
                "knowledge_events": by_channel.get("Knowledge Events", 0),
            },
            "AI Utilization": {
                "ai_events": by_channel.get("AI Events", 0),
            },
            "Organization Development": {
                "org_events": by_channel.get("Organization Events", 0),
            },
        }
        return {
            "trends": trends,
            "trend_names": list(TREND_TYPES),
            "ready": True,
        }

    # Step 8
    def visual_health_index(self) -> dict[str, Any]:
        events = self._events()
        patterns = self.patterns.detect(events)["patterns"]
        anomalies = self.anomaly_detection()
        by_channel = patterns.get("Activity Trends", {}).get("channels") or {}
        penalty = anomalies["count"] * 0.06
        indices = {
            "Organization Health": _clamp(0.7 + by_channel.get("Organization Events", 0) * 0.04 - penalty),
            "Department Health": _clamp(0.65 + patterns.get("Department Patterns", {}).get("count", 0) * 0.05 - penalty),
            "Workflow Health": _clamp(
                0.6
                + (by_channel.get("Workflow Events", 0) + by_channel.get("Task Events", 0)) * 0.03
                - (0.15 if anomalies["detected"].get("Workflow Bottlenecks") else 0)
            ),
            "Knowledge Health": _clamp(
                0.6 + by_channel.get("Knowledge Events", 0) * 0.05 - (0.2 if anomalies["detected"].get("Knowledge Gaps") else 0)
            ),
            "AI Health": _clamp(
                0.6 + by_channel.get("AI Events", 0) * 0.05 - (0.25 if anomalies["detected"].get("Inactive AI") else 0)
            ),
        }
        overall = round(sum(indices.values()) / len(indices), 3)
        indices["Overall Platform Health"] = overall
        return {
            "indices": indices,
            "index_names": list(HEALTH_INDICES),
            "overall": overall,
            "status": "healthy" if overall >= 0.7 else "watch" if overall >= 0.5 else "attention",
            "changes_business_logic": False,
            "generates_business_events": False,
            "ready": True,
        }

    # Step 9 — predictive foundation (no autonomous business decisions)
    def predictive_foundation(self) -> dict[str, Any]:
        events = self._events()
        health = self.visual_health_index()
        base = len(events)
        return {
            "apis": {
                "Capacity Forecast": {
                    "ready": True,
                    "projected_load": round(base * 1.15, 2),
                    "autonomous_decision": False,
                },
                "Growth Forecast": {
                    "ready": True,
                    "projected_growth": round(0.05 + min(0.2, base * 0.01), 3),
                    "autonomous_decision": False,
                },
                "Load Forecast": {
                    "ready": True,
                    "projected_events": int(base * 1.2),
                    "autonomous_decision": False,
                },
                "Risk Visualization": {
                    "ready": True,
                    "risk_score": round(1.0 - health["overall"], 3),
                    "autonomous_decision": False,
                },
                "Resource Forecast": {
                    "ready": True,
                    "visual_only": True,
                    "autonomous_decision": False,
                },
                "Future Expansion": {
                    "ready": True,
                    "planned": True,
                    "autonomous_decision": False,
                },
            },
            "api_names": list(PREDICTIVE_APIS),
            "autonomous_business_decisions": False,
            "note": "Predictive visualization foundation only — no autonomous business decisions.",
            "ready": True,
        }

    def ui_dashboard(self) -> dict[str, Any]:
        return {
            "surfaces": list(UI_SURFACES),
            "insight_center": self.executive_insights(),
            "executive_dashboard": self.executive_insights(),
            "health_overview": self.visual_health_index(),
            "recommendation_panel": self.attention_recommendations(),
            "trend_explorer": self.trend_engine(),
            "heatmap_viewer": self.visual_heatmaps(),
            "changes_business_logic": False,
            "generates_business_events": False,
            "ready": True,
        }

    def analyze_snapshot(self) -> dict[str, Any]:
        """Full analytics pass — visual recommendations only."""
        snapshot = {
            "patterns": self.pattern_detection(),
            "anomalies": self.anomaly_detection(),
            "recommendations": self.attention_recommendations(),
            "executive": self.executive_insights(),
            "heatmaps": self.visual_heatmaps(),
            "trends": self.trend_engine(),
            "health": self.visual_health_index(),
            "predictive": self.predictive_foundation(),
            "changes_business_logic": False,
            "generates_business_events": False,
        }
        return self.analytics.save_snapshot(snapshot)

    # Wizard
    def start_session(self) -> dict[str, Any]:
        sid = _id("vint")
        record = {
            "session_id": sid,
            "status": "in_progress",
            "step": 1,
            "draft": {},
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.store.intelligence_wizard_sessions.save(sid, record)
        return record

    def get_session(self, session_id: str) -> dict[str, Any]:
        session = self.store.intelligence_wizard_sessions.get(session_id)
        if not session:
            raise NotFoundError(f"Intelligence session not found: {session_id}")
        return session

    def update_session(self, session_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        session = self.get_session(session_id)
        if "step" in patch:
            step = int(patch["step"])
            if step < 1 or step > 10:
                raise ValidationError("step must be between 1 and 10")
            session["step"] = step
        if "draft" in patch and isinstance(patch["draft"], dict):
            session["draft"] = {**session.get("draft", {}), **patch["draft"]}
        session["updated_at"] = _now()
        self.store.intelligence_wizard_sessions.save(session_id, session)
        return session

    def summary(self, session_id: str) -> dict[str, Any]:
        return {
            "session_id": session_id,
            "title": "Visual Intelligence Engine Summary",
            "engine": self.engine_overview(),
            "patterns": self.pattern_detection(),
            "anomalies": self.anomaly_detection(),
            "recommendations": self.attention_recommendations(),
            "executive": self.executive_insights(),
            "heatmaps": self.visual_heatmaps(),
            "trends": self.trend_engine(),
            "health": self.visual_health_index(),
            "predictive": self.predictive_foundation(),
            "ui": self.ui_dashboard(),
        }

    def create(self, session_id: str) -> dict[str, Any]:
        session = self.get_session(session_id)
        snapshot = self.analyze_snapshot()

        eng_id = _id("vieng")
        insight_id = _id("vins")
        analytics_id = _id("vana_reg")
        rec_id = _id("vrec")

        intelligence_engine = {
            "intelligence_engine_id": eng_id,
            "internal_id": eng_id,
            "catalog": self.catalog(),
            "changes_business_logic": False,
            "generates_business_events": False,
            "analyzes_verified_events_only": True,
            "autonomous_business_decisions": False,
            "registered_at": _now(),
            "sprint": "29.10",
        }
        insight_registry = {
            "insight_registry_id": insight_id,
            "internal_id": insight_id,
            "insights": list(EXECUTIVE_INSIGHTS),
            "registered_at": _now(),
            "sprint": "29.10",
        }
        analytics_registry = {
            "analytics_registry_id": analytics_id,
            "internal_id": analytics_id,
            "snapshots": self.analytics.list_snapshots(),
            "registered_at": _now(),
            "sprint": "29.10",
        }
        recommendation_registry = {
            "recommendation_registry_id": rec_id,
            "internal_id": rec_id,
            "recommendations": list(ATTENTION_RECOMMENDATIONS),
            "produces_visual_recommendations_only": True,
            "registered_at": _now(),
            "sprint": "29.10",
        }

        self.store.intelligence_engines.save(eng_id, intelligence_engine)
        self.store.insight_registries.save(insight_id, insight_registry)
        self.store.analytics_registries.save(analytics_id, analytics_registry)
        self.store.recommendation_registries.save(rec_id, recommendation_registry)

        # Registry visual signal only — not a business event generator from intelligence analysis
        self.bus.publish(
            "Registry Events",
            "visual_intelligence_engine_registered",
            {"intelligence_engine_id": eng_id, "visual_only": True},
        )

        session["status"] = "created"
        session["registrations"] = {
            "intelligence_engine_id": eng_id,
            "insight_registry_id": insight_id,
            "analytics_registry_id": analytics_id,
            "recommendation_registry_id": rec_id,
            "analytics_snapshot_id": snapshot["analytics_id"],
        }
        session["updated_at"] = _now()
        self.store.intelligence_wizard_sessions.save(session_id, session)

        return {
            "ok": True,
            "session_id": session_id,
            "intelligence_engine": intelligence_engine,
            "insight_registry": insight_registry,
            "analytics_registry": analytics_registry,
            "recommendation_registry": recommendation_registry,
            "snapshot": snapshot,
            "message": "Visual Intelligence Engine, Insight Registry, Analytics Registry, and Recommendation Registry registered.",
        }
