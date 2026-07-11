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
        from database import register_module_workflow, log_audit
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
            user_id,
            module,
            f"Новая заявка #{request_number}",
            trigger="request_created",
            ref=f"request:{request_number}",
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
        from database import register_module_notification, log_audit
        from services.tasks import TaskService

        register_module_notification(
            manager_id,
            module,
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
        from database import register_module_notification, log_audit
        from services.statuses import normalize_status, is_terminal_status

        old_status = normalize_status(old_status)
        new_status = normalize_status(new_status)
        register_module_notification(
            user_id,
            module,
            title=f"Заявка #{request_number}: {old_status} → {new_status}",
            priority="INFO" if not is_terminal_status(new_status) else "WARNING",
        )
        if is_terminal_status(new_status):
            WorkflowTriggers._calendar(
                user_id,
                module,
                f"Заявка #{request_number} — {new_status}",
                trigger="request_status_changed",
                ref=f"request:{request_number}:{new_status}",
            )
        log_audit(
            user_id,
            "workflow_trigger",
            "workflow",
            f"status_changed:{request_number}:{old_status}:{new_status}",
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
            module=module if module in ("agro_trading", "crypto_otc", "law", "drone", "cafe_beauty") else "agro_trading",
            name=f"Event #{event_id}: {title[:40]}",
            trigger="calendar_event_created",
        )
        log_audit(user_id, "workflow_trigger", "workflow", f"calendar_event_created:{event_id}")

    @staticmethod
    def _calendar(user_id, module, title, trigger, ref):
        from database import register_calendar_event
        register_calendar_event(
            user_id,
            module,
            title=title,
            description=f"workflow:{trigger}|{ref}",
        )
