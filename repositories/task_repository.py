# Task repository — data access only (authorization in TaskService).

SYSTEM = "SYSTEM"


class TaskRepository:
    @staticmethod
    def get(task_id: int, user_id: int = None):
        from database import get_task

        return get_task(task_id, user_id)

    @staticmethod
    def create(creator_id: int, title: str, **kwargs) -> int:
        from database import _normalize_task_module, create_task

        task_type = kwargs.pop("task_type", SYSTEM)
        module = kwargs.pop("module", "system")
        assigned_user_id = kwargs.pop("assigned_user_id", None)
        due_date = kwargs.pop("due_date", None)
        project_id = kwargs.pop("project_id", None)
        description = kwargs.pop("description", "")
        priority = kwargs.pop("priority", "NORMAL")

        return create_task(
            creator_id=creator_id,
            title=title,
            description=description,
            module=_normalize_task_module(module),
            project_id=project_id,
            assignee_id=assigned_user_id,
            priority=priority,
            deadline=due_date,
            task_type=task_type,
            **kwargs,
        )

    @staticmethod
    def delete(task_id: int, user_id: int) -> bool:
        from database import delete_task

        return delete_task(task_id, user_id)

    @staticmethod
    def list_by_user(user_id: int, **kwargs) -> list:
        from database import get_tasks_by_user

        return get_tasks_by_user(user_id, **kwargs)
