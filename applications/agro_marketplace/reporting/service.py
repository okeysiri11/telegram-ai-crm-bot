# BI reporting — structured analytical reports.

from __future__ import annotations

from events.publisher import publish

from applications.agro_marketplace.analytics.events import ExecutiveReportCreatedEvent
from applications.agro_marketplace.analytics.models import BIReport
from applications.agro_marketplace.shared.exceptions import NotFoundError
from applications.agro_marketplace.shared.store import AgroStore, agro_store


class ReportingService:
    def __init__(self, store: AgroStore | None = None) -> None:
        self._store = store or agro_store

    def create(self, report: BIReport) -> BIReport:
        return self._store.bi_reports.save(report.report_id, report)

    def get(self, report_id: str) -> BIReport:
        report = self._store.bi_reports.get(report_id)
        if report is None:
            raise NotFoundError("BIReport", report_id)
        return report

    def list_reports(self, *, report_type: str | None = None) -> list[BIReport]:
        items = self._store.bi_reports.list_all()
        if report_type:
            items = [r for r in items if r.report_type == report_type]
        return sorted(items, key=lambda r: r.created_at, reverse=True)

    async def publish_executive(self, report: BIReport) -> BIReport:
        report.report_type = "executive"
        saved = self.create(report)
        await publish(
            ExecutiveReportCreatedEvent(report_id=saved.report_id, title=saved.title)
        )
        return saved


reporting_service = ReportingService()
