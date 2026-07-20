# Financial reports.

from __future__ import annotations

import time

from applications.auto_marketplace.finance.ai_assistant import FinanceAIAssistant, finance_ai_assistant
from applications.auto_marketplace.finance.models import FinancialReport
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class ReportService:
    def __init__(self, store: MarketplaceStore | None = None, ai: FinanceAIAssistant | None = None) -> None:
        self._store = store or marketplace_store
        self._ai = ai or finance_ai_assistant

    async def generate_summary(self, *, period_days: int = 30) -> FinancialReport:
        now = time.time()
        period_start = now - period_days * 86400
        invoices = self._store.finance_invoices.list_all()
        payments = self._store.finance_payments.list_all()
        summary = await self._ai.financial_summary(invoices, payments)
        report = FinancialReport(
            report_type="summary",
            period_start=period_start,
            period_end=now,
            metrics={
                **summary,
                "contracts_signed": len([c for c in self._store.contracts.list_all() if c.signed_at]),
                "settlements_pending": len(
                    [s for s in self._store.dealer_settlements.list_all() if s.status.value == "pending"]
                ),
            },
        )
        return self._store.financial_reports.save(report.report_id, report)

    def get(self, report_id: str) -> FinancialReport | None:
        return self._store.financial_reports.get(report_id)

    def list_reports(self) -> list[FinancialReport]:
        return self._store.financial_reports.list_all()


report_service = ReportService()
