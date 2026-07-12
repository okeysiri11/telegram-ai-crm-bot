# BidEx Connector — executes actual payments via Finance Core.
# Ledger records accounting intent; this module performs payment execution.

from config import OWNER_ID


class BidExConnector:
    """Bridge between Internal Ledger and BIDEX Financial Core."""

    _ACCOUNT_MAP = {
        "COMMISSION": ("COMMISSION", "CASH"),
        "PAYMENT": ("CASH", "BANK"),
        "WITHDRAW": ("CASH", "BANK"),
        "REFUND": ("BANK", "CASH"),
    }

    _FINANCE_TYPE_MAP = {
        "COMMISSION": "COMMISSION",
        "PAYMENT": "EXPENSE",
        "WITHDRAW": "EXPENSE",
        "REFUND": "REFUND",
    }

    @staticmethod
    def can_execute(user_id: int) -> bool:
        from database import has_finance_action
        return has_finance_action(user_id, "FINANCE_EXECUTE")

    @staticmethod
    def _resolve_account(account_type: str, currency: str = "USD") -> int | None:
        from database import cursor
        cursor.execute(
            """
            SELECT id FROM finance_accounts
            WHERE account_type = ? AND currency = ? AND status = 'ACTIVE'
            ORDER BY id ASC
            LIMIT 1
            """,
            (account_type.upper(), currency.upper()),
        )
        row = cursor.fetchone()
        return row[0] if row else None

    @staticmethod
    def execute(entry_row_id: int, user_id: int) -> int | None:
        """Execute a PENDING_EXECUTION ledger entry via Finance Core."""
        if not BidExConnector.can_execute(user_id):
            return None

        from database import (
            LEDGER_EXECUTION_ENTRY_TYPES,
            get_ledger_entry,
            mark_ledger_executed,
            create_finance_transaction,
            update_finance_transaction_status,
        )

        entry = get_ledger_entry(entry_row_id)
        if not entry:
            return None
        (
            _rid, entry_id, deal_id, module, entry_type, amount, currency,
            description, status, _finance_tx_id, _created_by, _created_at,
        ) = entry

        if entry_type not in LEDGER_EXECUTION_ENTRY_TYPES:
            return None
        if status != "PENDING_EXECUTION":
            return None

        debit_type, credit_type = BidExConnector._ACCOUNT_MAP.get(
            entry_type, ("CASH", "BANK"),
        )
        debit_id = BidExConnector._resolve_account(debit_type, currency)
        credit_id = BidExConnector._resolve_account(credit_type, currency)
        if not debit_id or not credit_id:
            return None

        finance_type = BidExConnector._FINANCE_TYPE_MAP.get(entry_type, "EXPENSE")
        tx_id = create_finance_transaction(
            user_id=user_id,
            transaction_type=finance_type,
            amount=amount,
            currency=currency,
            debit_account_id=debit_id,
            credit_account_id=credit_id,
            reference_type="LEDGER",
            reference_id=entry_row_id,
            notes=f"BidEx Connector: {entry_id} {entry_type} — {description or ''}",
            status="CREATED",
        )
        if not tx_id:
            return None

        for step in ("PENDING", "APPROVED", "EXECUTING", "COMPLETED"):
            if not update_finance_transaction_status(tx_id, user_id, step):
                break

        mark_ledger_executed(entry_row_id, user_id, tx_id)
        return tx_id

    @staticmethod
    def execute_pending(user_id: int, limit: int = 10) -> list[int]:
        """Execute all pending ledger entries (batch connector run)."""
        from database import list_ledger_entries
        executed = []
        for row in list_ledger_entries(status="PENDING_EXECUTION", limit=limit):
            tx_id = BidExConnector.execute(row[0], user_id)
            if tx_id:
                executed.append(tx_id)
        return executed

    @staticmethod
    def run_integration_test(user_id: int = None) -> dict:
        uid = user_id or OWNER_ID
        steps = {}
        try:
            from database import get_ledger_entry
            from services.ledger_engine import LedgerEngine

            entry_id = LedgerEngine.post(
                uid, "FINANCE", "WITHDRAW", 250.0,
                description="BidEx Connector integration test",
            )
            steps["ledger_entry"] = entry_id
            entry = get_ledger_entry(entry_id) if entry_id else None
            steps["initial_status"] = entry[8] if entry else None

            tx_id = BidExConnector.execute(entry_id, uid) if entry_id else None
            steps["finance_tx"] = tx_id

            entry_after = get_ledger_entry(entry_id) if entry_id else None
            steps["final_status"] = entry_after[8] if entry_after else None

            ok = (
                entry_id > 0
                and steps["initial_status"] == "PENDING_EXECUTION"
                and tx_id
                and steps["final_status"] == "EXECUTED"
            )
            return {"ok": ok, "status": "OK" if ok else "ERROR", "steps": steps}
        except Exception as exc:
            return {"ok": False, "status": "ERROR", "steps": steps, "error": str(exc)}
