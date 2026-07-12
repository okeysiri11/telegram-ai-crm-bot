# Partner Hub — registry, deal assignment, performance analytics.

from config import OWNER_ID


class PartnerEngine:
    @staticmethod
    def can_view(user_id: int) -> bool:
        from database import has_partner_action
        return has_partner_action(user_id, "PARTNER_VIEW")

    @staticmethod
    def can_create(user_id: int) -> bool:
        from database import has_partner_action
        return has_partner_action(user_id, "PARTNER_CREATE")

    @staticmethod
    def can_edit(user_id: int) -> bool:
        from database import has_partner_action
        return has_partner_action(user_id, "PARTNER_EDIT")

    @staticmethod
    def can_assign(user_id: int) -> bool:
        from database import has_partner_action
        return has_partner_action(user_id, "PARTNER_ASSIGN")

    @staticmethod
    def can_analytics(user_id: int) -> bool:
        from database import has_partner_action
        return has_partner_action(user_id, "PARTNER_ANALYTICS")

    @staticmethod
    def create(
        user_id: int,
        partner_type: str,
        company_name: str,
        **kwargs,
    ) -> int:
        if not PartnerEngine.can_create(user_id):
            return 0
        from database import create_partner
        return create_partner(user_id, partner_type, company_name, **kwargs)

    @staticmethod
    def get(partner_id: int, user_id: int = None):
        if user_id is not None and not PartnerEngine.can_view(user_id):
            return None
        from database import get_partner
        return get_partner(partner_id)

    @staticmethod
    def list(user_id: int, **kwargs) -> list:
        if not PartnerEngine.can_view(user_id):
            return []
        from database import list_partners
        return list_partners(**kwargs)

    @staticmethod
    def update(partner_id: int, user_id: int, **fields) -> bool:
        if not PartnerEngine.can_edit(user_id):
            return False
        from database import update_partner
        return update_partner(partner_id, user_id, **fields)

    @staticmethod
    def assign_to_deal(
        partner_id: int,
        deal_id: int,
        user_id: int,
        assignment_role: str = "PARTNER",
        notes: str = None,
    ) -> bool:
        if not PartnerEngine.can_assign(user_id):
            return False
        from database import assign_partner_to_deal
        return assign_partner_to_deal(
            partner_id, deal_id, user_id, assignment_role, notes,
        )

    @staticmethod
    def list_assignments(user_id: int, **kwargs) -> list:
        if not PartnerEngine.can_view(user_id):
            return []
        from database import list_partner_assignments
        return list_partner_assignments(**kwargs)

    @staticmethod
    def list_deals(partner_id: int, user_id: int, limit: int = 50) -> list:
        if not PartnerEngine.can_view(user_id):
            return []
        from database import list_deals_for_partner
        return list_deals_for_partner(partner_id, limit=limit)

    @staticmethod
    def performance(partner_id: int, user_id: int) -> dict:
        if not PartnerEngine.can_analytics(user_id):
            return {}
        from database import get_partner_performance
        return get_partner_performance(partner_id)

    @staticmethod
    def refresh_kpi(partner_id: int, period: str = None) -> int:
        from database import refresh_partner_kpi
        return refresh_partner_kpi(partner_id, period)

    @staticmethod
    def format_card(row: tuple) -> str:
        from database import format_partner_card
        return format_partner_card(row)

    @staticmethod
    def format_analytics(partner_id: int, period: str = None) -> str:
        from database import format_partner_analytics
        return format_partner_analytics(partner_id, period)

    @staticmethod
    def run_integration_test(user_id: int = None) -> dict:
        from database import (
            PARTNER_TYPES,
            cursor,
            create_deal,
            get_partner,
            list_partner_assignments,
            update_deal_status,
        )

        uid = user_id or OWNER_ID
        steps = {}
        try:
            created_ids = {}
            for ptype in PARTNER_TYPES:
                pid = PartnerEngine.create(
                    uid, ptype, f"Test {ptype} Co",
                    contact_person="Integration Test",
                    telegram=f"@{ptype.lower()}_test",
                    telegram_id=uid,
                    phone="+10000000000",
                    email=f"{ptype.lower()}@test.local",
                    rating=4.5,
                    regions=["EU", "MENA"],
                    services=["consulting", "execution"],
                )
                if pid:
                    created_ids[ptype] = pid
            steps["partners_created"] = len(created_ids)
            steps["partner_types"] = list(created_ids.keys())

            broker_id = created_ids.get("BROKER")
            partner = get_partner(broker_id) if broker_id else None
            steps["public_id"] = partner[12] if partner else None

            deal_id = create_deal(
                uid, "LOGISTICS", "SHIPMENT",
                manager_id=uid,
                amount=50000.0,
                currency="USD",
            )
            steps["create_deal"] = deal_id

            assigned = PartnerEngine.assign_to_deal(broker_id, deal_id, uid) if broker_id else False
            steps["assign_deal"] = assigned

            assignments = list_partner_assignments(deal_id=deal_id)
            steps["assignment_count"] = len(assignments)

            update_deal_status(deal_id, uid, "NEGOTIATION")
            update_deal_status(deal_id, uid, "IN_PROGRESS")
            update_deal_status(deal_id, uid, "COMPLETED")

            kpi_id = PartnerEngine.refresh_kpi(broker_id) if broker_id else 0
            steps["kpi_refreshed"] = kpi_id

            perf = PartnerEngine.performance(broker_id, uid) if broker_id else {}
            steps["total_deals"] = perf.get("total_deals", 0)
            steps["completed_deals"] = perf.get("completed_deals", 0)
            steps["total_volume"] = perf.get("total_volume", 0)
            steps["completion_rate"] = perf.get("completion_rate", 0)

            cursor.execute(
                "SELECT COUNT(*) FROM audit_log WHERE module = 'partners'"
            )
            steps["audit_count"] = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM platform_events WHERE event_type IN ('PARTNER_CREATED', 'PARTNER_ASSIGNED')"
            )
            steps["partner_events"] = cursor.fetchone()[0]

            ok = (
                steps["partners_created"] == len(PARTNER_TYPES)
                and set(PARTNER_TYPES).issubset(set(steps["partner_types"]))
                and deal_id > 0
                and assigned
                and steps["assignment_count"] >= 1
                and steps["completed_deals"] >= 1
                and steps["kpi_refreshed"] > 0
                and steps["audit_count"] >= 1
                and steps["partner_events"] >= 2
            )
            return {"ok": ok, "status": "OK" if ok else "ERROR", "steps": steps}
        except Exception as exc:
            return {"ok": False, "status": "ERROR", "steps": steps, "error": str(exc)}
