# CRM manager intelligence — command center, pipeline forecast, risk, team performance.

from __future__ import annotations

import time
from enum import Enum
from typing import Any

from applications.auto_marketplace.activities.service import ActivityService, activity_service
from applications.auto_marketplace.crm.automation import CRMAutomationEngine, crm_automation
from applications.auto_marketplace.crm.customer_360 import score_relationship
from applications.auto_marketplace.crm.execution import CRMExecutionEngine, crm_execution
from applications.auto_marketplace.crm.intelligence import CRMIntelligenceService, crm_intelligence
from applications.auto_marketplace.crm.models import (
    CRMDeal,
    CRMLeadStatus,
    DealStage,
    Interaction,
    InteractionType,
    TaskStatus,
)
from applications.auto_marketplace.crm.tenant import current_crm_tenant
from applications.auto_marketplace.deals.service import DealService, deal_service
from applications.auto_marketplace.leads.service import LeadService, lead_service
from applications.auto_marketplace.tasks.service import TaskService, task_service

CURRENCY_UNSPECIFIED = "unspecified"
REPORTING_WINDOW_SECONDS = 30 * 86400
DEFAULT_PIPELINE_LIMIT = 50
MAX_PIPELINE_LIMIT = 200
DEFAULT_TOP_LIMIT = 10
DEFAULT_ACTION_LIMIT = 50

_CLOSED_STAGES = frozenset({DealStage.CLOSED_WON, DealStage.CLOSED_LOST})
_OPEN_TASKS = frozenset({TaskStatus.PENDING, TaskStatus.IN_PROGRESS})
_MEANINGFUL_COMM = frozenset({InteractionType.CALL, InteractionType.EMAIL, InteractionType.MEETING})
_HOT_NO_ACTION = frozenset({"CALL_CUSTOMER", "CREATE_FOLLOW_UP", "COMPLETE_OVERDUE_TASK"})
STAGE_BASE_PROBABILITY = {
    DealStage.PROSPECT: 0.10,
    DealStage.QUALIFICATION: 0.25,
    DealStage.PROPOSAL: 0.45,
    DealStage.NEGOTIATION: 0.65,
    DealStage.APPROVAL: 0.85,
    DealStage.CLOSED_WON: 1.0,
    DealStage.CLOSED_LOST: 0.0,
}
PROB_ADJ_HOT = 0.08
PROB_ADJ_WARM = 0.03
PROB_ADJ_SCORE_HOT = 0.05
PROB_ADJ_SCORE_WARM = 0.02
PROB_ADJ_SCORE_COLD = -0.05
PROB_ADJ_REL_STRONG = 0.05
PROB_ADJ_REL_HEALTHY = 0.02
PROB_ADJ_REL_ATTENTION = -0.03
PROB_ADJ_REL_AT_RISK = -0.08
PROB_ADJ_STALE = -0.12
PROB_ADJ_SLA_DUE_SOON = -0.04
PROB_ADJ_SLA_OVERDUE = -0.08
PROB_ADJ_SLA_BREACHED = -0.15
PROB_ADJ_ESC_ATTENTION = -0.04
PROB_ADJ_ESC_MANAGER = -0.08
PROB_ADJ_ESC_CRITICAL = -0.12
PROB_ADJ_FOLLOW_UP_OVERDUE = -0.08
PROB_ADJ_HOT_NO_ACTION = -0.06

RISK_STALE = 25
RISK_NO_CONTACT = 15
RISK_FOLLOW_UP_OVERDUE = 20
RISK_TASK_OVERDUE = 18
RISK_SLA_AT_RISK = 12
RISK_SLA_BREACHED = 30
RISK_ESCALATED = 22
RISK_LOW_HEALTH = 20
RISK_HOT_NO_ACTION = 15
RISK_HIGH_VALUE_NEGLECTED = 25
RISK_OWNER_OVERLOADED = 15
RISK_MEDIUM = 20
RISK_HIGH = 45
RISK_CRITICAL = 70

WORKLOAD_OPEN_DEAL = 8
WORKLOAD_HIGH_PRIORITY = 12
WORKLOAD_OVERDUE_FOLLOW_UP = 15
WORKLOAD_OVERDUE_TASK = 12
WORKLOAD_SLA_AT_RISK = 8
WORKLOAD_SLA_BREACHED = 20
WORKLOAD_ESCALATION = 18
WORKLOAD_HIGH_RISK = 15
WORKLOAD_ELEVATED = 30
WORKLOAD_HIGH = 60
WORKLOAD_CRITICAL = 90

_RISK_RANK = {"critical": 3, "high": 2, "medium": 1, "low": 0}
_PRIORITY_RANK = {"critical": 3, "high": 2, "medium": 1, "low": 0}


class ForecastCategory(str, Enum):
    COMMIT = "commit"
    LIKELY = "likely"
    UPSIDE = "upside"
    PIPELINE = "pipeline"
    AT_RISK = "at_risk"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class DealRiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class WorkloadLevel(str, Enum):
    NORMAL = "normal"
    ELEVATED = "elevated"
    HIGH = "high"
    CRITICAL = "critical"


