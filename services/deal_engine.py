# Universal Deal Engine — shared deal lifecycle across verticals.

from config import OWNER_ID


class DealEngine:
    @staticmethod
    def can_view(user_id: int) -> bool:
        from database import has_deal_action
        return has_deal_action(user_id, "DEAL_VIEW")

    @staticmethod
    def can_create(user_id: int) -> bool:
        from database import has_deal_action
        return has_deal_action(user_id, "DEAL_CREATE")

    @staticmethod
    def can_edit(user_id: int) -> bool:
        from database import has_deal_action
        return has_deal_action(user_id, "DEAL_EDIT")

    @staticmethod
    def create(
        user_id: int,
        module: str,
        deal_type: str,
        **kwargs,
    ) -> int:
        if not DealEngine.can_create(user_id):
            return 0
        from database import create_deal
        return create_deal(user_id, module, deal_type, **kwargs)

    @staticmethod
    def get(deal_id: int, user_id: int = None):
        if user_id is not None and not DealEngine.can_view(user_id):
            return None
        from database import get_deal
        return get_deal(deal_id)

    @staticmethod
    def list(user_id: int, module: str = None, status: str = None, limit: int = 50) -> list:
        if not DealEngine.can_view(user_id):
            return []
        from database import list_deals, has_deal_action
        if has_deal_action(user_id, "DEAL_APPROVE"):
            return list_deals(module=module, status=status, limit=limit)
        return list_deals(
            module=module, status=status, manager_id=user_id, limit=limit,
        )

    @staticmethod
    def update(deal_id: int, user_id: int, **fields) -> bool:
        if not DealEngine.can_edit(user_id):
            return False
        from database import update_deal_fields
        return update_deal_fields(deal_id, user_id, **fields)

    @staticmethod
    def transition(deal_id: int, user_id: int, new_status: str) -> bool:
        from database import has_deal_action, update_deal_status
        if new_status == "COMPLETED" and not has_deal_action(user_id, "DEAL_APPROVE"):
            if not has_deal_action(user_id, "DEAL_EDIT"):
                return False
        elif not has_deal_action(user_id, "DEAL_EDIT"):
            return False
        ok = update_deal_status(deal_id, user_id, new_status)
        return ok

    @staticmethod
    def get_extension(deal_id: int, module: str) -> dict | None:
        from database import get_deal_extension
        return get_deal_extension(deal_id, module)

    @staticmethod
    def set_extension(deal_id: int, module: str, data: dict) -> bool:
        from database import upsert_deal_extension
        return upsert_deal_extension(deal_id, module, data)

    @staticmethod
    def sync_from_agro(agro_deal_id: int, user_id: int) -> int:
        from database import sync_universal_deal_from_agro
        return sync_universal_deal_from_agro(agro_deal_id, user_id)

    @staticmethod
    def format_card(deal_row: tuple) -> str:
        from database import format_deal_card
        return format_deal_card(deal_row)

    @staticmethod
    def run_integration_test(user_id: int = None) -> dict:
        from database import (
            cursor, get_deal, get_deal_extension, list_deals, log_audit,
        )

        uid = user_id or OWNER_ID
        steps = {}
        try:
            deal_id = DealEngine.create(
                uid, "AUTO", "SALE",
                customer_id=uid,
                amount=25000,
                currency="USD",
                extension={"vehicle_model": "Test SUV", "vin": "TEST123"},
            )
            steps["create_auto"] = deal_id

            legal_id = DealEngine.create(
                uid, "LEGAL", "CASE",
                extension={"case_number": "LC-001", "court_name": "Test Court"},
            )
            steps["create_legal"] = legal_id

            ok_neg = DealEngine.transition(deal_id, uid, "NEGOTIATION")
            ok_prog = DealEngine.transition(deal_id, uid, "IN_PROGRESS")
            ok_done = DealEngine.transition(deal_id, uid, "COMPLETED")
            steps["transitions"] = [ok_neg, ok_prog, ok_done]

            ext = get_deal_extension(deal_id, "AUTO")
            steps["extension"] = ext.get("vehicle_model") if ext else None

            deal = get_deal(deal_id)
            steps["final_status"] = deal[3] if deal else None
            steps["public_id"] = deal[12] if deal else None

            cursor.execute(
                "SELECT COUNT(*) FROM audit_log WHERE module = 'deals'"
            )
            steps["audit_count"] = cursor.fetchone()[0]
            steps["total_deals"] = len(list_deals(limit=100))

            ok = (
                deal_id > 0
                and legal_id > 0
                and all(steps["transitions"])
                and steps["final_status"] == "COMPLETED"
                and steps["audit_count"] >= 1
            )
            return {"ok": ok, "status": "OK" if ok else "ERROR", "steps": steps}
        except Exception as exc:
            return {"ok": False, "status": "ERROR", "steps": steps, "error": str(exc)}
