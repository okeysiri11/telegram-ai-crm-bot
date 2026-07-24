from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.enterprise_hub.shared.exceptions import NotFoundError, ValidationError
from applications.enterprise_hub.shared.store import EnterpriseHubStore, enterprise_hub_store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"

from applications.enterprise_hub.command_center.models import HEALTH_DIMENSIONS, MAP_ENTITY_KINDS


class EnterpriseHealthMonitor:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def evaluate(self, scores: dict[str, float] | None = None) -> dict[str, Any]:
        defaults = {
            "performance": 0.84,
            "financial_stability": 0.81,
            "resource_utilization": 0.76,
            "process_quality": 0.79,
            "integration_health": 0.88,
            "service_availability": 0.95,
            "user_activity": 0.72,
        }
        dims = dict(defaults)
        if scores:
            dims.update({k: float(v) for k, v in scores.items() if k in HEALTH_DIMENSIONS})
        overall = round(sum(dims.values()) / len(dims), 3)
        hid = _id("ecc_health")
        record = {
            "health_id": hid,
            "dimensions": dims,
            "enterprise_health_score": overall,
            "status": "healthy" if overall >= 0.75 else "watch" if overall >= 0.55 else "critical",
            "evaluated_at": _now(),
        }
        self.store.ecc_health.save(hid, record)
        return record


class AISituationRoom:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def brief(self) -> dict[str, Any]:
        sid = _id("ecc_sit")
        record = {
            "situation_id": sid,
            "events": ["event_bus spike", "workflow backlog cleared"],
            "deviations": ["SLA near breach in logistics"],
            "threats": ["cyber scan anomaly low"],
            "opportunities": ["automate customs checks"],
            "forecasts": {"throughput": "+6%", "margin": "+1.2pp"},
            "daily_brief": (
                "Enterprise is healthy. Logistics load elevated; AI recommends customs automation. "
                "No critical financial risks. Simulation suggests +6% throughput if berth plan optimized."
            ),
            "briefed_at": _now(),
        }
        self.store.ecc_situation.save(sid, record)
        return record


class AIExecutiveAssistant:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def assist(self, *, prompt: str = "daily report") -> dict[str, Any]:
        if not prompt:
            raise ValidationError("prompt is required")
        aid = _id("ecc_asst")
        record = {
            "assistant_id": aid,
            "prompt": prompt,
            "daily_report": "Ops stable; focus on logistics SLA and AI agent coverage.",
            "recommendations": [
                "Merge duplicate approval steps in procurement",
                "Scale maritime AI dispatch agents",
                "Invest in warehouse automation for ROI",
            ],
            "forecasts": {"q_growth": 0.08, "risk": 0.21},
            "risk_analysis": ["supplier delay risk medium", "integration lag low"],
            "investment_proposals": [{"name": "AI Customs", "roi": 0.27}],
            "optimization_plans": ["rebalance berth schedule", "auto-escalate SLA breaches"],
            "assisted_at": _now(),
        }
        self.store.ecc_assistant.save(aid, record)
        return record


class EnterpriseMap:
    def __init__(self, store: EnterpriseHubStore | None = None) -> None:
        self.store = store or enterprise_hub_store

    def render(self) -> dict[str, Any]:
        entities = [
            {"kind": "department", "name": "Operations HQ", "lat": 55.75, "lon": 37.61},
            {"kind": "warehouse", "name": "DC-1", "lat": 55.80, "lon": 37.50},
            {"kind": "production", "name": "Plant-A", "lat": 56.00, "lon": 37.80},
            {"kind": "vessel", "name": "MV Aurora", "lat": 59.93, "lon": 30.31},
            {"kind": "construction_site", "name": "Terminal-3", "lat": 59.90, "lon": 30.25},
            {"kind": "healthcare_facility", "name": "Clinic-East", "lat": 55.70, "lon": 37.70},
            {"kind": "ai_component", "name": "Orchestrator", "lat": 55.75, "lon": 37.62},
            {"kind": "transport", "name": "Fleet-12", "lat": 55.72, "lon": 37.55},
            {"kind": "equipment", "name": "Crane-7", "lat": 59.92, "lon": 30.28},
            {"kind": "facility", "name": "HQ Campus", "lat": 55.751, "lon": 37.617},
        ]
        mid = _id("ecc_map")
        record = {
            "map_id": mid,
            "entities": entities,
            "kinds": list(MAP_ENTITY_KINDS),
            "entity_count": len(entities),
            "rendered_at": _now(),
        }
        self.store.ecc_maps.save(mid, record)
        return record
