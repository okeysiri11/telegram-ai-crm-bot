# CRM sales execution — priority, SLA, escalation, manager queue.

from __future__ import annotations

import time
from enum import Enum
from typing import Any

from applications.auto_marketplace.crm.automation import DUE_WINDOW_SECONDS, CRMAutomationEngine, crm_automation
from applications.auto_marketplace.crm.intelligence import (
    HOT_THRESHOLD,
    INACTIVE_SECONDS,
    STALE_SECONDS,
    CRMIntelligenceService,
    crm_intelligence,
)
from applications.auto_marketplace.crm.models import CRMDeal, CRMLead, TaskStatus
from applications.auto_marketplace.crm.tenant import current_crm_tenant
from applications.auto_marketplace.deals.service import DealService, deal_service
from applications.auto_marketplace.leads.service import LeadService, lead_service
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.tasks.service import TaskService, task_service

SLA_BREACH_SECONDS = 7 * 86400
_OPEN_TASKS = frozenset({TaskStatus.PENDING, TaskStatus.IN_PROGRESS})
_DEAL_ACTIONS = frozenset({"ADVANCE_PIPELINE", "REVIEW_DEAL", "COMPLETE_OVERDUE_TASK", "CREATE_FOLLOW_UP"})
_PRIORITY_WEIGHTS = {
    "FOLLOW_UP_OVERDUE": 30,
    "TASK_OVERDUE": 25,
    "HOT_LEAD": 25,
    "HIGH_SCORE": 15,
    "STALE_OPPORTUNITY": 20,
    "NO_RECENT_ACTIVITY": 10,
    "DEAL_REQUIRES_ACTION": 15,
    "SLA_BREACHED": 35,
}
_PRIORITY_RANK = {"critical": 3, "high": 2, "medium": 1, "low": 0}
_SLA_RANK = {"breached": 0, "overdue": 1, "due_soon": 2, "on_time": 3}
_ESCALATION_RANK = {"critical": 0, "manager": 1, "attention": 2, "none": 3}


class ExecutionPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SLAStatus(str, Enum):
    ON_TIME = "on_time"
    DUE_SOON = "due_soon"
    OVERDUE = "overdue"
    BREACHED = "breached"


class EscalationLevel(str, Enum):
    NONE = "none"
    ATTENTION = "attention"
    MANAGER = "manager"
    CRITICAL = "critical"


def classify_sla(*, now: float, due_at: float | None, stale: bool, last_activity_age: float | None) -> SLAStatus:
    """Deterministic SLA. Reuses Sprint 8 due window (1h) and 7-day urgent overdue."""
    if due_at is not None:
        if due_at < now - SLA_BREACH_SECONDS:
            return SLAStatus.BREACHED
        if due_at < now:
            return SLAStatus.OVERDUE
        if due_at <= now + DUE_WINDOW_SECONDS:
            return SLAStatus.DUE_SOON
        return SLAStatus.ON_TIME
    if stale and last_activity_age is not None and last_activity_age >= STALE_SECONDS:
        return SLAStatus.BREACHED
    if last_activity_age is not None and last_activity_age >= INACTIVE_SECONDS:
        return SLAStatus.OVERDUE
    if stale:
        return SLAStatus.OVERDUE
    return SLAStatus.ON_TIME


def classify_priority(priority_score: int, *, sla: SLAStatus, reasons: list[str]) -> ExecutionPriority:
    label = ExecutionPriority.LOW
    if priority_score >= 70:
        label = ExecutionPriority.CRITICAL
    elif priority_score >= 40:
        label = ExecutionPriority.HIGH
    elif priority_score >= 20:
        label = ExecutionPriority.MEDIUM
    codes = set(reasons)
    if sla == SLAStatus.BREACHED and ({"HOT_LEAD", "STALE_OPPORTUNITY"} & codes):
        return ExecutionPriority.CRITICAL
    if sla == SLAStatus.BREACHED:
        return _max_priority(label, ExecutionPriority.HIGH)
    if "FOLLOW_UP_OVERDUE" in codes and "HOT_LEAD" in codes:
        return _max_priority(label, ExecutionPriority.HIGH)
    return label


