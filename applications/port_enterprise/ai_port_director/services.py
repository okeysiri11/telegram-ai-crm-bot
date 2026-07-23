"""Predictive logistics, autonomous ops, operational intelligence, executive AI."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from applications.port_enterprise.shared.exceptions import ValidationError
from applications.port_enterprise.shared.store import PortEnterpriseStore, port_enterprise_store

DASHBOARD_TYPES = [
    "ai_director",
    "decision_support",
    "predictive_logistics",
    "autonomous_operations",
    "executive_intelligence",
]
REGISTRY_TYPES = ["director", "decision", "forecast", "operations", "executive"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class PredictiveLogistics:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store

    def predict_arrival(self, *, vessel_ref: str, eta_hours: float) -> dict[str, Any]:
        pid = _id("ad_arr")
        return self.store.ad_arrival_pred.save(
            pid,
            {
                "prediction_id": pid,
                "vessel_ref": vessel_ref,
                "eta_hours": float(eta_hours),
                "confidence": 0.87,
                "at": _now(),
            },
        )

    def predict_departure(self, *, vessel_ref: str, etd_hours: float) -> dict[str, Any]:
        pid = _id("ad_dep")
        return self.store.ad_departure_pred.save(
            pid,
            {
                "prediction_id": pid,
                "vessel_ref": vessel_ref,
                "etd_hours": float(etd_hours),
                "confidence": 0.85,
                "at": _now(),
            },
        )

    def cargo_flow(self, *, terminal_ref: str, teu: float, days: int = 7) -> dict[str, Any]:
        fid = _id("ad_cflow")
        return self.store.ad_cargo_flow.save(
            fid,
            {
                "forecast_id": fid,
                "terminal_ref": terminal_ref,
                "teu": float(teu),
                "days": int(days),
                "predicted_teu": round(float(teu) * 1.06, 2),
                "at": _now(),
            },
        )

    def congestion(self, *, terminal_ref: str) -> dict[str, Any]:
        cid = _id("ad_cong")
        return self.store.ad_congestion.save(
            cid,
            {
                "forecast_id": cid,
                "terminal_ref": terminal_ref,
                "congestion_index": 0.54,
                "wait_hours": 3.2,
                "at": _now(),
            },
        )

    def equipment_utilization(self, *, equipment_type: str, utilization_pct: float) -> dict[str, Any]:
        eid = _id("ad_equt")
        return self.store.ad_equip_util.save(
            eid,
            {
                "forecast_id": eid,
                "equipment_type": equipment_type,
                "utilization_pct": float(utilization_pct),
                "predicted_pct": min(98.0, float(utilization_pct) * 1.05),
                "at": _now(),
            },
        )

    def demand(self, *, corridor: str, baseline: float, days: int = 30) -> dict[str, Any]:
        did = _id("ad_dmd")
        return self.store.ad_demand.save(
            did,
            {
                "forecast_id": did,
                "corridor": corridor,
                "days": int(days),
                "predicted": round(float(baseline) * 1.1, 2),
                "at": _now(),
            },
        )

    def supply_chain(self, *, chain_ref: str) -> dict[str, Any]:
        sid = _id("ad_sc")
        return self.store.ad_supply_chain.save(
            sid,
            {
                "forecast_id": sid,
                "chain_ref": chain_ref,
                "risk_index": 0.28,
                "at": _now(),
            },
        )

    def weather_impact(self, *, location: str, severity: float) -> dict[str, Any]:
        severity = float(severity)
        if severity < 0 or severity > 1:
            raise ValidationError("severity must be 0..1")
        wid = _id("ad_wx")
        return self.store.ad_weather.save(
            wid,
            {
                "forecast_id": wid,
                "location": location,
                "severity": severity,
                "ops_impact": "moderate" if severity >= 0.4 else "low",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "arrivals": self.store.ad_arrival_pred.count(),
            "departures": self.store.ad_departure_pred.count(),
            "cargo_flows": self.store.ad_cargo_flow.count(),
            "congestion": self.store.ad_congestion.count(),
        }


class AutonomousOperations:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store

    def schedule_dock(self, *, dock_ref: str, vessel_ref: str, window_start: str) -> dict[str, Any]:
        sid = _id("ad_adock")
        return self.store.ad_auto_dock.save(
            sid,
            {
                "schedule_id": sid,
                "dock_ref": dock_ref,
                "vessel_ref": vessel_ref,
                "window_start": window_start,
                "autonomous": True,
                "at": _now(),
            },
        )

    def allocate_berth(self, *, berth_ref: str, vessel_ref: str) -> dict[str, Any]:
        aid = _id("ad_aberth")
        return self.store.ad_auto_berth.save(
            aid,
            {
                "allocation_id": aid,
                "berth_ref": berth_ref,
                "vessel_ref": vessel_ref,
                "autonomous": True,
                "at": _now(),
            },
        )

    def schedule_equipment(self, *, equipment_ref: str, task: str) -> dict[str, Any]:
        sid = _id("ad_aeq")
        return self.store.ad_auto_equip.save(
            sid,
            {
                "task_id": sid,
                "equipment_ref": equipment_ref,
                "task": task,
                "autonomous": True,
                "at": _now(),
            },
        )

    def plan_container_move(self, *, container_ref: str, from_slot: str, to_slot: str) -> dict[str, Any]:
        pid = _id("ad_amove")
        return self.store.ad_auto_moves.save(
            pid,
            {
                "plan_id": pid,
                "container_ref": container_ref,
                "from_slot": from_slot,
                "to_slot": to_slot,
                "autonomous": True,
                "at": _now(),
            },
        )

    def optimize_yard(self, *, yard_ref: str) -> dict[str, Any]:
        oid = _id("ad_ayard")
        return self.store.ad_auto_yard.save(
            oid,
            {
                "optimization_id": oid,
                "yard_ref": yard_ref,
                "space_gain_pct": 9.5,
                "autonomous": True,
                "at": _now(),
            },
        )

    def coordinate_fleet(self, *, fleet_ref: str, objective: str = "throughput") -> dict[str, Any]:
        cid = _id("ad_afleet")
        return self.store.ad_auto_fleet.save(
            cid,
            {
                "coordination_id": cid,
                "fleet_ref": fleet_ref,
                "objective": objective,
                "autonomous": True,
                "at": _now(),
            },
        )

    def schedule_maintenance(self, *, asset_ref: str, due_at: str) -> dict[str, Any]:
        mid = _id("ad_amaint")
        return self.store.ad_auto_maint.save(
            mid,
            {
                "schedule_id": mid,
                "asset_ref": asset_ref,
                "due_at": due_at,
                "autonomous": True,
                "at": _now(),
            },
        )

    def emergency_plan(self, *, incident_type: str, severity: str = "medium") -> dict[str, Any]:
        if not incident_type:
            raise ValidationError("incident_type required")
        eid = _id("ad_aemrg")
        return self.store.ad_auto_emergency.save(
            eid,
            {
                "plan_id": eid,
                "incident_type": incident_type,
                "severity": severity,
                "steps": ["secure", "notify", "contain", "recover"],
                "autonomous": True,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "dock_schedules": self.store.ad_auto_dock.count(),
            "berth_allocations": self.store.ad_auto_berth.count(),
            "equipment_tasks": self.store.ad_auto_equip.count(),
            "yard_opts": self.store.ad_auto_yard.count(),
        }


class OperationalIntelligence:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store

    def risk_assess(self, *, domain: str, score: float) -> dict[str, Any]:
        score = float(score)
        if score < 0 or score > 1:
            raise ValidationError("score must be 0..1")
        rid = _id("ad_risk")
        return self.store.ad_op_risk.save(
            rid,
            {
                "assessment_id": rid,
                "domain": domain,
                "score": score,
                "band": "high" if score >= 0.7 else "medium" if score >= 0.4 else "low",
                "at": _now(),
            },
        )

    def delay_predict(self, *, subject_ref: str, risk: float) -> dict[str, Any]:
        risk = float(risk)
        if risk < 0 or risk > 1:
            raise ValidationError("risk must be 0..1")
        did = _id("ad_odel")
        return self.store.ad_op_delay.save(
            did,
            {
                "prediction_id": did,
                "subject_ref": subject_ref,
                "risk": risk,
                "expected_delay_hours": round(risk * 24, 1),
                "at": _now(),
            },
        )

    def bottleneck(self, *, location: str, severity: float) -> dict[str, Any]:
        bid = _id("ad_bn")
        return self.store.ad_bottlenecks.save(
            bid,
            {
                "detection_id": bid,
                "location": location,
                "severity": float(severity),
                "at": _now(),
            },
        )

    def incident_predict(self, *, domain: str, probability: float) -> dict[str, Any]:
        probability = float(probability)
        if probability < 0 or probability > 1:
            raise ValidationError("probability must be 0..1")
        iid = _id("ad_inc")
        return self.store.ad_incidents.save(
            iid,
            {
                "prediction_id": iid,
                "domain": domain,
                "probability": probability,
                "at": _now(),
            },
        )

    def capacity_forecast(self, *, node: str, teu: float) -> dict[str, Any]:
        cid = _id("ad_cap")
        return self.store.ad_op_capacity.save(
            cid,
            {
                "forecast_id": cid,
                "node": node,
                "teu": float(teu),
                "peak_utilization_pct": 82.0,
                "at": _now(),
            },
        )

    def kpi_predict(self, *, kpi: str, baseline: float) -> dict[str, Any]:
        kid = _id("ad_kpi")
        return self.store.ad_kpi_pred.save(
            kid,
            {
                "prediction_id": kid,
                "kpi": kpi,
                "baseline": float(baseline),
                "predicted": round(float(baseline) * 1.03, 2),
                "at": _now(),
            },
        )

    def optimize_performance(self, *, scope: str) -> dict[str, Any]:
        oid = _id("ad_perf")
        return self.store.ad_perf_opts.save(
            oid,
            {
                "optimization_id": oid,
                "scope": scope,
                "gain_pct": 7.8,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "risks": self.store.ad_op_risk.count(),
            "delays": self.store.ad_op_delay.count(),
            "bottlenecks": self.store.ad_bottlenecks.count(),
        }


class ExecutiveAI:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store

    def chat(self, *, message: str, executive: str = "CEO") -> dict[str, Any]:
        if not message:
            raise ValidationError("message required")
        cid = _id("ad_echat")
        return self.store.ad_exec_chat.save(
            cid,
            {
                "chat_id": cid,
                "executive": executive,
                "message": message,
                "reply": f"Executive summary: port operations are stable regarding '{message[:80]}'",
                "at": _now(),
            },
        )

    def daily_briefing(self, *, date: str = "") -> dict[str, Any]:
        bid = _id("ad_brief")
        return self.store.ad_briefings.save(
            bid,
            {
                "briefing_id": bid,
                "date": date or _now()[:10],
                "highlights": ["throughput on plan", "congestion moderate", "no critical incidents"],
                "at": _now(),
            },
        )

    def health_score(self, *, score: float) -> dict[str, Any]:
        score = float(score)
        if score < 0 or score > 100:
            raise ValidationError("score must be 0..100")
        hid = _id("ad_ehs")
        return self.store.ad_health_scores.save(
            hid,
            {
                "score_id": hid,
                "score": score,
                "band": "excellent" if score >= 85 else "good" if score >= 70 else "watch",
                "at": _now(),
            },
        )

    def strategic_recommendation(self, *, theme: str, action: str) -> dict[str, Any]:
        rid = _id("ad_estrat")
        return self.store.ad_exec_strategy.save(
            rid,
            {
                "recommendation_id": rid,
                "theme": theme,
                "action": action,
                "at": _now(),
            },
        )

    def financial_insight(self, *, metric: str, value: float) -> dict[str, Any]:
        fid = _id("ad_fin")
        return self.store.ad_financial.save(
            fid,
            {
                "insight_id": fid,
                "metric": metric,
                "value": float(value),
                "trend": "up",
                "at": _now(),
            },
        )

    def investment_plan(self, *, project: str, amount: float) -> dict[str, Any]:
        if not project:
            raise ValidationError("project required")
        iid = _id("ad_inv")
        return self.store.ad_investments.save(
            iid,
            {
                "plan_id": iid,
                "project": project,
                "amount": float(amount),
                "roi_years": 4.5,
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {
            "chats": self.store.ad_exec_chat.count(),
            "briefings": self.store.ad_briefings.count(),
            "health_scores": self.store.ad_health_scores.count(),
        }


class DirectorDashboard:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store
        self.types = list(DASHBOARD_TYPES)

    def render(self, *, dashboard_type: str = "ai_director") -> dict[str, Any]:
        if dashboard_type not in self.types:
            raise ValidationError(f"dashboard_type must be one of {self.types}")
        metrics = {
            "ai_director": {
                "assistant": self.store.ad_assistant.count(),
                "advisories": self.store.ad_advisories.count(),
            },
            "decision_support": {
                "decisions": self.store.ad_decisions.count(),
                "scenarios": self.store.ad_scenarios.count(),
            },
            "predictive_logistics": {
                "arrivals": self.store.ad_arrival_pred.count(),
                "congestion": self.store.ad_congestion.count(),
            },
            "autonomous_operations": {
                "docks": self.store.ad_auto_dock.count(),
                "yard": self.store.ad_auto_yard.count(),
            },
            "executive_intelligence": {
                "briefings": self.store.ad_briefings.count(),
                "health": self.store.ad_health_scores.count(),
            },
        }[dashboard_type]
        did = _id("ad_dash")
        return self.store.ad_dashboards.save(
            did,
            {"dashboard_id": did, "dashboard_type": dashboard_type, "metrics": metrics, "generated_at": _now()},
        )

    def status(self) -> dict[str, Any]:
        return {"dashboards": self.store.ad_dashboards.count(), "types": self.types}


class DirectorKnowledge:
    def __init__(self, store: PortEnterpriseStore | None = None) -> None:
        self.store = store or port_enterprise_store
        self.types = list(REGISTRY_TYPES)

    def publish(self, *, registry_type: str, key: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if registry_type not in self.types:
            raise ValidationError(f"registry_type must be one of {self.types}")
        if not key:
            raise ValidationError("key required")
        rid = _id("ad_reg")
        return self.store.ad_registries.save(
            rid,
            {
                "registry_id": rid,
                "registry_type": registry_type,
                "key": key,
                "payload": payload or {},
                "graph_node": f"ad:{registry_type}:{key}",
                "at": _now(),
            },
        )

    def status(self) -> dict[str, Any]:
        return {"entries": self.store.ad_registries.count(), "types": self.types}
