# Finance workflow bridge — approvals, payments, refunds.

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class FinanceWorkflowBridge:
    @staticmethod
    async def document_approval(document_id: str, approver_id: str) -> str | None:
        try:
            from platform_workflow import workflow_engine
            from platform_workflow.models import WorkflowStep

            workflow = await workflow_engine.create_workflow(
                f"doc-approval-{document_id}",
                [WorkflowStep(name="review", assignee_id=approver_id), WorkflowStep(name="approve", assignee_id=approver_id)],
                metadata={"document_id": document_id},
            )
            return workflow.workflow_id
        except Exception:
            logger.debug("workflow unavailable for document approval")
            return None

    @staticmethod
    async def contract_approval(contract_id: str, approver_id: str) -> str | None:
        try:
            from platform_workflow import workflow_engine
            from platform_workflow.models import WorkflowStep

            workflow = await workflow_engine.create_workflow(
                f"contract-approval-{contract_id}",
                [WorkflowStep(name="legal_review", assignee_id=approver_id), WorkflowStep(name="sign", assignee_id="customer")],
                metadata={"contract_id": contract_id},
            )
            return workflow.workflow_id
        except Exception:
            return None

    @staticmethod
    async def payment_workflow(payment_id: str) -> dict[str, Any]:
        try:
            from platform_workflow import workflow_engine
            from platform_workflow.models import WorkflowStep

            workflow = await workflow_engine.create_workflow(
                f"payment-{payment_id}",
                [
                    WorkflowStep(name="authorize", assignee_id="payment-gateway"),
                    WorkflowStep(name="capture", assignee_id="payment-gateway"),
                ],
                metadata={"payment_id": payment_id},
            )
            return {"workflow_id": workflow.workflow_id, "payment_id": payment_id}
        except Exception:
            return {"payment_id": payment_id, "simulated": True}

    @staticmethod
    async def invoice_approval(invoice_id: str, approver_id: str) -> str | None:
        try:
            from platform_workflow import workflow_engine
            from platform_workflow.models import WorkflowStep

            workflow = await workflow_engine.create_workflow(
                f"invoice-approval-{invoice_id}",
                [WorkflowStep(name="finance_review", assignee_id=approver_id)],
                metadata={"invoice_id": invoice_id},
            )
            return workflow.workflow_id
        except Exception:
            return None

    @staticmethod
    async def refund_workflow(refund_id: str, approver_id: str) -> dict[str, Any]:
        try:
            from platform_workflow import workflow_engine
            from platform_workflow.models import WorkflowStep

            workflow = await workflow_engine.create_workflow(
                f"refund-{refund_id}",
                [
                    WorkflowStep(name="review", assignee_id=approver_id),
                    WorkflowStep(name="process_refund", assignee_id="finance-system"),
                ],
                metadata={"refund_id": refund_id},
            )
            return {"workflow_id": workflow.workflow_id, "refund_id": refund_id}
        except Exception:
            return {"refund_id": refund_id, "simulated": True}


finance_workflow_bridge = FinanceWorkflowBridge()
