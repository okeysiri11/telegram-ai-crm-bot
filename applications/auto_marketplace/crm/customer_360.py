# CRM Customer 360 — unified timeline and relationship intelligence.

from __future__ import annotations

import time
from enum import Enum
from typing import Any

from applications.auto_marketplace.activities.service import ActivityService, activity_service
from applications.auto_marketplace.calendar.service import CalendarService, calendar_service
from applications.auto_marketplace.communications.service import CommunicationService, communication_service
from applications.auto_marketplace.crm.automation import CRMAutomationEngine, crm_automation
from applications.auto_marketplace.crm.execution import CRMExecutionEngine, crm_execution
from applications.auto_marketplace.crm.intelligence import INACTIVE_SECONDS
from applications.auto_marketplace.crm.models import (
    CRMDeal,
    CRMLead,
    CustomerProfile,
    DealStage,
    Interaction,
    InteractionType,
    TaskStatus,
)
from applications.auto_marketplace.crm.tenant import current_crm_tenant
from applications.auto_marketplace.customers.profile_service import CustomerProfileService, customer_profile_service
from applications.auto_marketplace.deals.service import DealService, deal_service
from applications.auto_marketplace.leads.service import LeadService, lead_service
from applications.auto_marketplace.tasks.service import TaskService, task_service

_CLOSED_STAGES = frozenset({DealStage.CLOSED_WON, DealStage.CLOSED_LOST})
_OPEN_TASKS = frozenset({TaskStatus.PENDING, TaskStatus.IN_PROGRESS})
_MEANINGFUL_COMM = frozenset({InteractionType.CALL, InteractionType.EMAIL, InteractionType.MEETING})
_EVENT_MAP = {
    InteractionType.LEAD_CREATED: "lead_created",
    InteractionType.CUSTOMER_CREATED: "lead_created",
    InteractionType.DEAL_CREATED: "opportunity_created",
    InteractionType.LEAD_CONVERTED: "opportunity_created",
    InteractionType.STAGE_CHANGE: "stage_changed",
    InteractionType.STATUS_CHANGE: "stage_changed",
    InteractionType.CALL: "communication",
    InteractionType.EMAIL: "communication",
    InteractionType.MEETING: "communication",
    InteractionType.SMS: "communication",
    InteractionType.CHAT: "communication",
    InteractionType.MESSAGE: "communication",
    InteractionType.NOTE: "note_added",
    InteractionType.TASK_CREATED: "task_created",
    InteractionType.TASK_COMPLETED: "task_completed",
    InteractionType.FOLLOW_UP_SCHEDULED: "follow_up_scheduled",
    InteractionType.FOLLOW_UP_RESCHEDULED: "follow_up_scheduled",
    InteractionType.FOLLOW_UP_COMPLETED: "follow_up_completed",
    InteractionType.FOLLOW_UP_CANCELLED: "automation_action",
    InteractionType.AUTOMATION_TASK_CREATED: "automation_action",
    InteractionType.REMINDER_CREATED: "follow_up_scheduled",
    InteractionType.REMINDER_COMPLETED: "follow_up_completed",
    InteractionType.MEETING_CANCELLED: "communication",
}
_HEALTH_WEIGHTS = {
    "RECENT_CONTACT": 18,
    "HOT_LEAD": 12,
    "OPEN_DEAL": 10,
    "FOLLOW_UP_OVERDUE": -20,
    "TASK_OVERDUE": -15,
    "SLA_BREACHED": -25,
    "SLA_AT_RISK": -8,
    "STALE_OPPORTUNITY": -18,
    "NO_RECENT_CONTACT": -15,
    "ESCALATED": -12,
    "HOT_LEAD_NO_ACTION": -10,
    "HIGH_VALUE_DEAL_AT_RISK": -20,
}


class RelationshipHealth(str, Enum):
    STRONG = "strong"
    HEALTHY = "healthy"
    ATTENTION = "attention"
    AT_RISK = "at_risk"