def classify_escalation(
    *,
    sla: SLAStatus,
    reasons: list[str],
    overdue: bool,
    stale: bool,
    deal_amount: float,
) -> tuple[EscalationLevel, list[str]]:
    codes = set(reasons)
    escalation_reasons: list[str] = []
    level = EscalationLevel.NONE
    if sla == SLAStatus.BREACHED and ("HOT_LEAD" in codes or (stale and deal_amount > 0)):
        level = EscalationLevel.CRITICAL
        escalation_reasons.append("SLA_BREACHED")
        if "HOT_LEAD" in codes:
            escalation_reasons.append("HOT_LEAD")
        if stale and deal_amount > 0:
            escalation_reasons.append("STALE_OPPORTUNITY")
    elif sla == SLAStatus.BREACHED:
        level = EscalationLevel.MANAGER
        escalation_reasons.append("SLA_BREACHED")
    elif "FOLLOW_UP_OVERDUE" in codes and "HOT_LEAD" in codes:
        level = EscalationLevel.MANAGER
        escalation_reasons.extend(["FOLLOW_UP_OVERDUE", "HOT_LEAD"])
    elif "TASK_OVERDUE" in codes and "HOT_LEAD" in codes:
        level = EscalationLevel.MANAGER
        escalation_reasons.extend(["TASK_OVERDUE", "HOT_LEAD"])
    elif stale and deal_amount > 0:
        level = EscalationLevel.MANAGER
        escalation_reasons.append("STALE_OPPORTUNITY")
    elif overdue or sla == SLAStatus.DUE_SOON or stale:
        level = EscalationLevel.ATTENTION
        for code in ("FOLLOW_UP_OVERDUE", "TASK_OVERDUE", "STALE_OPPORTUNITY", "NO_RECENT_ACTIVITY", "DEAL_REQUIRES_ACTION"):
            if code in codes:
                escalation_reasons.append(code)
        if not escalation_reasons:
            escalation_reasons.append("DEAL_REQUIRES_ACTION")
    return level, sorted(set(escalation_reasons))


def _max_priority(left: ExecutionPriority, right: ExecutionPriority) -> ExecutionPriority:
    return left if _PRIORITY_RANK[left.value] >= _PRIORITY_RANK[right.value] else right


