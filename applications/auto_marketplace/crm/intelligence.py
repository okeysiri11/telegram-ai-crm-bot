# CRM sales intelligence — deterministic scoring, temperature, NBA, stale detection.

from __future__ import annotations

import time
from enum import Enum
from typing import Any

from applications.auto_marketplace.activities.service import ActivityService, activity_service
from applications.auto_marketplace.calendar.service import CalendarService, calendar_service
from applications.auto_marketplace.communications.service import CommunicationService, communication_service
from applications.auto_marketplace.crm.automation import CRMAutomationEngine, crm_automation
from applications.auto_marketplace.crm.models import (
    CRMDeal,
    CRMLead,
    CRMLeadStatus,
    CustomerProfile,
    DealStage,
    TaskPriority,
    TaskStatus,
)
from applications.auto_marketplace.customers.profile_service import CustomerProfileService, customer_profile_service
from applications.auto_marketplace.deals.service import DealService, deal_service
from applications.auto_marketplace.leads.service import LeadService, lead_service
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.tasks.service import TaskService, task_service

HOT_THRESHOLD = 75
WARM_THRESHOLD = 45
BASE_SCORE = 40
RECENT_SECONDS = 3 * 86400
INACTIVE_SECONDS = 7 * 86400
STALE_SECONDS = 14 * 86400
_CLOSED_STAGES = frozenset({DealStage.CLOSED_WON, DealStage.CLOSED_LOST})
_OPEN_TASKS = frozenset({TaskStatus.PENDING, TaskStatus.IN_PROGRESS})
_STAGE_BONUS = {
    DealStage.QUALIFICATION: 6,
    DealStage.PROPOSAL: 10,
    DealStage.NEGOTIATION: 16,
    DealStage.APPROVAL: 20,
}


class SalesTemperature(str, Enum):
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"


class NextBestAction(str, Enum):
    CALL_CUSTOMER = "CALL_CUSTOMER"
    SEND_EMAIL = "SEND_EMAIL"
    SCHEDULE_MEETING = "SCHEDULE_MEETING"
    CREATE_FOLLOW_UP = "CREATE_FOLLOW_UP"
    COMPLETE_OVERDUE_TASK = "COMPLETE_OVERDUE_TASK"
    REVIEW_DEAL = "REVIEW_DEAL"
    ADVANCE_PIPELINE = "ADVANCE_PIPELINE"
    NO_ACTION = "NO_ACTION"


def classify_temperature(score: float, *, active: bool) -> SalesTemperature:
    if not active:
        return SalesTemperature.COLD
    if score >= HOT_THRESHOLD:
        return SalesTemperature.HOT
    if score >= WARM_THRESHOLD:
        return SalesTemperature.WARM
    return SalesTemperature.COLD


def _clamp(score: float) -> int:
    return max(0, min(100, int(round(score))))


def _factor(code: str, impact: int, reason: str) -> dict[str, Any]:
    return {"code": code, "impact": impact, "reason": reason}


