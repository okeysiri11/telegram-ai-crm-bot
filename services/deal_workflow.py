# Shared Deal Workflow Engine — module-agnostic deal lifecycle hooks.


class DealWorkflowEngine:
    MODULE_TRIGGERS = {
        "AGRO": (
            "DEAL_CREATED", "DEAL_NEGOTIATION", "DEAL_COMPLETED",
        ),
        "AUTO": (
            "DEAL_CREATED", "AUTO_TRADEIN_STARTED", "DEAL_COMPLETED",
        ),
        "LEGAL": (
            "DEAL_CREATED", "LEGAL_CASE_CREATED", "DEAL_COMPLETED",
        ),
        "DRONE": (
            "DEAL_CREATED", "DRONE_PROJECT_CREATED", "DEAL_COMPLETED",
        ),
        "FINANCE": (
            "DEAL_CREATED", "FINANCE_PAYMENT_CONFIRMED", "DEAL_COMPLETED",
        ),
        "LOGISTICS": (
            "DEAL_CREATED", "SHIPMENT_STARTED", "DEAL_COMPLETED",
        ),
    }

    @staticmethod
    def on_created(deal_id: int, user_id: int, module: str, payload: dict = None) -> list:
        return DealWorkflowEngine._emit(
            "DEAL_CREATED", deal_id, user_id, module, payload,
        )

    @staticmethod
    def on_status_changed(
        deal_id: int,
        user_id: int,
        module: str,
        old_status: str,
        new_status: str,
    ) -> list:
        payload = {"old_status": old_status, "new_status": new_status}
        log_ids = DealWorkflowEngine._emit(
            "DEAL_STATUS_CHANGED", deal_id, user_id, module, payload,
        )
        if new_status == "NEGOTIATION" and module == "AUTO":
            from events import EventBus
            from database import DEAL_MODULE_TO_HUB
            EventBus.publish(
                "AUTO_TRADEIN_STARTED",
                user_id=user_id,
                entity_id=deal_id,
                module=DEAL_MODULE_TO_HUB.get("AUTO", "automotive"),
                payload={"deal_id": deal_id},
            )
        elif new_status == "NEGOTIATION" and module == "LEGAL":
            from events import EventBus
            from database import DEAL_MODULE_TO_HUB
            EventBus.publish(
                "LEGAL_CASE_CREATED",
                user_id=user_id,
                entity_id=deal_id,
                module=DEAL_MODULE_TO_HUB.get("LEGAL", "law"),
                payload={"deal_id": deal_id},
            )
        elif new_status == "IN_PROGRESS" and module == "DRONE":
            from events import EventBus
            from database import DEAL_MODULE_TO_HUB
            EventBus.publish(
                "DRONE_PROJECT_CREATED",
                user_id=user_id,
                entity_id=deal_id,
                module=DEAL_MODULE_TO_HUB.get("DRONE", "drone"),
                payload={"deal_id": deal_id},
            )
        return log_ids

    @staticmethod
    def on_completed(
        deal_id: int,
        user_id: int,
        module: str,
        payload: dict = None,
    ) -> list:
        return DealWorkflowEngine._emit(
            "DEAL_COMPLETED", deal_id, user_id, module, payload or {},
        )

    @staticmethod
    def _emit(
        trigger_code: str,
        deal_id: int,
        user_id: int,
        module: str,
        payload: dict = None,
    ) -> list:
        from database import DEAL_MODULE_TO_HUB, log_audit
        from services.workflow_engine import WorkflowEngine
        from services.timeline import TimelineService

        module = (module or "AGRO").upper()
        hub_module = DEAL_MODULE_TO_HUB.get(module, module.lower())
        payload = payload or {}

        log_ids = WorkflowEngine.execute_workflow(
            trigger_code,
            user_id,
            hub_module,
            entity_type="deal",
            entity_id=deal_id,
            payload={
                "title": payload.get("title") or f"Deal #{deal_id} · {trigger_code}",
                "message": payload.get("message", ""),
                **payload,
            },
        )
        TimelineService.record(
            "DEAL", deal_id, trigger_code, user_id,
            description=f"{module} deal #{deal_id}: {trigger_code}",
        )
        log_audit(
            user_id, f"deal_workflow_{trigger_code.lower()}",
            "deals", f"deal={deal_id}|module={module}",
        )
        return log_ids
