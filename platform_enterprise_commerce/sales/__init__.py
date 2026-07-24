"""Sales Engine — Sprint 22.7."""

from __future__ import annotations

from typing import Any
import time

from platform_enterprise_commerce.models import LINE_KINDS, PAYMENT_METHODS, PAYMENT_MODES


class SalesEngine:
    def sell(
        self,
        *,
        lines: list[dict[str, Any]],
        payments: list[dict[str, Any]],
        customer_id: str = "",
        mode: str = "full",
        industry: str = "beauty",
    ) -> dict[str, Any]:
        if not lines:
            raise ValueError("sale requires at least one line")
        if mode not in PAYMENT_MODES:
            raise ValueError(f"unknown payment mode: {mode}")
        started = time.perf_counter()
        total = 0.0
        normalized = []
        for line in lines:
            kind = line.get("kind", "service")
            if kind not in LINE_KINDS:
                raise ValueError(f"unknown line kind: {kind}")
            qty = float(line.get("qty", 1) or 1)
            price = float(line.get("price", 0) or 0)
            amount = qty * price
            total += amount
            normalized.append({**line, "kind": kind, "qty": qty, "price": price, "amount": amount})
        paid = 0.0
        pay_rows = []
        for p in payments or []:
            method = p.get("method", "cash")
            if method not in PAYMENT_METHODS:
                raise ValueError(f"unknown payment method: {method}")
            amount = float(p.get("amount", 0) or 0)
            paid += amount
            pay_rows.append({"method": method, "amount": amount})
        if mode == "full" and abs(paid - total) > 0.01 and paid < total:
            raise ValueError("full payment requires covering total")
        if mode == "partial" and paid <= 0:
            raise ValueError("partial payment requires amount > 0")
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return {
            "lines": normalized,
            "payments": pay_rows,
            "total": round(total, 2),
            "paid": round(paid, 2),
            "balance": round(total - paid, 2),
            "mode": mode,
            "customer_id": customer_id or None,
            "industry": industry,
            "status": "completed" if paid >= total else "open",
            "mixed_payment": len({p["method"] for p in pay_rows}) > 1,
            "elapsed_ms": elapsed_ms,
            "under_20s": elapsed_ms < 20000,
            "finance_ref": "enterprise_finance",
            "refundable": True,
        }

    def refund(self, sale: dict[str, Any], *, amount: float | None = None) -> dict[str, Any]:
        refund_amount = float(amount if amount is not None else sale.get("paid", 0))
        if refund_amount <= 0:
            raise ValueError("refund amount must be positive")
        if refund_amount > float(sale.get("paid", 0)):
            raise ValueError("refund exceeds paid amount")
        return {
            "sale_id": sale.get("sale_id"),
            "refund_amount": round(refund_amount, 2),
            "status": "refunded",
            "finance_ref": "enterprise_finance",
        }
