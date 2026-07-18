# Partner repository — data access only (authorization in PartnerEngine).


class PartnerRepository:
    @staticmethod
    def create(user_id: int, partner_type: str, company_name: str, **kwargs) -> int:
        from database import create_partner

        return create_partner(user_id, partner_type, company_name, **kwargs)

    @staticmethod
    def get(partner_id: int, user_id: int = None):
        from database import get_partner

        return get_partner(partner_id)

    @staticmethod
    def list(user_id: int, **kwargs) -> list:
        from database import list_partners

        return list_partners(**kwargs)

    @staticmethod
    def assign_to_deal(partner_id: int, deal_id: int, user_id: int, **kwargs) -> bool:
        from database import assign_partner_to_deal

        assignment_role = kwargs.pop("assignment_role", "PARTNER")
        notes = kwargs.pop("notes", None)
        return assign_partner_to_deal(partner_id, deal_id, user_id, assignment_role, notes)

    @staticmethod
    def performance(partner_id: int, user_id: int) -> dict:
        from database import get_partner_performance

        return get_partner_performance(partner_id)
