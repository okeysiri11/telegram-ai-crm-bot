# Unified TaskService over the central `tasks` table.

from config import OWNER_ID, MANAGER_ID

TASK_TYPES = ("HUMAN", "AI", "SYSTEM", "WORKFLOW")


class TaskService:
    HUMAN = "HUMAN"
    AI = "AI"
    SYSTEM = "SYSTEM"
    WORKFLOW = "WORKFLOW"

    @staticmethod
    def can_access(user_id: int, task_row) -> bool:
        if not task_row:
            return False
        if user_id in (OWNER_ID, MANAGER_ID):
            return True
        creator_id, assignee_id = task_row[5], task_row[6]
        if user_id in (creator_id, assignee_id):
            return True
        from services.permissions import PermissionService
        return PermissionService.is_crm_operator(user_id)

    @staticmethod
    def can_edit(user_id: int, task_row) -> bool:
        if not task_row:
            return False
        from services.permissions import PermissionService
        return PermissionService.can_edit_entity(
            user_id, "task", task_row[0], owner_id=task_row[5],
        )

    @staticmethod
    def create(
        task_type: str,
        creator_id: int,
        title: str,
        description: str = "",
        module: str = "system",
        priority: str = "NORMAL",
        assigned_user_id: int = None,
        due_date: str = None,
        project_id: int = None,
    ) -> int:
        from database import create_task, _normalize_task_module

        if task_type not in TASK_TYPES:
            task_type = TaskService.SYSTEM
        if task_type == TaskService.AI:
            module = "ai_assistant"

        task_id = create_task(
            creator_id=creator_id,
            title=title,
            description=description,
            module=_normalize_task_module(module),
            project_id=project_id,
            assignee_id=assigned_user_id,
            priority=priority,
            deadline=due_date,
            task_type=task_type,
        )

        if task_id:
            pass  # TASK_CREATED event published by create_task via EventBus
        return task_id

    @staticmethod
    def get_task(task_id: int, user_id: int):
        from database import get_task
        return get_task(task_id, user_id)

    @staticmethod
    def get_tasks_by_user(
        user_id: int,
        scope: str = "my",
        status: str = None,
        active_only: bool = False,
        overdue_only: bool = False,
        limit: int = 20,
    ):
        from database import get_tasks_by_user
        return get_tasks_by_user(
            user_id,
            scope=scope,
            status=status,
            active_only=active_only,
            overdue_only=overdue_only,
            limit=limit,
        )

    @staticmethod
    def get_tasks_by_module(module: str, user_id: int = None, limit: int = 20):
        from database import get_tasks_by_module
        return get_tasks_by_module(module, user_id=user_id, limit=limit)

    @staticmethod
    def update_task_status(task_id: int, user_id: int, status: str) -> bool:
        from database import update_task_status
        return update_task_status(task_id, user_id, status)

    @staticmethod
    def assign_task(task_id: int, user_id: int, assignee_id: int) -> bool:
        from database import assign_task
        return assign_task(task_id, user_id, assignee_id)

    @staticmethod
    def delete_task(task_id: int, user_id: int) -> bool:
        from database import delete_task
        return delete_task(task_id, user_id)

    @staticmethod
    def update_deadline(task_id: int, user_id: int, deadline: str) -> bool:
        from database import update_task_deadline
        return update_task_deadline(task_id, user_id, deadline)

    @staticmethod
    def update_fields(task_id: int, user_id: int, **fields) -> bool:
        from database import update_task_fields
        return update_task_fields(task_id, user_id, **fields)

    # Legacy compatibility
    @staticmethod
    def get_tasks(task_type: str, user_id: int, scope: str = "my", limit: int = 20):
        module = "ai_assistant" if task_type == TaskService.AI else None
        rows = TaskService.get_tasks_by_user(user_id, scope=scope, limit=limit)
        if module:
            rows = [r for r in rows if r[3] == module]
        return rows

    @staticmethod
    def update_status(task_type: str, user_id: int, task_id: int, status: str) -> bool:
        return TaskService.update_task_status(task_id, user_id, status)

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
            project_id=kwargs.get("project_id"),
        )
