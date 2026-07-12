# Central permission checks for modules and entities.

from config import MANAGER_ID, OWNER_ID


class PermissionService:
    CRM_PERMISSIONS = frozenset({"agro_access", "crypto_access"})
    CRM_ROLES = frozenset({
        "OWNER", "ADMIN", "MANAGER", "AGRO_MANAGER", "OTC_MANAGER",
        "CRYPTO_MANAGER", "SUPER_MANAGER",
    })
    EDIT_ROLES = frozenset({
        "OWNER", "ADMIN", "MANAGER", "AGRO_MANAGER", "OTC_MANAGER",
        "CRYPTO_MANAGER", "SUPER_MANAGER",
    })
    DELETE_ROLES = frozenset({"OWNER", "ADMIN"})
    BUSINESS_FULL_ACCESS_ROLES = frozenset({"OWNER", "ADMIN", "SUPER_MANAGER"})

    @staticmethod
    def has_permission(user_id: int, permission: str) -> bool:
        from database import (
            get_user_roles,
            SYSTEM_PERMISSIONS,
            ROLE_PERMISSIONS,
        )
        if permission not in SYSTEM_PERMISSIONS:
            return False
        roles = get_user_roles(user_id)
        if not roles:
            return False
        for role in roles:
            if permission in ROLE_PERMISSIONS.get(role, set()):
                return True
        return False

    @staticmethod
    def can_access_module(user_id: int, module: str) -> bool:
        from database import MODULE_PERMISSIONS
        if user_id in (OWNER_ID, MANAGER_ID):
            return True
        roles = PermissionService._user_roles(user_id)
        if roles & PermissionService.BUSINESS_FULL_ACCESS_ROLES:
            return True
        permission = MODULE_PERMISSIONS.get(module)
        if not permission:
            return False
        return PermissionService.has_permission(user_id, permission)

    @staticmethod
    def has_owner_only_action(user_id: int, action: str) -> bool:
        from database import OWNER_ONLY_ACTIONS
        if action not in OWNER_ONLY_ACTIONS:
            return True
        if user_id == OWNER_ID:
            return True
        roles = PermissionService._user_roles(user_id)
        if "ADMIN" in roles and action != "OWNER_ONLY":
            return action not in {"SYSTEM_RESET", "DATABASE_DROP"}
        return False

    @staticmethod
    def can_edit_entity(
        user_id: int,
        entity_type: str,
        entity_id: int = None,
        owner_id: int = None,
    ) -> bool:
        if user_id in (OWNER_ID, MANAGER_ID):
            return True
        roles = PermissionService._user_roles(user_id)
        if roles & PermissionService.EDIT_ROLES:
            return True
        if owner_id is not None and user_id == owner_id:
            return entity_type in {"task", "file", "workflow", "calendar_event", "notification"}
        if entity_type == "request":
            return bool(roles & PermissionService.CRM_ROLES)
        return False

    @staticmethod
    def can_delete_entity(
        user_id: int,
        entity_type: str,
        entity_id: int = None,
        owner_id: int = None,
    ) -> bool:
        if user_id == OWNER_ID:
            return True
        roles = PermissionService._user_roles(user_id)
        if "SUPER_MANAGER" in roles:
            return entity_type in {"task", "file", "workflow", "notification"}
        if roles & PermissionService.DELETE_ROLES:
            if entity_type == "request":
                return "ADMIN" in roles or "OWNER" in roles
            if entity_type in {"user", "role"}:
                return False
            return True
        if owner_id is not None and user_id == owner_id:
            return entity_type in {"task", "file", "workflow", "notification"}
        return False

    @staticmethod
    def is_crm_operator(user_id: int) -> bool:
        if user_id in (OWNER_ID, MANAGER_ID):
            return True
        roles = PermissionService._user_roles(user_id)
        if roles & PermissionService.CRM_ROLES:
            return True
        for perm in PermissionService.CRM_PERMISSIONS:
            if PermissionService.has_permission(user_id, perm):
                return True
        return False

    @staticmethod
    def _user_roles(user_id: int) -> set:
        from database import get_user_roles
        return set(get_user_roles(user_id))

    @staticmethod
    def has_crypto_action(user_id: int, action: str) -> bool:
        from database import has_crypto_action
        return has_crypto_action(user_id, action)

    @staticmethod
    def has_finance_action(user_id: int, action: str) -> bool:
        from database import has_finance_action
        return has_finance_action(user_id, action)

    @staticmethod
    def has_deal_action(user_id: int, action: str) -> bool:
        from database import has_deal_action
        return has_deal_action(user_id, action)

    @staticmethod
    def has_commission_action(user_id: int, action: str) -> bool:
        from database import has_commission_action
        return has_commission_action(user_id, action)

    @staticmethod
    def has_partner_action(user_id: int, action: str) -> bool:
        from database import has_partner_action
        return has_partner_action(user_id, action)