class CRMIntelligenceService:
    """Read-only derived CRM scoring. PostgreSQL facts only. No lifecycle mutations."""

    def __init__(
        self,
        *,
        leads: LeadService | None = None,
        deals: DealService | None = None,
        tasks: TaskService | None = None,
        calendar: CalendarService | None = None,
        activities: ActivityService | None = None,
        communications: CommunicationService | None = None,
        automation: CRMAutomationEngine | None = None,
        customers: CustomerProfileService | None = None,
    ) -> None:
        self._leads = leads or lead_service
        self._deals = deals or deal_service
        self._tasks = tasks or task_service
        self._calendar = calendar or calendar_service
        self._activities = activities or activity_service
        self._communications = communications or communication_service
        self._automation = automation or crm_automation
        self._customers = customers or customer_profile_service

    @staticmethod
    def classify_temperature(score: float, *, active: bool = True) -> SalesTemperature:
        return classify_temperature(score, active=active)

    async def calculate_score(self, *, lead_id: str = "", deal_id: str = "", now: float | None = None) -> dict[str, Any]:
        return await self.explain_score(lead_id=lead_id, deal_id=deal_id, now=now)

    async def explain_score(self, *, lead_id: str = "", deal_id: str = "", now: float | None = None) -> dict[str, Any]:
        return await self._evaluate(lead_id=lead_id, deal_id=deal_id, now=now)

    async def next_best_action(self, *, lead_id: str = "", deal_id: str = "", now: float | None = None) -> dict[str, Any]:
        report = await self._evaluate(lead_id=lead_id, deal_id=deal_id, now=now)
        return report["next_best_action"]

    async def detect_stale(self, *, lead_id: str = "", deal_id: str = "", now: float | None = None) -> dict[str, Any]:
        report = await self._evaluate(lead_id=lead_id, deal_id=deal_id, now=now)
        return {
            "stale": report["stale"],
            "reasons": report["stale_reasons"],
            "active": report["active"],
            "entity_type": report["entity_type"],
            "entity_id": report["entity_id"],
        }

    async def lead_intelligence(self, lead_id: str, *, now: float | None = None) -> dict[str, Any]:
        return await self._evaluate(lead_id=lead_id, now=now)

    async def deal_intelligence(self, deal_id: str, *, now: float | None = None) -> dict[str, Any]:
        return await self._evaluate(deal_id=deal_id, now=now)

    async def manager_overview(self, *, now: float | None = None, limit: int = 10) -> dict[str, Any]:
        clock = now if now is not None else time.time()
        reports: list[dict[str, Any]] = []
        for lead in await self._leads.list_leads():
            reports.append(await self._evaluate(lead_id=lead.lead_id, now=clock))
        seen_deals = {str(item.get("deal_id") or "") for item in reports}
        for deal in await self._deals.list_deals():
            if deal.deal_id not in seen_deals:
                reports.append(await self._evaluate(deal_id=deal.deal_id, now=clock))
        active = [item for item in reports if item["active"]]
        hottest = sorted(
            [item for item in active if item["temperature"] == SalesTemperature.HOT.value],
            key=lambda row: (-row["score"], row["entity_id"]),
        )[:limit]
        neglected = [item for item in active if item["stale"] and item.get("deal_id")]
        neglected.sort(key=lambda row: (row["score"], row["entity_id"]))
        overdue = await self._automation.get_overdue_follow_ups(now=clock)
        recommended = [item["next_best_action"] for item in hottest + neglected[:limit]]
        counts = {
            SalesTemperature.HOT.value: sum(1 for item in active if item["temperature"] == "hot"),
            SalesTemperature.WARM.value: sum(1 for item in active if item["temperature"] == "warm"),
            SalesTemperature.COLD.value: sum(1 for item in active if item["temperature"] == "cold"),
        }
        return {
            "hottest": hottest[:limit],
            "neglected": neglected[:limit],
            "overdue_follow_ups": overdue,
            "recommended_actions": recommended[: limit * 2],
            "temperatures": counts,
            "generated_at": clock,
        }

    async def _evaluate(self, *, lead_id: str = "", deal_id: str = "", now: float | None = None) -> dict[str, Any]:
        if not lead_id and not deal_id:
            raise ValidationError("lead_id or deal_id is required")
        clock = now if now is not None else time.time()
        lead, deal, customer = await self._load_entities(lead_id=lead_id, deal_id=deal_id)
        entity_type, entity_id = self._entity_ref(lead, deal)
        facts = await self._collect_facts(lead, deal, customer, now=clock)
        active = not self._is_inactive(lead, deal)
        factors = self._score_factors(lead, deal, customer, facts, now=clock, active=active)
        score = _clamp(BASE_SCORE + sum(int(item["impact"]) for item in factors))
        temperature = classify_temperature(score, active=active)
        stale_reasons = self._stale_reasons(lead, deal, facts, now=clock, active=active)
        nba = self._recommend(lead, deal, facts, now=clock, active=active)
        return {
            "score": score,
            "temperature": temperature.value,
            "active": active,
            "factors": factors,
            "next_best_action": nba,
            "stale": bool(stale_reasons) and active,
            "stale_reasons": stale_reasons if active else [],
            "entity_type": entity_type,
            "entity_id": entity_id,
            "lead_id": lead.lead_id if lead else "",
            "deal_id": deal.deal_id if deal else "",
            "customer_id": customer.customer_id if customer else (lead.customer_id if lead else deal.customer_id if deal else ""),
        }

    async def _load_entities(
        self, *, lead_id: str, deal_id: str
    ) -> tuple[CRMLead | None, CRMDeal | None, CustomerProfile | None]:
        lead: CRMLead | None = None
        deal: CRMDeal | None = None
        requested_deal_id = deal_id
        if lead_id:
            lead = await self._leads.get(lead_id)
            deal_id = deal_id or str(lead.metadata.get("converted_deal_id") or "")
        if deal_id:
            try:
                deal = await self._deals.get(deal_id)
            except NotFoundError:
                if requested_deal_id:
                    raise
                deal = None
        if lead is None and deal is not None:
            for item in await self._leads.list_leads():
                if str(item.metadata.get("converted_deal_id") or "") == deal.deal_id:
                    lead = item
                    break
        customer_id = (lead.customer_id if lead else "") or (deal.customer_id if deal else "")
        customer = None
        if customer_id:
            try:
                customer = await self._customers.get(customer_id)
            except NotFoundError:
                customer = None
        return lead, deal, customer

    async def _collect_facts(
        self,
        lead: CRMLead | None,
        deal: CRMDeal | None,
        customer: CustomerProfile | None,
        *,
        now: float,
    ) -> dict[str, Any]:
        lead_id = lead.lead_id if lead else ""
        deal_id = deal.deal_id if deal else ""
        customer_id = customer.customer_id if customer else ""
        activities = [
            item
            for item in await self._activities.list_activities()
            if self._linked(item, lead_id, deal_id, customer_id)
        ]
        calls = [item for item in await self._communications.list_calls() if self._linked(item, lead_id, deal_id, customer_id)]
        emails = [item for item in await self._communications.list_emails() if self._linked(item, lead_id, deal_id, customer_id)]
        meetings = [item for item in await self._calendar.list_meetings() if self._linked(item, lead_id, deal_id, customer_id)]
        tasks = [item for item in await self._tasks.list_tasks() if self._linked(item, lead_id, deal_id, customer_id)]
        follow_ups = [
            item
            for item in await self._automation.list_follow_ups(now=now)
            if (lead_id and item.get("lead_id") == lead_id)
            or (deal_id and item.get("deal_id") == deal_id)
            or (customer_id and item.get("customer_id") == customer_id)
        ]
        next_candidates: list[dict[str, Any]] = []
        if lead_id:
            item = await self._automation.next_action(lead_id=lead_id, now=now)
            if item:
                next_candidates.append(item)
        if deal_id:
            item = await self._automation.next_action(deal_id=deal_id, now=now)
            if item:
                next_candidates.append(item)
        next_action = (
            min(next_candidates, key=lambda row: (row.get("next_action_at") or 0, row.get("follow_up_id") or ""))
            if next_candidates
            else None
        )
        timestamps = [float(item.created_at or 0) for item in activities]
        timestamps.extend(float(item.created_at or 0) for item in calls)
        timestamps.extend(float(item.created_at or 0) for item in emails)
        timestamps.extend(float(item.created_at or 0) for item in meetings)
        last_activity = max(timestamps) if timestamps else 0.0
        return {
            "activities": activities,
            "calls": calls,
            "emails": emails,
            "meetings": meetings,
            "tasks": tasks,
            "follow_ups": follow_ups,
            "next_action": next_action,
            "last_activity_at": last_activity,
        }

    def _score_factors(
        self,
        lead: CRMLead | None,
        deal: CRMDeal | None,
        customer: CustomerProfile | None,
        facts: dict[str, Any],
        *,
        now: float,
        active: bool,
    ) -> list[dict[str, Any]]:
        factors: list[dict[str, Any]] = []
        if lead and lead.source.value in {"referral", "dealer"}:
            factors.append(_factor("quality_source", 8, "High-quality lead source"))
        if lead and lead.vehicle_id:
            factors.append(_factor("vehicle_interest", 5, "Vehicle interest specified"))
        if lead and lead.status == CRMLeadStatus.CONVERTED:
            factors.append(_factor("converted", 8, "Lead converted to a deal"))
        if customer and customer.intent_score > 50:
            factors.append(_factor("customer_intent", 10, "Customer intent is elevated"))
        if deal and deal.amount > 0:
            impact = min(10, int(deal.amount / 5000) or 1)
            factors.append(_factor("deal_value", impact, "Open deal has recorded value"))
        if deal and deal.stage in _STAGE_BONUS:
            impact = _STAGE_BONUS[deal.stage]
            factors.append(_factor("deal_progress", impact, f"Deal is in {deal.stage.value}"))
        last_at = float(facts["last_activity_at"] or 0)
        if last_at and now - last_at <= RECENT_SECONDS:
            factors.append(_factor("recent_activity", 12, "Recent customer interaction"))
        if any(item.status == "completed" or item.completed for item in facts["meetings"]):
            factors.append(_factor("completed_meeting", 15, "Meeting completed"))
        if any(item.status == "completed" for item in facts["calls"]):
            factors.append(_factor("completed_call", 12, "Call completed"))
        if any(item.status in {"sent", "logged"} for item in facts["emails"]):
            factors.append(_factor("recent_email", 8, "Email contact recorded"))
        open_follow = [item for item in facts["follow_ups"] if item.get("status") in {"upcoming", "due"}]
        overdue_follow = [item for item in facts["follow_ups"] if item.get("status") == "overdue"]
        if open_follow:
            factors.append(_factor("active_follow_up", 10, "Active follow-up is scheduled"))
        overdue_tasks = [
            item
            for item in facts["tasks"]
            if item.status in _OPEN_TASKS and item.due_at is not None and item.due_at < now
        ]
        open_tasks = [item for item in facts["tasks"] if item.status in _OPEN_TASKS and item not in overdue_tasks]
        if open_tasks:
            factors.append(_factor("open_task", 6, "Open actionable task exists"))
        if last_at and now - last_at >= STALE_SECONDS:
            factors.append(_factor("inactivity", -20, "No activity for 14 days or more"))
        elif last_at and now - last_at >= INACTIVE_SECONDS:
            factors.append(_factor("inactivity", -12, "No recent activity"))
        elif not last_at and active:
            factors.append(_factor("inactivity", -12, "No recorded activity"))
        if overdue_follow:
            factors.append(_factor("overdue_follow_up", -15, "Follow-up is overdue"))
        if overdue_tasks:
            factors.append(_factor("overdue_task", -12, "Task is overdue"))
        if deal and deal.stage not in _CLOSED_STAGES and last_at and now - last_at >= STALE_SECONDS:
            factors.append(_factor("stale_pipeline", -15, "Pipeline stage has been inactive"))
        if active and not facts["next_action"] and not facts["follow_ups"]:
            factors.append(_factor("missing_follow_up", -8, "No scheduled follow-up"))
        missed = sum(1 for item in facts["calls"] if item.status == "missed")
        if missed:
            factors.append(_factor("unanswered_attempts", -6 * min(missed, 3), "Repeated unanswered contact attempts"))
        if deal and deal.stage == DealStage.CLOSED_LOST:
            factors.append(_factor("closed_lost", -20, "Deal is closed lost"))
        factors.sort(key=lambda item: item["code"])
        return factors

    def _stale_reasons(
        self,
        lead: CRMLead | None,
        deal: CRMDeal | None,
        facts: dict[str, Any],
        *,
        now: float,
        active: bool,
    ) -> list[str]:
        if not active:
            return []
        reasons: list[str] = []
        last_at = float(facts["last_activity_at"] or 0)
        if not last_at or now - last_at >= STALE_SECONDS:
            reasons.append("no_recent_activity")
        if any(item.get("status") == "overdue" for item in facts["follow_ups"]):
            reasons.append("overdue_follow_up")
        if any(
            item.status in _OPEN_TASKS and item.due_at is not None and item.due_at < now for item in facts["tasks"]
        ):
            reasons.append("overdue_task")
        if not facts["next_action"]:
            reasons.append("missing_next_action")
        if deal and deal.stage not in _CLOSED_STAGES and last_at and now - last_at >= STALE_SECONDS:
            reasons.append("pipeline_inactivity")
        return reasons

    def _recommend(
        self,
        lead: CRMLead | None,
        deal: CRMDeal | None,
        facts: dict[str, Any],
        *,
        now: float,
        active: bool,
    ) -> dict[str, Any]:
        entity_type, entity_id = self._entity_ref(lead, deal)
        if not active:
            return self._nba(NextBestAction.NO_ACTION, TaskPriority.LOW, "Entity is closed", entity_type, entity_id)
        overdue_tasks = [
            item
            for item in facts["tasks"]
            if item.status in _OPEN_TASKS and item.due_at is not None and item.due_at < now
        ]
        if overdue_tasks:
            task = overdue_tasks[0]
            return self._nba(
                NextBestAction.COMPLETE_OVERDUE_TASK,
                TaskPriority.URGENT,
                "An open task is overdue",
                "task",
                task.task_id,
            )
        overdue_follow = [item for item in facts["follow_ups"] if item.get("status") == "overdue"]
        if overdue_follow:
            item = overdue_follow[0]
            action_type = str(item.get("action_type") or "call")
            action = {
                "email": NextBestAction.SEND_EMAIL,
                "meeting": NextBestAction.SCHEDULE_MEETING,
            }.get(action_type, NextBestAction.CALL_CUSTOMER)
            return self._nba(
                action,
                TaskPriority.HIGH,
                "Follow-up is overdue",
                "follow_up",
                str(item.get("follow_up_id") or entity_id),
            )
        if lead and lead.status == CRMLeadStatus.NEW and not facts["calls"]:
            return self._nba(
                NextBestAction.CALL_CUSTOMER,
                TaskPriority.HIGH,
                "New lead has not been contacted",
                entity_type,
                entity_id,
            )
        if not facts["next_action"]:
            return self._nba(
                NextBestAction.CREATE_FOLLOW_UP,
                TaskPriority.HIGH,
                "No next action is scheduled",
                entity_type,
                entity_id,
            )
        if deal and deal.stage in {DealStage.NEGOTIATION, DealStage.APPROVAL}:
            return self._nba(
                NextBestAction.ADVANCE_PIPELINE,
                TaskPriority.HIGH,
                f"Deal is in {deal.stage.value}",
                "deal",
                deal.deal_id,
            )
        if deal and deal.stage in {DealStage.PROPOSAL, DealStage.QUALIFICATION}:
            return self._nba(
                NextBestAction.REVIEW_DEAL,
                TaskPriority.NORMAL,
                "Deal needs pipeline review",
                "deal",
                deal.deal_id,
            )
        if not facts["meetings"]:
            return self._nba(
                NextBestAction.SCHEDULE_MEETING,
                TaskPriority.NORMAL,
                "No meeting has been scheduled",
                entity_type,
                entity_id,
            )
        return self._nba(
            NextBestAction.SEND_EMAIL,
            TaskPriority.NORMAL,
            "Continue engagement by email",
            entity_type,
            entity_id,
        )

    @staticmethod
    def _nba(action: NextBestAction, priority: TaskPriority, reason: str, entity_type: str, entity_id: str) -> dict[str, Any]:
        return {
            "action": action.value,
            "priority": priority.value,
            "reason": reason,
            "entity_type": entity_type,
            "entity_id": entity_id,
        }

    @staticmethod
    def _entity_ref(lead: CRMLead | None, deal: CRMDeal | None) -> tuple[str, str]:
        if deal is not None and lead is None:
            return "deal", deal.deal_id
        if lead is not None:
            return "lead", lead.lead_id
        if deal is not None:
            return "deal", deal.deal_id
        return "unknown", ""

    @staticmethod
    def _is_inactive(lead: CRMLead | None, deal: CRMDeal | None) -> bool:
        if deal is not None and deal.stage in _CLOSED_STAGES:
            return True
        if lead is not None and lead.status in {CRMLeadStatus.LOST}:
            return True
        return False

    @staticmethod
    def _linked(item: object, lead_id: str, deal_id: str, customer_id: str) -> bool:
        if lead_id and getattr(item, "lead_id", "") == lead_id:
            return True
        if deal_id and getattr(item, "deal_id", "") == deal_id:
            return True
        if customer_id and getattr(item, "customer_id", "") == customer_id:
            return True
        return False


crm_intelligence = CRMIntelligenceService()