def classify_relationship(score: int) -> RelationshipHealth:
    if score >= 75:
        return RelationshipHealth.STRONG
    if score >= 55:
        return RelationshipHealth.HEALTHY
    if score >= 35:
        return RelationshipHealth.ATTENTION
    return RelationshipHealth.AT_RISK


def _clamp(score: int) -> int:
    return max(0, min(100, score))


class Customer360Service:
    """Read-only Customer 360. PostgreSQL facts only. No lifecycle mutations."""

    def __init__(
        self,
        *,
        customers: CustomerProfileService | None = None,
        leads: LeadService | None = None,
        deals: DealService | None = None,
        activities: ActivityService | None = None,
        communications: CommunicationService | None = None,
        tasks: TaskService | None = None,
        calendar: CalendarService | None = None,
        automation: CRMAutomationEngine | None = None,
        execution: CRMExecutionEngine | None = None,
    ) -> None:
        self._customers = customers or customer_profile_service
        self._leads = leads or lead_service
        self._deals = deals or deal_service
        self._activities = activities or activity_service
        self._communications = communications or communication_service
        self._tasks = tasks or task_service
        self._calendar = calendar or calendar_service
        self._automation = automation or crm_automation
        self._execution = execution or crm_execution

    async def get_360(self, customer_id: str, *, now: float | None = None, timeline_limit: int = 100) -> dict[str, Any]:
        clock = now if now is not None else time.time()
        customer = await self._customers.get(customer_id)
        leads = await self._leads.list_leads(customer_id=customer_id)
        deals = await self._deals.list_deals(customer_id=customer_id)
        lead_ids = {lead.lead_id for lead in leads}
        deal_ids = {deal.deal_id for deal in deals}
        activities = await self._related_activities(customer_id, lead_ids, deal_ids)
        tasks = await self._related_tasks(customer_id, lead_ids, deal_ids)
        follow_ups = await self._related_follow_ups(customer_id, lead_ids, deal_ids, now=clock)
        executions = await self._related_executions(leads, deals, now=clock)
        timeline = self._timeline(activities, limit=timeline_limit)
        signals = self._attention_signals(activities, tasks, follow_ups, executions, deals, now=clock)
        relationship = self._relationship(signals, executions, deals, now=clock)
        primary = self._primary_execution(executions)
        open_deals = [deal for deal in deals if deal.stage not in _CLOSED_STAGES]
        closed_deals = [deal for deal in deals if deal.stage in _CLOSED_STAGES]
        open_tasks = [task for task in tasks if task.status in _OPEN_TASKS]
        overdue_tasks = [task for task in open_tasks if task.due_at is not None and task.due_at < clock]
        next_follow = self._next_follow_up(follow_ups)
        latest_comm = self._latest_communication(activities)
        last_activity = activities[0] if activities else None
        owner_id = customer.owner_agent_id or (leads[0].assigned_agent_id if leads else "") or (deals[0].owner_agent_id if deals else "")
        stage = self._lifecycle_stage(customer, leads, open_deals, closed_deals)
        return {
            "customer_id": customer.customer_id,
            "tenant_id": current_crm_tenant(),
            "identity": {
                "customer_id": customer.customer_id,
                "first_name": customer.first_name,
                "last_name": customer.last_name,
                "email": customer.email,
                "phone": customer.phone,
                "segment": customer.segment,
            },
            "contact": {"email": customer.email, "phone": customer.phone},
            "lifecycle_stage": stage,
            "owner_id": owner_id,
            "leads": [{"lead_id": lead.lead_id, "status": lead.status.value, "assigned_agent_id": lead.assigned_agent_id} for lead in leads],
            "open_opportunities": [self._deal_brief(deal) for deal in open_deals],
            "closed_opportunities": [self._deal_brief(deal) for deal in closed_deals],
            "deal_value": sum(float(deal.amount or 0) for deal in open_deals),
            "latest_communication": latest_comm,
            "last_meaningful_activity": self._activity_brief(last_activity) if last_activity else None,
            "next_follow_up": next_follow,
            "open_tasks": [self._task_brief(task) for task in open_tasks],
            "overdue_tasks": [self._task_brief(task) for task in overdue_tasks],
            "automation_status": next_follow.get("status") if next_follow else "none",
            "lead_score": primary.get("score") if primary else 0,
            "lead_temperature": primary.get("temperature") if primary else "cold",
            "next_best_action": {
                "action": primary.get("recommended_action") if primary else "NO_ACTION",
                "reason": primary.get("recommended_action_reason") if primary else "No related sales work",
            },
            "stale_opportunity": any(item.get("stale") for item in executions),
            "execution_priority": primary.get("priority") if primary else "low",
            "sla_status": primary.get("sla_status") if primary else "on_time",
            "escalation_status": primary.get("escalation_level") if primary else "none",
            "relationship_health": relationship["relationship_health"],
            "relationship_score": relationship["relationship_score"],
            "relationship_reason_codes": relationship["reason_codes"],
            "relationship_explanation": relationship["explanation"],
            "attention_signals": signals,
            "timeline": timeline,
            "timeline_count": len(timeline),
            "derived_at": clock,
        }

    async def manager_customer_view(self, customer_id: str, *, now: float | None = None) -> dict[str, Any]:
        return await self.get_360(customer_id, now=now)

    async def timeline(self, customer_id: str, *, limit: int = 100) -> list[dict[str, Any]]:
        await self._customers.get(customer_id)
        leads = await self._leads.list_leads(customer_id=customer_id)
        deals = await self._deals.list_deals(customer_id=customer_id)
        activities = await self._related_activities(customer_id, {lead.lead_id for lead in leads}, {deal.deal_id for deal in deals})
        return self._timeline(activities, limit=limit)

    async def _related_activities(self, customer_id: str, lead_ids: set[str], deal_ids: set[str]) -> list[Interaction]:
        items = [
            item
            for item in await self._activities.list_activities()
            if self._is_related(item.customer_id, item.lead_id, item.deal_id, customer_id, lead_ids, deal_ids)
        ]
        items.sort(key=lambda item: (-float(item.created_at or 0), item.interaction_type.value, item.interaction_id))
        return items

    async def _related_tasks(self, customer_id: str, lead_ids: set[str], deal_ids: set[str]) -> list:
        return [
            item
            for item in await self._tasks.list_tasks()
            if self._is_related(item.customer_id, item.lead_id, item.deal_id, customer_id, lead_ids, deal_ids)
        ]

    async def _related_follow_ups(
        self, customer_id: str, lead_ids: set[str], deal_ids: set[str], *, now: float
    ) -> list[dict[str, Any]]:
        return [
            item
            for item in await self._automation.list_follow_ups(now=now)
            if self._is_related(
                str(item.get("customer_id") or ""),
                str(item.get("lead_id") or ""),
                str(item.get("deal_id") or ""),
                customer_id,
                lead_ids,
                deal_ids,
            )
        ]

    async def _related_executions(self, leads: list[CRMLead], deals: list[CRMDeal], *, now: float) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        seen_deals: set[str] = set()
        for lead in leads:
            item = await self._execution.evaluate(lead_id=lead.lead_id, now=now)
            items.append(item)
            if item.get("deal_id"):
                seen_deals.add(str(item["deal_id"]))
        for deal in deals:
            if deal.deal_id not in seen_deals:
                items.append(await self._execution.evaluate(deal_id=deal.deal_id, now=now))
        return items

    def _timeline(self, activities: list[Interaction], *, limit: int) -> list[dict[str, Any]]:
        events = [self._normalize_event(item) for item in activities]
        events.sort(key=lambda item: (-float(item["occurred_at"] or 0), item["event_type"], item["event_id"]))
        cap = max(0, int(limit))
        return events[:cap]

    def _normalize_event(self, item: Interaction) -> dict[str, Any]:
        event_type = _EVENT_MAP.get(item.interaction_type, "note_added")
        body = str(item.body or "")
        if item.interaction_type == InteractionType.STAGE_CHANGE and body == DealStage.CLOSED_WON.value:
            event_type = "deal_won"
        elif item.interaction_type == InteractionType.STAGE_CHANGE and body == DealStage.CLOSED_LOST.value:
            event_type = "deal_lost"
        return {
            "event_id": item.interaction_id,
            "event_type": event_type,
            "occurred_at": float(item.created_at or 0),
            "customer_id": item.customer_id,
            "lead_id": item.lead_id,
            "deal_id": item.deal_id,
            "actor_id": item.agent_id,
            "title": item.subject or event_type,
            "summary": item.body or item.subject or event_type,
            "source": "activity",
            "metadata": {"activity_type": item.interaction_type.value, "idempotency_key": item.idempotency_key},
        }

    def _attention_signals(
        self,
        activities: list[Interaction],
        tasks: list,
        follow_ups: list[dict[str, Any]],
        executions: list[dict[str, Any]],
        deals: list[CRMDeal],
        *,
        now: float,
    ) -> list[dict[str, str]]:
        codes: list[str] = []
        if any(item.get("status") == "overdue" for item in follow_ups):
            codes.append("FOLLOW_UP_OVERDUE")
        if any(task.status in _OPEN_TASKS and task.due_at is not None and task.due_at < now for task in tasks):
            codes.append("TASK_OVERDUE")
        last_comm = self._latest_communication_at(activities)
        if last_comm is None or now - last_comm >= INACTIVE_SECONDS:
            codes.append("NO_RECENT_CONTACT")
        sla_states = {str(item.get("sla_status") or "") for item in executions}
        if "due_soon" in sla_states:
            codes.append("SLA_AT_RISK")
        if "breached" in sla_states:
            codes.append("SLA_BREACHED")
        if any(item.get("escalation_level") in {"manager", "critical"} for item in executions):
            codes.append("ESCALATED")
        if any(item.get("stale") and item.get("deal_id") for item in executions):
            codes.append("STALE_OPPORTUNITY")
        if any(
            item.get("temperature") == "hot"
            and item.get("active")
            and item.get("recommended_action") in {"CALL_CUSTOMER", "CREATE_FOLLOW_UP", "COMPLETE_OVERDUE_TASK"}
            for item in executions
        ):
            codes.append("HOT_LEAD_NO_ACTION")
        open_value = sum(float(deal.amount or 0) for deal in deals if deal.stage not in _CLOSED_STAGES)
        if open_value > 0 and (
            "STALE_OPPORTUNITY" in codes or "SLA_BREACHED" in codes or "FOLLOW_UP_OVERDUE" in codes
        ):
            codes.append("HIGH_VALUE_DEAL_AT_RISK")
        unique = sorted(set(codes))
        return [{"code": code, "reason": code.replace("_", " ").lower()} for code in unique]

    def _relationship(
        self,
        signals: list[dict[str, str]],
        executions: list[dict[str, Any]],
        deals: list[CRMDeal],
        *,
        now: float,
    ) -> dict[str, Any]:
        codes = [item["code"] for item in signals]
        reasons: list[str] = []
        score = 50
        if "NO_RECENT_CONTACT" not in codes:
            reasons.append("RECENT_CONTACT")
            score += _HEALTH_WEIGHTS["RECENT_CONTACT"]
        if any(item.get("temperature") == "hot" and item.get("active") for item in executions):
            reasons.append("HOT_LEAD")
            score += _HEALTH_WEIGHTS["HOT_LEAD"]
        if any(deal.stage not in _CLOSED_STAGES for deal in deals):
            reasons.append("OPEN_DEAL")
            score += _HEALTH_WEIGHTS["OPEN_DEAL"]
        for code in codes:
            if code in _HEALTH_WEIGHTS:
                reasons.append(code)
                score += _HEALTH_WEIGHTS[code]
        reasons = sorted(set(reasons))
        score = _clamp(score)
        health = classify_relationship(score)
        explanation = ", ".join(code.replace("_", " ").lower() for code in reasons) or "No relationship signals"
        return {
            "relationship_health": health.value,
            "relationship_score": score,
            "reason_codes": reasons,
            "explanation": explanation,
        }

    @staticmethod
    def _primary_execution(executions: list[dict[str, Any]]) -> dict[str, Any] | None:
        active = [item for item in executions if item.get("active")]
        pool = active or executions
        if not pool:
            return None
        return sorted(pool, key=lambda item: (-int(item.get("priority_score") or 0), item.get("entity_id") or ""))[0]

    @staticmethod
    def _lifecycle_stage(
        customer: CustomerProfile,
        leads: list[CRMLead],
        open_deals: list[CRMDeal],
        closed_deals: list[CRMDeal],
    ) -> str:
        if open_deals:
            return open_deals[0].stage.value
        if closed_deals:
            return closed_deals[0].stage.value
        if leads:
            return leads[0].status.value
        return customer.segment or "customer"

    @staticmethod
    def _deal_brief(deal: CRMDeal) -> dict[str, Any]:
        return {
            "deal_id": deal.deal_id,
            "opportunity_id": deal.opportunity_id or deal.deal_id,
            "stage": deal.stage.value,
            "amount": deal.amount,
            "owner_id": deal.owner_agent_id,
        }

    @staticmethod
    def _task_brief(task: Any) -> dict[str, Any]:
        return {
            "task_id": task.task_id,
            "title": task.title,
            "status": task.status.value,
            "due_at": task.due_at,
            "owner_id": task.assigned_agent_id,
        }

    @staticmethod
    def _activity_brief(item: Interaction) -> dict[str, Any]:
        return {
            "activity_id": item.interaction_id,
            "activity_type": item.interaction_type.value,
            "subject": item.subject,
            "occurred_at": item.created_at,
        }

    @staticmethod
    def _latest_communication(activities: list[Interaction]) -> dict[str, Any] | None:
        comms = [item for item in activities if item.interaction_type in _MEANINGFUL_COMM]
        if not comms:
            return None
        item = comms[0]
        return {
            "activity_id": item.interaction_id,
            "channel": item.interaction_type.value,
            "subject": item.subject,
            "occurred_at": item.created_at,
        }

    @staticmethod
    def _latest_communication_at(activities: list[Interaction]) -> float | None:
        comms = [float(item.created_at or 0) for item in activities if item.interaction_type in _MEANINGFUL_COMM]
        return max(comms) if comms else None

    @staticmethod
    def _next_follow_up(follow_ups: list[dict[str, Any]]) -> dict[str, Any] | None:
        open_items = [item for item in follow_ups if item.get("status") in {"upcoming", "due", "overdue"}]
        if not open_items:
            return None
        item = min(open_items, key=lambda row: (float(row.get("due_at") or 0), str(row.get("follow_up_id") or "")))
        return {
            "follow_up_id": item.get("follow_up_id"),
            "action_type": item.get("action_type"),
            "due_at": item.get("due_at"),
            "status": item.get("status"),
            "priority": item.get("priority"),
        }

    @staticmethod
    def _is_related(
        customer_id: str,
        lead_id: str,
        deal_id: str,
        target_customer: str,
        lead_ids: set[str],
        deal_ids: set[str],
    ) -> bool:
        if customer_id and customer_id == target_customer:
            return True
        if lead_id and lead_id in lead_ids:
            return True
        if deal_id and deal_id in deal_ids:
            return True
        return False


customer_360 = Customer360Service()
