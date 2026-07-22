# Inspection Engine — Sprint 10.1 vehicle inspection reports.

from __future__ import annotations

from applications.auto_marketplace.foundation.models import InspectionReport, VehicleCondition
from applications.auto_marketplace.shared.exceptions import NotFoundError, ValidationError
from applications.auto_marketplace.shared.store import MarketplaceStore, marketplace_store


class InspectionEngine:
    """Create and retrieve vehicle inspection reports."""

    def __init__(self, store: MarketplaceStore | None = None) -> None:
        self._store = store or marketplace_store

    def create_report(self, report: InspectionReport) -> InspectionReport:
        if not report.vehicle_id:
            raise ValidationError("vehicle_id is required")
        report.passed = report.score >= 60 and report.condition != VehicleCondition.SALVAGE
        return self._store.inspection_reports.save(report.report_id, report)

    def get(self, report_id: str) -> InspectionReport:
        report = self._store.inspection_reports.get(report_id)
        if report is None:
            raise NotFoundError("InspectionReport", report_id)
        return report

    def list_for_vehicle(self, vehicle_id: str) -> list[InspectionReport]:
        return [r for r in self._store.inspection_reports.list_all() if r.vehicle_id == vehicle_id]

    def metrics(self) -> dict:
        return {"inspection_reports": self._store.inspection_reports.count()}


inspection_engine = InspectionEngine()
