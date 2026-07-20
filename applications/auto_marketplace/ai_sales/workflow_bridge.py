# AI Sales workflow bridge — onboarding, nurturing, follow-ups, offers.

from __future__ import annotations

import logging
import time
from typing import Any

from applications.auto_marketplace.ai_sales.integration import ai_sales_platform_bridge

logger = logging.getLogger(__name__)


class AISalesWorkflowBridge:
    @staticmethod
    async def onboard_customer(customer_id: str) -> dict[str, Any]:
        workflow_id = await ai_sales_platform_bridge.start_workflow(
            f"ai-onboard-{customer_id}",
            ["welcome", "collect_preferences", "recommend_vehicles"],
            {"customer_id": customer_id},
        )
        return {"workflow_id": workflow_id, "customer_id": customer_id, "status": "started"}

    @staticmethod
    async def nurture_lead(lead_id: str, customer_id: str) -> dict[str, Any]:
        workflow_id = await ai_sales_platform_bridge.start_workflow(
            f"ai-nurture-{lead_id}",
            ["send_content", "check_engagement", "schedule_follow_up"],
            {"lead_id": lead_id, "customer_id": customer_id},
        )
        return {"workflow_id": workflow_id, "lead_id": lead_id}

    @staticmethod
    async def schedule_follow_up(
        lead_id: str,
        customer_id: str,
        *,
        delay_hours: int = 24,
        channel: str = "email",
    ) -> dict[str, Any]:
        try:
            from applications.auto_marketplace.crm.workflow_bridge import crm_workflow_bridge

            result = await crm_workflow_bridge.schedule_follow_up(lead_id, customer_id, delay_hours)
            result["channel"] = channel
            return result
        except Exception:
            return {"scheduled_at": time.time() + delay_hours * 3600, "channel": channel, "simulated": True}

    @staticmethod
    async def schedule_test_drive(customer_id: str, vehicle_id: str, dealer_id: str) -> dict[str, Any]:
        workflow_id = await ai_sales_platform_bridge.start_workflow(
            f"ai-testdrive-{customer_id}",
            ["confirm_availability", "book_slot", "send_reminder"],
            {"customer_id": customer_id, "vehicle_id": vehicle_id, "dealer_id": dealer_id},
        )
        return {"workflow_id": workflow_id, "vehicle_id": vehicle_id, "dealer_id": dealer_id}

    @staticmethod
    async def generate_offer_workflow(offer_id: str, customer_id: str) -> dict[str, Any]:
        workflow_id = await ai_sales_platform_bridge.start_workflow(
            f"ai-offer-{offer_id}",
            ["draft_offer", "manager_review", "send_to_customer"],
            {"offer_id": offer_id, "customer_id": customer_id},
        )
        return {"workflow_id": workflow_id, "offer_id": offer_id}

    @staticmethod
    async def reminder_automation(task_id: str, customer_id: str) -> dict[str, Any]:
        workflow_id = await ai_sales_platform_bridge.start_workflow(
            f"ai-reminder-{task_id}",
            ["trigger_reminder", "escalate_if_missed"],
            {"task_id": task_id, "customer_id": customer_id},
        )
        return {"workflow_id": workflow_id, "task_id": task_id}


ai_sales_workflow_bridge = AISalesWorkflowBridge()
