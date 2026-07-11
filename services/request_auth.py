# Authorization for CRM request operations (additive layer, legacy MANAGER_ID preserved).

from config import MANAGER_ID, OWNER_ID
from services.permissions import PermissionService


class RequestAuthService:
    @staticmethod
    def can_view_request(user_id: int, request_row) -> bool:
        if not request_row:
            return False
        if user_id in (OWNER_ID, MANAGER_ID):
            return True
        if PermissionService.is_crm_operator(user_id):
            return True
        client_id = request_row[2] if len(request_row) > 2 else None
        manager_id = request_row[7] if len(request_row) > 7 else None
        if client_id == user_id:
            return True
        if manager_id == user_id:
            return True
        return False

    @staticmethod
    def can_assign_manager(user_id: int, request_row) -> bool:
        if not request_row:
            return False
        if not PermissionService.is_crm_operator(user_id):
            return False
        manager_id = request_row[7] if len(request_row) > 7 else None
        return manager_id is None or manager_id == 0

    @staticmethod
    def can_take_request(user_id: int, request_row) -> bool:
        return RequestAuthService.can_assign_manager(user_id, request_row)

    @staticmethod
    def can_update_status(user_id: int, request_row) -> bool:
        if not request_row:
            return False
        if user_id in (OWNER_ID, MANAGER_ID):
            return True
        if PermissionService.is_crm_operator(user_id):
            manager_id = request_row[7] if len(request_row) > 7 else None
            if manager_id in (None, 0, user_id):
                return True
        client_id = request_row[2] if len(request_row) > 2 else None
        if client_id == user_id:
            from services.statuses import normalize_status
            current = normalize_status(request_row[6] if len(request_row) > 6 else "NEW")
            return current == "NEW"
        return False

    @staticmethod
    def can_cancel_request(user_id: int, request_row) -> bool:
        return RequestAuthService.can_update_status(user_id, request_row)

    @staticmethod
    def deny_message(action: str = "access") -> str:
        return f"⛔ Недостаточно прав для операции: {action}."
