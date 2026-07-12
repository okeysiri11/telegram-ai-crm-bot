# Agro ERP Phase 2 — workflow triggers with audit, workflow_log, notifications.

class AgroErpWorkflow:
    MODULE = "agro_trading"

    TRIGGERS = (
        "REQUEST_CREATED",
        "REQUEST_TAKEN",
        "DEAL_CREATED",
        "CONTRACT_SIGNED",
        "SHIPMENT_STARTED",
        "PAYMENT_RECEIVED",
        "DEAL_COMPLETED",
    )

    @staticmethod
    def emit(
        trigger_code: str,
        user_id: int,
        entity_type: str = None,
        entity_id: int = None,
        payload: dict = None,
    ) -> list[int]:
        from database import log_audit
        from services.workflow_engine import WorkflowEngine

        payload = payload or {}
        log_ids = WorkflowEngine.execute_workflow(
            trigger_code,
            user_id,
            AgroErpWorkflow.MODULE,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload,
        )
        log_audit(
            user_id,
            f"agro_erp_{trigger_code.lower()}",
            AgroErpWorkflow.MODULE,
            f"{entity_type}:{entity_id}|{payload.get('message', '')[:120]}",
        )
        return log_ids
