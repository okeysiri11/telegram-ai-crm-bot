# Real workflow triggers wired to platform modules.


class WorkflowTriggers:
    MODULE = "agro_trading"

    @staticmethod
    def on_request_created(
        user_id: int,
        request_number: int,
        module: str = "agro_trading",
        product: str = None,
    ) -> int:
        from database import log_audit

        if module == "agro_trading":
            from services.agro_deal_lifecycle import AgroDealLifecycle
            deal_id = AgroDealLifecycle.on_request_created(
                user_id, request_number, product=product,
            )
            log_audit(user_id, "workflow_trigger", "workflow", f"request_created:{request_number}")
            return deal_id

        from database import register_module_workflow
        from services.tasks import TaskService

        process_id = register_module_workflow(
            created_by=user_id,
            module=module,
            name=f"Заявка #{request_number}",
            trigger="request_created",
        )
        TaskService.create(
            task_type=TaskService.WORKFLOW,
            creator_id=user_id,
            title=f"Обработать заявку #{request_number}",
            description=product or "",
            module=module,
            priority="HIGH",
        )
        WorkflowTriggers._calendar(
            user_id, module, f"Новая заявка #{request_number}",
            trigger="request_created", ref=f"request:{request_number}",
        )
        log_audit(user_id, "workflow_trigger", "workflow", f"request_created:{request_number}")
        return process_id

    @staticmethod
    def on_manager_assigned(
        user_id: int,
        request_number: int,
        manager_id: int,
        module: str = "agro_trading",
    ) -> None:
        from database import log_audit

        if module == "agro_trading":
            from services.agro_deal_lifecycle import AgroDealLifecycle
            AgroDealLifecycle.on_manager_assigned(user_id, request_number, manager_id)
            log_audit(user_id, "workflow_trigger", "workflow", f"manager_assigned:{request_number}:{manager_id}")
            return

        from database import register_module_notification
        from services.tasks import TaskService

        register_module_notification(
            manager_id, module,
            title=f"Назначена заявка #{request_number}",
            message=f"Менеджер ID: {manager_id}",
            priority="INFO",
        )
        TaskService.create(
            task_type=TaskService.WORKFLOW,
            creator_id=manager_id,
            title=f"Заявка #{request_number} — в работе",
            module=module,
            assigned_user_id=manager_id,
            priority="NORMAL",
        )
        log_audit(user_id, "workflow_trigger", "workflow", f"manager_assigned:{request_number}:{manager_id}")

    @staticmethod
    def on_request_status_changed(
        user_id: int,
        request_number: int,
        old_status: str,
        new_status: str,
        module: str = "agro_trading",
    ) -> None:
        from database import log_audit, register_module_notification
        from services.statuses import normalize_status, is_terminal_status

        old_status = normalize_status(old_status)
        new_status = normalize_status(new_status)

        if module == "agro_trading":
            from services.agro_deal_lifecycle import AgroDealLifecycle
            AgroDealLifecycle.on_status_changed(user_id, request_number, old_status, new_status)
            return

        register_module_notification(
            user_id, module,
            title=f"Заявка #{request_number}: {old_status} → {new_status}",
            priority="INFO" if not is_terminal_status(new_status) else "WARNING",
        )
        if is_terminal_status(new_status):
            WorkflowTriggers._calendar(
                user_id, module, f"Заявка #{request_number} — {new_status}",
                trigger="request_status_changed",
                ref=f"request:{request_number}:{new_status}",
            )
        log_audit(
            user_id, "workflow_trigger", "workflow",
            f"status_changed:{request_number}:{old_status}:{new_status}",
        )

    @staticmethod
    def on_deal_entity_bound(
        user_id: int,
        request_number: int,
        entity_type: str,
        entity_id: int,
    ) -> None:
        from database import register_module_workflow, register_module_notification, log_audit

        trigger = f"agro_deal_{entity_type}_bound"
        register_module_workflow(
            created_by=user_id,
            module=WorkflowTriggers.MODULE,
            name=f"Сделка #{request_number} · {entity_type} #{entity_id}",
            trigger=trigger,
        )
        register_module_notification(
            user_id,
            WorkflowTriggers.MODULE,
            title=f"Сделка #{request_number}: привязан {entity_type} #{entity_id}",
            priority="INFO",
        )
        log_audit(
            user_id, "workflow_trigger", "workflow",
            f"{trigger}:{request_number}:{entity_id}",
        )

    @staticmethod
    def on_deal_closed(user_id: int, request_number: int) -> None:
        from database import register_module_workflow, log_audit

        register_module_workflow(
            created_by=user_id,
            module=WorkflowTriggers.MODULE,
            name=f"Сделка #{request_number} закрыта",
            trigger="agro_deal_closed",
        )
        log_audit(
            user_id, "workflow_trigger", "workflow",
            f"agro_deal_closed:{request_number}",
        )

    @staticmethod
    def on_deal_report_generated(
        user_id: int,
        request_number: int,
        file_id: int,
    ) -> None:
        from database import register_module_workflow, log_audit

        register_module_workflow(
            created_by=user_id,
            module=WorkflowTriggers.MODULE,
            name=f"Отчёт сделки #{request_number}",
            trigger="agro_deal_report_generated",
        )
        log_audit(
            user_id, "workflow_trigger", "workflow",
            f"agro_deal_report:{request_number}:{file_id}",
        )

    @staticmethod
    def on_task_created(
        user_id: int,
        task_id: int,
        task_type: str = "SYSTEM",
        title: str = "",
        module: str = "ai_assistant",
    ) -> None:
        from database import register_module_workflow, log_audit

        if task_type == "WORKFLOW":
            return
        register_module_workflow(
            created_by=user_id,
            module=module,
            name=f"Task #{task_id}: {title[:40]}",
            trigger=f"task_created:{task_type}",
        )
        log_audit(user_id, "workflow_trigger", "workflow", f"task_created:{task_id}:{task_type}")

    @staticmethod
    def on_calendar_event_created(
        user_id: int,
        event_id: int,
        title: str,
        module: str = "calendar",
    ) -> None:
        from database import register_module_workflow, log_audit

        register_module_workflow(
            created_by=user_id,
            module=module if module in (
                "agro_trading", "crypto_otc", "law", "drone", "cafe_beauty",
            ) else "agro_trading",
            name=f"Event #{event_id}: {title[:40]}",
            trigger="calendar_event_created",
        )
        log_audit(user_id, "workflow_trigger", "workflow", f"calendar_event_created:{event_id}")

    @staticmethod
    def _calendar(user_id, module, title, trigger, ref):
        from database import create_calendar_event
        from datetime import datetime
        create_calendar_event(
            responsible_user=user_id,
            title=title,
            start_datetime=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            description=f"workflow:{trigger}|{ref}",
            module=module,
        )