def clamp_probability(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def deal_currency(_deal: CRMDeal | None = None) -> str:
    return CURRENCY_UNSPECIFIED


def add_money(buckets: dict[str, float], currency: str, amount: float) -> None:
    key = currency or CURRENCY_UNSPECIFIED
    buckets[key] = round(float(buckets.get(key) or 0.0) + float(amount or 0.0), 2)


def money_payload(buckets: dict[str, float]) -> dict[str, Any]:
    ordered = {key: buckets[key] for key in sorted(buckets)}
    mixed = len(ordered) > 1
    return {
        "by_currency": ordered,
        "mixed_currencies": mixed,
        "canonical_total": None if mixed else next(iter(ordered.values()), 0.0),
    }


def _explain(codes: list[str]) -> str:
    return ", ".join(code.replace("_", " ").lower() for code in codes) or "No forecast adjustments"


def forecast_probability(
    *,
    stage: DealStage,
    score: int,
    temperature: str,
    relationship_health: str,
    stale: bool,
    sla_status: str,
    escalation_level: str,
    follow_up_overdue: bool,
    hot_no_action: bool,
) -> dict[str, Any]:
    base = STAGE_BASE_PROBABILITY.get(stage, 0.2)
    reasons = [f"STAGE_{stage.value.upper()}"]
    if stage in _CLOSED_STAGES:
        return {
            "forecast_probability": clamp_probability(base),
            "reason_codes": reasons,
            "explanation": _explain(reasons),
        }
    adjustments: list[tuple[str, float]] = []
    if temperature == "hot":
        adjustments.append(("TEMPERATURE_HOT", PROB_ADJ_HOT))
    elif temperature == "warm":
        adjustments.append(("TEMPERATURE_WARM", PROB_ADJ_WARM))
    if score >= 75:
        adjustments.append(("LEAD_SCORE_HOT", PROB_ADJ_SCORE_HOT))
    elif score >= 45:
        adjustments.append(("LEAD_SCORE_WARM", PROB_ADJ_SCORE_WARM))
    elif score < 30:
        adjustments.append(("LEAD_SCORE_COLD", PROB_ADJ_SCORE_COLD))
    if relationship_health == "strong":
        adjustments.append(("RELATIONSHIP_STRONG", PROB_ADJ_REL_STRONG))
    elif relationship_health == "healthy":
        adjustments.append(("RELATIONSHIP_HEALTHY", PROB_ADJ_REL_HEALTHY))
    elif relationship_health == "attention":
        adjustments.append(("RELATIONSHIP_ATTENTION", PROB_ADJ_REL_ATTENTION))
    elif relationship_health == "at_risk":
        adjustments.append(("RELATIONSHIP_AT_RISK", PROB_ADJ_REL_AT_RISK))
    if stale:
        adjustments.append(("STALE_DEAL", PROB_ADJ_STALE))
    if sla_status == "due_soon":
        adjustments.append(("SLA_AT_RISK", PROB_ADJ_SLA_DUE_SOON))
    elif sla_status == "overdue":
        adjustments.append(("SLA_OVERDUE", PROB_ADJ_SLA_OVERDUE))
    elif sla_status == "breached":
        adjustments.append(("SLA_BREACHED", PROB_ADJ_SLA_BREACHED))
    if escalation_level == "attention":
        adjustments.append(("ESCALATION_ATTENTION", PROB_ADJ_ESC_ATTENTION))
    elif escalation_level == "manager":
        adjustments.append(("ESCALATION_MANAGER", PROB_ADJ_ESC_MANAGER))
    elif escalation_level == "critical":
        adjustments.append(("ESCALATION_CRITICAL", PROB_ADJ_ESC_CRITICAL))
    if follow_up_overdue:
        adjustments.append(("FOLLOW_UP_OVERDUE", PROB_ADJ_FOLLOW_UP_OVERDUE))
    if hot_no_action:
        adjustments.append(("HOT_LEAD_NO_ACTION", PROB_ADJ_HOT_NO_ACTION))
    probability = base
    for code, delta in adjustments:
        reasons.append(code)
        probability += delta
    reasons = sorted(set(reasons))
    return {
        "forecast_probability": round(clamp_probability(probability), 4),
        "reason_codes": reasons,
        "explanation": _explain(reasons),
    }


def classify_forecast_category(
    *,
    stage: DealStage,
    probability: float,
    risk_level: str,
    stale: bool,
) -> dict[str, Any]:
    if stage == DealStage.CLOSED_WON:
        codes = ["CLOSED_WON"]
        return {"forecast_category": ForecastCategory.CLOSED_WON.value, "reason_codes": codes, "explanation": _explain(codes)}
    if stage == DealStage.CLOSED_LOST:
        codes = ["CLOSED_LOST"]
        return {"forecast_category": ForecastCategory.CLOSED_LOST.value, "reason_codes": codes, "explanation": _explain(codes)}
    if risk_level in {DealRiskLevel.HIGH.value, DealRiskLevel.CRITICAL.value} or stale or probability < 0.20:
        codes = ["AT_RISK_SIGNALS"]
        if stale:
            codes.append("STALE_DEAL")
        if risk_level in {DealRiskLevel.HIGH.value, DealRiskLevel.CRITICAL.value}:
            codes.append(f"RISK_{risk_level.upper()}")
        if probability < 0.20:
            codes.append("LOW_PROBABILITY")
        codes = sorted(set(codes))
        return {"forecast_category": ForecastCategory.AT_RISK.value, "reason_codes": codes, "explanation": _explain(codes)}
    if stage == DealStage.APPROVAL and probability >= 0.75 and not stale:
        codes = ["STAGE_APPROVAL", "HIGH_PROBABILITY"]
        return {"forecast_category": ForecastCategory.COMMIT.value, "reason_codes": codes, "explanation": _explain(codes)}
    if stage in {DealStage.NEGOTIATION, DealStage.APPROVAL} and probability >= 0.50:
        codes = ["LATE_STAGE", "LIKELY_PROBABILITY"]
        return {"forecast_category": ForecastCategory.LIKELY.value, "reason_codes": codes, "explanation": _explain(codes)}
    if stage in {DealStage.PROPOSAL, DealStage.QUALIFICATION} and probability >= 0.30:
        codes = ["MID_STAGE", "UPSIDE_PROBABILITY"]
        return {"forecast_category": ForecastCategory.UPSIDE.value, "reason_codes": codes, "explanation": _explain(codes)}
    codes = ["OPEN_PIPELINE"]
    return {"forecast_category": ForecastCategory.PIPELINE.value, "reason_codes": codes, "explanation": _explain(codes)}


def classify_deal_risk(
    *,
    stale: bool,
    follow_up_overdue: bool,
    task_overdue: bool,
    sla_status: str,
    escalation_level: str,
    relationship_health: str,
    hot_no_action: bool,
    high_value_neglected: bool,
    no_recent_contact: bool,
    owner_overloaded: bool = False,
) -> dict[str, Any]:
    flags: list[str] = []
    score = 0
    if stale:
        flags.append("STALE_DEAL")
        score += RISK_STALE
    if no_recent_contact:
        flags.append("NO_RECENT_CONTACT")
        score += RISK_NO_CONTACT
    if follow_up_overdue:
        flags.append("FOLLOW_UP_OVERDUE")
        score += RISK_FOLLOW_UP_OVERDUE
    if task_overdue:
        flags.append("TASK_OVERDUE")
        score += RISK_TASK_OVERDUE
    if sla_status in {"due_soon", "overdue"}:
        flags.append("SLA_AT_RISK")
        score += RISK_SLA_AT_RISK
    if sla_status == "breached":
        flags.append("SLA_BREACHED")
        score += RISK_SLA_BREACHED
    if escalation_level in {"manager", "critical"}:
        flags.append("ESCALATED")
        score += RISK_ESCALATED
    if relationship_health == "at_risk":
        flags.append("LOW_RELATIONSHIP_HEALTH")
        score += RISK_LOW_HEALTH
    if hot_no_action:
        flags.append("HOT_LEAD_NO_ACTION")
        score += RISK_HOT_NO_ACTION
    if high_value_neglected:
        flags.append("HIGH_VALUE_DEAL_NEGLECTED")
        score += RISK_HIGH_VALUE_NEGLECTED
    if owner_overloaded:
        flags.append("OWNER_OVERLOADED")
        score += RISK_OWNER_OVERLOADED
    flags = sorted(set(flags))
    if score >= RISK_CRITICAL:
        level = DealRiskLevel.CRITICAL
    elif score >= RISK_HIGH:
        level = DealRiskLevel.HIGH
    elif score >= RISK_MEDIUM:
        level = DealRiskLevel.MEDIUM
    else:
        level = DealRiskLevel.LOW
    return {
        "risk_level": level.value,
        "risk_score": score,
        "risk_flags": flags,
        "reason_codes": flags,
        "explanation": _explain(flags) if flags else "No material deal risk signals",
    }


def classify_workload(
    *,
    open_deals: int,
    high_priority_items: int,
    overdue_follow_ups: int,
    overdue_tasks: int,
    sla_at_risk: int,
    sla_breaches: int,
    escalations: int,
    high_risk_deals: int,
) -> dict[str, Any]:
    score = (
        open_deals * WORKLOAD_OPEN_DEAL
        + high_priority_items * WORKLOAD_HIGH_PRIORITY
        + overdue_follow_ups * WORKLOAD_OVERDUE_FOLLOW_UP
        + overdue_tasks * WORKLOAD_OVERDUE_TASK
        + sla_at_risk * WORKLOAD_SLA_AT_RISK
        + sla_breaches * WORKLOAD_SLA_BREACHED
        + escalations * WORKLOAD_ESCALATION
        + high_risk_deals * WORKLOAD_HIGH_RISK
    )
    if score >= WORKLOAD_CRITICAL:
        level = WorkloadLevel.CRITICAL
    elif score >= WORKLOAD_HIGH:
        level = WorkloadLevel.HIGH
    elif score >= WORKLOAD_ELEVATED:
        level = WorkloadLevel.ELEVATED
    else:
        level = WorkloadLevel.NORMAL
    reasons = []
    if open_deals:
        reasons.append("ACTIVE_DEALS")
    if high_priority_items:
        reasons.append("HIGH_PRIORITY_ITEMS")
    if overdue_follow_ups:
        reasons.append("OVERDUE_FOLLOW_UPS")
    if overdue_tasks:
        reasons.append("OVERDUE_TASKS")
    if sla_at_risk:
        reasons.append("SLA_AT_RISK")
    if sla_breaches:
        reasons.append("SLA_BREACHED")
    if escalations:
        reasons.append("ESCALATIONS")
    if high_risk_deals:
        reasons.append("HIGH_RISK_DEALS")
    return {
        "workload_level": level.value,
        "workload_score": score,
        "reason_codes": reasons,
        "explanation": _explain(reasons) if reasons else "Operational workload is within normal bounds",
    }


def _owner_key(value: str | None) -> str:
    return value or "unassigned"


def _matches_filters(item: dict[str, Any], filters: dict[str, str | None]) -> bool:
    mapping = {
        "owner": "owner_id",
        "stage": "stage",
        "forecast_category": "forecast_category",
        "risk_level": "risk_level",
        "temperature": "temperature",
        "relationship_health": "relationship_health",
    }
    for name, field in mapping.items():
        expected = filters.get(name)
        if expected and str(item.get(field) or "") != expected:
            return False
    return True


class ManagerIntelligenceService:
    """Read-only manager command center. Consumes Sprints 8–11. No CRM mutations."""

    def __init__(
        self,
        *,
        deals: DealService | None = None,
        leads: LeadService | None = None,
        tasks: TaskService | None = None,
        activities: ActivityService | None = None,
        automation: CRMAutomationEngine | None = None,
        execution: CRMExecutionEngine | None = None,
        intelligence: CRMIntelligenceService | None = None,
    ) -> None:
        self._deals = deals or deal_service
        self._leads = leads or lead_service
        self._tasks = tasks or task_service
        self._activities = activities or activity_service
        self._automation = automation or crm_automation
        self._execution = execution or crm_execution
        self._intelligence = intelligence or crm_intelligence

    async def command_center(
        self,
        *,
        now: float | None = None,
        owner: str | None = None,
        stage: str | None = None,
        forecast_category: str | None = None,
        risk_level: str | None = None,
        temperature: str | None = None,
        relationship_health: str | None = None,
        top_limit: int = DEFAULT_TOP_LIMIT,
        action_limit: int = DEFAULT_ACTION_LIMIT,
    ) -> dict[str, Any]:
        clock = now if now is not None else time.time()
        filters = {
            "owner": owner,
            "stage": stage,
            "forecast_category": forecast_category,
            "risk_level": risk_level,
            "temperature": temperature,
            "relationship_health": relationship_health,
        }
        snapshots = await self._snapshots(now=clock)
        filtered = [item for item in snapshots if _matches_filters(item, filters)]
        queue = await self._execution.queue(now=clock, owner=owner, limit=max(action_limit * 2, 50))
        actions = self._action_center(filtered, queue["items"], limit=action_limit)
        changes = await self._pipeline_changes(now=clock)
        return {
            "tenant_id": current_crm_tenant(),
            "generated_at": clock,
            "currency": CURRENCY_UNSPECIFIED,
            "pipeline_summary": self._forecast_summary(filtered, now=clock),
            "revenue_intelligence": self._revenue_intelligence(filtered, now=clock),
            "team_performance": self._team_performance(filtered, queue["items"]),
            "top_opportunities": self._top_opportunities(filtered, limit=top_limit),
            "top_risks": self._top_risks(filtered, limit=top_limit),
            "action_center": actions,
            "pipeline_changes": changes,
            "next_actions": [item.get("recommended_action") for item in actions["items"][:top_limit]],
        }

    async def pipeline_snapshot(
        self,
        *,
        now: float | None = None,
        owner: str | None = None,
        stage: str | None = None,
        forecast_category: str | None = None,
        risk_level: str | None = None,
        temperature: str | None = None,
        relationship_health: str | None = None,
        limit: int = DEFAULT_PIPELINE_LIMIT,
        offset: int = 0,
    ) -> dict[str, Any]:
        clock = now if now is not None else time.time()
        filters = {
            "owner": owner,
            "stage": stage,
            "forecast_category": forecast_category,
            "risk_level": risk_level,
            "temperature": temperature,
            "relationship_health": relationship_health,
        }
        snapshots = [item for item in await self._snapshots(now=clock) if _matches_filters(item, filters)]
        cap = max(0, min(int(limit), MAX_PIPELINE_LIMIT))
        start = max(0, int(offset))
        return {
            "tenant_id": current_crm_tenant(),
            "generated_at": clock,
            "currency": CURRENCY_UNSPECIFIED,
            "items": snapshots[start : start + cap],
            "total": len(snapshots),
            "limit": cap,
            "offset": start,
        }

    async def forecast(
        self,
        *,
        now: float | None = None,
        owner: str | None = None,
        stage: str | None = None,
        forecast_category: str | None = None,
        risk_level: str | None = None,
        temperature: str | None = None,
        relationship_health: str | None = None,
    ) -> dict[str, Any]:
        clock = now if now is not None else time.time()
        filters = {
            "owner": owner,
            "stage": stage,
            "forecast_category": forecast_category,
            "risk_level": risk_level,
            "temperature": temperature,
            "relationship_health": relationship_health,
        }
        snapshots = [item for item in await self._snapshots(now=clock) if _matches_filters(item, filters)]
        summary = self._forecast_summary(snapshots, now=clock)
        summary["tenant_id"] = current_crm_tenant()
        summary["generated_at"] = clock
        summary["currency"] = CURRENCY_UNSPECIFIED
        return summary

    async def team_performance(
        self,
        *,
        now: float | None = None,
        owner: str | None = None,
    ) -> dict[str, Any]:
        clock = now if now is not None else time.time()
        snapshots = await self._snapshots(now=clock)
        if owner:
            snapshots = [item for item in snapshots if item["owner_id"] == owner]
        queue = await self._execution.queue(now=clock, owner=owner, limit=500)
        report = self._team_performance(snapshots, queue["items"])
        report["tenant_id"] = current_crm_tenant()
        report["generated_at"] = clock
        return report

    async def executive_summary(self, *, now: float | None = None) -> dict[str, Any]:
        clock = now if now is not None else time.time()
        center = await self.command_center(now=clock, top_limit=5, action_limit=5)
        summary = center["pipeline_summary"]
        return {
            "open_pipeline": summary["total_open_pipeline"],
            "weighted_forecast": summary["weighted_pipeline"],
            "commit_forecast": summary["commit_forecast"],
            "won_revenue": summary["won_value"],
            "at_risk_value": summary["at_risk_value"],
            "critical_deal_count": summary["critical_deal_count"],
            "sla_breach_count": summary["sla_breach_count"],
            "escalation_count": summary["escalation_count"],
            "top_opportunities": center["top_opportunities"],
            "top_risks": center["top_risks"],
            "currency": CURRENCY_UNSPECIFIED,
            "generated_at": clock,
            "tenant_id": current_crm_tenant(),
        }

    async def operational_summary(
        self,
        *,
        now: float | None = None,
        owner: str | None = None,
    ) -> dict[str, Any]:
        """Sprint 13 — deterministic production operations summary.

        Read-only composition of persisted CRM facts (deals, leads, tasks,
        follow-ups) through the existing Sprint 8–12 engines. No new
        datastore, no snapshot table — every number is recomputed from
        PostgreSQL-backed services on each call.
        """
        clock = now if now is not None else time.time()
        snapshots = await self._snapshots(now=clock)
        if owner:
            snapshots = [item for item in snapshots if item["owner_id"] == owner]
        open_items = [item for item in snapshots if item["active"]]
        summary = self._forecast_summary(snapshots, now=clock)
        queue = await self._execution.queue(now=clock, owner=owner, limit=100)
        actions = self._action_center(snapshots, queue["items"], limit=DEFAULT_ACTION_LIMIT)

        leads = await self._leads.list_leads()
        active_lead_statuses = {
            CRMLeadStatus.NEW,
            CRMLeadStatus.CONTACTED,
            CRMLeadStatus.QUALIFIED,
        }
        active_leads = [
            lead
            for lead in leads
            if lead.status in active_lead_statuses
            and (not owner or (lead.assigned_agent_id or "unassigned") == owner)
        ]

        tasks = await self._tasks.list_tasks()
        open_task_statuses = {TaskStatus.PENDING, TaskStatus.IN_PROGRESS}
        open_tasks = [task for task in tasks if task.status in open_task_statuses]

        overdue_follow_ups = await self._automation.list_follow_ups(now=clock, overdue=True)

        return {
            "tenant_id": current_crm_tenant(),
            "generated_at": clock,
            "currency": CURRENCY_UNSPECIFIED,
            "active_leads": len(active_leads),
            "active_deals": summary["open_deal_count"],
            "won_deals": summary["won_deal_count"],
            "lost_deals": summary["lost_deal_count"],
            "open_tasks": len(open_tasks),
            "overdue_follow_ups": len(overdue_follow_ups),
            "sla_at_risk": sum(
                1 for item in open_items if item["sla_status"] in {"due_soon", "overdue", "breached"}
            ),
            "sla_breached": summary["sla_breach_count"],
            "escalated": summary["escalation_count"],
            "critical_deals": summary["critical_deal_count"],
            "stale_deals": sum(1 for item in open_items if item["stale"]),
            "weighted_pipeline": summary["weighted_pipeline"],
            "forecast": {
                "total_open_pipeline": summary["total_open_pipeline"],
                "commit_forecast": summary["commit_forecast"],
                "likely_forecast": summary["likely_forecast"],
                "upside_forecast": summary["upside_forecast"],
                "at_risk_value": summary["at_risk_value"],
                "won_value": summary["won_value"],
            },
            "top_priority_actions": actions["items"][:5],
        }

    async def _snapshots(self, *, now: float) -> list[dict[str, Any]]:
        deals = await self._deals.list_deals()
        follow_ups = await self._automation.list_follow_ups(now=now)
        tasks = await self._tasks.list_tasks()
        activities = await self._activities.list_activities()
        last_activity = self._last_activity_index(activities)
        next_follow_up = self._next_follow_up_index(follow_ups)
        overdue_tasks = self._overdue_task_index(tasks, now=now)
        snapshots: list[dict[str, Any]] = []
        for deal in deals:
            execution = await self._execution.evaluate(deal_id=deal.deal_id, now=now)
            snapshots.append(
                self._snapshot_from_facts(
                    deal,
                    execution,
                    last_activity=last_activity,
                    next_follow_up=next_follow_up,
                    overdue_tasks=overdue_tasks,
                    now=now,
                )
            )
        workloads = self._owner_workloads(snapshots, [])
        overloaded = {
            owner
            for owner, item in workloads.items()
            if item["workload_level"] in {WorkloadLevel.HIGH.value, WorkloadLevel.CRITICAL.value}
        }
        for item in snapshots:
            if item["owner_id"] in overloaded and item["stage"] not in {DealStage.CLOSED_WON.value, DealStage.CLOSED_LOST.value}:
                risk = classify_deal_risk(
                    stale=bool(item["stale"]),
                    follow_up_overdue="FOLLOW_UP_OVERDUE" in item["risk_flags"],
                    task_overdue="TASK_OVERDUE" in item["risk_flags"],
                    sla_status=item["sla_status"],
                    escalation_level=item["escalation_status"],
                    relationship_health=item["relationship_health"],
                    hot_no_action="HOT_LEAD_NO_ACTION" in item["risk_flags"],
                    high_value_neglected="HIGH_VALUE_DEAL_NEGLECTED" in item["risk_flags"],
                    no_recent_contact="NO_RECENT_CONTACT" in item["risk_flags"],
                    owner_overloaded=True,
                )
                item.update(risk)
                category = classify_forecast_category(
                    stage=DealStage(item["stage"]),
                    probability=item["forecast_probability"],
                    risk_level=item["risk_level"],
                    stale=bool(item["stale"]),
                )
                item["forecast_category"] = category["forecast_category"]
                item["forecast_category_reasons"] = category["reason_codes"]
                item["forecast_category_explanation"] = category["explanation"]
        snapshots.sort(key=lambda row: row["deal_id"])
        return snapshots

    def _snapshot_from_facts(
        self,
        deal: CRMDeal,
        execution: dict[str, Any],
        *,
        last_activity: dict[str, float],
        next_follow_up: dict[str, float],
        overdue_tasks: set[str],
        now: float,
    ) -> dict[str, Any]:
        closed = deal.stage in _CLOSED_STAGES
        reasons = list(execution.get("reason_codes") or [])
        stale = bool(execution.get("stale")) and not closed
        follow_up_overdue = "FOLLOW_UP_OVERDUE" in reasons
        task_overdue = "TASK_OVERDUE" in reasons or deal.deal_id in overdue_tasks
        hot_no_action = (
            execution.get("temperature") == "hot"
            and bool(execution.get("active"))
            and execution.get("recommended_action") in _HOT_NO_ACTION
        )
        sla_status = "on_time" if closed else str(execution.get("sla_status") or "on_time")
        escalation = "none" if closed else str(execution.get("escalation_level") or "none")
        no_recent_contact = "NO_RECENT_ACTIVITY" in reasons or stale
        amount = float(deal.amount or 0)
        high_value_neglected = amount > 0 and (stale or follow_up_overdue or sla_status == "breached")
        signal_codes: list[str] = []
        if follow_up_overdue:
            signal_codes.append("FOLLOW_UP_OVERDUE")
        if task_overdue:
            signal_codes.append("TASK_OVERDUE")
        if no_recent_contact:
            signal_codes.append("NO_RECENT_CONTACT")
        if sla_status == "due_soon":
            signal_codes.append("SLA_AT_RISK")
        if sla_status == "breached":
            signal_codes.append("SLA_BREACHED")
        if escalation in {"manager", "critical"}:
            signal_codes.append("ESCALATED")
        if stale:
            signal_codes.append("STALE_OPPORTUNITY")
        if hot_no_action:
            signal_codes.append("HOT_LEAD_NO_ACTION")
        if high_value_neglected:
            signal_codes.append("HIGH_VALUE_DEAL_AT_RISK")
        relationship = score_relationship(
            signal_codes=signal_codes,
            hot=execution.get("temperature") == "hot" and bool(execution.get("active")),
            open_deal=not closed,
        )
        risk = classify_deal_risk(
            stale=stale,
            follow_up_overdue=follow_up_overdue,
            task_overdue=task_overdue,
            sla_status=sla_status,
            escalation_level=escalation,
            relationship_health=relationship["relationship_health"],
            hot_no_action=hot_no_action,
            high_value_neglected=high_value_neglected,
            no_recent_contact=no_recent_contact,
        )
        forecast = forecast_probability(
            stage=deal.stage,
            score=int(execution.get("score") or 0),
            temperature=str(execution.get("temperature") or "cold"),
            relationship_health=relationship["relationship_health"],
            stale=stale,
            sla_status=sla_status,
            escalation_level=escalation,
            follow_up_overdue=follow_up_overdue,
            hot_no_action=hot_no_action,
        )
        category = classify_forecast_category(
            stage=deal.stage,
            probability=forecast["forecast_probability"],
            risk_level=risk["risk_level"],
            stale=stale,
        )
        open_deal = not closed
        weighted = round(amount * forecast["forecast_probability"], 2) if open_deal else 0.0
        nba = execution.get("recommended_action") or "NO_ACTION"
        return {
            "deal_id": deal.deal_id,
            "opportunity_id": deal.opportunity_id or deal.deal_id,
            "customer_id": deal.customer_id,
            "lead_id": execution.get("lead_id") or "",
            "owner_id": _owner_key(deal.owner_agent_id or execution.get("owner_id")),
            "stage": deal.stage.value,
            "deal_value": amount,
            "currency": deal_currency(deal),
            "lead_score": int(execution.get("score") or 0),
            "temperature": execution.get("temperature") or "cold",
            "relationship_health": relationship["relationship_health"],
            "relationship_score": relationship["relationship_score"],
            "stale": stale,
            "next_best_action": nba,
            "sla_status": sla_status,
            "escalation_status": escalation,
            "execution_priority": execution.get("priority") or "low",
            "last_meaningful_activity": last_activity.get(deal.deal_id),
            "next_follow_up": next_follow_up.get(deal.deal_id) or next_follow_up.get(execution.get("lead_id") or ""),
            "forecast_category": category["forecast_category"],
            "forecast_category_reasons": category["reason_codes"],
            "forecast_category_explanation": category["explanation"],
            "forecast_probability": forecast["forecast_probability"],
            "forecast_reasons": forecast["reason_codes"],
            "forecast_explanation": forecast["explanation"],
            "weighted_value": weighted,
            "risk_level": risk["risk_level"],
            "risk_score": risk["risk_score"],
            "risk_flags": risk["risk_flags"],
            "risk_explanation": risk["explanation"],
            "reason_codes": sorted(set(forecast["reason_codes"] + risk["reason_codes"] + category["reason_codes"])),
            "win": deal.win,
            "created_at": float(deal.created_at or 0),
            "closed_at": float(deal.closed_at) if deal.closed_at is not None else None,
            "active": open_deal,
        }

    def _forecast_summary(self, snapshots: list[dict[str, Any]], *, now: float) -> dict[str, Any]:
        open_items = [item for item in snapshots if item["active"]]
        won_items = [item for item in snapshots if item["stage"] == DealStage.CLOSED_WON.value]
        lost_items = [item for item in snapshots if item["stage"] == DealStage.CLOSED_LOST.value]
        open_money: dict[str, float] = {}
        weighted_money: dict[str, float] = {}
        commit_money: dict[str, float] = {}
        likely_money: dict[str, float] = {}
        upside_money: dict[str, float] = {}
        at_risk_money: dict[str, float] = {}
        won_money: dict[str, float] = {}
        lost_money: dict[str, float] = {}
        for item in open_items:
            currency = item["currency"]
            add_money(open_money, currency, item["deal_value"])
            add_money(weighted_money, currency, item["weighted_value"])
            if item["forecast_category"] == ForecastCategory.COMMIT.value:
                add_money(commit_money, currency, item["weighted_value"])
            elif item["forecast_category"] == ForecastCategory.LIKELY.value:
                add_money(likely_money, currency, item["weighted_value"])
            elif item["forecast_category"] == ForecastCategory.UPSIDE.value:
                add_money(upside_money, currency, item["weighted_value"])
            if item["forecast_category"] == ForecastCategory.AT_RISK.value:
                add_money(at_risk_money, currency, item["deal_value"])
        for item in won_items:
            add_money(won_money, item["currency"], item["deal_value"])
        for item in lost_items:
            add_money(lost_money, item["currency"], item["deal_value"])
        return {
            "total_open_pipeline": money_payload(open_money),
            "weighted_pipeline": money_payload(weighted_money),
            "commit_forecast": money_payload(commit_money),
            "likely_forecast": money_payload(likely_money),
            "upside_forecast": money_payload(upside_money),
            "at_risk_value": money_payload(at_risk_money),
            "won_value": money_payload(won_money),
            "lost_value": money_payload(lost_money),
            "deal_count": len(snapshots),
            "open_deal_count": len(open_items),
            "won_deal_count": len(won_items),
            "lost_deal_count": len(lost_items),
            "critical_deal_count": sum(1 for item in open_items if item["risk_level"] == "critical"),
            "sla_breach_count": sum(1 for item in open_items if item["sla_status"] == "breached"),
            "escalation_count": sum(1 for item in open_items if item["escalation_status"] in {"manager", "critical"}),
            "by_stage": self._count_breakdown(snapshots, "stage"),
            "by_owner": self._owner_totals(snapshots),
            "by_temperature": self._count_breakdown(open_items, "temperature"),
            "by_relationship_health": self._count_breakdown(open_items, "relationship_health"),
            "by_forecast_category": self._count_breakdown(open_items, "forecast_category"),
            "by_risk_level": self._count_breakdown(open_items, "risk_level"),
            "period": self._period_metrics(snapshots, now=now),
        }

    def _revenue_intelligence(self, snapshots: list[dict[str, Any]], *, now: float) -> dict[str, Any]:
        summary = self._forecast_summary(snapshots, now=now)
        return {
            "current_open_pipeline": summary["total_open_pipeline"],
            "weighted_expected_pipeline": summary["weighted_pipeline"],
            "closed_won_revenue": summary["won_value"],
            "closed_lost_value": summary["lost_value"],
            "revenue_by_owner": summary["by_owner"],
            "revenue_by_stage": self._value_breakdown(snapshots, "stage"),
            "revenue_by_forecast_category": self._value_breakdown(
                [item for item in snapshots if item["active"]], "forecast_category"
            ),
            "at_risk_pipeline_value": summary["at_risk_value"],
            "period": summary["period"],
        }

    def _period_metrics(self, snapshots: list[dict[str, Any]], *, now: float) -> dict[str, Any]:
        start = now - REPORTING_WINDOW_SECONDS
        won = [item for item in snapshots if item["stage"] == "closed_won" and item["closed_at"] and item["closed_at"] >= start]
        lost = [item for item in snapshots if item["stage"] == "closed_lost" and item["closed_at"] and item["closed_at"] >= start]
        created = [item for item in snapshots if item["created_at"] >= start]
        won_money: dict[str, float] = {}
        lost_money: dict[str, float] = {}
        created_money: dict[str, float] = {}
        for item in won:
            add_money(won_money, item["currency"], item["deal_value"])
        for item in lost:
            add_money(lost_money, item["currency"], item["deal_value"])
        for item in created:
            if item["active"]:
                add_money(created_money, item["currency"], item["deal_value"])
        return {
            "window_seconds": REPORTING_WINDOW_SECONDS,
            "won_this_period": money_payload(won_money),
            "lost_this_period": money_payload(lost_money),
            "new_pipeline_this_period": money_payload(created_money),
            "won_count": len(won),
            "lost_count": len(lost),
            "new_count": len(created),
        }

    def _team_performance(self, snapshots: list[dict[str, Any]], queue_items: list[dict[str, Any]]) -> dict[str, Any]:
        owners = sorted({item["owner_id"] for item in snapshots} | {_owner_key(item.get("owner_id")) for item in queue_items})
        workloads = self._owner_workloads(snapshots, queue_items)
        rows = []
        for owner in owners:
            owned = [item for item in snapshots if item["owner_id"] == owner]
            open_items = [item for item in owned if item["active"]]
            queue_owned = [item for item in queue_items if _owner_key(item.get("owner_id")) == owner]
            open_money: dict[str, float] = {}
            weighted_money: dict[str, float] = {}
            won_money: dict[str, float] = {}
            lost_money: dict[str, float] = {}
            for item in open_items:
                add_money(open_money, item["currency"], item["deal_value"])
                add_money(weighted_money, item["currency"], item["weighted_value"])
            for item in owned:
                if item["stage"] == "closed_won":
                    add_money(won_money, item["currency"], item["deal_value"])
                elif item["stage"] == "closed_lost":
                    add_money(lost_money, item["currency"], item["deal_value"])
            health_scores = [int(item["relationship_score"]) for item in open_items]
            avg_health = round(sum(health_scores) / len(health_scores), 2) if health_scores else None
            stale = sum(1 for item in open_items if item["stale"])
            high_risk = sum(1 for item in open_items if item["risk_level"] in {"high", "critical"})
            open_count = len(open_items)
            pipeline_health, pipeline_reason = self._pipeline_health(open_count, high_risk, stale)
            overdue_follow = sum(1 for item in open_items if "FOLLOW_UP_OVERDUE" in item["risk_flags"])
            follow_up_discipline = "on_track" if open_count and overdue_follow / open_count < 0.25 else ("watch" if open_count else "n_a")
            if overdue_follow and open_count and overdue_follow / open_count >= 0.5:
                follow_up_discipline = "weak"
            risk_concentration = round(high_risk / open_count, 4) if open_count else 0.0
            rows.append(
                {
                    "owner_id": owner,
                    "open_pipeline": money_payload(open_money),
                    "weighted_pipeline": money_payload(weighted_money),
                    "won_value": money_payload(won_money),
                    "lost_value": money_payload(lost_money),
                    "open_deals": open_count,
                    "won_deals": sum(1 for item in owned if item["stage"] == "closed_won"),
                    "lost_deals": sum(1 for item in owned if item["stage"] == "closed_lost"),
                    "high_risk_deals": high_risk,
                    "stale_deals": stale,
                    "hot_leads": sum(1 for item in open_items if item["temperature"] == "hot"),
                    "overdue_follow_ups": overdue_follow,
                    "overdue_tasks": sum(1 for item in open_items if "TASK_OVERDUE" in item["risk_flags"]),
                    "sla_warnings": sum(1 for item in open_items if item["sla_status"] in {"due_soon", "overdue"}),
                    "sla_breaches": sum(1 for item in open_items if item["sla_status"] == "breached"),
                    "escalations": sum(1 for item in open_items if item["escalation_status"] in {"manager", "critical"}),
                    "average_relationship_health": avg_health,
                    "recent_activity": sum(1 for item in open_items if item.get("last_meaningful_activity")),
                    "priority_workload": workloads[owner]["workload_score"] if owner in workloads else 0,
                    "workload": workloads.get(owner) or classify_workload(
                        open_deals=0,
                        high_priority_items=0,
                        overdue_follow_ups=0,
                        overdue_tasks=0,
                        sla_at_risk=0,
                        sla_breaches=0,
                        escalations=0,
                        high_risk_deals=0,
                    ),
                    "pipeline_health": pipeline_health,
                    "pipeline_health_reason": pipeline_reason,
                    "attention_load": (workloads.get(owner) or {}).get("workload_level", "normal"),
                    "follow_up_discipline": follow_up_discipline,
                    "risk_concentration": risk_concentration,
                    "queue_items": len(queue_owned),
                }
            )
        rows.sort(key=lambda row: (row["owner_id"]))
        return {"owners": rows, "owner_count": len(rows), "targets": None}

    def _owner_workloads(self, snapshots: list[dict[str, Any]], queue_items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        owners = sorted({item["owner_id"] for item in snapshots} | {_owner_key(item.get("owner_id")) for item in queue_items})
        result: dict[str, dict[str, Any]] = {}
        for owner in owners:
            owned = [item for item in snapshots if item["owner_id"] == owner and item["active"]]
            queue_owned = [item for item in queue_items if _owner_key(item.get("owner_id")) == owner and item.get("active")]
            result[owner] = classify_workload(
                open_deals=len(owned),
                high_priority_items=sum(1 for item in queue_owned if item.get("priority") in {"high", "critical"}),
                overdue_follow_ups=sum(1 for item in owned if "FOLLOW_UP_OVERDUE" in item["risk_flags"]),
                overdue_tasks=sum(1 for item in owned if "TASK_OVERDUE" in item["risk_flags"]),
                sla_at_risk=sum(1 for item in owned if item["sla_status"] in {"due_soon", "overdue"}),
                sla_breaches=sum(1 for item in owned if item["sla_status"] == "breached"),
                escalations=sum(1 for item in owned if item["escalation_status"] in {"manager", "critical"}),
                high_risk_deals=sum(1 for item in owned if item["risk_level"] in {"high", "critical"}),
            )
        return result

    @staticmethod
    def _pipeline_health(open_count: int, high_risk: int, stale: int) -> tuple[str, str]:
        if open_count == 0:
            return "empty", "No open deals"
        if high_risk / open_count >= 0.4:
            return "weak", "High-risk concentration"
        if stale / open_count >= 0.3:
            return "strained", "Stale opportunity concentration"
        return "healthy", "Risk and staleness within observed bounds"

    def _top_opportunities(self, snapshots: list[dict[str, Any]], *, limit: int) -> list[dict[str, Any]]:
        open_items = [item for item in snapshots if item["active"]]
        ranked = sorted(
            open_items,
            key=lambda item: (-item["weighted_value"], -item["forecast_probability"], -item["deal_value"], item["deal_id"]),
        )
        cap = max(0, int(limit))
        results = []
        for item in ranked[:cap]:
            reasons = ["WEIGHTED_VALUE"]
            if item["temperature"] == "hot":
                reasons.append("HOT_LEAD")
            if item["forecast_probability"] >= 0.5:
                reasons.append("HIGH_PROBABILITY")
            if item["relationship_health"] in {"strong", "healthy"}:
                reasons.append("HEALTHY_RELATIONSHIP")
            results.append({**item, "rank_reason_codes": reasons})
        return results

    def _top_risks(self, snapshots: list[dict[str, Any]], *, limit: int) -> list[dict[str, Any]]:
        open_items = [item for item in snapshots if item["active"] and item["risk_level"] != "low"]
        ranked = sorted(
            open_items,
            key=lambda item: (-_RISK_RANK.get(item["risk_level"], 0), -item["deal_value"], item["deal_id"]),
        )
        return ranked[: max(0, int(limit))]

    def _action_center(
        self,
        snapshots: list[dict[str, Any]],
        queue_items: list[dict[str, Any]],
        *,
        limit: int,
    ) -> dict[str, Any]:
        by_deal = {item["deal_id"]: item for item in snapshots}
        actions: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in queue_items:
            key = item.get("execution_id") or f"{item.get('entity_type')}:{item.get('entity_id')}"
            if key in seen:
                continue
            seen.add(key)
            snap = by_deal.get(item.get("deal_id") or "")
            actions.append(
                {
                    "item": item.get("execution_id"),
                    "customer_id": item.get("customer_id") or "",
                    "deal_id": item.get("deal_id") or "",
                    "lead_id": item.get("lead_id") or "",
                    "owner_id": _owner_key(item.get("owner_id")),
                    "priority": item.get("priority") or "low",
                    "reason": item.get("recommended_action_reason") or "",
                    "reason_codes": list(item.get("reason_codes") or []),
                    "due_state": item.get("sla_status") or "on_time",
                    "sla_state": item.get("sla_status") or "on_time",
                    "risk_state": snap["risk_level"] if snap else "low",
                    "recommended_action": item.get("recommended_action") or "NO_ACTION",
                    "source_engine": "sales_execution",
                }
            )
        for snap in snapshots:
            if snap["risk_level"] not in {"high", "critical"}:
                continue
            key = f"deal-risk:{snap['deal_id']}"
            if snap["deal_id"] and any(item.get("deal_id") == snap["deal_id"] for item in actions):
                continue
            if key in seen:
                continue
            seen.add(key)
            actions.append(
                {
                    "item": key,
                    "customer_id": snap["customer_id"],
                    "deal_id": snap["deal_id"],
                    "lead_id": snap["lead_id"],
                    "owner_id": snap["owner_id"],
                    "priority": snap["execution_priority"],
                    "reason": snap["risk_explanation"],
                    "reason_codes": snap["risk_flags"],
                    "due_state": snap["sla_status"],
                    "sla_state": snap["sla_status"],
                    "risk_state": snap["risk_level"],
                    "recommended_action": snap["next_best_action"],
                    "source_engine": "deal_risk",
                }
            )
        actions.sort(
            key=lambda item: (
                -_PRIORITY_RANK.get(str(item["priority"]), 0),
                -_RISK_RANK.get(str(item["risk_state"]), 0),
                item["deal_id"] or item["lead_id"] or item["item"],
            )
        )
        cap = max(0, int(limit))
        return {"items": actions[:cap], "total": len(actions)}

    async def _pipeline_changes(self, *, now: float) -> dict[str, Any]:
        activities = await self._activities.list_activities()
        changes = []
        for item in activities:
            mapped = self._map_change(item)
            if mapped is not None:
                changes.append(mapped)
        changes.sort(key=lambda row: (-row["occurred_at"], row["change_type"], row["event_id"]))
        return {
            "capability": "limited_by_existing_history",
            "supported_events": [
                "deal_created",
                "stage_changed",
                "deal_won",
                "deal_lost",
                "follow_up_scheduled",
                "follow_up_completed",
            ],
            "unsupported_events": [
                "forecast_category_changed",
                "historical_risk_delta",
                "historical_sla_snapshots",
            ],
            "explanation": "Changes are current activity facts only. Forecast category and SLA history are not persisted.",
            "items": changes[:100],
            "generated_at": now,
        }

    @staticmethod
    def _map_change(item: Interaction) -> dict[str, Any] | None:
        event_type = item.interaction_type
        change_type = ""
        if event_type == InteractionType.DEAL_CREATED:
            change_type = "deal_created"
        elif event_type == InteractionType.LEAD_CONVERTED:
            change_type = "deal_created"
        elif event_type == InteractionType.STAGE_CHANGE:
            if item.body == DealStage.CLOSED_WON.value:
                change_type = "deal_won"
            elif item.body == DealStage.CLOSED_LOST.value:
                change_type = "deal_lost"
            else:
                change_type = "stage_changed"
        elif event_type == InteractionType.FOLLOW_UP_SCHEDULED:
            change_type = "follow_up_scheduled"
        elif event_type == InteractionType.FOLLOW_UP_COMPLETED:
            change_type = "follow_up_completed"
        else:
            return None
        return {
            "event_id": item.interaction_id,
            "change_type": change_type,
            "deal_id": item.deal_id,
            "customer_id": item.customer_id,
            "occurred_at": float(item.created_at or 0),
            "detail": item.body or item.subject,
            "source": "activity",
        }

    @staticmethod
    def _last_activity_index(activities: list[Interaction]) -> dict[str, float]:
        index: dict[str, float] = {}
        for item in activities:
            if item.interaction_type not in _MEANINGFUL_COMM:
                continue
            stamp = float(item.created_at or 0)
            if item.deal_id:
                index[item.deal_id] = max(index.get(item.deal_id, 0.0), stamp)
        return index

    @staticmethod
    def _next_follow_up_index(follow_ups: list[dict[str, Any]]) -> dict[str, float]:
        index: dict[str, float] = {}
        for item in follow_ups:
            if item.get("status") in {"completed", "cancelled", "dismissed"}:
                continue
            due = float(item.get("due_at") or 0)
            for key in (item.get("deal_id"), item.get("lead_id")):
                if key:
                    current = index.get(key)
                    index[key] = due if current is None else min(current, due)
        return index

    @staticmethod
    def _overdue_task_index(tasks: list[Any], *, now: float) -> set[str]:
        overdue: set[str] = set()
        for task in tasks:
            if task.status not in _OPEN_TASKS or task.due_at is None or task.due_at >= now:
                continue
            if task.deal_id:
                overdue.add(task.deal_id)
        return overdue

    @staticmethod
    def _count_breakdown(items: list[dict[str, Any]], field: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for item in items:
            key = str(item.get(field) or "")
            counts[key] = counts.get(key, 0) + 1
        return {key: counts[key] for key in sorted(counts)}

    @staticmethod
    def _value_breakdown(items: list[dict[str, Any]], field: str) -> dict[str, Any]:
        buckets: dict[str, dict[str, float]] = {}
        for item in items:
            key = str(item.get(field) or "")
            buckets.setdefault(key, {})
            add_money(buckets[key], item["currency"], item["deal_value"] if field == "stage" else item.get("weighted_value") or item["deal_value"])
        return {key: money_payload(buckets[key]) for key in sorted(buckets)}

    @staticmethod
    def _owner_totals(snapshots: list[dict[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        owners = sorted({item["owner_id"] for item in snapshots})
        for owner in owners:
            owned = [item for item in snapshots if item["owner_id"] == owner]
            open_items = [item for item in owned if item["active"]]
            open_money: dict[str, float] = {}
            weighted: dict[str, float] = {}
            for item in open_items:
                add_money(open_money, item["currency"], item["deal_value"])
                add_money(weighted, item["currency"], item["weighted_value"])
            result[owner] = {
                "open_deals": len(open_items),
                "open_pipeline": money_payload(open_money),
                "weighted_pipeline": money_payload(weighted),
            }
        return result


crm_manager_intelligence = ManagerIntelligenceService()
