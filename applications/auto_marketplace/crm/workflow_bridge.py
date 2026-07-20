# Workflow bridge — lead assignment, tasks, reminders, approvals.

from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


class CRMWorkflowBridge:
    @staticmethod
    async def assign_lead(lead_id: str, *, dealer_id: str = "") -> str | None:
        try:
            from platform_workflow import workflow_engine
            from platform_workflow.models import WorkflowStep

            workflow = await workflow_engine.create_workflow(
                f"crm-lead-assign-{lead_id}",
                [WorkflowStep(name="assign_agent", assignee_id="crm-router")],
                metadata={"lead_id": lead_id, "dealer_id": dealer_id},
            )
            return workflow.workflow_id
        except Exception:
            logger.debug("workflow unavailable for lead assignment")
            return None

    @staticmethod
    async def schedule_follow_up(lead_id: str, customer_id: str, delay_hours: int = 24) -> dict[str, Any]:
        try:
            from platform_workflow import workflow_engine
            from platform_workflow.models import WorkflowStep

            workflow = await workflow_engine.create_workflow(
                f"crm-followup-{lead_id}",
                [WorkflowStep(name="follow_up", assignee_id="crm-agent")],
                metadata={"lead_id": lead_id, "customer_id": customer_id, "delay_hours": delay_hours},
            )
            return {"workflow_id": workflow.workflow_id, "scheduled_at": time.time() + delay_hours * 3600}
        except Exception:
            return {"scheduled_at": time.time() + delay_hours * 3600, "simulated": True}

    @staticmethod
    async def notify_manager(team_id: str, message: str) -> None:
        try:
            from applications.auto_marketplace.notifications.service import notification_service

            notification_service.send(
                channel="internal",
                recipient=team_id,
                subject="CRM Manager Alert",
                body=message,
            )
        except Exception:
            logger.debug("notification unavailable")

    @staticmethod
    async def approval_workflow(deal_id: str, approver_id: str) -> str | None:
        try:
            from platform_workflow import workflow_engine
            from platform_workflow.models import WorkflowStep

            workflow = await workflow_engine.create_workflow(
                f"crm-deal-approval-{deal_id}",
                [
                    WorkflowStep(name="manager_review", assignee_id=approver_id),
                    WorkflowStep(name="finalize", assignee_id="crm-agent"),
                ],
                metadata={"deal_id": deal_id},
            )
            return workflow.workflow_id
        except Exception:
            return None


crm_workflow_bridge = CRMWorkflowBridge()
