# Commission Engine — accruals, approvals, payouts; integrates with Finance Core.

from config import OWNER_ID


class CommissionEngine:
    @staticmethod
    def can_view(user_id: int) -> bool:
        from database import has_commission_action
        return has_commission_action(user_id, "COMMISSION_VIEW")

    @staticmethod
    def can_create(user_id: int) -> bool:
        from database import has_commission_action
        return has_commission_action(user_id, "COMMISSION_CREATE")

    @staticmethod
    def can_approve(user_id: int) -> bool:
        from database import has_commission_action
        return has_commission_action(user_id, "COMMISSION_APPROVE")

    @staticmethod
    def can_pay(user_id: int) -> bool:
        from database import has_commission_action
        return has_commission_action(user_id, "COMMISSION_PAY")

    @staticmethod
    def create_rule(
        user_id: int,
        rule_name: str,
        commission_type: str,
        rate_value: float,
        **kwargs,
    ) -> int:
        if not CommissionEngine.can_create(user_id):
            return 0
        from database import create_commission_rule
        return create_commission_rule(
            user_id, rule_name, commission_type, rate_value, **kwargs,
        )

    @staticmethod
    def list_rules(commission_type: str = None) -> list:
        from database import list_commission_rules
        return list_commission_rules(commission_type=commission_type)

    @staticmethod
    def create(
        user_id: int,
        recipient_id: int,
        recipient_role: str,
        commission_type: str,
        amount: float,
        **kwargs,
    ) -> int:
        if not CommissionEngine.can_create(user_id):
            return 0
        from database import create_commission
        return create_commission(
            user_id, recipient_id, recipient_role, commission_type, amount, **kwargs,
        )

    @staticmethod
    def get(commission_id: int, user_id: int = None):
        if user_id is not None and not CommissionEngine.can_view(user_id):
            return None
        from database import get_commission
        return get_commission(commission_id)

    @staticmethod
    def list(user_id: int, **kwargs) -> list:
        if not CommissionEngine.can_view(user_id):
            return []
        from database import list_commissions
        return list_commissions(**kwargs)

    @staticmethod
    def approve(commission_id: int, user_id: int) -> bool:
        if not CommissionEngine.can_approve(user_id):
            return False
        from database import update_commission_status
        return update_commission_status(commission_id, user_id, "APPROVED")

    @staticmethod
    def cancel(commission_id: int, user_id: int) -> bool:
        if not CommissionEngine.can_approve(user_id):
            return False
        from database import update_commission_status
        return update_commission_status(commission_id, user_id, "CANCELLED")

    @staticmethod
    def pay(commission_id: int, user_id: int, **kwargs) -> int | None:
        if not CommissionEngine.can_pay(user_id):
            return None
        from database import pay_commission
        return pay_commission(commission_id, user_id, **kwargs)

    @staticmethod
    def accrue_for_deal(deal_id: int, user_id: int, recipients: dict = None) -> list[int]:
        if not CommissionEngine.can_create(user_id):
            return []
        from database import accrue_commissions_for_deal
        return accrue_commissions_for_deal(deal_id, user_id, recipients=recipients)

    @staticmethod
    def calculate(base_amount: float, commission_type: str, module: str = None, currency: str = "USD"):
        from database import calculate_commission_amount
        return calculate_commission_amount(base_amount, commission_type, module, currency)

    @staticmethod
    def format_card(row: tuple) -> str:
        from database import format_commission_card
        return format_commission_card(row)

    @staticmethod
    def run_integration_test(user_id: int = None) -> dict:
        from database import (
            COMMISSION_TYPES,
            cursor,
            create_deal,
            get_commission,
            list_commission_rules,
            list_commissions,
            update_deal_status,
            _get_commission_pool_account_id,
            _get_commission_payout_account_id,
            create_finance_transaction,
            update_finance_transaction_status,
            list_finance_transactions,
        )

        uid = user_id or OWNER_ID
        steps = {}
        try:
            rules = list_commission_rules()
            steps["rules_count"] = len(rules)
            steps["rule_types"] = sorted({r[2] for r in rules})

            deal_id = create_deal(
                uid, "FINANCE", "LOAN",
                manager_id=uid,
                partner_id=uid,
                amount=10000.0,
                currency="USD",
            )
            steps["create_deal"] = deal_id
            if not deal_id:
                return {"ok": False, "status": "ERROR", "steps": steps, "error": "create_deal failed"}

            update_deal_status(deal_id, uid, "NEGOTIATION")
            update_deal_status(deal_id, uid, "IN_PROGRESS")
            update_deal_status(deal_id, uid, "COMPLETED")
            accrued = CommissionEngine.accrue_for_deal(
                deal_id, uid,
                recipients={
                    "agent_id": uid,
                    "broker_id": uid,
                    "insurance_id": uid,
                    "referral_id": uid,
                },
            )
            steps["accrual_count"] = len(accrued)
            steps["accrual_types"] = sorted({
                get_commission(cid)[3] for cid in accrued if get_commission(cid)
            })

            all_for_deal = list_commissions(deal_id=deal_id, limit=20)
            steps["total_commissions"] = len(all_for_deal)
            steps["commission_types"] = sorted({row[3] for row in all_for_deal})

            pending = list_commissions(deal_id=deal_id, status="PENDING")
            approved = 0
            for row in pending:
                if CommissionEngine.approve(row[0], uid):
                    approved += 1
            steps["approved_count"] = approved

            pool_id = _get_commission_pool_account_id("USD")
            cash_id = _get_commission_payout_account_id("USD")
            steps["pool_account"] = pool_id
            steps["payout_account"] = cash_id

            if pool_id and cash_id and cash_id != pool_id:
                fund_tx = create_finance_transaction(
                    user_id=uid,
                    transaction_type="INTERNAL_TRANSFER",
                    amount=5000.0,
                    currency="USD",
                    debit_account_id=cash_id,
                    credit_account_id=pool_id,
                    reference_type="COMMISSION",
                    reference_id=deal_id,
                    notes="Commission pool funding for integration test",
                )
                for st in ("PENDING", "APPROVED", "EXECUTING", "COMPLETED"):
                    update_finance_transaction_status(fund_tx, uid, st)
                steps["pool_funded"] = fund_tx

            pay_target = accrued[0] if accrued else (all_for_deal[0][0] if all_for_deal else None)
            tx_id = CommissionEngine.pay(pay_target, uid) if pay_target else None
            steps["pay_tx"] = tx_id

            paid = get_commission(pay_target) if pay_target else None
            steps["paid_status"] = paid[7] if paid else None
            steps["payment_reference"] = paid[9] if paid else None

            cursor.execute(
                "SELECT COUNT(*) FROM commission_payments WHERE commission_id = ?",
                (pay_target,),
            )
            steps["payment_rows"] = cursor.fetchone()[0] if pay_target else 0

            cursor.execute(
                """
                SELECT COUNT(*) FROM audit_log
                WHERE module = 'commissions'
                """
            )
            steps["audit_count"] = cursor.fetchone()[0]

            finance_rows = list_finance_transactions(
                reference_type="COMMISSION", reference_id=pay_target, limit=5,
            )
            steps["finance_commission_tx"] = len(finance_rows)

            cursor.execute(
                """
                SELECT COUNT(*) FROM platform_events
                WHERE event_type = 'FINANCE_COMMISSION_PAID'
                """
            )
            steps["commission_paid_events"] = cursor.fetchone()[0]

            ok = (
                deal_id > 0
                and steps["rules_count"] >= 6
                and set(COMMISSION_TYPES).issubset(set(steps["rule_types"]))
                and steps["total_commissions"] >= 6
                and set(COMMISSION_TYPES).issubset(set(steps["commission_types"]))
                and steps["approved_count"] >= 1
                and tx_id
                and steps["paid_status"] == "PAID"
                and steps["payment_rows"] >= 1
                and steps["finance_commission_tx"] >= 1
                and steps["audit_count"] >= 1
            )
            return {"ok": ok, "status": "OK" if ok else "ERROR", "steps": steps}
        except Exception as exc:
            return {"ok": False, "status": "ERROR", "steps": steps, "error": str(exc)}
