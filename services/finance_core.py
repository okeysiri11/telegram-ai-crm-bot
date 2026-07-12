# BIDEX Financial Core Phase 1 — accounts & transactions engine.

from config import OWNER_ID


class FinanceCoreService:
    @staticmethod
    def create_account(
        user_id: int,
        account_name: str,
        account_type: str = "CASH",
        currency: str = "USD",
        balance: float = 0,
    ) -> int:
        from services.finance_auth import FinanceAuthService
        if not FinanceAuthService.can_create(user_id):
            return 0
        from database import create_finance_account
        return create_finance_account(
            user_id, account_name, account_type, currency, balance,
        )

    @staticmethod
    def get_account(account_id: int, user_id: int):
        from services.finance_auth import FinanceAuthService
        if not FinanceAuthService.can_view(user_id):
            return None
        from database import get_finance_account
        return get_finance_account(account_id)

    @staticmethod
    def list_accounts(user_id: int, status: str = None, limit: int = 50) -> list:
        from services.finance_auth import FinanceAuthService
        if not FinanceAuthService.can_view(user_id):
            return []
        from database import list_finance_accounts
        return list_finance_accounts(status=status, limit=limit)

    @staticmethod
    def create_transaction(
        user_id: int,
        transaction_type: str,
        amount: float,
        currency: str = "USD",
        debit_account_id: int = None,
        credit_account_id: int = None,
        reference_type: str = None,
        reference_id: int = None,
        notes: str = None,
    ) -> int:
        from services.finance_auth import FinanceAuthService
        if not FinanceAuthService.can_create(user_id):
            return 0
        from database import create_finance_transaction
        return create_finance_transaction(
            user_id=user_id,
            transaction_type=transaction_type,
            amount=amount,
            currency=currency,
            debit_account_id=debit_account_id,
            credit_account_id=credit_account_id,
            reference_type=reference_type,
            reference_id=reference_id,
            notes=notes,
            status="CREATED",
        )

    @staticmethod
    def get_transaction(transaction_id: int, user_id: int):
        from services.finance_auth import FinanceAuthService
        if not FinanceAuthService.can_view(user_id):
            return None
        from database import get_finance_transaction
        return get_finance_transaction(transaction_id)

    @staticmethod
    def update_transaction_status(
        transaction_id: int,
        user_id: int,
        new_status: str,
    ) -> bool:
        from services.finance_auth import FinanceAuthService
        from database import get_finance_transaction

        tx = get_finance_transaction(transaction_id)
        if not tx:
            return False

        target = new_status.strip().upper()
        if target in ("APPROVED", "DISPUTED") and not FinanceAuthService.can_approve(user_id):
            return False
        if target in ("EXECUTING", "COMPLETED") and not FinanceAuthService.can_execute(user_id):
            return False
        if target in ("PENDING", "CANCELLED", "CREATED") and not FinanceAuthService.can_create(user_id):
            if not FinanceAuthService.can_approve(user_id):
                return False

        from database import update_finance_transaction_status
        return update_finance_transaction_status(transaction_id, user_id, target)

    @staticmethod
    def run_integration_test(user_id: int = None) -> dict:
        """Verify account creation, transaction flow, status change, audit_log."""
        from database import (
            cursor,
            create_finance_account,
            create_finance_transaction,
            update_finance_transaction_status,
            get_finance_transaction,
            get_finance_account,
            list_finance_accounts,
        )

        uid = user_id or OWNER_ID
        steps = {}
        try:
            accounts = list_finance_accounts(limit=5)
            if not accounts:
                return {"ok": False, "status": "ERROR", "steps": steps, "error": "no seed accounts"}

            debit_id = accounts[0][0]
            credit_id = accounts[1][0] if len(accounts) > 1 else accounts[0][0]

            acc_id = create_finance_account(
                uid, "[TEST] BIDEX Finance Account", "PARTNER", "USD", 0,
            )
            steps["create_account"] = acc_id
            if not acc_id:
                return {"ok": False, "status": "ERROR", "steps": steps, "error": "create_account failed"}

            tx_id = create_finance_transaction(
                user_id=uid,
                transaction_type="INTERNAL_TRANSFER",
                amount=100.0,
                currency="USD",
                debit_account_id=debit_id,
                credit_account_id=credit_id,
                reference_type="TEST",
                reference_id=acc_id,
                notes="BIDEX Financial Core integration test",
            )
            steps["create_transaction"] = tx_id
            if not tx_id:
                return {"ok": False, "status": "ERROR", "steps": steps, "error": "create_transaction failed"}

            flow = ["PENDING", "APPROVED", "EXECUTING", "COMPLETED"]
            status_ok = True
            for st in flow:
                ok = update_finance_transaction_status(tx_id, uid, st)
                steps[f"status_{st.lower()}"] = ok
                if not ok:
                    status_ok = False
                    break

            tx = get_finance_transaction(tx_id)
            steps["final_status"] = tx[6] if tx else None

            cursor.execute(
                """
                SELECT COUNT(*) FROM audit_log
                WHERE module = 'finance'
                  AND action IN (
                      'finance_account_create',
                      'finance_transaction_create',
                      'finance_transaction_status'
                  )
                """
            )
            audit_count = cursor.fetchone()[0]
            steps["audit_log_entries"] = audit_count

            debit_after = get_finance_account(debit_id)
            credit_after = get_finance_account(credit_id)
            steps["debit_balance"] = debit_after[4] if debit_after else None
            steps["credit_balance"] = credit_after[4] if credit_after else None

            ok = (
                acc_id > 0
                and tx_id > 0
                and status_ok
                and tx and tx[6] == "COMPLETED"
                and audit_count >= 3
            )
            return {
                "ok": ok,
                "status": "OK" if ok else "ERROR",
                "steps": steps,
            }
        except Exception as exc:
            return {"ok": False, "status": "ERROR", "steps": steps, "error": str(exc)}
