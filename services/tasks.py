# Unified task facade: HUMAN, AI, SYSTEM, WORKFLOW.

TASK_TYPES = ("HUMAN", "AI", "SYSTEM", "WORKFLOW")


class TaskService:
    HUMAN = "HUMAN"
    AI = "AI"
    SYSTEM = "SYSTEM"
    WORKFLOW = "WORKFLOW"

    @staticmethod
    def create(
        task_type: str,
        creator_id: int,
        title: str,
        description: str = "",
        module: str = "ai_assistant",
        priority: str = "NORMAL",
        assigned_user_id: int = None,
        due_date: str = None,
        project_id: int = None,
    ) -> int:
        if task_type not in TASK_TYPES:
            task_type = TaskService.SYSTEM

        if task_type == TaskService.AI:
            from database import create_ai_task
            task_id = create_ai_task(creator_id, title, project_id=project_id)
        else:
            from database import create_system_task
            task_id = create_system_task(
                creator_id=creator_id,
                title=title,
                description=description,
                module=module,
                priority=priority,
                assigned_user_id=assigned_user_id,
                due_date=due_date,
                task_source=task_type,
            )

        if task_id:
            from services.workflow_triggers import WorkflowTriggers
            WorkflowTriggers.on_task_created(
                creator_id,
                task_id,
                task_type=task_type,
                title=title,
                module=module,
            )
        return task_id

    @staticmethod
    def get_tasks(
        task_type: str,
        user_id: int,
        scope: str = "my",
        limit: int = 20,
    ):
        if task_type == TaskService.AI:
            from database import get_ai_tasks
            return get_ai_tasks(user_id)
        from database import get_system_tasks
        return get_system_tasks(
            user_id,
            scope=scope,
            limit=limit,
            task_source=task_type if task_type in TASK_TYPES else None,
        )

    @staticmethod
    def update_status(task_type: str, user_id: int, task_id: int, status: str) -> bool:
        from services.statuses import normalize_status
        status = normalize_status(status)
        if task_type == TaskService.AI:
            from database import update_ai_task_status
            return update_ai_task_status(user_id, task_id, status.lower())
        from database import update_system_task_status
        return update_system_task_status(task_id, user_id, status)

    @staticmethod
    def register_module_task(
        creator_id: int,
        module: str,
        title: str,
        task_type: str = "SYSTEM",
        **kwargs,
    ) -> int:
        return TaskService.create(
            task_type=task_type,
            creator_id=creator_id,
            title=title,
            module=module,
            description=kwargs.get("description", ""),
            priority=kwargs.get("priority", "NORMAL"),
            assigned_user_id=kwargs.get("assigned_user_id"),
            due_date=kwargs.get("due_date"),
        )
