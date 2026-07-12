# Commission repository — commission access layer.


class CommissionRepository:
    @staticmethod
    def create(user_id: int, recipient_id: int, recipient_role: str, commission_type: str, amount: float, **kwargs) -> int:
        from services.commission_engine import CommissionEngine
        return CommissionEngine.create(
            user_id, recipient_id, recipient_role, commission_type, amount, **kwargs,
        )

    @staticmethod
    def get(commission_id: int, user_id: int = None):
        from services.commission_engine import CommissionEngine
        return CommissionEngine.get(commission_id, user_id)

    @staticmethod
    def list(user_id: int, **kwargs) -> list:
        from services.commission_engine import CommissionEngine
        return CommissionEngine.list(user_id, **kwargs)

    @staticmethod
    def approve(commission_id: int, user_id: int) -> bool:
        from services.commission_engine import CommissionEngine
        return CommissionEngine.approve(commission_id, user_id)

    @staticmethod
    def pay(commission_id: int, user_id: int, **kwargs) -> int | None:
        from services.commission_engine import CommissionEngine
        return CommissionEngine.pay(commission_id, user_id, **kwargs)

    @staticmethod
    def accrue_for_deal(deal_id: int, user_id: int, recipients: dict = None) -> list[int]:
        from services.commission_engine import CommissionEngine
        return CommissionEngine.accrue_for_deal(deal_id, user_id, recipients=recipients)
