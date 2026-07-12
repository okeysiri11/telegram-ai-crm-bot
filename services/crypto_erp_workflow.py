# Crypto OTC ERP Phase 1 — workflow triggers (module crypto_otc).


class CryptoErpWorkflow:
    MODULE = "crypto_otc"

    TRIGGERS = (
        "REQUEST_CREATED",
        "DEAL_CREATED",
        "PAYMENT_RECEIVED",
        "DELIVERY_COMPLETED",
        "DEAL_CLOSED",
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
            CryptoErpWorkflow.MODULE,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload,
        )
        log_audit(
            user_id,
            f"crypto_erp_{trigger_code.lower()}",
            CryptoErpWorkflow.MODULE,
            f"{entity_type}:{entity_id}|{payload.get('message', '')[:120]}",
        )
        return log_ids
