# Finance repository — data access via FinanceCoreService.


class FinanceRepository:
    @staticmethod
    def list_accounts(user_id: int, **kwargs) -> list:
        from services.finance_core import FinanceCoreService
        return FinanceCoreService.list_accounts(user_id, **kwargs)

    @staticmethod
    def create_account(user_id: int, account_name: str, **kwargs) -> int:
        from services.finance_core import FinanceCoreService
        return FinanceCoreService.create_account(user_id, account_name, **kwargs)

    @staticmethod
    def create_transaction(user_id: int, transaction_type: str, amount: float, **kwargs) -> int:
        from services.finance_core import FinanceCoreService
        return FinanceCoreService.create_transaction(
            user_id, transaction_type, amount, **kwargs,
        )

    @staticmethod
    def update_transaction_status(transaction_id: int, user_id: int, status: str) -> bool:
        from services.finance_core import FinanceCoreService
        return FinanceCoreService.update_transaction_status(
            transaction_id, user_id, status,
        )