class CRMExecutionEngine:
    """Read-only derived sales execution. Consumes Sprint 8 automation and Sprint 9 intelligence."""

    def __init__(
        self,
        *,
        intelligence: CRMIntelligenceService | None = None,
        automation: CRMAutomationEngine | None = None,
        leads: LeadService | None = None,
        deals: DealService | None = None,
        tasks: TaskService | None = None,
    ) -> None:
        self._intelligence = intelligence or crm_intelligence
        self._automation = automation or crm_automation
        self._leads = leads or lead_service
        self._deals = deals or deal_service
        self._tasks = tasks or task_service

    async def evaluate(self, *, lead_id: str = "", deal_id: str = "", now: float | None = None) -> dict[str, Any]:
        if not lead_id and not deal_id:
            raise ValidationError("lead_id or deal_id is required")
        clock = now if now is not None else time.time()
        report = await self._intelligence.calculate_score(lead_id=lead_id, deal_id=deal_id, now=clock)
        lead, deal = await self._load_owners(report)
        due_at, last_age = await self._due_context(report, now=clock)
        reasons = self._reason_codes(report, sla=SLAStatus.ON_TIME)
        sla = classify_sla(
            now=clock,
            due_at=due_at,
            stale=bool(report["stale"]),
            last_activity_age=last_age,
        )
        if sla == SLAStatus.BREACHED:
            reasons = self._reason_codes(report, sla=sla)
        reasons = sorted(set(reasons))
        priority_score = sum(_PRIORITY_WEIGHTS[code] for code in reasons if code in _PRIORITY_WEIGHTS)
        priority = classify_priority(priority_score, sla=sla, reasons=reasons)
        overdue = sla in {SLAStatus.OVERDUE, SLAStatus.BREACHED}
        amount = float(deal.amount) if deal is not None else 0.0
        escalation, escalation_reasons = classify_escalation(
            sla=sla,
            reasons=reasons,
            overdue=overdue,
            stale=bool(report["stale"]),
            deal_amount=amount,
        )
        if not report["active"]:
            priority = ExecutionPriority.LOW
            sla = SLAStatus.ON_TIME
            overdue = False
            escalation = EscalationLevel.NONE
            escalation_reasons = []
            reasons = []
            priority_score = 0
        owner_id = ""
        created_at = 0.0
        if lead is not None:
            owner_id = lead.assigned_agent_id
            created_at = float(lead.created_at or 0)
        if deal is not None:
            owner_id = owner_id or deal.owner_agent_id
            created_at = created_at or float(deal.created_at or 0)
        nba = report["next_best_action"]
        return {
            "execution_id": f"exec:{report['entity_type']}:{report['entity_id']}",
            "tenant_id": current_crm_tenant(),
            "entity_type": report["entity_type"],
            "entity_id": report["entity_id"],
            "lead_id": report.get("lead_id") or "",
            "deal_id": report.get("deal_id") or "",
            "customer_id": report.get("customer_id") or "",
            "owner_id": owner_id,
            "priority": priority.value,
            "priority_score": priority_score,
            "temperature": report["temperature"],
            "score": report["score"],
            "recommended_action": nba["action"],
            "recommended_action_reason": nba.get("reason") or "",
            "reason_codes": reasons,
            "due_at": due_at,
            "overdue": overdue,
            "sla_status": sla.value,
            "escalation_level": escalation.value,
            "escalation_reasons": escalation_reasons,
            "stale": bool(report["stale"]) and report["active"],
            "active": report["active"],
            "created_at": created_at,
            "derived_at": clock,
        }

    async def queue(
        self,
        *,
        now: float | None = None,
        limit: int = 100,
        owner: str | None = None,
        priority: str | None = None,
        temperature: str | None = None,
        overdue: bool | None = None,
        sla_status: str | None = None,
        escalation_level: str | None = None,
        entity_type: str | None = None,
    ) -> dict[str, Any]:
        clock = now if now is not None else time.time()
        items = await self._all_items(now=clock)
        active = [item for item in items if item["active"]]
        filtered = [item for item in active if self._matches(item, owner, priority, temperature, overdue, sla_status, escalation_level, entity_type)]
        filtered.sort(key=self._queue_sort_key)
        cap = max(0, int(limit))
        return {
            "items": filtered[:cap],
            "summary": self._summarize(active),
            "generated_at": clock,
        }

    async def summary(self, *, now: float | None = None) -> dict[str, Any]:
        clock = now if now is not None else time.time()
        items = [item for item in await self._all_items(now=clock) if item["active"]]
        counts = self._summarize(items)
        counts["generated_at"] = clock
        counts["tenant_id"] = current_crm_tenant()
        return counts

    async def lead_execution(self, lead_id: str, *, now: float | None = None) -> dict[str, Any]:
        return await self.evaluate(lead_id=lead_id, now=now)

    async def deal_execution(self, deal_id: str, *, now: float | None = None) -> dict[str, Any]:
        return await self.evaluate(deal_id=deal_id, now=now)

    async def _all_items(self, *, now: float) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        seen_deals: set[str] = set()
        for lead in await self._leads.list_leads():
            item = await self.evaluate(lead_id=lead.lead_id, now=now)
            items.append(item)
            if item.get("deal_id"):
                seen_deals.add(item["deal_id"])
        for deal in await self._deals.list_deals():
            if deal.deal_id not in seen_deals:
                items.append(await self.evaluate(deal_id=deal.deal_id, now=now))
        return items

    async def _load_owners(self, report: dict[str, Any]) -> tuple[CRMLead | None, CRMDeal | None]:
        lead = None
        deal = None
        if report.get("lead_id"):
            try:
                lead = await self._leads.get(report["lead_id"])
            except NotFoundError:
                lead = None
        if report.get("deal_id"):
            try:
                deal = await self._deals.get(report["deal_id"])
            except NotFoundError:
                deal = None
        return lead, deal

    async def _due_context(self, report: dict[str, Any], *, now: float) -> tuple[float | None, float | None]:
        nxt = None
        if report.get("lead_id"):
            nxt = await self._automation.next_action(lead_id=report["lead_id"], now=now)
        if nxt is None and report.get("deal_id"):
            nxt = await self._automation.next_action(deal_id=report["deal_id"], now=now)
        due_at = float(nxt["next_action_at"]) if nxt and nxt.get("next_action_at") is not None else None
        task_due = await self._earliest_open_task_due(report, now=now)
        if task_due is not None and (due_at is None or task_due < due_at):
            due_at = task_due
        last_age = None
        inactivity = next((item for item in report.get("factors") or [] if item.get("code") == "inactivity"), None)
        if inactivity:
            last_age = STALE_SECONDS if int(inactivity.get("impact") or 0) <= -20 else INACTIVE_SECONDS
        elif report.get("stale"):
            last_age = STALE_SECONDS
        return due_at, last_age

    async def _earliest_open_task_due(self, report: dict[str, Any], *, now: float) -> float | None:
        tasks = []
        if report.get("lead_id"):
            tasks.extend(await self._tasks.list_tasks(lead_id=report["lead_id"]))
        if report.get("deal_id"):
            tasks.extend(await self._tasks.list_tasks(deal_id=report["deal_id"]))
        seen: set[str] = set()
        dues: list[float] = []
        for task in tasks:
            if task.task_id in seen:
                continue
            seen.add(task.task_id)
            if task.status in _OPEN_TASKS and task.due_at is not None:
                dues.append(float(task.due_at))
        return min(dues) if dues else None

    @staticmethod
    def _reason_codes(report: dict[str, Any], *, sla: SLAStatus) -> list[str]:
        factor_codes = {str(item.get("code") or "") for item in report.get("factors") or []}
        stale_reasons = set(report.get("stale_reasons") or [])
        nba = str((report.get("next_best_action") or {}).get("action") or "")
        reasons: list[str] = []
        if "overdue_follow_up" in factor_codes:
            reasons.append("FOLLOW_UP_OVERDUE")
        if "overdue_task" in factor_codes:
            reasons.append("TASK_OVERDUE")
        if report.get("temperature") == "hot" and report.get("active"):
            reasons.append("HOT_LEAD")
        if int(report.get("score") or 0) >= HOT_THRESHOLD and report.get("active"):
            reasons.append("HIGH_SCORE")
        if report.get("stale") and report.get("deal_id"):
            reasons.append("STALE_OPPORTUNITY")
        if "inactivity" in factor_codes or "no_recent_activity" in stale_reasons:
            reasons.append("NO_RECENT_ACTIVITY")
        if nba in _DEAL_ACTIONS:
            reasons.append("DEAL_REQUIRES_ACTION")
        if sla == SLAStatus.BREACHED:
            reasons.append("SLA_BREACHED")
        return reasons

    @staticmethod
    def _matches(
        item: dict[str, Any],
        owner: str | None,
        priority: str | None,
        temperature: str | None,
        overdue: bool | None,
        sla_status: str | None,
        escalation_level: str | None,
        entity_type: str | None,
    ) -> bool:
        if owner and item.get("owner_id") != owner:
            return False
        if priority and item.get("priority") != priority:
            return False
        if temperature and item.get("temperature") != temperature:
            return False
        if overdue is not None and bool(item.get("overdue")) != overdue:
            return False
        if sla_status and item.get("sla_status") != sla_status:
            return False
        if escalation_level and item.get("escalation_level") != escalation_level:
            return False
        if entity_type and item.get("entity_type") != entity_type:
            return False
        return True

    @staticmethod
    def _queue_sort_key(item: dict[str, Any]) -> tuple:
        due = item.get("due_at")
        due_sort = float(due) if due is not None else float("inf")
        return (
            _ESCALATION_RANK.get(str(item.get("escalation_level") or "none"), 9),
            _SLA_RANK.get(str(item.get("sla_status") or "on_time"), 9),
            -int(item.get("priority_score") or 0),
            due_sort,
            str(item.get("entity_id") or ""),
        )

    @staticmethod
    def _summarize(items: list[dict[str, Any]]) -> dict[str, int]:
        return {
            "critical": sum(1 for item in items if item["priority"] == "critical"),
            "high": sum(1 for item in items if item["priority"] == "high"),
            "overdue": sum(1 for item in items if item["overdue"]),
            "sla_breaches": sum(1 for item in items if item["sla_status"] == "breached"),
            "manager_escalations": sum(1 for item in items if item["escalation_level"] in {"manager", "critical"}),
            "hot_leads_requiring_action": sum(
                1
                for item in items
                if item["temperature"] == "hot" and item["recommended_action"] != "NO_ACTION"
            ),
            "stale_opportunities": sum(1 for item in items if item["stale"] and item.get("deal_id")),
        }


crm_execution = CRMExecutionEngine()
