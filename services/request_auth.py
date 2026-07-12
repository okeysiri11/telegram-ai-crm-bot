# Authorization for CRM Agro request operations (legacy MANAGER_ID preserved).

from config import MANAGER_ID, OWNER_ID
from services.permissions import PermissionService


class RequestAuthService:
    AGRO_REQUEST_ACTIONS = {
        "take": {
            "permission": "AGRO_TAKE_REQUEST",
            "roles": ("OWNER", "ADMIN", "MANAGER", "AGRO_MANAGER"),
        },
        "view": {
            "permission": "AGRO_VIEW_REQUEST",
            "roles": ("OWNER", "ADMIN", "MANAGER", "AGRO_MANAGER", "CLIENT"),
        },
        "update": {
            "permission": "AGRO_UPDATE_STATUS",
            "roles": ("OWNER", "ADMIN", "MANAGER", "AGRO_MANAGER"),
        },
        "cancel": {
            "permission": "AGRO_CANCEL_REQUEST",
            "roles": ("OWNER", "ADMIN", "MANAGER", "AGRO_MANAGER"),
        },
        "bind": {
            "permission": "AGRO_BIND_DEAL",
            "roles": ("OWNER", "ADMIN", "MANAGER", "AGRO_MANAGER"),
        },
        "close": {
            "permission": "AGRO_CLOSE_DEAL",
            "roles": ("OWNER", "ADMIN", "MANAGER", "AGRO_MANAGER"),
        },
        "report": {
            "permission": "AGRO_VIEW_REPORT",
            "roles": ("OWNER", "ADMIN", "MANAGER", "AGRO_MANAGER"),
        },
    }

    @staticmethod
    def can_access_agro_requests(user_id: int) -> bool:
        if user_id in (OWNER_ID, MANAGER_ID):
            return True
        return PermissionService.has_permission(user_id, "agro_access")

    @staticmethod
    def can_view_request(user_id: int, request_row) -> bool:
        if not request_row:
            return False
        if user_id in (OWNER_ID, MANAGER_ID):
            return True
        client_id = request_row[2] if len(request_row) > 2 else None
        manager_id = request_row[7] if len(request_row) > 7 else None
        if client_id == user_id:
            return True
        if manager_id == user_id:
            return True
        return RequestAuthService.can_access_agro_requests(user_id)

    @staticmethod
    def can_assign_manager(user_id: int, request_row) -> bool:
        if not request_row:
            return False
        if not RequestAuthService.can_access_agro_requests(user_id):
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
        if RequestAuthService.can_access_agro_requests(user_id):
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
    def _user_role_label(user_id: int) -> str:
        from database import get_user_roles
        roles = get_user_roles(user_id)
        if not roles:
            return "—"
        return roles[0]

    @staticmethod
    def deny_message(action: str = "access", user_id: int = None) -> str:
        meta = RequestAuthService.AGRO_REQUEST_ACTIONS.get(action, {})
        permission = meta.get("permission", f"AGRO_{action.upper()}")
        allowed_roles = meta.get("roles", ("OWNER", "AGRO_MANAGER"))
        role_label = RequestAuthService._user_role_label(user_id) if user_id else "—"
        roles_line = "\n".join(allowed_roles)
        return (
            "❌ Недостаточно прав.\n\n"
            f"Требуется:\n{permission}\n\n"
            f"Ваша роль:\n{role_label}\n\n"
            f"Разрешенные роли:\n{roles_line}"
        )
