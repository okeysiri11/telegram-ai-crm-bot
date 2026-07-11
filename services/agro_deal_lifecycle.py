# Full Agro deal lifecycle orchestration (Tasks, Calendar, Files, Workflow, Notifications, Reports).

from datetime import datetime

MODULE = "agro_trading"


class AgroDealLifecycle:
    @staticmethod
    def on_request_created(
        user_id: int,
        request_number: int,
        product: str = None,
    ) -> int:
        from database import (
            get_request_by_number,
            create_agro_deal,
            update_agro_deal,
            register_module_workflow,
            register_module_notification,
            create_calendar_event,
            register_module_file,
            log_audit,
        )
        from services.tasks import TaskService
        from services.statuses import normalize_status

        request = get_request_by_number(request_number)
        if not request:
            return 0

        client_id = request[2]
        manager_id = request[7]
        product = product or request[4]

        deal_id = create_agro_deal(
            request_number=request_number,
            client_id=client_id,
            product=product,
            manager_id=manager_id,
            status=normalize_status("NEW"),
        )

        process_id = register_module_workflow(
            created_by=user_id,
            module=MODULE,
            name=f"Сделка #{request_number}",
            trigger="agro_deal_created",
        )

        task_id = TaskService.create(
            task_type=TaskService.WORKFLOW,
            creator_id=user_id,
            title=f"[Agro] Обработать заявку #{request_number}",
            description=product or "",
            module=MODULE,
            assigned_user_id=manager_id,
            priority="HIGH",
        )

        event_id = create_calendar_event(
            responsible_user=manager_id or user_id,
            title=f"[Agro] Новая сделка #{request_number}",
            start_datetime=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            description=f"agro_deal:{deal_id}|request:{request_number}",
            module=MODULE,
            priority="high",
        )

        folder_id = register_module_file(
            uploaded_by=user_id,
            module=MODULE,
            filename=f"agro/deals/{request_number}/.folder",
            original_filename=f"Сделка #{request_number}",
            description=f"document_folder|request:{request_number}",
            tags=f"deal,{request_number},folder",
        )

        update_agro_deal(
            request_number,
            workflow_process_id=process_id,
            manager_task_id=task_id,
            calendar_event_id=event_id,
            document_folder_id=folder_id,
        )

        if manager_id:
            register_module_notification(
                manager_id,
                MODULE,
                title=f"Новая Agro-сделка #{request_number}",
                message=product or "",
                priority="INFO",
            )

        log_audit(user_id, "agro_deal_lifecycle", MODULE, f"created:{request_number}")
        return deal_id

    @staticmethod
    def on_manager_assigned(
        actor_id: int,
        request_number: int,
        manager_id: int,
    ) -> None:
        from database import (
            get_agro_deal_by_request,
            update_agro_deal,
            create_calendar_event,
            register_module_notification,
            log_audit,
        )
        from services.tasks import TaskService
        from services.statuses import normalize_status

        deal = get_agro_deal_by_request(request_number)
        if deal:
            update_agro_deal(
                request_number,
                manager_id=manager_id,
                status=normalize_status("IN_PROGRESS"),
            )
        else:
            AgroDealLifecycle.on_request_created(actor_id, request_number)

        task_id = TaskService.create(
            task_type=TaskService.WORKFLOW,
            creator_id=manager_id,
            title=f"[Agro] Сделка #{request_number} — в работе",
            module=MODULE,
            assigned_user_id=manager_id,
            priority="NORMAL",
        )

        event_id = create_calendar_event(
            responsible_user=manager_id,
            title=f"[Agro] Менеджер назначен · #{request_number}",
            start_datetime=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            description=f"agro_deal:manager_assigned|request:{request_number}",
            module=MODULE,
        )

        if deal:
            update_agro_deal(
                request_number,
                manager_task_id=task_id,
                calendar_event_id=event_id,
            )

        register_module_notification(
            manager_id,
            MODULE,
            title=f"Вам назначена сделка #{request_number}",
            message=f"Менеджер ID: {manager_id}",
            priority="INFO",
        )
        log_audit(actor_id, "agro_deal_lifecycle", MODULE, f"manager:{request_number}:{manager_id}")

    @staticmethod
    def on_status_changed(
        actor_id: int,
        request_number: int,
        old_status: str,
        new_status: str,
    ) -> None:
        from database import (
            update_agro_deal,
            register_module_notification,
            log_audit,
        )
        from services.statuses import normalize_status, is_terminal_status

        new_status = normalize_status(new_status)
        old_status = normalize_status(old_status)
        update_agro_deal(request_number, status=new_status)

        register_module_notification(
            actor_id,
            MODULE,
            title=f"Сделка #{request_number}: {old_status} → {new_status}",
            priority="WARNING" if is_terminal_status(new_status) else "INFO",
        )

        if new_status == "DONE":
            AgroDealLifecycle.close_deal(actor_id, request_number)
        log_audit(
            actor_id,
            "agro_deal_lifecycle",
            MODULE,
            f"status:{request_number}:{old_status}:{new_status}",
        )

    @staticmethod
    def bind_contract(
        user_id: int,
        request_number: int,
        contract_number: str = None,
        contract_type: str = "FOB",
    ) -> int:
        from database import create_agro_contract, bind_agro_deal_contract, log_audit

        contract_number = contract_number or f"AGR-{request_number}"
        contract_id = create_agro_contract(
            created_by=user_id,
            contract_number=contract_number,
            contract_type=contract_type,
            request_number=request_number,
            execution_status="DRAFT",
        )
        bind_agro_deal_contract(request_number, contract_id)
        from services.workflow_triggers import WorkflowTriggers
        WorkflowTriggers.on_deal_entity_bound(user_id, request_number, "contract", contract_id)
        log_audit(user_id, "agro_deal_bind", MODULE, f"contract:{request_number}:{contract_id}")
        return contract_id

    @staticmethod
    def bind_logistics(
        user_id: int,
        request_number: int,
        transport: str = "TBD",
        route: str = "TBD",
    ) -> int:
        from database import create_agro_logistics, bind_agro_deal_logistics, log_audit

        logistics_id = create_agro_logistics(
            created_by=user_id,
            request_number=request_number,
            transport=transport,
            route=route,
            delivery_status="PLANNED",
        )
        bind_agro_deal_logistics(request_number, logistics_id)
        from services.workflow_triggers import WorkflowTriggers
        WorkflowTriggers.on_deal_entity_bound(user_id, request_number, "logistics", logistics_id)
        log_audit(user_id, "agro_deal_bind", MODULE, f"logistics:{request_number}:{logistics_id}")
        return logistics_id

    @staticmethod
    def bind_finance(
        user_id: int,
        request_number: int,
        deal_amount: float = 0,
        currency: str = "USD",
    ) -> int:
        from database import create_agro_finance, bind_agro_deal_finance, log_audit

        finance_id = create_agro_finance(
            created_by=user_id,
            request_number=request_number,
            deal_amount=deal_amount,
            currency=currency,
        )
        bind_agro_deal_finance(request_number, finance_id)
        from services.workflow_triggers import WorkflowTriggers
        WorkflowTriggers.on_deal_entity_bound(user_id, request_number, "finance", finance_id)
        log_audit(user_id, "agro_deal_bind", MODULE, f"finance:{request_number}:{finance_id}")
        return finance_id

    @staticmethod
    def close_deal(user_id: int, request_number: int) -> bool:
        from database import (
            close_agro_deal,
            get_agro_deal_by_request,
            complete_workflow_process,
            log_audit,
        )

        deal = get_agro_deal_by_request(request_number)
        ok = close_agro_deal(request_number, user_id)
        if ok:
            if deal and deal[6]:
                complete_workflow_process(deal[6], user_id)
            from services.workflow_triggers import WorkflowTriggers
            WorkflowTriggers.on_deal_closed(user_id, request_number)
            AgroDealLifecycle.generate_report(user_id, request_number)
            log_audit(user_id, "agro_deal_lifecycle", MODULE, f"closed:{request_number}")
        return ok

    @staticmethod
    def generate_report(user_id: int, request_number: int) -> int:
        from database import (
            generate_agro_deal_report,
            register_module_notification,
            log_audit,
        )

        file_id = generate_agro_deal_report(request_number, user_id)
        if file_id:
            from services.workflow_triggers import WorkflowTriggers
            WorkflowTriggers.on_deal_report_generated(user_id, request_number, file_id)
        register_module_notification(
            user_id,
            MODULE,
            title=f"Отчёт по сделке #{request_number}",
            message=f"Файл отчёта #{file_id or '—'}",
            priority="INFO",
        )
        log_audit(user_id, "agro_deal_report", MODULE, f"report:{request_number}:{file_id}")
        return file_id
