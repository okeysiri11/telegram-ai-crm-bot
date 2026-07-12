# Full Agro request lifecycle via WorkflowEngine (additive — does not replace AgroDealLifecycle).

from datetime import datetime


class AgroRequestWorkflow:
    MODULE = "agro_trading"

    @staticmethod
    def on_request_created(
        user_id: int,
        request_number: int,
        product: str = "",
        client_name: str = "",
    ) -> None:
        from services.workflow_engine import WorkflowEngine
        from database import log_audit

        WorkflowEngine.execute_workflow(
            "AGRO_REQUEST_CREATED",
            user_id,
            AgroRequestWorkflow.MODULE,
            entity_type="request",
            entity_id=request_number,
            payload={
                "title": f"Новая Agro заявка #{request_number}",
                "message": f"{client_name} · {product}".strip(" ·"),
                "product": product,
                "priority": "HIGH",
                "request_number": request_number,
            },
        )
        log_audit(
            user_id,
            "workflow_request_created",
            AgroRequestWorkflow.MODULE,
            f"#{request_number}",
        )

    @staticmethod
    def on_request_assigned(
        actor_id: int,
        request_number: int,
        manager_id: int,
    ) -> None:
        from services.workflow_engine import WorkflowEngine
        from database import (
            get_agro_deal_by_request,
            update_task_status,
            assign_task,
            log_audit,
        )

        deal = get_agro_deal_by_request(request_number)
        task_id = deal[7] if deal else None
        if task_id:
            assign_task(task_id, actor_id, manager_id)
            update_task_status(task_id, actor_id, "IN_PROGRESS")

        WorkflowEngine.execute_workflow(
            "REQUEST_ASSIGNED",
            manager_id,
            AgroRequestWorkflow.MODULE,
            entity_type="request",
            entity_id=request_number,
            payload={
                "title": f"Заявка #{request_number} назначена",
                "message": f"Менеджер ID: {manager_id}",
                "manager_id": manager_id,
                "request_number": request_number,
                "task_id": task_id,
                "priority": "HIGH",
            },
        )
        log_audit(
            actor_id,
            "workflow_request_assigned",
            AgroRequestWorkflow.MODULE,
            f"#{request_number}:manager={manager_id}",
        )

    @staticmethod
    def on_request_done(
        actor_id: int,
        request_number: int,
    ) -> None:
        from services.workflow_engine import WorkflowEngine
        from database import (
            get_agro_deal_by_request,
            get_request_client,
            update_task_status,
            log_audit,
        )
        from services.calendar_service import CalendarService

        deal = get_agro_deal_by_request(request_number)
        task_id = deal[7] if deal else None
        cal_id = deal[9] if deal else None
        client_id = get_request_client(request_number)

        if task_id:
            update_task_status(task_id, actor_id, "DONE")
        if cal_id:
            CalendarService.update_event(cal_id, actor_id, status="DONE")

        WorkflowEngine.execute_workflow(
            "REQUEST_DONE",
            actor_id,
            AgroRequestWorkflow.MODULE,
            entity_type="request",
            entity_id=request_number,
            payload={
                "title": f"Заявка #{request_number} завершена",
                "request_number": request_number,
                "client_id": client_id,
                "task_id": task_id,
                "calendar_event_id": cal_id,
                "priority": "NORMAL",
            },
        )
        log_audit(
            actor_id,
            "workflow_request_done",
            AgroRequestWorkflow.MODULE,
            f"#{request_number}",
        )

    @staticmethod
    def on_request_cancelled(
        actor_id: int,
        request_number: int,
    ) -> None:
        from services.workflow_engine import WorkflowEngine
        from database import (
            get_agro_deal_by_request,
            get_request_by_number,
            update_task_status,
            log_audit,
        )
        from services.calendar_service import CalendarService

        deal = get_agro_deal_by_request(request_number)
        task_id = deal[7] if deal else None
        cal_id = deal[9] if deal else None
        req = get_request_by_number(request_number)
        client_id = req[2] if req else None
        manager_id = req[7] if req else None

        if task_id:
            update_task_status(task_id, actor_id, "CANCELLED")
        if cal_id:
            CalendarService.update_event(cal_id, actor_id, status="CANCELLED")

        WorkflowEngine.execute_workflow(
            "REQUEST_CANCELLED",
            actor_id,
            AgroRequestWorkflow.MODULE,
            entity_type="request",
            entity_id=request_number,
            payload={
                "title": f"Заявка #{request_number} отменена",
                "request_number": request_number,
                "client_id": client_id,
                "manager_id": manager_id,
                "task_id": task_id,
                "calendar_event_id": cal_id,
                "priority": "WARNING",
            },
        )
        log_audit(
            actor_id,
            "workflow_request_cancelled",
            AgroRequestWorkflow.MODULE,
            f"#{request_number}",
        )
