# Workflow bridge — Platform Core workflow hooks for trading (no platform mods).

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class TradingWorkflowBridge:
    @staticmethod
    async def start_lead_assignment(lead_id: str, assignee_id: str) -> str | None:
        try:
            from applications.agro_marketplace.integrations.platform_bridge import platform_bridge

            return await platform_bridge.start_order_workflow(
                f"lead-{lead_id}",
                {"workflow": "lead_assignment", "lead_id": lead_id, "assignee_id": assignee_id},
            )
        except Exception:
            logger.debug("lead assignment workflow unavailable")
            return None

    @staticmethod
    async def start_offer_approval(offer_id: str, payload: dict[str, Any] | None = None) -> str | None:
        try:
            from applications.agro_marketplace.integrations.platform_bridge import platform_bridge

            return await platform_bridge.start_order_workflow(
                f"offer-{offer_id}",
                {"workflow": "offer_approval", "offer_id": offer_id, **(payload or {})},
            )
        except Exception:
            logger.debug("offer approval workflow unavailable")
            return None

    @staticmethod
    async def start_negotiation_workflow(negotiation_id: str) -> str | None:
        try:
            from applications.agro_marketplace.integrations.platform_bridge import platform_bridge

            return await platform_bridge.start_order_workflow(
                f"nego-{negotiation_id}",
                {"workflow": "negotiation", "negotiation_id": negotiation_id},
            )
        except Exception:
            logger.debug("negotiation workflow unavailable")
            return None

    @staticmethod
    async def start_order_workflow(order_id: str) -> str | None:
        try:
            from applications.agro_marketplace.integrations.platform_bridge import platform_bridge

            return await platform_bridge.start_order_workflow(order_id, {"workflow": "marketplace_order"})
        except Exception:
            logger.debug("order workflow unavailable")
            return None

    @staticmethod
    async def start_contract_workflow(contract_id: str) -> str | None:
        try:
            from applications.agro_marketplace.integrations.platform_bridge import platform_bridge

            return await platform_bridge.start_order_workflow(
                f"contract-{contract_id}",
                {"workflow": "contract", "contract_id": contract_id},
            )
        except Exception:
            logger.debug("contract workflow unavailable")
            return None

    @staticmethod
    def notify(recipient_id: str, title: str, body: str) -> None:
        try:
            from applications.agro_marketplace.notifications.service import notification_service

            notification_service.notify(recipient_id, title, body, channel="workflow")
        except Exception:
            logger.debug("notification workflow unavailable")


trading_workflow = TradingWorkflowBridge()
