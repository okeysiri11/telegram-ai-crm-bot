# Partner repository — partner access layer.


class PartnerRepository:
    @staticmethod
    def create(user_id: int, partner_type: str, company_name: str, **kwargs) -> int:
        from services.partner_engine import PartnerEngine
        return PartnerEngine.create(user_id, partner_type, company_name, **kwargs)

    @staticmethod
    def get(partner_id: int, user_id: int = None):
        from services.partner_engine import PartnerEngine
        return PartnerEngine.get(partner_id, user_id)

    @staticmethod
    def list(user_id: int, **kwargs) -> list:
        from services.partner_engine import PartnerEngine
        return PartnerEngine.list(user_id, **kwargs)

    @staticmethod
    def assign_to_deal(partner_id: int, deal_id: int, user_id: int, **kwargs) -> bool:
        from services.partner_engine import PartnerEngine
        return PartnerEngine.assign_to_deal(partner_id, deal_id, user_id, **kwargs)

    @staticmethod
    def performance(partner_id: int, user_id: int) -> dict:
        from services.partner_engine import PartnerEngine
        return PartnerEngine.performance(partner_id, user_id)
