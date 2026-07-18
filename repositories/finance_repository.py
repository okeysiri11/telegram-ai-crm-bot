# Finance repository — data access only (authorization in FinanceCoreService).


class FinanceRepository:
    @staticmethod
    def list_accounts(user_id: int, **kwargs) -> list:
        from database import list_finance_accounts

        return list_finance_accounts(**kwargs)

    @staticmethod
    def create_account(user_id: int, account_name: str, **kwargs) -> int:
        from database import create_finance_account

        return create_finance_account(user_id, account_name, **kwargs)

    @staticmethod
    def create_transaction(user_id: int, transaction_type: str, amount: float, **kwargs) -> int:
        from database import create_finance_transaction

        return create_finance_transaction(
            user_id=user_id,
            transaction_type=transaction_type,
            amount=amount,
            **kwargs,
        )

    @staticmethod
    def update_transaction_status(transaction_id: int, user_id: int, status: str) -> bool:
        from database import update_finance_transaction_status

        return update_finance_transaction_status(transaction_id, user_id, status)
