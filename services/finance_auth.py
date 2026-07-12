# Finance RBAC — action-level permissions for BIDEX Financial Core.

from config import MANAGER_ID, OWNER_ID


class FinanceAuthService:
    @staticmethod
    def has_action(user_id: int, action: str) -> bool:
        from database import has_finance_action
        return has_finance_action(user_id, action)

    @staticmethod
    def can_view(user_id: int) -> bool:
        return FinanceAuthService.has_action(user_id, "FINANCE_VIEW")

    @staticmethod
    def can_create(user_id: int) -> bool:
        return FinanceAuthService.has_action(user_id, "FINANCE_CREATE")

    @staticmethod
    def can_approve(user_id: int) -> bool:
        return FinanceAuthService.has_action(user_id, "FINANCE_APPROVE")

    @staticmethod
    def can_execute(user_id: int) -> bool:
        return FinanceAuthService.has_action(user_id, "FINANCE_EXECUTE")

    @staticmethod
    def deny_message(action: str = "view") -> str:
        return f"Нет доступа к финансовой операции ({action})."
