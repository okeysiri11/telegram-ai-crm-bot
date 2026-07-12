# Ledger repository — internal ledger access layer.


class LedgerRepository:
    @staticmethod
    def post(user_id: int, module: str, entry_type: str, amount: float, **kwargs) -> int:
        from services.ledger_engine import LedgerEngine
        return LedgerEngine.post(user_id, module, entry_type, amount, **kwargs)

    @staticmethod
    def get(entry_row_id: int, user_id: int = None):
        from services.ledger_engine import LedgerEngine
        return LedgerEngine.get(entry_row_id, user_id)

    @staticmethod
    def list(user_id: int, **kwargs) -> list:
        from services.ledger_engine import LedgerEngine
        return LedgerEngine.list(user_id, **kwargs)

    @staticmethod
    def balance(user_id: int, **kwargs) -> dict:
        from services.ledger_engine import LedgerEngine
        return LedgerEngine.balance(user_id, **kwargs)
