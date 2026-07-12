# Task repository — handlers should use this instead of direct database access.


class TaskRepository:
    @staticmethod
    def get(task_id: int, user_id: int = None):
        from services.tasks import TaskService
        return TaskService.get_task(task_id, user_id)

    @staticmethod
    def create(creator_id: int, title: str, **kwargs) -> int:
        from services.tasks import TaskService
        return TaskService.create(
            task_type=kwargs.pop("task_type", TaskService.SYSTEM),
            creator_id=creator_id,
            title=title,
            **kwargs,
        )

    @staticmethod
    def delete(task_id: int, user_id: int) -> bool:
        from services.tasks import TaskService
        return TaskService.delete_task(task_id, user_id)

    @staticmethod
    def list_by_user(user_id: int, **kwargs) -> list:
        from services.tasks import TaskService
        return TaskService.get_tasks_by_user(user_id, **kwargs)
