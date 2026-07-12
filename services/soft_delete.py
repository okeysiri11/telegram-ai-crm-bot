# Soft delete engine — logical deletion with restore and purge.


class SoftDeleteService:
    @staticmethod
    def soft_delete(entity_type: str, entity_id: int, user_id: int) -> bool:
        from database import soft_delete
        return soft_delete(entity_type, entity_id, user_id)

    @staticmethod
    def restore(entity_type: str, entity_id: int, user_id: int) -> bool:
        from database import restore
        return restore(entity_type, entity_id, user_id)

    @staticmethod
    def purge_deleted(entity_type: str = None, older_than_days: int = 90) -> int:
        from database import purge_deleted
        return purge_deleted(entity_type, older_than_days)

    @staticmethod
    def can_restore(user_id: int) -> bool:
        from config import OWNER_ID, MANAGER_ID
        from database import get_user_roles
        roles = set(get_user_roles(user_id))
        return bool(
            user_id in (OWNER_ID, MANAGER_ID)
            or roles & {"OWNER", "SUPER_MANAGER"}
        )
