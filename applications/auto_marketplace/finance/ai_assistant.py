# Finance AI assistant — document generation, analysis, anomaly detection.

from __future__ import annotations

import logging
from typing import Any

from applications.auto_marketplace.finance.models import Contract, Document, FinanceInvoice, FinancePayment

logger = logging.getLogger(__name__)


class FinanceAIAssistant:
    @staticmethod
    async def generate_document_content(template_content: str, variables: dict[str, Any]) -> str:
        content = template_content
        for key, value in variables.items():
            content = content.replace(f"{{{{{key}}}}}", str(value))
        try:
            from platform_reasoning import reasoning_engine
            from platform_reasoning.models import ReasoningContext

            result = await reasoning_engine.reason(
                ReasoningContext(
                    request="Generate legal document content",
                    metadata={"template": template_content[:500], "variables": variables},
                )
            )
            if hasattr(result, "conclusion") and isinstance(result.conclusion, dict):
                return result.conclusion.get("content", content)
        except Exception:
            logger.debug("reasoning engine unavailable for document generation")
        return content

    @staticmethod
    async def analyze_contract(contract: Contract) -> dict[str, Any]:
        risks: list[str] = []
        if contract.amount > 100000:
            risks.append("high_value_transaction")
        if not contract.terms.get("warranty"):
            risks.append("missing_warranty_clause")
        try:
            from platform_reasoning import reasoning_engine
            from platform_reasoning.models import ReasoningContext

            result = await reasoning_engine.reason(
                ReasoningContext(
                    request="Analyze contract risk",
                    metadata={"contract": contract.to_dict()},
                )
            )
            if hasattr(result, "conclusion") and isinstance(result.conclusion, dict):
                risks.extend(result.conclusion.get("risks", []))
        except Exception:
            pass
        risk_level = "high" if len(risks) >= 2 else "medium" if risks else "low"
        return {"contract_id": contract.contract_id, "risk_level": risk_level, "risks": risks}

    @staticmethod
    async def detect_payment_anomaly(payment: FinancePayment, history: list[dict]) -> dict[str, Any]:
        anomaly = False
        reasons: list[str] = []
        if payment.amount > 150000:
            anomaly = True
            reasons.append("unusually_high_amount")
        avg = sum(h.get("amount", 0) for h in history) / max(len(history), 1)
        if history and payment.amount > avg * 3:
            anomaly = True
            reasons.append("deviation_from_average")
        return {"payment_id": payment.payment_id, "anomaly": anomaly, "reasons": reasons}

    @staticmethod
    async def financial_summary(invoices: list[FinanceInvoice], payments: list[FinancePayment]) -> dict[str, Any]:
        total_invoiced = sum(i.total_amount for i in invoices)
        total_paid = sum(p.amount for p in payments if p.status == "completed")
        return {
            "total_invoiced": round(total_invoiced, 2),
            "total_paid": round(total_paid, 2),
            "outstanding": round(total_invoiced - total_paid, 2),
            "invoice_count": len(invoices),
            "payment_count": len(payments),
        }

    @staticmethod
    async def classify_document(document: Document) -> str:
        title = document.title.lower()
        content = document.content.lower()
        if "purchase" in title or "purchase" in content:
            return "purchase_agreement"
        if "invoice" in title:
            return "invoice"
        if "receipt" in title:
            return "receipt"
        if "trade" in title or "trade-in" in content:
            return "trade_in"
        return document.category or "general"


finance_ai_assistant = FinanceAIAssistant()
