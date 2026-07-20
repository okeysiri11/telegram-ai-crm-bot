# BI Reports — daily, weekly, monthly, quarterly, annual, custom with export.

from __future__ import annotations

from events.publisher import publish

from applications.auto_marketplace.analytics.engine import AnalyticsEngine, analytics_engine
from applications.auto_marketplace.business_intelligence.events import BIReportGeneratedEvent
from applications.auto_marketplace.business_intelligence.models import BIReport, ExportFormat, ReportPeriod
from applications.auto_marketplace.kpi.service import KPIService, kpi_service
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class BIReportService:
    _PERIOD_TITLES = {
        ReportPeriod.DAILY: "Daily Business Report",
        ReportPeriod.WEEKLY: "Weekly Business Report",
        ReportPeriod.MONTHLY: "Monthly Business Report",
        ReportPeriod.QUARTERLY: "Quarterly Business Report",
        ReportPeriod.ANNUAL: "Annual Business Report",
        ReportPeriod.CUSTOM: "Custom Business Report",
    }

    def __init__(
        self,
        store: MarketplaceStore | None = None,
        kpi: KPIService | None = None,
        analytics: AnalyticsEngine | None = None,
    ) -> None:
        self._store = store or marketplace_store
        self._kpi = kpi or kpi_service
        self._analytics = analytics or analytics_engine

    async def generate(self, period: ReportPeriod | str = ReportPeriod.DAILY, *, title: str = "") -> BIReport:
        if isinstance(period, str):
            period = ReportPeriod(period)
        report = BIReport(
            title=title or self._PERIOD_TITLES.get(period, "Business Report"),
            period=period,
            sections={
                "kpis": [k.to_dict() for k in self._kpi.compute_all()],
                "analytics": self._analytics.all_analytics(),
            },
            export_urls={
                ExportFormat.PDF.value: f"/reports/{{id}}.pdf",
                ExportFormat.EXCEL.value: f"/reports/{{id}}.xlsx",
                ExportFormat.CSV.value: f"/reports/{{id}}.csv",
            },
        )
        report.export_urls = {k: v.replace("{id}", report.report_id) for k, v in report.export_urls.items()}
        self._store.bi_reports.save(report.report_id, report)
        await publish(BIReportGeneratedEvent(report_id=report.report_id, period=period.value, title=report.title))
        return report

    def get(self, report_id: str) -> BIReport | None:
        return self._store.bi_reports.get(report_id)

    def list_reports(self) -> list[BIReport]:
        return self._store.bi_reports.list_all()

    def export(self, report_id: str, fmt: ExportFormat | str = ExportFormat.PDF) -> dict:
        report = self._store.bi_reports.get(report_id)
        if report is None:
            raise ValueError(f"Report not found: {report_id}")
        if isinstance(fmt, str):
            fmt = ExportFormat(fmt)
        url = report.export_urls.get(fmt.value, "")
        return {"report_id": report_id, "format": fmt.value, "url": url, "sections": report.sections}


bi_report_service = BIReportService()
