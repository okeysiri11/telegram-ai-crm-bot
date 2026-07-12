# Deal repository — universal deal access layer.


class DealRepository:
    @staticmethod
    def create(user_id: int, module: str, deal_type: str, **kwargs) -> int:
        from services.deal_engine import DealEngine
        return DealEngine.create(user_id, module, deal_type, **kwargs)

    @staticmethod
    def get(deal_id: int, user_id: int = None):
        from services.deal_engine import DealEngine
        return DealEngine.get(deal_id, user_id)

    @staticmethod
    def list(user_id: int, **kwargs) -> list:
        from services.deal_engine import DealEngine
        return DealEngine.list(user_id, **kwargs)

    @staticmethod
    def transition(deal_id: int, user_id: int, status: str) -> bool:
        from services.deal_engine import DealEngine
        return DealEngine.transition(deal_id, user_id, status)
