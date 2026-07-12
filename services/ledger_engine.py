# Internal Ledger — accounting state only; no payment execution.

from config import OWNER_ID


class LedgerEngine:
    @staticmethod
    def can_view(user_id: int) -> bool:
        from database import has_ledger_action
        return has_ledger_action(user_id, "LEDGER_VIEW")

    @staticmethod
    def can_create(user_id: int) -> bool:
        from database import has_ledger_action
        return has_ledger_action(user_id, "LEDGER_CREATE")

    @staticmethod
    def can_reverse(user_id: int) -> bool:
        from database import has_ledger_action
        return has_ledger_action(user_id, "LEDGER_REVERSE")

    @staticmethod
    def post(
        user_id: int,
        module: str,
        entry_type: str,
        amount: float,
        **kwargs,
    ) -> int:
        """Record ledger entry — never executes payments."""
        if not LedgerEngine.can_create(user_id):
            return 0
        from database import create_ledger_entry
        return create_ledger_entry(
            user_id, module, entry_type, amount, **kwargs,
        )

    @staticmethod
    def get(entry_row_id: int, user_id: int = None):
        if user_id is not None and not LedgerEngine.can_view(user_id):
            return None
        from database import get_ledger_entry
        return get_ledger_entry(entry_row_id)

    @staticmethod
    def list(user_id: int, **kwargs) -> list:
        if not LedgerEngine.can_view(user_id):
            return []
        from database import list_ledger_entries
        return list_ledger_entries(**kwargs)

    @staticmethod
    def reverse(entry_row_id: int, user_id: int) -> bool:
        if not LedgerEngine.can_reverse(user_id):
            return False
        from database import reverse_ledger_entry
        return reverse_ledger_entry(entry_row_id, user_id)

    @staticmethod
    def balance(user_id: int, **kwargs) -> dict:
        if not LedgerEngine.can_view(user_id):
            return {}
        from database import get_ledger_balance
        return get_ledger_balance(**kwargs)

    @staticmethod
    def summary(user_id: int, module: str = None, currency: str = "USD") -> dict:
        if not LedgerEngine.can_view(user_id):
            return {}
        from database import get_ledger_summary
        return get_ledger_summary(module=module, currency=currency)

    @staticmethod
    def format_card(row: tuple) -> str:
        from database import format_ledger_entry_card
        return format_ledger_entry_card(row)

    @staticmethod
    def run_integration_test(user_id: int = None) -> dict:
        from database import (
            LEDGER_ENTRY_TYPES,
            LEDGER_EXECUTION_ENTRY_TYPES,
            cursor,
            create_deal,
            get_ledger_entry,
            list_ledger_entries,
            update_deal_status,
        )

        uid = user_id or OWNER_ID
        steps = {}
        try:
            deal_id = create_deal(
                uid, "FINANCE", "SETTLEMENT",
                manager_id=uid,
                amount=25000.0,
                currency="USD",
            )
            steps["create_deal"] = deal_id

            posted = {}
            for etype in LEDGER_ENTRY_TYPES:
                if etype in LEDGER_EXECUTION_ENTRY_TYPES:
                    continue
                eid = LedgerEngine.post(
                    uid, "FINANCE", etype, 1000.0,
                    deal_id=deal_id,
                    description=f"Integration test {etype}",
                )
                if eid:
                    posted[etype] = eid
            steps["posted_types"] = list(posted.keys())

            payment_id = LedgerEngine.post(
                uid, "FINANCE", "PAYMENT", 500.0,
                deal_id=deal_id,
                description="Test payment (pending connector)",
            )
            steps["payment_entry"] = payment_id
            payment = get_ledger_entry(payment_id) if payment_id else None
            steps["payment_status"] = payment[8] if payment else None

            import importlib.util
            _spec = importlib.util.spec_from_file_location(
                "bidex_connector", "services/bidex_connector.py",
            )
            _connector_mod = importlib.util.module_from_spec(_spec)
            _spec.loader.exec_module(_connector_mod)
            tx_id = _connector_mod.BidExConnector.execute(payment_id, uid) if payment_id else None
            steps["connector_tx"] = tx_id

            executed = get_ledger_entry(payment_id) if payment_id else None
            steps["executed_status"] = executed[8] if executed else None
            steps["finance_tx_id"] = executed[9] if executed else None

            update_deal_status(deal_id, uid, "NEGOTIATION")
            update_deal_status(deal_id, uid, "IN_PROGRESS")
            update_deal_status(deal_id, uid, "COMPLETED")

            income_rows = list_ledger_entries(deal_id=deal_id, entry_type="INCOME")
            steps["deal_income_entries"] = len(income_rows)

            bal = LedgerEngine.balance(uid, deal_id=deal_id, currency="USD")
            steps["net_balance"] = bal.get("net_balance")
            steps["summary"] = LedgerEngine.summary(uid, module="FINANCE")

            cursor.execute("SELECT COUNT(*) FROM audit_log WHERE module = 'ledger'")
            steps["audit_count"] = cursor.fetchone()[0]

            cursor.execute(
                """
                SELECT COUNT(*) FROM platform_events
                WHERE event_type IN ('LEDGER_ENTRY_CREATED', 'LEDGER_ENTRY_EXECUTED')
                """
            )
            steps["ledger_events"] = cursor.fetchone()[0]

            ok = (
                deal_id > 0
                and len(steps["posted_types"]) >= 3
                and steps["payment_status"] == "PENDING_EXECUTION"
                and tx_id
                and steps["executed_status"] == "EXECUTED"
                and steps["finance_tx_id"]
                and steps["deal_income_entries"] >= 1
                and steps["audit_count"] >= 1
                and steps["ledger_events"] >= 2
            )
            return {"ok": ok, "status": "OK" if ok else "ERROR", "steps": steps}
        except Exception as exc:
            return {"ok": False, "status": "ERROR", "steps": steps, "error": str(exc)}
