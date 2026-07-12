# Crypto OTC authorization — action-level permissions.

from config import MANAGER_ID, OWNER_ID


class CryptoAuthService:
    @staticmethod
    def can_access_crypto(user_id: int) -> bool:
        if user_id in (OWNER_ID, MANAGER_ID):
            return True
        from services.permissions import PermissionService
        return PermissionService.can_access_module(user_id, "crypto_otc")

    @staticmethod
    def can_view_deals(user_id: int) -> bool:
        from database import has_crypto_action
        return has_crypto_action(user_id, "CRYPTO_VIEW_DEALS")

    @staticmethod
    def can_edit_deals(user_id: int) -> bool:
        from database import has_crypto_action
        return has_crypto_action(user_id, "CRYPTO_EDIT_DEALS")

    @staticmethod
    def can_view_finance(user_id: int) -> bool:
        from database import has_crypto_action
        return has_crypto_action(user_id, "CRYPTO_VIEW_FINANCE")

    @staticmethod
    def deny_message(action: str = "CRYPTO_VIEW_DEALS", user_id: int = None) -> str:
        from database import get_user_roles, CRYPTO_MANAGER_ROLES
        roles = get_user_roles(user_id) if user_id else []
        role_label = roles[0] if roles else "—"
        return (
            "❌ Недостаточно прав Crypto OTC.\n\n"
            f"Требуется: {action}\n"
            f"Ваша роль: {role_label}\n\n"
            f"Менеджеры: {', '.join(sorted(CRYPTO_MANAGER_ROLES))}"
        )
